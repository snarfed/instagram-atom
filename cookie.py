"""Fetch www.instagram.com with a cookie and convert it to Atom.
"""

import logging
import re
import urllib
import urllib2

import appengine_config
from granary import atom, instagram
import webapp2
from oauth_dropins.webutil import util


class CookieHandler(webapp2.RequestHandler):

  def get(self):
    cookie = 'sessionid=%s' % urllib.quote(util.get_required_param(self, 'sessionid'))
    logging.info('Fetching with Cookie: %s', cookie)
    resp = urllib2.urlopen(urllib2.Request(
      'https://www.instagram.com/',
      headers={'Cookie': cookie}),
      timeout=60)
    body = resp.read().decode('utf-8')
    logging.info('Response: %s', resp.getcode())

    if resp.getcode() != 200 or 'not-logged-in' in body:
      return self.abort(401, "Couldn't log into Instagram with cookie %s" % cookie)

    ig = instagram.Instagram()
    activities, viewer = ig.html_to_activities(body)
    if viewer:
      logging.info('Logged in as %s (%s)',
                   viewer.get('username'), viewer.get('displayName'))
    else:
      logging.warning("Couldn't determine Instagram user!")

    title = 'instagram-atom feed for %s' % ig.actor_name(viewer)
    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(atom.activities_to_atom(
      activities, viewer, title=title, host_url=self.request.host_url + '/',
      request_url=self.request.path_url))


application = webapp2.WSGIApplication(
  [('/cookie', CookieHandler),
   ], debug=False)

