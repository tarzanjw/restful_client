__author__ = 'tarzan'

import requests
import urlparse
from urllib import urlencode
import re
import json
import logging

logger = logging.getLogger(__name__)

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
            self.params = {k:v[0] if isinstance(v, (list, tuple)) and len(v) == 1 else v
                           for k,v in urlparse.parse_qs(str(params)).items()}

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
                 data=None, session=None, **session_args):
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
            params= {}
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
                 response_cls=None,
                 force_json_response=True,
                 args=None,
                 before_request_filters=None,
                 after_request_filters=None,
                 okay_status_code=None,
                 **session_args):
        self.url = self.join_url(url)
        if args is None:
            args = _populate_arg_names_from_url(str(self.url))
        self.method = method
        self.response_cls = response_cls
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
        if okay_status_code is not None:
            self.okay_status_code = okay_status_code

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
        ar = ApiRequest(self.method, url, params=bind, data=data, **self.session_args)
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
            data = json.loads(res.text)
        else:
            assert False, 'Unsupport content type "%s"' % content_type
        if self.response_cls is None:
            return data
        logger.debug('Start making "%s" response from data. Data: %s'
                     % (self.response_cls.__name__, data))
        res = self.response_cls.deserialize(data)
        return res

    def __call__(self, *args, **kwargs):
        if self.method in (Api.POST, Api.PUT):
            assert len(args) > 0, "Args have to specify POST data"
            data = args.pop(0)
        else:
            data = None
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