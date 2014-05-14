#!/usr/bin/env python
from getpass import getpass
import logging

import chatexchange
from chatexchange.events import MessageEdited


logging.basicConfig(level=logging.DEBUG)

email = raw_input('Email: ')
password = getpass()
client = chatexchange.Client('stackexchange.com', email, password)

me = client.get_me()
sandbox = client.get_room(11540)
my_message = None

with sandbox.messages() as messages:
    sandbox.send_message("hello worl")

    for message in messages:
        if message.owner is me:
            my_message = message
            assert my_message.content == "hello worl"
            print "message sent successfully"
            break

with sandbox.events(MessageEdited) as edits:
    my_message.edit("hello world")

    for edit in edits:
        if edit.message is my_message:
            assert my_message.content == "hello world"
            print "message edited successfully"
            break
