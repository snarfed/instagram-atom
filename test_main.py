"""Unit tests for main.py."""
import copy
import unittest

from granary.tests.test_instagram import (
    HTML_FEED_COMPLETE_V2,
    HTML_ACTIVITIES_FULL_V2,
)
from granary.instagram import Instagram
from oauth_dropins.webutil import testutil, util
from oauth_dropins.webutil.appengine_config import ndb_client
from oauth_dropins.webutil.util import json_dumps, json_loads
import requests

from main import app, Feed


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
        resp = self.client.post('/feed/store?token=towkin', data=HTML_FEED_COMPLETE_V2)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('OK', resp.get_data(as_text=True))

        feed = Feed.get_by_id('towkin')
        self.assertEqual(HTML_FEED_COMPLETE_V2, feed.html)
        self.assertEqual(HTML_ACTIVITIES_FULL_V2, json_loads(feed.as1_json))
