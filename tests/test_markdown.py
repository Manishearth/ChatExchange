import sys
import logging
if sys.version_info[:2] <= (2, 6):
    logging.Logger.getChild = lambda self, suffix:\
        self.manager.getLogger('.'.join((self.name, suffix)) if self.root is not self else suffix)

import pytest

from chatexchange.markdown_detector import markdown


logger = logging.getLogger(__name__)


def test_markdown():
    assert markdown('no markdown here') is None
    assert markdown('    code formatting') is not None
    assert markdown('hello `code` here') is not None
    assert markdown('bare url https://example.com/link gets linked') is not None
    assert markdown('[hello](http://example.com/hello)') is not None
    assert markdown('adjacent[hello](http://example.com/hello)text') is not None
    assert markdown('adjacent.[hello](https://example.com/hello).x') is not None
    assert markdown('[ftp](ftp://example.com/link) works too') is not None
    assert markdown('text with *italics*') is not None
    assert markdown('and **bold** too') is not None
    assert markdown('*not italics') is None
    assert markdown('**not bold either') is None
    assert markdown('***not both neither too also as well') is None
    assert markdown('****not bold or italic') is None
    # Odd corner cases: many backticks
    assert markdown('two ``backticks`` code') is not None
    assert markdown('unpaired `single double`` fail') is None
    assert markdown('unpaired `single triple``` fail') is None
    # Weirdly, 'unpaired ``double triple```' gets rendered as
    # 'unpaired <code>double triple</code>`'
    #assert markdown('unpaired ``double triple``` fail') is not None
    assert markdown('``````````````````18 ticks``````````````````') is not None
    # Odd corner cases: broken links
    assert markdown(
        '[](http://example.com/link) gets linked inside parens') is not None
    assert markdown('[no link]() is not linked') is None
    assert markdown('[mailto is not linked](mailto:self@example.com)') is None
    assert markdown('[sftp](sftp://example.com/link) is not linked') is None
    assert markdown('[ftps](ftps://example.com/link) is not linked') is None
    assert markdown(
        '[https://example.com/no-link]() link in square brackets') is not None
    assert markdown(
        'empty anchor, link in parens [](https://example.com/)') is not None
    # Odd corner cases: mixed bold and italics
    assert markdown('this is ***bold italics***') is not None
    assert markdown('this is **bold and *italics* too**') is not None
    assert markdown(
        'this is *italics and **bold** and **more** too*') is not None
    # Odd corner cases: broken bold or italics
    assert markdown('**unpaired neither*') is None
    assert markdown('*unpaired nor**') is None
    assert markdown('***unpaired** in the end') is None
    # chat actually briefly formats as bold italics, then reverts
    #assert markdown('****this is weird****') is None
