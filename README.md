ChatExchange3 - [![Build Status](https://travis-ci.org/ByteCommander/ChatExchange3.svg)](https://travis-ci.org/ByteCommander/ChatExchange3)
============



A Python 3 API for talking to Stack Exchange chat.

## Dependencies

 - BeautifulSoup (`sudo apt-get install python3-beautifulsoup`)
 - Requests (`pip3 install requests`). Usually there by default. Please upgrade it with `pip3 install requests --upgrade`  
   *Note that Ubuntu comes with an old version of `pip3` that is not compatible any more with the latest version of `requests`. It will be broken after you installed `requests`, except if you update it before (or afterwards) with `easy_install pip3` or `pip3 install --upgrade pip` (that one works only before).*
 - python-websockets for the experimental websocket listener (`pip3 install websocket-client`). This module is optional, without it `initSocket()` from SEChatBrowser will not work

## Shortcuts

1. `make install-dependencies` will install the necessary Python package dependencies into your current environment (active virtualenv or system site packages)
2. `make test` will run the tests
3. `make run-example` will run the example script
4. `make` will run the above three in order


This project is licensed under [GPL](https://www.gnu.org/copyleft/gpl.html)
