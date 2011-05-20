from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from email.utils import parsedate
from models import Event
from datetime import datetime
import gdata
import logging
import os

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

GDATA_TOKEN = "1/k6mv81Oi9C9QfiRtfTl-TYDRADKetfBrE9EE1cSPGhc"
GCAL_ID = "mindcandy.com_kfnhda4e3d0v7dinf08340u2hk@group.calendar.google.com"

class IncomingEventHandler(InboundMailHandler):
    def __init__(self):
        self.calendar_client = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(self.calendar_client)
        self.calendar_client.SetAuthSubToken(GDATA_TOKEN)
            
    def receive(self, mail_message):
        logging.debug("Received a message from: " + mail_message.sender)
        logging.debug("Date: " + mail_message.date)
        
        plaintext_bodies = mail_message.bodies('text/plain').next()
        event_message = "%s : %s" % (mail_message.subject, plaintext_bodies[1].decode())
        # event = Event(sender=mail_message.sender,
        #                      sent=datetime(*parsedate(mail_message.date)[0:6]),
        #                      message=event_message)
        #         
        #         event_entry = gdata.calendar.CalendarEventEntry()
        #         event_entry.title = atom.Title(text=event.title)
        #         event_entry.content = atom.Content(text=event.description)
        #         start_time = '%s.000Z' % event.time.isoformat()
        #         event_entry.when.append(gdata.calendar.When(start_time=start_time))
        #         event_entry.where.append(
        #          gdata.calendar.Where(value_string=event.location))
                                     
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