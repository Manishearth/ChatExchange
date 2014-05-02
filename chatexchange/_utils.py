# encoding: utf-8
from HTMLParser import HTMLParser
import htmlentitydefs


class HTMLTextExtractor(HTMLParser):
    # Originally posted at http://stackoverflow.com/a/7778368.
    # by Søren Løvborg (http://stackoverflow.com/u/13679) and Eloff.

    def __init__(self):
        HTMLParser.__init__(self)
        self.result = [ ]

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
