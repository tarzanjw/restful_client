__author__ = 'tarzan'

def session_arg(name, value):
    def set_session_arg(factory):
        """
        :type factory: restful_client.BaseApiFactory
        :return:
        """
        factory.session_args[name] = value
        return factory
    return set_session_arg

def _session_arg_decorator(name):
    def _decorator(value):
        return session_arg(name, value)
    return _decorator

headers = _session_arg_decorator('headers')
cookies = _session_arg_decorator('cookies')
files = _session_arg_decorator('files')
auth = _session_arg_decorator('auth')
timeout = _session_arg_decorator('timeout')
allow_redirects = _session_arg_decorator('allow_redirects')
proxies = _session_arg_decorator('proxies')
hooks = _session_arg_decorator('hooks')
stream = _session_arg_decorator('stream')
verify = _session_arg_decorator('verify')
cert = _session_arg_decorator('cert')