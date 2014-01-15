__author__ = 'tarzan'

import itertools
import inspect
import requests
import urlparse
from urllib import urlencode
import re
import json
import logging

logger = logging.getLogger(__name__)


class RestFulError(ValueError):
    def __init__(self, response, message, **kwargs):
        self.response = response
        self.message = message
        logger.debug("JSON response could be decoded: %s" % self.response.text)
        return super(RestFulError, self).__init__(message, **kwargs)

    def __str__(self):
        return "JSON response could be decoded (%d): %s" \
               % (self.response.status_code, self.response.text)


def _populate_arg_names_from_url(url):
    return [g.group(1) for g in re.finditer(r"\{([\w-]+)\}", url)]


class ApiFailed(BaseException):
    """
    Raised whenever an API returns an not okay status code
    """

    def __init__(self, req):
        self.request = req
        self.response = req.response

    def __str__(self):
        return "API %s failed with status code %d" \
               % (self.request, self.response.status_code)


CONTENT_TYPE_JSON = 'application/json'


class URL(object):
    """
    Represent URL as structured data type
    """

    def __init__(self, scheme="", netloc="", path="", params=""):
        self.scheme = scheme
        self.netloc = netloc
        self.path = path
        if isinstance(params, dict):
            self.params = params
        else:
            self.params = {k: v[0] if isinstance(v, (list, tuple)) and len(v) == 1 else v
                           for k, v in urlparse.parse_qs(str(params)).items()}

    @classmethod
    def parse(cls, url):
        scheme, netloc, path, params, fragment = urlparse.urlsplit(url)
        return cls(scheme, netloc, path, params)

    def __str__(self):
        return urlparse.urlunsplit((self.scheme, self.netloc,
                                    self.path, urlencode(self.params), None))


class ApiRequest(object):
    """
    This package do a request to API Provider
    """

    def __init__(self, method, url, params=None,
                 data=None, session=None, api=None, **session_args):
        """
        @parm url: the API url can be string or URL
        @param session: The session to execute request, if None, it will be
        created automatically
        @param session_args: the arguments that will be passed
        onto requests.Session.request

        @type session: requests.Session
        @type url: URL
        """
        if params is None:
            params = {}
        if data is None:
            data = {}
        if session is None:
            session = requests.Session()
        self.url = URL.parse(url)
        self.method = method
        self.url.params.update(params)
        self.data = data
        self.session = session
        session_args['params'] = self.url.params
        session_args['data'] = data
        self.session_args = session_args
        self.api = api

    def __str__(self):
        return self.method + "#" + str(self.url)

    def execute(self):
        """
        Execute the API
        @rtype requests.Response
        """
        logger.debug("Start executing API %s" % self)
        self.response = self.session.request(self.method, str(self.url), **self.session_args)
        return self.response


class Api(object):
    """
    Use to manage an API, every time the API is called, this will create an
    ApiRequest then execute it
    """
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"

    def __init__(self, method, url,
                 schema_cls=None,
                 object_cls=None,
                 force_json_response=True,
                 args=None,
                 default_params=None,
                 default_data=None,
                 before_request_filters=None,
                 after_request_filters=None,
                 okay_status_code=None,
                 **session_args):
        if default_params is None:
            default_params = {}
        if default_data is None:
            default_data = {}
        self.url = self.join_url(url)
        if args is None:
            args = _populate_arg_names_from_url(str(self.url))
        self.method = method
        self.schema_cls = schema_cls
        if self.schema_cls:
            self._data_schema = self.schema_cls()
            try:
                # try formencode first
                self.deserialize_data = self._data_schema.to_python
            except AttributeError:
                try:
                    # then colander
                    self.deserialize_data = self._data_schema.deserialize
                except AttributeError:
                    # just let it default (no deserialize)
                    pass
        self.object_cls = object_cls
        self.force_json_response = force_json_response
        self.args = args
        self.session_args = session_args

        if before_request_filters is None:
            before_request_filters = []
        elif not isinstance(before_request_filters, list):
            before_request_filters = [before_request_filters, ]
        if after_request_filters is None:
            after_request_filters = []
        elif not isinstance(after_request_filters, list):
            after_request_filters = [after_request_filters, ]
        self.before_request_filters = before_request_filters
        self.after_request_filters = after_request_filters
        if okay_status_code is None:
            okay_status_code = [200, ]
        self.okay_status_code = okay_status_code
        self.default_params = default_params
        self.default_data = default_data

    def join_url(self, url):
        try:
            base_url = self.__class__.__base_url__
        except AttributeError:
            return url
        return urlparse.urljoin(base_url, url)

    def create_api_request(self, bind, data):
        """
        @rtype ApiRequest
        """
        pattern = re.compile("\{(%s)\}" % '|'.join(bind.keys()))
        arg_names = [g.group(1) for g in pattern.finditer(self.url)]
        url = pattern.sub(lambda x: bind[x.group(1)], self.url)
        for aname in arg_names:
            del bind[aname]
        api_params = self.default_params.copy()
        api_params.update(bind)
        api_data = self.default_data.copy()
        api_data.update(data)
        ar = ApiRequest(self.method, url, params=api_params, data=api_data,
                        api=self, **self.session_args)
        return ar

    def _before_request(self, req):
        logger.debug("Firing before request signal on %s" % req)
        for fn in self.before_request_filters:
            fn(req)

    def _after_request(self, req):
        logger.debug("Firing after request signal on %s" % req)
        for fn in self.after_request_filters:
            fn(req)

    def add_before_request_filter(self, filter):
        self.before_request_filters.append(filter)

    def add_after_request_filter(self, filter):
        self.after_request_filters.append(filter)

    def deserialize_data(self, data):
        return data

    def _make_response(self, res):
        """
        Make response as python object from RESTful response
        @type res: requests.Response
        """
        if self.force_json_response:
            content_type = CONTENT_TYPE_JSON
        else:
            content_type = res.headers.get('content-type', 'Unknown').lower()
        if content_type == CONTENT_TYPE_JSON:
            try:
                data = json.loads(res.text)
            except ValueError, e:
                raise RestFulError(res, "JSON object could be decoded")
        else:
            assert False, 'Unsupport content type "%s"' % content_type
        if self.schema_cls is None:
            return data
        logger.debug('Start making "%s" response from data. Data: %s'
                     % (self.schema_cls.__name__, res.text))

        data = self.deserialize_data(data)
        if self.object_cls:
            if isinstance(data, (list, tuple)):
                res = [self.object_cls(**attrs) for attrs in data]
            else:
                res = self.object_cls(**data)
        else:
            res = data

        return res

    def __call__(self, *args, **kwargs):
        if self.method in (Api.POST, Api.PUT):
            assert len(args) > 0, "Args have to specify POST data"
            data = args[0]
            args = args[1:]
        else:
            data = {}
        assert len(args) <= len(self.args), \
            "Args has to have <= %d elments" % len(self.args)
        bind_data = dict(zip(self.args[:len(args)], args))
        bind_data.update(kwargs)
        req = self.create_api_request(bind_data, data)
        logger.debug("Going to call API %s" % req)
        self._before_request(req)
        req.execute()
        self._after_request(req)
        logger.debug("API %s executed done" % req)
        if req.response.status_code not in self.okay_status_code:
            raise ApiFailed(req)
        return self._make_response(req.response)


class _BaseObjectMeta(type):
    def __new__(meta, cls_name, bases, new_attrs):
        cls = type.__new__(meta, cls_name, bases, new_attrs)
        cls.__object_attr_types__ = {}
        for fname, ftype in new_attrs.iteritems():
            if not (inspect.isclass(ftype) or isinstance(ftype, (list, tuple))) \
                or fname in cls.__ignored_attrs__ \
                or (fname.startswith('__') and fname.endswith('__')):
                continue
            cls.__object_attr_types__[fname] = ftype
            # cls_property = property(cls.obj_attr_getter(fname),
            #                         cls.obj_attr_setter(fname))
            # setattr(cls, fname, cls_property)
        return cls


class BaseObject(object):
    __metaclass__ = _BaseObjectMeta

    __ignored_attrs__ = set([])

    __schema_names_mapping__ = {}

    __object_attr_types__ = {}

    def _create_attr_value(self, ftype, value):
        if isinstance(ftype, (list, tuple)):
            assert isinstance(value, (list, tuple))
            values = []
            for _type, _value in itertools.izip(itertools.cycle(ftype), value):
                values.append(self._create_attr_value(_type, _value))
            return values
        if issubclass(ftype, BaseObject) and isinstance(value, dict):
            return ftype(**value)
        return ftype(value)

    def __setattr__(self, name, value):
        if name not in self.__class__.__object_attr_types__:
            return super(BaseObject, self).__setattr__(name, value)
        ftype = self.__object_attr_types__[name]
        value = self._create_attr_value(ftype, value)
        self.__dict__[name] = value
        return value

    def __init__(self, **attrs):
        self.__object_attr_data__ = {}
        for fname, fvalue in attrs.iteritems():
            fname = self.__schema_names_mapping__.get(fname, fname)
            setattr(self, fname, fvalue)
