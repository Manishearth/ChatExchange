import sys
import logging
if sys.version_info[:2] <= (2, 6):
    logging.Logger.getChild = lambda self, suffix:\
        self.manager.getLogger('.'.join((self.name, suffix)) if self.root is not self else suffix)

import pytest

import chatexchange
from chatexchange.events import MessageEdited, MessageDeleted

from tests import live_testing


logger = logging.getLogger(__name__)


if live_testing.enabled:
    @pytest.mark.timeout(240)
    def test_room_info():
        client = chatexchange.Client('stackexchange.com')

        a_feeds_user = client.get_user(-2)
        bot_user = client.get_user(146115)
        sandbox = client.get_room(1)

        assert bot_user in sandbox.owners
        assert a_feeds_user not in sandbox.owners
        assert sandbox.user_count >= 4
        assert sandbox.message_count >= 10
        assert 'sandbox' in sandbox.tags

        # we aren't checking these result, just that it doesn't blow up
        sandbox.description
        sandbox.text_description
        sandbox.parent_site_name
        sandbox.name

    @pytest.mark.timeout(240)
    def test_room_iterators():
        client = chatexchange.Client(
            'stackexchange.com', live_testing.email, live_testing.password)

        me = client.get_me()
        sandbox = client.get_room(1)

        my_message = None

        with sandbox.new_messages() as messages:
            sandbox.send_message("hello worl")

            for message in messages:
                if message.owner is me:
                    my_message = message
                    assert my_message.content == "hello worl"
                    break
                else:
                    logger.info("ignoring message: %r", message)

        with sandbox.new_events(MessageEdited) as edits:
            my_message.edit("hello world")

            for edit in edits:
                assert isinstance(edit, MessageEdited)

                if edit.message is my_message:
                    assert my_message.content == "hello world"
                    break

        with sandbox.new_events(MessageDeleted) as deletions:
            my_message.delete()

            for deletion in deletions:
                assert isinstance(deletion, MessageDeleted)

                if deletion.message is my_message:
                    break
