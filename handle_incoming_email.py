from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from email.utils import parsedate
from models import Event
from datetime import datetime
import logging
import os

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

class IncomingEventHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.debug("Received a message from: " + mail_message.sender)
        logging.debug("Date: " + mail_message.date)

        plaintext_bodies = mail_message.bodies('text/plain').next()
        event_message = "%s : %s" % (mail_message.subject, plaintext_bodies[1].decode())
        event = Event(sender=mail_message.sender,
                     sent=datetime(*parsedate(mail_message.date)[0:6]),
                     message=event_message)
        event.put()
        
        memcache.delete("homepage")

def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            IncomingEventHandler.mapping(),
                                         ], debug=DEBUG)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()