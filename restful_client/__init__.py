__author__ = 'tarzan'

import requests
import urlparse
from urllib import urlencode
import re
import logging

logger = logging.getLogger(__name__)

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
        logger.debug("Start executing API %s" % self)
        return self.session.request(self.method, str(self.url), **self.session_args)

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
                 args=None,
                 **kwargs):
        self.url = url
        if args is None:
            args = Api._populate_arg_names_from_url(str(self.url))
        self.method = method
        self.args = args

    @staticmethod
    def _populate_arg_names_from_url(url):
        return [g.group(1) for g in re.finditer(r"\{([\w-]+)\}", url)]

    def create_api_request(self, bind, data):
        """
        @rtype ApiRequest
        """
        pattern = re.compile("\{(%s)\}" % '|'.join(bind.keys()))
        url = pattern.sub(lambda x: bind[x.group(1)], self.url)
        ar = ApiRequest(self.method, url, data=data)
        return ar

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
        return req.execute()

class BaseApiFactory(object):
    pass