ChatExchange
============

[![Travis CI build status for master](https://travis-ci.org/Manishearth/ChatExchange.svg?branch=master)](https://travis-ci.org/Manishearth/ChatExchange)

A Python API for talking to Stack Exchange chat.

## Dependencies

 - BeautifulSoup (`sudo apt-get install python-beautifulsoup`)
 - Requests (`pip install requests`). Usually there by default. Please upgrade it with `pip install requests --upgrade`
 - python-websockets for the experimental websocket listener (`pip install websocket-client`). This module is optional, without it `initSocket()` from SEChatBrowser will not work

## Shortcuts

1. `make install-dependencies` will install the necessary Python package dependencies into your current environment (active virtualenv or system site packages)
2. `make test` will run the tests
3. `make run-example` will run the example script
4. `make` will run the above three in order


This project is licensed under [GPL](https://www.gnu.org/copyleft/gpl.html)
