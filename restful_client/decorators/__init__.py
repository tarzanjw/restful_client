__author__ = 'tarzan'

import session

def response_class(value):
    def set_response_class(factory):
        factory.response_cls = value
        return factory
    return set_response_class
