__author__ = 'tarzan'

from unittest import TestCase
from . import BaseApiFactory, Api, ApiRequest
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

class TestApiRequest(TestCase):
    def test_url_parse(self):
        r = ApiRequest("GET", "https://Domain.com:808/path/to/api?q1=1&q2=2&q3=3",
                       params={"q2":6,"q4":4})
        self.assertDictEqual(r.url.params, {
            "q1": "1", "q2": 6, "q3": "3", "q4": 4
        })

    def test_execute(self):
        url = 'http://graph.facebook.com/hocdt'
        req = ApiRequest("GET", url)
        res = req.execute()
        self.assertIsInstance(res, requests.Response)
        self.assertEqual(res.status_code, 200)

class TestApi(TestCase):
    def test_request_get(self):
        url = "http://graph.facebook.com/{fbid}"
        api = Api("GET", url)
        self.assertListEqual(api.args, ['fbid',])
        data = api("hocdt")
        print data
        assert False
