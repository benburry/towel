#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from models import Event
import gdata
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
        
def main():
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.WARN)

    application = webapp.WSGIApplication([
                                            (r'/$', MainHandler),
                                         ], debug=DEBUG)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
