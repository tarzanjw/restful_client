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


class FilterTester(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._before_called = set([])
        self._after_called = set([])

    def before_request(self, value):
        def filter(req):
            print 'before', value, req
            self._before_called.add(value)
        return filter

    def after_request(self, value):
        def filter(req):
            print 'after', value, req
            self._after_called.add(value)
        return filter
    
    def has_before_called(self, value):
        return value in self._before_called
    
    def has_after_called(self, value):
        return value in self._after_called

filter_tester = FilterTester()

@decorators.session.auth(('test', '1234'))
@decorators.response_class(FacebookPublicInfo)
@decorators.before_request(filter_tester.before_request('decorate'))
@decorators.after_request(filter_tester.after_request('decorate'))
class FacebookAPIs(BaseApiFactory):
    session_args = {
        "params": {"haha": "he he"}
    }
    before_request_filters = [filter_tester.before_request('static'),]
    after_request_filters = [filter_tester.after_request('static'),]

    get_info = Api("GET", "http://graph.facebook.com/{fbid}")
    post_info = Api("POST", "http://graph.facebook.com/{fbid}", response_cls=MyResponse)

# print FacebookAPIs.response_cls
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

        res = FacebookAPIs.get_info('hocdt')
        self.assertIsInstance(res, FacebookPublicInfo)
        self.assertTrue(filter_tester.has_before_called('decorate'))
        self.assertTrue(filter_tester.has_before_called('static'))
        self.assertFalse(filter_tester.has_before_called('dynamic'))
        self.assertTrue(filter_tester.has_after_called('decorate'))
        self.assertTrue(filter_tester.has_after_called('static'))
        self.assertFalse(filter_tester.has_after_called('dynamic'))

        filter_tester.reset()
        factory = FacebookAPIs(MyResponse, auth=("abc","xyz"),
                               before_request_filters=filter_tester.before_request('dynamic'),
                               after_request_filters=filter_tester.after_request('dynamic'),
                               )
        self.assertIs(factory.response_cls, MyResponse)
        self.assertIs(factory.get_info.response_cls, MyResponse)
        self.assertIs(factory.post_info.response_cls, MyResponse)
        self.assertDictEqual(factory.get_info.session_args,
            {'auth': ("abc","xyz"), 'params': {'haha': 'he he'}})

        res = factory.get_info('hocdt')
        self.assertTrue(filter_tester.has_before_called('decorate'))
        self.assertTrue(filter_tester.has_before_called('static'))
        self.assertTrue(filter_tester.has_before_called('dynamic'))
        self.assertTrue(filter_tester.has_after_called('decorate'))
        self.assertTrue(filter_tester.has_after_called('static'))
        self.assertTrue(filter_tester.has_after_called('dynamic'))

        self.assertIs(FacebookAPIs.get_info.response_cls, FacebookPublicInfo)
        self.assertIs(FacebookAPIs.post_info.response_cls, MyResponse)
        self.assertDictEqual(FacebookAPIs.get_info.session_args,
            {'params':{'haha': 'he he'},'auth':('test', '1234')})