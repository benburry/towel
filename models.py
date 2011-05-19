__author__ = 'ben'

from google.appengine.ext import db

class Event(db.Model):
    sender = db.StringProperty(required=True)
    sent = db.DateTimeProperty(required=True, indexed=True)
    created = db.DateTimeProperty(auto_now_add=True)
    message = db.TextProperty(required=True)
    event = db.LinkProperty()
    