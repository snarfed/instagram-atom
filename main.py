"""Fetch www.instagram.com with a cookie and convert it to Atom.
"""
import datetime
import logging
import re
import urllib.parse

from flask import Flask, render_template, request
from flask.views import View
from flask_caching import Cache
import flask_gae_static
from granary import atom, instagram, microformats2, source
from oauth_dropins.webutil import appengine_config, appengine_info, flask_util, util

CACHE_EXPIRATION = datetime.timedelta(minutes=10)

# See https://www.cloudimage.io/
IMAGE_PROXY_URL_BASE = 'https://aujtzahimq.cloudimg.io/v7/'
# https://dash.cloudflare.com/dcc4dadb279e9e9e69e9e84ec82d9303/workers/view/caching-proxy
VIDEO_PROXY_URL_BASE = 'https://caching-proxy.snarfed.workers.dev/'

# Flask app
app = Flask('instagram-atom')
app.template_folder = './templates'
app.config.from_mapping(
    ENV='development' if appengine_info.DEBUG else 'production',
    CACHE_TYPE='SimpleCache',
    SECRET_KEY=util.read('flask_secret_key'),
)
app.after_request(flask_util.default_modern_headers)
app.register_error_handler(Exception, flask_util.handle_exception)
flask_gae_static.init_app(app)
app.wsgi_app = flask_util.ndb_context_middleware(
    app.wsgi_app, client=appengine_config.ndb_client)

cache = Cache(app)


@app.route('/cookie')
@flask_util.cached(cache, CACHE_EXPIRATION)
def feed():
  cookie = 'sessionid=%s' % urllib.parse.quote(
    request.args['sessionid'].encode('utf-8'))
  logging.info('Fetching with Cookie: %s', cookie)

  ig = instagram.Instagram()
  try:
    resp = ig.get_activities_response(group_id=source.FRIENDS, scrape=True,
                                      cookie=cookie)
  except Exception as e:
    status, text = util.interpret_http_exception(e)
    if status in ('403',):
      data = atom.activities_to_atom([{
        'object': {
          'url': request.url,
          'content': 'Your instagram-atom cookie isn\'t working. <a href="%s">Click here to regenerate your feed!</a>' % request.host_url,
        },
      }], {}, title='instagram-atom', host_url=request.host_url, request_url=request.url)
      return data, {'Content-Type': 'application/atom+xml'}
    elif status == '401':
      # IG returns 401 sometimes as a form of rate limiting or bot detection
      return 'Sorry, Instagram is rate limiting us', 429
    elif status:
      return text, status
    else:
      logging.exception('oops!')
      return '', 500

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
  format = request.args.get('format') or 'atom'
  if format == 'atom':
    title = 'instagram-atom feed for %s' % ig.actor_name(actor)
    return atom.activities_to_atom(
      activities, actor, title=title, host_url=request.host_url,
      request_url=request.url, xml_base='https://www.instagram.com/',
    ), {'Content-Type': 'application/atom+xml'}

  elif format == 'html':
    return microformats2.activities_to_html(activities)
  else:
    flask_util.error(f'format must be either atom or html; got {format}')

