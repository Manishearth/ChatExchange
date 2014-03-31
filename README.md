ChatExchange
============

A Python API for talking to Stack Exchange chat


Dependencies:

 - BeautifulSoup (`sudo apt-get install python-beautifulsoup`)
 - Requests (`pip install requests`). Usually there by default. Please upgrade it with `pip install requests --upgrade`
 - python-websockets for the experimental websocket listener (`pip install websocket-client`). This module is optional, without it `initSocket()` from SEChatBrowser will not work
