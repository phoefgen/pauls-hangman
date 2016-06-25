#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import PaulsHangmanApi
from models import Game

from models import User


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        # from the list off all users with email addresses, generate a list of
        # all players with incomplete games:
        contactable_users = []
        for user in users:
            game_search = Game.query(Game.user == user.key,
                                     Game.game_over == False)
            if len(game_search.fetch()) > 0:
                contactable_users.append(user)

        # Spam users with incomplete games.
        for user in contactable_users:
                subject = 'You have incomplete Hangman games!!'
                body = ('Hello {}, stop what your doing and finish your game'
                                                             ).format(user.name)

                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                                                                   user.email,
                                                                   subject,
                                                                   body)

class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        PaulsHangmanApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
