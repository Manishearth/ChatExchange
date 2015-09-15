"""
This module looks for live testing configuration in environment
variables, and exports them for test use if found.
"""

import os


enabled = False


if (os.environ.get('ChatExchangeU') and
    os.environ.get('ChatExchangeP')):
    enabled = True
    email = os.environ['ChatExchangeU']
    password = os.environ['ChatExchangeP']
