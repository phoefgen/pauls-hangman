'''The file provides utility functions for the operation of the game.'''
import random
import sys

def rand_english_word(length):
    """takes the length of a desired word, and returns a dictionary word of
    that length 0 indexed. Word is represented as a list of characters."""

    potential_word = []
    # run through a dictionary, return a random words of the defined length.
    with open('dictionary.dat') as f:
        wordlist = f.readlines()
        for word in wordlist:
            if len(word) == length + 1:
                potential_word.append(word)
    # count how many words meet the criteria, and use that in the range when
    # generating a random int, then make sure the game settings match the data:
    word_number = len(potential_word)
    try:
        word = potential_word[random.randint(1,word_number-1)]
    except ValueError as e:
        print 'Game Config Error: No words of specified length in word list'
        sys.exit(1)

    # verified word, convert to list of chars and del the newline:
    word = potential_word[random.randint(1,word_number)]
    # debug:
    return word
