#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import users
from models import Event
import gdata.alt.appengine
import gdata.calendar
import gdata.calendar.service
import gdata.gauth
import os
import logging

DEBUG = os.getenv('SERVER_SOFTWARE').split('/')[0] == "Development" if os.getenv('SERVER_SOFTWARE') else False

class MainHandler(webapp.RequestHandler):
    def get(self):                        
        page = memcache.get("homepage")
        if page is None:
            events = Event.all().order("-sent").fetch(1000)
            path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
            page = template.render(path, {"events": events,})
            memcache.add("homepage", page)
        self.response.out.write(page)
        
class AuthHandler(webapp.RequestHandler):
    def __init__(self):
        self.calendar_client = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(self.calendar_client)
        
    def get(self):
        auth_token = gdata.auth.extract_auth_sub_token_from_url(self.request.uri)
        if auth_token:
            session_token = self.calendar_client.upgrade_to_session_token(auth_token)
            if session_token and users.get_current_user():
                new_style_token = gdata.gauth.AuthSubToken(session_token.get_token_string(), ['http://calendar.google.com/feeds/'])
                gdata.gauth.ae_save(new_style_token, users.get_current_user().user_id())
        self.redirect('/')
        
def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            (r'/$', MainHandler),
                                            (r'/auth$', AuthHandler)
                                         ], debug=DEBUG)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
