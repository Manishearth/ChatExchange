ChatExchange6 - [![Build Status](https://travis-ci.org/ByteCommander/ChatExchange6.svg?branch=master)](https://travis-ci.org/ByteCommander/ChatExchange6)
============

A Python2 and Python3 cross-version API for talking to Stack Exchange chat.

 - Supported Python versions (Travis-CI build passes):  
    <kbd>2.7</kbd> <kbd>3.2</kbd> <kbd>3.3</kbd> <kbd>3.4</kbd> <kbd>3.5</kbd> <kbd>3.5-dev</kbd>  
 - Currently unsupported versions (Travis-CI build fails because of ChatExchange6 problems):  
    Those Python versions are always built by Travis-CI, but the result is ignored in the summary.  
    <kbd>2.6</kbd>  
 - Unclear versions (Travis-CI build fails because of the packages we use for our Travis-CI tests only):  
    Those Python versions are always built by Travis-CI, but the result is ignored in the summary.  
    <kbd>3.6-dev (nightly)</kbd> because of package `coverage` (see [link](https://bitbucket.org/ned/coveragepy/issues/391))

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
