#pauls-hangman
utilising startup code from udactiy full stack ND project 4.

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
 Deploy your application.



##Game Description:
Hangman is a word guessing game. Each game begins with a random 'target'
word at the specified length, and a maximum number of
'attempts'. 'Guesses' are sent to the `make_move` endpoint which will reply
with game state information, including JSON indicating either: wrong guess,
correct guess, you win, or game over (if the maximum
number of attempts is reached).
Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

A game is scores points based on the number of remaining attempts when a puzzle
is solved. Difficulty can be increased by reducing the number of attempts.
Consistent high performance over a number of games is reflected in a sliding
global rank score, which allows players to be ranked across multiple games, and
reflects varying difficulty settings. The global rank rewards higher difficulty
settings. 

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 - gamefunc.py: for generating target words from a list of the 10 000 most common english words.
 - dictionary.dat: A list of the 10 000 most common english words.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will
    raise a ConflictException if a User with that user_name already exists.

- **del_game**
  - Path: 'del_game'
  - Method: POST
  - Parameters: urlsafe_game_key
  - Returns: Message confirming deletion of game
  - Description: Deletes a game in progress. Will
  raise a ForbiddenException if attempting to delete a completed game, and will
  raise a NotFoundException if attempting to delete a game that does not exist.

 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, max_tries, word_size
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. max_tries determines
    how many incorrect guesses are available before game ends. This also impacts
    the global rankings caluclations. A higher max tries, means a lower ranking
    score. word_size determines the length of the target word. Word length also
    impacts the ranking score of the game. the longer the word, the more ranking
    points. Also adds a task to a task queue to update the average moves
    remaining for active games. Throws NotFoundException if the user name is not
    valid, throws BadRequestException if there are no words available to match
    word length in dictionary.dat


   - **get_game**
      - Path: 'game/{urlsafe_game_key}'
      - Method: GET
      - Parameters: urlsafe_game_key
      - Returns: GameForm with current game state.
      - Description: Returns the current state of a game.

  - **get_game_history**
     - Path: 'game/history/{urlsafe_game_key}'
     - Method: GET
     - Parameters: urlsafe_game_key
     - Returns: a list of all game operations performed.
     - Description: Returns all the manipulations on the game state since the game
    was started, including attempts and success of attempts.


   - **make_move**
      - Path: 'game/{urlsafe_game_key}'
      - Method: PUT
      - Parameters: urlsafe_game_key, guess
      - Returns: GameForm with new game state.
      - Description: Accepts a 'guess' and returns the updated state of the game.
      If this causes a game to end, a corresponding Score entity will be created.

   - **get_scores**
      - Path: 'scores'
      - Method: GET
      - Parameters: None
      - Returns: ScoreForms.
      - Description: Returns all Scores in the database (unordered).

   - **get_user_scores**
      - Path: 'scores/user/{user_name}'
      - Method: GET
      - Parameters: user_name
      - Returns: ScoreForms.
      - Description: Returns all Scores recorded by the provided player (unordered).
      Will raise a NotFoundException if the User does not exist.

  - **get_user_games**
     - Path: 'games/user/{user_name}'
     - Method: GET
     - Parameters: user_name
     - Returns: All GameForms for the user.  
     - Description: Returns all Games recorded by the provided player (unordered).
     Will raise a NotFoundException if the User does not exist.

  - **get_user_rankings**
    - Path: 'get_user_rankings'
    - Method: GET
    - Parameters: None.
    - Returns: An ordered list of player rankings.  
    - Description: Returns all users with completed games, ranked by average
    historical score.

  - **get_leader_board**
    - Path: 'get_leader_board'
    - Method: POST
    - Parameters: Number of results
    - Returns: An ordered list of all games.  
    - Description: Returns all games, ranked by points scored in this single game.
    differs from user rankings, because it ignores historical games, or users
    history.

   - **get_active_game_count**
      - Path: 'games/active'
      - Method: GET
      - Parameters: None
      - Returns: StringMessage
      - Description: Gets the average number of attempts remaining for all games
      from a previously cached memcache key.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.

 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.

 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **UserRank**
    - Representation of a users global rank compared to all players. (username,
      ranking score)
- **GameHistory**
   - Representation of all moves taken by a player during a game (move_history)  

  # Utility Forms:
 - **ScoreForms**
  - Multiple ScoreForm container.
- **UserGames**
   - Multiple UserGame container.
- **UserRankings**
  - Multiple UserRank container.
 - **StringMessage**
    - General purpose String container.
