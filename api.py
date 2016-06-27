# -*- coding: utf-8 -*-`
"""This API allows access to game logic for an implementation of Hangman"""

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import (User,
                    Game,
                    Score)
from models import (StringMessage,
                    NewGameForm,
                    GameForm,
                    MakeMoveForm,
                    ScoreForms,
                    UserGames,
                    UserRankings,
                    GameHistory)
from utils import get_by_urlsafe
from gamefunc import rand_english_word

################################################################################
    ### GAE Resource Containers: ###
################################################################################
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
DEL_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
GET_GAME_HISTORY = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
USER_GAMES = endpoints.ResourceContainer(UserGames)
LEADERBOARD = endpoints.ResourceContainer(
                                     number_of_results=messages.IntegerField(1))
MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='paulshangman', version='v1')
class PaulsHangmanApi(remote.Service):
    """Game API"""


################################################################################
    ### User Management Methods ###
################################################################################

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        if not request.email:
            raise endpoints.BadRequestException(
                    'No email address supplied.')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=UserGames,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key).filter(
                                                        Game.game_over == False,
                                                     Game.game_deleted == False)
        return UserGames(items=[game.to_form('Active Game.') for game in games])

################################################################################
    ### Game Management Methods ###
################################################################################
    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game_word = rand_english_word(request.word_size)
        except ValueError:
            raise endpoints.BadRequestException('No target words of requested '
                                                'length available!')

        # Input has been validated, generating game object.
        game = Game.new_game(user.key, game_word, request.attempts)

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Pauls Hangman!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_deleted:
                raise endpoints.ForbiddenException ('game has been deleted')
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_HISTORY,
                      response_message=GameHistory,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return the historical game moves."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_history_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=DEL_GAME_REQUEST,
                      response_message=GameForm,
                      path='del_game/{urlsafe_game_key}',
                      name='del_game',
                      http_method='PUT')
    def del_game(self, request):
        """Delete a game in progress from the DB."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if not game.game_over:
                game.game_deleted = True
                game.game_over = True
                game.put()
                return game.to_form('Game Deleted')
            else:
                raise endpoints.ForbiddenException(
                                                'Cannot delete completed games')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""

        # check pre-existing game state:
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            raise endpoints.ForbiddenException(
                                        'Illegal action: Game is already over.')
        if game.game_deleted:
            raise endpoints.ForbiddenException(
                                        'Illegal action: Game is deleted.')
        if not request.guess.isalpha():
            raise endpoints.ForbiddenException(
                                        'Illegal action: Only a-z allowed')

        # init completness tracker on first valid guess:
        if game.current_guesses == []:
            completed_letters = []  # init success tracking
            for i in game.game_word:
                completed_letters.append('_')
            game.current_guesses = completed_letters[:-1] # remove newline char

        ## Track all moves in the datastore:
        # process new moves:
        move_outcome = 'Correct Guess: False'
        if request.guess == game.game_word or request.guess in game.game_word:
            move_outcome = 'Correct Guess: True'
        move = '(Player Guess: {0} {1})'.format(request.guess, move_outcome)
        game.move_history.append(move)

        # process a correct guess.
        if not request.guess == game.game_word and request.guess in game.game_word:
            # check each letter against each position, update completness
            # tracking in the current_guesses list:
            if request.guess == game.game_word[:-1]:
                game.current_guesses = ['winner']
            else:
                for char in game.game_word:
                    count = 0
                    while count < len(game.current_guesses):
                        if request.guess == game.game_word[count]:
                            game.current_guesses[count] = request.guess
                        count += 1
            msg = 'correct guess! {}'.format(game.current_guesses)

        # process a failed request
        else:
            # update game progress:
            game.tries_remaining -= 1
            msg = 'Wrong guess, {} tries remaining'.format(game.tries_remaining)

        # handle end game state.
        if game.tries_remaining < 1:
            game.end_game(False)
            game.move_history.append('Failed to guess word, Game Over!')
            game.put()
            return game.to_form(msg + ' Game over!')

        # As the game progresses, the _ are removed from the current_guesses
        # list. The absence of an _ indicates a final guess was succesful.
        if '_' not in game.current_guesses:
            game.end_game(True)
            msg = '{msg} You win, the word was {solution}'.format(
                                                        msg=msg,
                                                        solution=game.game_word)
        game.put()
        return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

################################################################################
    ### Game Ranking Methods ###
################################################################################
    @endpoints.method(request_message=LEADERBOARD,
                      response_message=ScoreForms,
                      path='leader_board',
                      name='leader_board',
                      http_method='POST')
    def leader_board(self, request):
        """Return a leaderboard. A complete game with more tries_remaining ranks
           higher than a complete game with less tries remaining. A correct
           guess does not reduce tries_remaining."""

        # Catch no games finished:
        scores = Score.query(Score.won == True).order(-Score.points)
        if not scores:
            raise endpoints.NotFoundException(
                    'No Games exist.')
        # Optionally limit results to passed in param.
        scores = scores.fetch(limit=request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_tries_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @endpoints.method(response_message=UserRankings,
                      path='get_user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def ranking(self, request):
        """Return a global ranking. User ranking is updated at the end of each
           game"""
        # Return all users who have a completed_games, in order of ranking.
        rankings = User.query().order(-User.ranking_score)
        return UserRankings(
                        items=[rank.to_rank_form() for rank in rankings])

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_tries_remaining = sum([game.tries_remaining
                                        for game in games])
            average = float(total_tries_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))

api = endpoints.api_server([PaulsHangmanApi])
