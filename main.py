"""An App Engine app that provides "private" Atom feeds for your Instagram news
feed, ie photos from people you follow.
"""

__author__ = 'Ryan Barrett <instagram-atom@ryanb.org>'

import json
import logging
import os
import urllib2

from activitystreams import appengine_config
from activitystreams import atom
from activitystreams import instagram
from activitystreams.oauth_dropins import instagram as oauth_instagram
from activitystreams.oauth_dropins.webutil import handlers
from activitystreams.oauth_dropins.webutil import util
import webapp2

from google.appengine.ext.webapp import template


class CallbackHandler(oauth_instagram.CallbackHandler):
  def finish(self, auth_entity, state=None):
    """Gets an access token based on an auth code."""
    atom_url = '%s/atom?access_token=%s' % (
      self.request.host_url, auth_entity.access_token())
    logging.info('generated feed URL: %s', atom_url)
    self.response.out.write(template.render(
        os.path.join(os.path.dirname(__file__), 'templates', 'generated.html'),
        {'atom_url': atom_url}))


def actor_name(actor):
  return actor.get('displayName') or actor.get('username') or 'you'


class AtomHandler(webapp2.RequestHandler):
  """Proxies the Atom feed for a Instagram user's stream.

  Authenticates to the Instagram API with the user's stored OAuth credentials.
  """
  handle_exception = handlers.handle_exception

  def get(self):
    host_url = self.request.host_url + "/"
    ig = instagram.Instagram(access_token=util.get_required_param(self, 'access_token'))
    activities = ig.get_activities(count=50)
    actor = ig.get_actor()
    title = 'instagram-atom feed for %s' % ig.actor_name(actor)

    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(atom.activities_to_atom(
        activities, actor, title=title,
        host_url=host_url, request_url=self.request.path_url))


application = webapp2.WSGIApplication(
  [('/generate', oauth_instagram.StartHandler.to('/instagram/oauth_callback')),
   ('/instagram/oauth_callback', CallbackHandler),
   ('/atom', AtomHandler),
   ], debug=appengine_config.DEBUG)
