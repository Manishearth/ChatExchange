import os

"""
This module looks for live testing configuration in environment
variables, and exports them for test use if found.
"""

enabled = False


if (os.environ.get('ChatExchangeU') and
    os.environ.get('ChatExchangeP')):
    enabled = True
    username = os.environ['ChatExchangeU']
    password = os.environ['ChatExchangeP']
