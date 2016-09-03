"""An App Engine app that provides "private" Atom feeds for your Instagram news
feed, ie photos from people you follow.
"""

__author__ = 'Ryan Barrett <instagram-atom@ryanb.org>'

import json
import logging
import os
import urllib2

from granary import appengine_config
from granary import atom
from granary import instagram
from oauth_dropins import instagram as oauth_instagram
from oauth_dropins.webutil import handlers
from oauth_dropins.webutil import util
import webapp2

from google.appengine.ext.webapp import template


def actor_name(actor):
  return actor.get('displayName') or actor.get('username') or 'you'


class AtomHandler(handlers.ModernHandler):
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

    # switchover warning
    activities.append({
      'verb': 'post',
      'published': '2016-01-19T00:00:00',
      'id': 'tag:instagram-atom.appspot.com,2016:0',
      'url': 'https://instagram-atom.appspot.com/',
      'title': 'ATTENTION: Please update your instagram-atom feed!',
      'actor': {
        'displayName': 'Ryan Barrett',
        'id': 'https://snarfed.org/',
        'url': 'https://snarfed.org/',
      },
      'object': {
        'id': 'tag:instagram-atom.appspot.com,2016:0',
        'published': '2016-01-19T00:00:00',
        'content': """
<div style="color: red; font-style: italic;">
  <p><b>Hi! Thanks for using instagram-atom. Instagram is
  <a href="http://developers.instagram.com/post/133424514006/instagram-platform-update">changing their API</a>
  in June 2016 and blocking the part we use.  Don't worry, we've adapted, but
  you'll need to update your feed. Please
  <a href="https://instagram-atom.appspot.com/">click here to generate a new one</a>.
  Apologies for the inconvenience!</b></p>
</div>""",
      },
    })

    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(atom.activities_to_atom(
        activities, actor, title=title,
        host_url=host_url, request_url=self.request.path_url))


application = webapp2.WSGIApplication(
  [('/atom', AtomHandler),
   ], debug=appengine_config.DEBUG)
