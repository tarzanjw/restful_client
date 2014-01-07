__author__ = 'tarzan'

import logging
import copy

from api import Api, ApiRequest

logger = logging.getLogger(__name__)

class _ApiFactoryMeta(type):
    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        cls._apis = {}
        for name, api in new_attrs.items():
            if isinstance(api, Api):
                cls._apis[name] = api
                api._attach_to_factory(cls)
        return cls

class BaseApiFactory(object):
    __metaclass__ = _ApiFactoryMeta

    response_cls = None
    session_args = {}

    before_request_filters = []
    after_request_filters = []

    def __init__(self, response_cls=None,
                 before_request_filters=None,
                 after_request_filters=None,
                 **session_args):
        cls = self.__class__
        response_cls = response_cls or cls.response_cls
        sargs = copy.deepcopy(cls.session_args)
        sargs.update(session_args)
        self.response_cls = response_cls
        self.session_args = sargs

        if before_request_filters is None:
            before_request_filters = []
        elif not isinstance(before_request_filters, list):
            before_request_filters = [before_request_filters, ]
        if after_request_filters is None:
            after_request_filters = []
        elif not isinstance(after_request_filters, list):
            after_request_filters = [after_request_filters, ]
        before_request_filters += cls.before_request_filters
        after_request_filters += cls.after_request_filters
        print before_request_filters
        print after_request_filters
        self.before_request_filters = before_request_filters
        self.after_request_filters = after_request_filters

        for name, api in self.__class__._apis.items():
            api = copy.deepcopy(api)
            api._attach_to_factory(self)
            self.__setattr__(name, api)