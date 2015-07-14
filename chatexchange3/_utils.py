# encoding: utf-8
from HTMLParser import HTMLParser
import functools
import htmlentitydefs
import logging
import weakref


def log_and_ignore_exceptions(
    f, exceptions=Exception, logger=logging.getLogger('exceptions')
):
    """
    Wraps a function to catch its exceptions, log them, and return None.
    """
    @functools.wraps(f)
    def wrapper(*a, **kw):
        try:
            return f(*a, **kw)
        except exceptions:
            logger.exception("ignored unhandled exception in %s", f)
            return None

    return wrapper


class HTMLTextExtractor(HTMLParser):
    # Originally posted at http://stackoverflow.com/a/7778368.
    # by Søren Løvborg (http://stackoverflow.com/u/13679) and Eloff.

    def __init__(self):
        HTMLParser.__init__(self)
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def handle_charref(self, number):
        if number[0] in (u'x', u'X'):
            codepoint = int(number[1:], 16)
        else:
            codepoint = int(number)
        self.result.append(unichr(codepoint))

    def handle_entityref(self, name):
        codepoint = htmlentitydefs.name2codepoint[name]
        self.result.append(unichr(codepoint))

    def get_text(self):
        return u''.join(self.result)


def html_to_text(html):
    s = HTMLTextExtractor()
    s.feed(html)
    return s.get_text()


class LazyFrom(object):
    """
    A descriptor used when multiple lazy attributes depend on a common
    source of data.
    """
    def __init__(self, method_name):
        """
        method_name is the name of the method that will be invoked if
        the value is not known. It must assign a value for the attribute
        attribute (through this descriptor).
        """
        self.method_name = method_name
        self.values = weakref.WeakKeyDictionary()

    def __get__(self, obj, cls):
        if obj is None:
            return self

        if obj not in self.values:
            method = getattr(obj, self.method_name)
            method()

        assert obj in self.values, "method failed to populate attribute"

        return self.values[obj]

    def __set__(self, obj, value):
        self.values[obj] = value

    def __delete__(self, obj):
        if obj in self.values:
            del self.values[obj]
