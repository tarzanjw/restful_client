__author__ = 'tarzan'

from unittest import TestCase
from . import BaseApiFactory, Api, ApiRequest
import requests
import logging
import colander
import limone

@limone.content_schema
class FacebookPublicInfo(colander.MappingSchema):
    id = colander.SchemaNode(colander.Integer())
    first_name = colander.SchemaNode(colander.String())
    last_name = colander.SchemaNode(colander.String())
    link = colander.SchemaNode(colander.String())
    username = colander.SchemaNode(colander.String())
    gender = colander.SchemaNode(colander.String())
    locale = colander.SchemaNode(colander.String())
    not_exists = colander.SchemaNode(colander.String(), missing='afds')

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
        api = Api("GET", url, response_cls=FacebookPublicInfo)
        self.assertListEqual(api.args, ['fbid',])
        fb = api("hocdt")
        self.assertIsInstance(fb, FacebookPublicInfo)
