"""Fetch www.instagram.com with a cookie and convert it to Atom.
"""
import datetime
import logging
import re
import urllib.parse

from granary import atom, instagram, microformats2, source
from oauth_dropins.webutil import appengine_info, appengine_config, handlers, util
import webapp2

CACHE_EXPIRATION = datetime.timedelta(minutes=10)

# See https://www.cloudimage.io/
IMAGE_PROXY_URL_BASE = 'https://aujtzahimq.cloudimg.io/v7/'
# https://dash.cloudflare.com/dcc4dadb279e9e9e69e9e84ec82d9303/workers/view/caching-proxy
VIDEO_PROXY_URL_BASE = 'https://caching-proxy.snarfed.workers.dev/'


class CookieHandler(handlers.ModernHandler):
  handle_exception = handlers.handle_exception

  @handlers.cache_response(CACHE_EXPIRATION)
  def get(self):
    cookie = 'sessionid=%s' % urllib.parse.quote(
      util.get_required_param(self, 'sessionid').encode('utf-8'))
    logging.info('Fetching with Cookie: %s', cookie)

    host_url = self.request.host_url + '/'
    ig = instagram.Instagram()
    try:
      resp = ig.get_activities_response(group_id=source.FRIENDS, scrape=True,
                                        cookie=cookie)
    except Exception as e:
      status, text = util.interpret_http_exception(e)
      if status in ('403',):
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.response.out.write(atom.activities_to_atom([{
          'object': {
            'url': self.request.url,
            'content': 'Your instagram-atom cookie isn\'t working. <a href="%s">Click here to regenerate your feed!</a>' % host_url,
            },
          }], {}, title='instagram-atom', host_url=host_url,
          request_url=self.request.path_url))
        return
      elif status == '401':
        # IG returns 401 sometimes as a form of rate limiting or bot detection
        self.response.status = '429'
      elif status:
        self.response.status = status
      else:
        logging.exception('oops!')
        self.response.status = 500

      self.response.text = text or 'Unknown error.'
      return

    actor = resp.get('actor')
    if actor:
      logging.info('Logged in as %s (%s)',
                   actor.get('username'), actor.get('displayName'))
    else:
      logging.warning("Couldn't determine Instagram user!")

    activities = resp.get('items', [])

    # Pass images and videos through caching proxy to cache them
    for a in activities:
      microformats2.prefix_image_urls(a, IMAGE_PROXY_URL_BASE)
      microformats2.prefix_video_urls(a, VIDEO_PROXY_URL_BASE)

    # Generate output
    format = self.request.get('format', 'atom')
    if format == 'atom':
      title = 'instagram-atom feed for %s' % ig.actor_name(actor)
      self.response.headers['Content-Type'] = 'application/atom+xml'
      self.response.out.write(atom.activities_to_atom(
        activities, actor, title=title, host_url=host_url,
        request_url=self.request.path_url, xml_base='https://www.instagram.com/'))
    elif format == 'html':
      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(microformats2.activities_to_html(activities))
    else:
      self.abort(400, 'format must be either atom or html; got %s' % format)


application = webapp2.WSGIApplication([
  ('/cookie', CookieHandler),
], debug=appengine_info.DEBUG)

