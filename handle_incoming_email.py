from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from google.appengine.api import mail
from google.appengine.api import users
from email.utils import parsedate
from models import Event
from datetime import datetime
import time
import traceback
import gdata.alt.appengine
import gdata.calendar
import gdata.calendar.service
import gdata.gauth
import atom
import logging
import os

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

#GDATA_TOKEN = "1/k6mv81Oi9C9QfiRtfTl-TYDRADKetfBrE9EE1cSPGhc"
GCAL_ID = "mindcandy.com_kfnhda4e3d0v7dinf08340u2hk@group.calendar.google.com"

class IncomingEventHandler(InboundMailHandler):
    def __init__(self):
        self.calendar_client = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(self.calendar_client)
        #self.calendar_client.SetAuthSubToken(GDATA_TOKEN)
            
    def receive(self, mail_message):
        session_key = gdata.gauth.ae_load(users.get_current_user().user_id())
        logging.debug("Session key: %s" % session_key.token_string)
        if not session_key: return self.authenticate(mail_message)
        
        self.calendar_client.SetAuthSubToken(session_key.token_string)
        
        logging.debug("Received a message from: " + mail_message.sender)
        logging.debug("Message received date: " + mail_message.date)        
        # logging.debug("time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()): " + time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()))
        
        plaintext_bodies = mail_message.bodies('text/plain').next()
        
        event_time = time.mktime(parsedate(mail_message.date))
        # logging.debug("time.mktime(email.utils.parsedate('%s')): %s" % (mail_message.date, event_time))
        
        try:
            event = Event(sender=mail_message.sender,
                             sent=datetime.utcfromtimestamp(event_time),
                             subject=mail_message.subject,
                             message=plaintext_bodies[1].decode())
                
            event_entry = gdata.calendar.CalendarEventEntry()
            event_entry.title = atom.Title(text=event.subject)
            event_entry.content = atom.Content(text=event.message)
            start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(event_time))
            # logging.debug("time.strftime('%%Y-%%m-%%dT%%H:%%M:%%S.000Z', time.gmtime('%s')): %s" % (event_time, start_time))
            logging.debug("GCal start time: " + start_time)
       
            event_entry.when.append(gdata.calendar.When(start_time=start_time))
        
            cal_event = self.calendar_client.InsertEvent(event_entry, 
                                    'http://www.google.com/calendar/feeds/%s/private/full' % GCAL_ID)
            alternate_link = cal_event.GetHtmlLink()
            logging.debug("Created gcal event at " + alternate_link.href)
            if alternate_link and alternate_link.href:
                event.event_url = alternate_link.href
            
            event.put()
            memcache.delete("homepage")
        
        except Exception, ex:
            logging.exception("Unable to store event:\n %s" % traceback.format_exc())
            request_error = ex[0]
            if request_error['status'] == 401 or request_error['status'] == 403:
                self.authenticate(mail_message)
                return
            else:
                mail.send_mail(sender=mail_message.to,
                                to=mail_message.sender,
                                subject="Re: %s" % mail_message.subject,
                                body="ERROR: We were unable to store your event:\n %s" % traceback.format_exc())
                
        else:
            mail.send_mail(sender=mail_message.to,
                            to=mail_message.sender,
                            subject="Re: %s" % mail_message.subject,
                            body="Your event has been stored: %s" % event.event_url)

    def authenticate(self, mail_message):
        auth_url = gdata.gauth.generate_auth_sub_url('https://mc-towel.appspot.com/auth', 'http://www.google.com/calendar/feeds/', secure=False, session=True, domain='mindcandy.com')
        logging.debug("Generated auth_url " + str(auth_url))
        mail.send_mail(sender=mail_message.to,
                        to=mail_message.sender,
                        subject="Re: %s" % mail_message.subject,
                        body="ERROR: Please visit this url for authorization:\n %s" % auth_url)
def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            IncomingEventHandler.mapping(),
                                         ], debug=DEBUG)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
