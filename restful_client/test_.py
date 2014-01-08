__author__ = 'tarzan'

from pyramid.config import Configurator
from unittest import TestCase
from . import Api, ApiRequest, BaseObject
import requests
import logging
import colander
import limone
from formencode import Schema, validators

class FBColanderSchema(colander.MappingSchema):
    id = colander.SchemaNode(colander.Integer())
    first_name = colander.SchemaNode(colander.String())
    last_name = colander.SchemaNode(colander.String())
    link = colander.SchemaNode(colander.String())
    username = colander.SchemaNode(colander.String())
    gender = colander.SchemaNode(colander.String())
    locale = colander.SchemaNode(colander.String())
    not_exists = colander.SchemaNode(colander.String(), missing='afds')

class FBFormEncodeSchema(Schema):
    allow_extra_fields = True
    id = validators.Int()
    first_name = validators.UnicodeString()
    last_name = validators.UnicodeString()
    link = validators.UnicodeString()
    username = validators.UnicodeString()
    gender = validators.UnicodeString()
    locale = validators.UnicodeString()
    not_exists = validators.UnicodeString(if_missing='asf')

class BankInfo(BaseObject):
    pass

class FBInfo(BaseObject):
    id = int
    first_name = unicode
    bank = BankInfo
    banks = [BankInfo,]


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
        api = Api("GET", url,
                  schema_cls=FBColanderSchema,
                  object_cls=FBInfo)
        self.assertListEqual(api.args, ['fbid',])
        fb = api("hocdt")
        self.assertIsInstance(fb, FBInfo)
        self.assertEqual(fb.id, 1138601866)

    def test_request_post(self):
        # TODO I do not has public server to test this function
        pass