import logging
from logging import *


class Logger26(logging.getLoggerClass()):

    def getChild(self, suffix):
        """
        (copied from module "logging" for Python 3.4)

        Get a logger which is a descendant to this one.

        This is a convenience method, such that

        logging.getLogger('abc').getChild('def.ghi')

        is the same as

        logging.getLogger('abc.def.ghi')

        It's useful, for example, when the parent logger is named using
        __name__ rather than a literal string.
        """
        if self.root is not self:
            suffix = '.'.join((self.name, suffix))
        return self.manager.getLogger(suffix)


logging.setLoggerClass(Logger26)
