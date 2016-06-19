#!/usr/bin/env python
# Local implementation of hangman game to aid in API design.

import gamefunc
import sys

# Game Settings:
WORD_SIZE = 6
MAX_TRIES = 5
DEAD = '''
 ___________.._______
| .__________))______|
| | / /      ||
| |/ /       ||
| | /        ||.-''.
| |/         |/  _  \
| |          ||  `/,|
| |          (\\`_.'
| |         .-`--'.
| |        /Y . . Y\
| |       // |   | \\
| |      //  | . |  \\
| |     ')   |   |   (`
| |          ||'||
| |          || ||
| |          || ||
| |          || ||
| |         / | | \
""""""""""|_`-' `-' |"""|
|"|"""""""\ \       '"|"|
| |        \ \        | |
: :         \ \       : :  sk
. .          `'       . .

'''

class hangman():
    def __init__(self):
        '''Create a game'''
        self.game_word = gamefunc.rand_english_word(WORD_SIZE)
        self.max_tries = MAX_TRIES
        self.num_guesses = 0
        self.completed_letters = self._guess_status()

    def _guess_status(self, completed_letters=[]):
        if completed_letters == []:
            for i in range(WORD_SIZE):
                completed_letters.append('_')
        return completed_letters

    def make_guess(self):
        '''Accept a character, sanitize.'''
        # check that only one character is entered, and numbers are rejected:
        letter = 'aa'
        while len(letter) > 1:
            letter = raw_input('Enter your guess: ')
            if len(letter) >= 2:
                print "only 1 character allowed"
            if letter[0] in '1234567890':
                print 'Numbers not valid.'
                letter = 'aa'
        return letter

    def _verify_guess(self, guess):
        # check to see if guess is in game word.
        if guess in self.game_word:
            location = self.game_word.index(guess)
            self.completed_letters[location] = guess
            return True
        else:
            return False

    def play(self):
        game = hangman()
        print "Welcome to Paul's Hangman!\n"
        print "A word has been generated, its {} characters long.\
                                                             ".format(WORD_SIZE)
        wrong_guesses = 0
        while wrong_guesses < self.max_tries:
            print "current status of word:"
            print self.completed_letters
            print 'Guess a letter!'
            guess = self.make_guess()
            if self._verify_guess(guess):
                print 'Correct Guess!'
                if '_' not in self.completed_letters:
                    print 'Game over! You Win!'
                    sys.exit(0)
            else:
                print 'Incorrect Guess!'
                wrong_guesses += 1
        print DEAD
        print "Max Tries Exceeded, you lose."


if __name__ == '__main__':
    # Fire the gameloop:
    hangman.play(hangman())
