"""Unit tests for main.py."""
import copy
import unittest

from granary.tests.test_instagram import (
    HTML_ACTIVITIES_FULL_V2,
    HTML_FEED_V2,
)
from granary.instagram import Instagram
from oauth_dropins.webutil import testutil, util
from oauth_dropins.webutil.appengine_config import ndb_client
from oauth_dropins.webutil.util import json_dumps, json_loads
import requests

from main import app, Feed

ATOM = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xml:lang="en-US"
      xmlns="http://www.w3.org/2005/Atom"
      xmlns:activity="http://activitystrea.ms/spec/1.0/"
      xmlns:georss="http://www.georss.org/georss"
      xmlns:ostatus="http://ostatus.org/schema/1.0"
      xmlns:thr="http://purl.org/syndication/thread/1.0"
      xml:base="https://www.instagram.com/">
<generator uri="https://granary.io/">granary</generator>
<id>http://localhost/</id>
<title>instagram-atom feed for Unknown</title>


<updated>2016-01-17T20:46:33+00:00</updated>
<author>
 <activity:object-type>http://activitystrea.ms/schema/1.0/person</activity:object-type>
 <uri></uri>
 
 
</author>

<link rel="alternate" href="http://localhost/" type="text/html" />


<link rel="self" href="http://localhost/feed/get?token=towkin" type="application/atom+xml" />



<entry>


<author>
 <activity:object-type>http://activitystrea.ms/schema/1.0/person</activity:object-type>
 <uri>https://www.instagram.com/jc/</uri>
 
 <name>Jerry C</name>
 
 
</author>

  
    <activity:object-type>http://activitystrea.ms/schema/1.0/photo</activity:object-type>
  

  
  <id>tag:instagram.com:123_456</id>
  <title>Elvis hits out of RCA Studio B</title>

  

  <content type="xhtml">
  <div xmlns="http://www.w3.org/1999/xhtml">



  


Elvis hits out of RCA Studio B
<p>
<a class="link" href="https://www.instagram.com/p/ABC123/">
<img class="u-photo" src="https://aujtzahimq.cloudimg.io/v7/https://scontent-sjc2-1.cdninstagram.com/hphotos-xfp1/t51.2885-15/e35/12545499_1662965520652470_1466520818_n.jpg" alt="" />
</a>
</p>
<p>  <span class="p-location h-card">
    <data class="p-uid" value="tag:instagram.com:345924646"></data>
    <a class="p-name u-url" href="https://instagram.com/explore/locations/345924646/">RCA Studio B</a>
    
    
  </span>
</p>

  </div>
  </content>

  <link rel="alternate" type="text/html" href="https://www.instagram.com/p/ABC123/" />
  <link rel="ostatus:conversation" href="https://www.instagram.com/p/ABC123/" />
  
  
    <activity:verb>http://activitystrea.ms/schema/1.0/post</activity:verb>
  
  
  <published>2016-01-17T20:46:33+00:00</published>
  <updated>2016-01-17T20:46:33+00:00</updated>
  
  
  
    <georss:point>38.2 -121.1</georss:point>
  
  
    <georss:featureName>RCA Studio B</georss:featureName>
  

  <link rel="self" type="application/atom+xml" href="https://www.instagram.com/p/ABC123/" />

  
    
      <link rel="enclosure" href="https://aujtzahimq.cloudimg.io/v7/https://scontent-sjc2-1.cdninstagram.com/hphotos-xfp1/t51.2885-15/e35/12545499_1662965520652470_1466520818_n.jpg" type="image/jpeg" />
    
  
</entry>

<entry>


<author>
 <activity:object-type>http://activitystrea.ms/schema/1.0/person</activity:object-type>
 <uri>https://www.instagram.com/jc/</uri>
 
 <name>Jerry C</name>
 
 
</author>

  
    <activity:object-type>http://activitystrea.ms/schema/1.0/video</activity:object-type>
  

  
  <id>tag:instagram.com:789_456</id>
  <title>Eye of deer 👁 and #selfie from me</title>

  

  <content type="xhtml">
  <div xmlns="http://www.w3.org/1999/xhtml">



  


Eye of deer 👁 and #selfie from me
<p><video class="u-video" src="https://caching-proxy.snarfed.workers.dev/https://scontent-sjc2-1.cdninstagram.com/hphotos-xtp1/t50.2886-16/12604073_746855092124622_46574942_n.mp4" controls="controls" poster="https://aujtzahimq.cloudimg.io/v7/https://scontent-sjc2-1.cdninstagram.com/hphotos-xpf1/t51.2885-15/s750x750/sh0.08/e35/12424348_567037233461060_1986731502_n.jpg">Your browser does not support the video tag. <a href="https://caching-proxy.snarfed.workers.dev/https://scontent-sjc2-1.cdninstagram.com/hphotos-xtp1/t50.2886-16/12604073_746855092124622_46574942_n.mp4">Click here to view directly. <img src="https://aujtzahimq.cloudimg.io/v7/https://scontent-sjc2-1.cdninstagram.com/hphotos-xpf1/t51.2885-15/s750x750/sh0.08/e35/12424348_567037233461060_1986731502_n.jpg" /></a></video>
</p>

  </div>
  </content>

  <link rel="alternate" type="text/html" href="https://www.instagram.com/p/XYZ789/" />
  <link rel="ostatus:conversation" href="https://www.instagram.com/p/XYZ789/" />
  
    
      <link rel="ostatus:attention" href="https://www.instagram.com/ap/" />
      <link rel="mentioned" href="https://www.instagram.com/ap/" />
      
        <a href="https://www.instagram.com/ap/">ap</a>
      
    
  
  
    <activity:verb>http://activitystrea.ms/schema/1.0/post</activity:verb>
  
  
  <published>2016-01-17T13:15:52+00:00</published>
  <updated>2016-01-17T13:15:52+00:00</updated>
  
  
  
  

  <link rel="self" type="application/atom+xml" href="https://www.instagram.com/p/XYZ789/" />

  
    
      <link rel="enclosure" href="https://caching-proxy.snarfed.workers.dev/https://scontent-sjc2-1.cdninstagram.com/hphotos-xtp1/t50.2886-16/12604073_746855092124622_46574942_n.mp4" type="video/mp4" />
    
  
</entry>

</feed>"""

class InstagramAtomTest(unittest.TestCase, testutil.Asserts):
    maxDiff = None

    def setUp(self):
        super().setUp()
        app.testing = True
        self.client = app.test_client()

        # clear datastore
        requests.post('http://%s/reset' % ndb_client.host)
        self.ndb_context = ndb_client.context()
        self.ndb_context.__enter__()

    def tearDown(self):
        self.ndb_context.__exit__(None, None, None)
        super().tearDown()

    def test_store_feed(self):
        resp = self.client.post('/feed/store?token=towkin', json=HTML_FEED_V2)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('OK', resp.get_data(as_text=True))

        feed = Feed.get_by_id('towkin')
        self.assert_equals(HTML_FEED_V2, json_loads(feed.input))
        self.assert_equals(HTML_ACTIVITIES_FULL_V2, json_loads(feed.as1_json))

    def test_store_feed_existing(self):
        Feed(id='towkin', input='foo', as1_json='[]', actor_json='{}').put()
        self.test_store_feed()

    def test_get_feed(self):
        Feed(id='towkin',
             as1_json=json_dumps(HTML_ACTIVITIES_FULL_V2),
             actor_json='null').put()

        resp = self.client.get('/feed/get?token=towkin')
        self.assert_equals(200, resp.status_code)
        self.assert_multiline_equals(ATOM, resp.get_data(as_text=True))

    def test_get_feed_missing(self):
        resp = self.client.get('/feed/get?token=missing')
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.get_data(as_text=True).startswith(
            '<?xml version="1.0" encoding="UTF-8"?>'))
