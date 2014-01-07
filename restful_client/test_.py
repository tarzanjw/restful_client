__author__ = 'tarzan'

from pyramid.config import Configurator
from unittest import TestCase
from . import BaseApiFactory, Api, ApiRequest
import decorators
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

@limone.content_schema
class MyResponse(colander.MappingSchema):
    id = colander.SchemaNode(colander.Integer())


@decorators.session.auth(('test', '1234'))
@decorators.response_class(FacebookPublicInfo)
class FacebookAPIs(BaseApiFactory):
    session_args = {
        "params": {"haha": "he he"}
    }
    get_info = Api("GET", "http://graph.facebook.com/{fbid}")
    post_info = Api("POST", "http://graph.facebook.com/{fbid}", response_cls=MyResponse)

print FacebookAPIs.response_cls
# assert False

class MyAPIs(BaseApiFactory):
    get_info = Api("GET", "localhost")

logging.basicConfig(level=logging.DEBUG)

class TestAll(TestCase):

    def test_api_url_parse(self):
        r = ApiRequest("GET", "https://Domain.com:808/path/to/api?q1=1&q2=2&q3=3",
                       params={"q2":6,"q4":4})
        self.assertDictEqual(r.url.params, {
            "q1": "1", "q2": 6, "q3": "3", "q4": 4
        })

    def test_api_execute(self):
        url = 'http://graph.facebook.com/hocdt'
        req = ApiRequest("GET", url)
        res = req.execute()
        self.assertIsInstance(res, requests.Response)
        self.assertEqual(res.status_code, 200)

    def test_api_request_get(self):
        url = "http://graph.facebook.com/{fbid}"
        api = Api("GET", url, response_cls=FacebookPublicInfo)
        self.assertListEqual(api.args, ['fbid',])
        fb = api("hocdt")
        self.assertIsInstance(fb, FacebookPublicInfo)

    def test_request_post(self):
        # TODO I do not has public server to test this function
        pass

    def test_api_factory(self):
        self.assertIs(FacebookAPIs.get_info.response_cls, FacebookPublicInfo)
        self.assertIs(FacebookAPIs.post_info.response_cls, MyResponse)
        self.assertDictEqual(FacebookAPIs.get_info.session_args,
            {'params':{'haha': 'he he'},'auth':('test', '1234')})
        self.assertTupleEqual(FacebookAPIs.session_args['auth'], ('test', '1234'))

        factory = FacebookAPIs(MyResponse, auth="abc")
        self.assertIs(factory.response_cls, MyResponse)
        self.assertIs(factory.get_info.response_cls, MyResponse)
        self.assertIs(factory.post_info.response_cls, MyResponse)
        self.assertDictEqual(factory.get_info.session_args,
            {'auth': 'abc', 'params': {'haha': 'he he'}})

        self.assertIs(FacebookAPIs.get_info.response_cls, FacebookPublicInfo)
        self.assertIs(FacebookAPIs.post_info.response_cls, MyResponse)
        self.assertDictEqual(FacebookAPIs.get_info.session_args,
            {'params':{'haha': 'he he'},'auth':('test', '1234')})
