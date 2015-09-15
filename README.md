ChatExchange6 - [![Build Status](https://travis-ci.org/ByteCommander/ChatExchange6.svg?branch=master)](https://travis-ci.org/ByteCommander/ChatExchange6)
============

A Python2 and Python3 cross-version API for talking to Stack Exchange chat.

Supported Python versions (currently checked by Travis-CI): `2.7` `3.3` `3.4` `3.5-dev`  
Python versions with previously failing Travis-CI builds (now excluded from tests): `2.6` `3.2` `3.5` `3.6-dev (nightly)`

## Dependencies
**Make sure you use either `pip2` or `pip3` depending on which Python version you want to run this on.**


 - BeautifulSoup (`pip install beautifulsoup4`)
 - Requests (`pip install requests`). Usually there by default. Please upgrade it with `pip install requests --upgrade`  
   *Note that Ubuntu comes with an old version of `pip` that is not compatible any more with the latest version of `requests`. It will be broken after you installed `requests`, except if you update it before (or afterwards) with `easy_install pip` or `pip install --upgrade pip` (that one works only before).*
 - python-websockets for the experimental websocket listener (`pip install websocket-client`). This module is optional, without it `initSocket()` from SEChatBrowser will not work

## Shortcuts

1. `make install-dependencies` will install the necessary Python package dependencies into your current environment (active virtualenv or system site packages)
2. `make test` will run the tests
3. `make run-example` will run the example script
4. `make` will run the above three in order


This project is licensed under [GPL](https://www.gnu.org/copyleft/gpl.html)
