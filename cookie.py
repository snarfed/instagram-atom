"""Fetch www.instagram.com with a cookie and convert it to Atom.
"""

import datetime
import logging
import re
import urllib
import urllib2

import appengine_config
from granary import atom, instagram, source
from oauth_dropins.webutil import handlers, util
import webapp2
from webob import exc

CACHE_EXPIRATION = datetime.timedelta(minutes=10)


class CookieHandler(handlers.ModernHandler):
  handle_exception = handlers.handle_exception

  @handlers.memcache_response(CACHE_EXPIRATION)
  def get(self):
    cookie = 'sessionid=%s' % urllib.quote(
      util.get_required_param(self, 'sessionid').encode('utf-8'))
    logging.info('Fetching with Cookie: %s', cookie)

    ig = instagram.Instagram()
    try:
      resp = ig.get_activities_response(group_id=source.FRIENDS, scrape=True,
                                        cookie=cookie)
    except Exception as e:
      status, text = util.interpret_http_exception(e)
      if status:
        self.response.status = 502 if status == 500 else status
      elif util.is_connection_failure(e):
        self.response.status = 504  # HTTP 504 Gateway Timeout
      else:
        logging.exception('oops!')
        self.response.status = 500

      if isinstance(text, str):
        text = text.decode('utf-8')
      self.response.text = text or u'Unknown error.'
      return

    actor = resp.get('actor')
    if actor:
      logging.info('Logged in as %s (%s)',
                   actor.get('username'), actor.get('displayName'))
    else:
      logging.warning("Couldn't determine Instagram user!")

    title = 'instagram-atom feed for %s' % ig.actor_name(actor)
    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(atom.activities_to_atom(
      resp.get('items', []), actor, title=title, host_url=self.request.host_url + '/',
      request_url=self.request.path_url, xml_base='https://www.instagram.com/'))


application = webapp2.WSGIApplication(
  [('/cookie', CookieHandler),
   ], debug=False)

