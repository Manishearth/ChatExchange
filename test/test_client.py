import logging
import time
import uuid
import os
import Queue

import pytest

from chatexchange.client import Client
from chatexchange import events

import live_testing


logger = logging.getLogger(__name__)


TEST_ROOMS = [
    ('stackexchange.com', '14219'),  # Charcoal Sandbox
]


if (os.environ.get('TRAVIS_BUILD_ID') and
    os.environ.get('TRAVIS_REPO_SLUG') and
    os.environ.get('TRAVIS_COMMIT')):
    TEST_MESSAGE_FORMAT = (
        "[ [ChatExchange@Travis](https://travis-ci.org/"
        "{0[TRAVIS_REPO_SLUG]}/builds/{0[TRAVIS_BUILD_ID]} \"This is "
        "a test message for ChatExchange using the nonce {{0}}.\") ] "
        "This is a test of [{0[TRAVIS_REPO_SLUG]}@{short_commit}]("
        "https://github.com/{0[TRAVIS_REPO_SLUG]}/commit/{0[TRAVIS_COMMIT]})."
    ).format(os.environ, short_commit=os.environ['TRAVIS_COMMIT'][:8])
else:
    TEST_MESSAGE_FORMAT = (
        "[ [ChatExchange@localhost](https://github.com/Manishearth/"
        "ChatExchange/ \"This is a test message for ChatExchange using "
        "the nonce {0}.\") ] This is a test message for ChatExchange.")


if live_testing.enabled:
    @pytest.mark.parametrize('host_id,room_id', TEST_ROOMS)
    @pytest.mark.timeout(240)
    def test_se_message_echo(host_id, room_id):
        """
        Tests that we are able to send a message, and recieve it back,
        send a reply, and recieve that back, within a reasonable amount
        of time.

        This is a lot of complexity for a single test, but we don't want
        to flood Stack Exchange with more test messages than necessary.
        """

        client = Client(host_id)
        client.login(
            live_testing.email,
            live_testing.password)

        timeout_duration = 60

        pending_events = Queue.Queue()

        def get_event(predicate):
            """
            Waits until it has seen a message passing the specified
            predicate from both polling and sockets.

            Asserts that it has not waited longer than the specified
            timeout, and asserts that the events from difference sources
            have the same ID.

            This may dequeue any number of additional unrelated events
            while it is running, so it's not appropriate if you are
            trying to wait for multiple events at once.
            """

            socket_event = None
            polling_event = None

            timeout = time.time() + timeout_duration

            while (not (socket_event and polling_event)
                   and time.time() < timeout):
                try:
                    is_socket, event = pending_events.get(timeout=1)
                except Queue.Empty:
                    continue

                if predicate(event):
                    logger.info(
                        "Expected event (is_socket==%r): %r",
                        is_socket, event)
                    if is_socket:
                        assert socket_event is None
                        socket_event = event
                    else:
                        assert polling_event is None
                        polling_event = event
                else:
                    logger.debug("Unexpected events: %r", event)

            assert socket_event and polling_event
            assert type(socket_event) is type(polling_event)
            assert socket_event.id == polling_event.id

            return socket_event

        logger.debug("Joining chat")

        room = client.get_room(room_id)

        room.join()

        room.watch_polling(lambda event, _:
            pending_events.put((False, event)), 5)
        room.watch_socket(lambda event, _:
            pending_events.put((True, event)))

        time.sleep(2)  # Avoid race conditions

        test_message_nonce = uuid.uuid4().hex
        test_message_content = TEST_MESSAGE_FORMAT.format(test_message_nonce)

        logger.debug("Sending test message")
        room.send_message(test_message_content)

        @get_event
        def test_message_posted(event):
            return (
                isinstance(event, events.MessagePosted)
                and test_message_nonce in event.content
            )

        logger.debug("Observed test edit")

        test_reply_nonce = uuid.uuid4().hex
        test_reply_content = TEST_MESSAGE_FORMAT.format(test_reply_nonce)

        logger.debug("Sending test reply")
        test_message_posted.message.reply(test_reply_content)

        # XXX: The limitations of get_event don't allow us to also
        # XXX: look for the corresponding MessagePosted event.
        @get_event
        def test_reply(event):
            return (
                isinstance(event, events.MessageReply)
                and test_reply_nonce in event.content
            )

        logger.debug("Observed test reply")

        assert test_reply.parent_message_id == test_message_posted.message.id
        assert test_reply.message.parent.id == test_reply.parent_message_id
        assert test_message_posted.message.id == test_message_posted.message.id
        assert test_reply.message.parent is test_message_posted.message

        # unsafe - html content is unstable; may be inconsistent between views
        # assert test_reply.message.parent.content == test_message_posted.content

        test_edit_nonce = uuid.uuid4().hex
        test_edit_content = TEST_MESSAGE_FORMAT.format(test_edit_nonce)

        logger.debug("Sending test edits")

        # Send a lot of edits in a row, to ensure we don't lose any
        # from throttling being ignored.
        test_message_posted.message.edit(
            "**this is a** test edit and should be edited again")
        test_message_posted.message.edit(
            "this is **another test edit** and should be edited again")
        test_message_posted.message.edit(
            "this is **yet** another test edit and **should be edited again**")
        test_message_posted.message.edit(test_edit_content)

        @get_event
        def test_edit(event):
            return (
                isinstance(event, events.MessageEdited)
                and test_edit_nonce in event.content
            )

        logger.debug("Observed final test edit")

        assert test_message_posted.message is test_edit.message
        assert test_edit.message.id == test_message_posted.message.id
        assert test_edit.message.edits == 4
        assert test_edit.message.content_source == test_edit_content

        # it should be safe to assume that there isn't so much activity
        # that these events will have been flushed out of recent_events.
        assert test_message_posted in client._recently_gotten_objects
        assert test_reply in client._recently_gotten_objects
        assert test_edit in client._recently_gotten_objects

        client.logout()
