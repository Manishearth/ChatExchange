"""
A simple module to decide whether a chat message contains Markdown formatting
"""

import re


mdre_code = re.compile(r'^ {4}')
mdre_mono = re.compile(r'(?<!`)(`+)(?:[^`](?:.*?[^`])?)\1(?!`)')
mdre_url  = re.compile(r'\b(?:https?|ftp)://[-~.%\w/]+')
mdre_link = re.compile(r'\[(?:[^]\\]|\\.)+\]\({0}\)'.format(mdre_url.pattern))
mdre_italics = re.compile(
    r'(?<![*])[*](?:[^*]+|[*]{3,}|[*]{2}[^*]+[*]{2})+[*](?![*])')
mdre_bold = re.compile(
    r'(?<![*])[*][*](?:[^*]+|[*]{3,}[*][^*]+[*])+[*][*](?![*])')


def markdown(text):
    """
    Return match object if text is Markdown-formatted, otherwise None.
    @param text: The message to check for Markdown formatting.
    @type text: L{str}
    """
    return mdre_code.match(text) or mdre_mono.search(text) or \
        mdre_link.search(text) or mdre_url.search(text) or \
            mdre_italics.search(text) or mdre_bold.search(text)
