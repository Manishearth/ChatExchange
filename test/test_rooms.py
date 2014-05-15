import pytest

import chatexchange
from chatexchange.events import MessageEdited

import live_testing


if live_testing:
    @pytest.mark.xfail(reason="not implemented yet")
    def test_room_iterators():
        client = chatexchange.Client(
            'stackexchange.com', live_testing.email, live_testing.password)

        me = client.get_me()
        sandbox = client.get_room(11540)
        my_message = None

        with sandbox.messages() as messages:
            sandbox.send_message("hello worl")

            for message in messages:
                if message.owner is me:
                    my_message = message
                    assert my_message.content == "hello worl"
                    break

        with sandbox.events(MessageEdited) as edits:
            my_message.edit("hello world")

            for edit in edits:
                assert isinstance(edit, MessageEdited)

                if edit.message is my_message:
                    assert my_message.content == "hello world"
                    break
