__author__ = 'tarzan'

import session

def response_class(value):
    def set_response_class(factory):
        factory.response_cls = value
        return factory
    return set_response_class

def before_request(filter):
    def add_filter(factory):
        factory.before_request_filters.append(filter)
        return factory
    return add_filter

def after_request(filter):
    def add_filter(factory):
        factory.after_request_filters.append(filter)
        return factory
    return add_filter