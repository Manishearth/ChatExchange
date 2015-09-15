#!/usr/bin/env python
import getpass
import logging
import os

import chatexchange
from chatexchange.events import MessageEdited


logging.basicConfig(level=logging.DEBUG)

if 'ChatExchangeU' in os.environ:
    email = os.environ['ChatExchangeU']
else:
    email = input("Email: ")
if 'ChatExchangeP' in os.environ:
    password = os.environ['ChatExchangeP']
else:
    password = getpass.getpass("Password: ")
client = chatexchange.Client('stackexchange.com', email, password)

me = client.get_me()
sandbox = client.get_room(14219)
my_message = None

with sandbox.new_messages() as messages:
    sandbox.send_message("hello worl")

    for message in messages:
        if message.owner is me:
            my_message = message
            assert my_message.content == "hello worl"
            print("message sent successfully")
            break

with sandbox.new_events(MessageEdited) as edits:
    my_message.edit("hello world")

    for edit in edits:
        if edit.message is my_message:
            assert my_message.content == "hello world"
            print("message edited successfully")
            break
