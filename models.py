"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

################################################################################
    ### Tracking user details.  ###
################################################################################
class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    ranking_score = ndb.IntegerProperty(required=True, default=0)
    completed_games = ndb.IntegerProperty(required=True, default=0)


    @classmethod
    def to_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         won=self.won,
                         date=str(self.date),
                         guesses=self.guesses,
                         points=self.points)

    def to_rank_form(self):
        return UserRank(user_name=self.name,
                        ranking_score=self.ranking_score)


################################################################################
    ### Tracking Games ###
################################################################################
class Game(ndb.Model):
    """Game object"""
    game_word = ndb.StringProperty(required=True)
    max_tries = ndb.IntegerProperty(required=True)
    tries_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_deleted = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    current_guesses = ndb.StringProperty(repeated=True)
    move_history = ndb.StringProperty(repeated=True)

    @classmethod
    def new_game(cls, user, game_word, attempts):
        """Creates and returns a new game"""
        game = Game(user=user,
                    game_word=game_word,
                    max_tries=attempts,
                    tries_remaining=attempts,
                    game_over=False,
                    move_history=[])
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.tries_remaining = self.tries_remaining
        form.game_over = self.game_over
        form.message = message
        form.game_deleted = self.game_deleted
        return form

    def to_history_form(self):
        """ returns all moves in a game """
        form = GameHistory()
        form.move_history = str(self.move_history)
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()

        # Add the game to the score 'board'
        # Count the length of the target word, multiply it by the number of
        # guesses that remain (demonstrated skill). Reduce points for a large
        # number of max tries (reflect difficulty setting a game was played at.)
        points = int(float((len(self.game_word) * self.tries_remaining))
                                                               / self.max_tries)

        score = Score(user=self.user,
                      date=date.today(),
                      won=won,
                      wrong_guesses=self.max_tries - self.tries_remaining,
                      points=points)
        score.put()
        self._update_ranking()
        return

    def _update_ranking(self):
        """ Updates the ranking value associated the user"""
        # DB calls, this operation relies on two seperate kinds.
        player = User.query(User.key == self.user).get()
        scores = Score.query(Score.user == self.user)

        # Take this game into account when ranking:
        player.completed_games = player.completed_games + 1
        # Collect All Scores. calculate average score:
        total_score = 0
        for score in scores:
            total_score = total_score + score.points
            total_score = float(total_score) / player.completed_games

        # Write average score to User datastore.
        #write updated rank to user Datastore, sort ranks on retrieval.
        player.ranking_score = int(total_score)
        player.put()
        return

################################################################################
    ### Define ranking and scoring ###
################################################################################

class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    wrong_guesses = ndb.IntegerProperty(required=True)
    points = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         won=self.won,
                         date=str(self.date),
                         guesses=self.wrong_guesses,
                         points=self.points)

################################################################################
    ### Define IO Messages###
################################################################################
class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    tries_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)
    game_deleted = messages.BooleanField(6, required=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    word_size = messages.IntegerField(2, default=5)
    attempts = messages.IntegerField(4, default=5)

class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)
    points = messages.IntegerField(5, required=True)

class UserRank(messages.Message):
    """UserRank for outbound ranking information """
    user_name = messages.StringField(1, required=True)
    ranking_score = messages.IntegerField(2, required=True)

class GameHistory(messages.Message):
    move_history = messages.StringField(1, required=True)

################################################################################
    ### Meta-Form Messages###
################################################################################

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class UserGames(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class UserRankings(messages.Message):
    """Return multiple UserRanks"""
    items = messages.MessageField(UserRank, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
