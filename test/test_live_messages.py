import logging
import time
import uuid
import os

import pytest

from chatexchange.wrapper import SEChatWrapper

import live_testing


logger = logging.getLogger(__name__)



TEST_ROOMS = [
    ('SE', '14219'), # Charcoal Sandbox
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
    def test_se_message_echo(host_id, room_id):
        """
        Tests that we are able to send a message, and recieve it back
        within a reasonable amount of time, on Stack Exchange chat.
        """

        wrapper = SEChatWrapper(host_id)
        wrapper.login(
            live_testing.username,
            live_testing.password)

        test_message_nonce = uuid.uuid4().hex
        test_message = TEST_MESSAGE_FORMAT.format(test_message_nonce)

        seen_message_with_socket = []
        seen_message_with_polling = []

        def on_socket_message(message, wrapper):
            if (message['event_type'] == 1 and
                test_message_nonce in message['content']):
                seen_message_with_socket.append(message)
                logger.debug("Saw test message in socket")

        def on_polling_message(message, wrapper):
            if (message['event_type'] == 1 and
                test_message_nonce in message['content']):
                seen_message_with_polling.append(message)
                logger.debug("Saw test message in polling")

        logger.debug("Joining chat")
        wrapper.joinRoom(room_id)

        wrapper.watchRoom(room_id, on_polling_message, 1)
        wrapper.watchRoomSocket(room_id, on_socket_message)

        time.sleep(2) # Avoid race conditions
        logger.debug("Sending test message")
        wrapper.sendMessage(room_id, test_message)

        timeout_time = time.time() + 15.0

        while time.time() < timeout_time and not (
            seen_message_with_socket and seen_message_with_polling):
            time.sleep(1)

        assert seen_message_with_polling, "didn't see own message using HTTP polling"
        assert seen_message_with_socket, "didn't see own message using WebSockets"

        wrapper.logout()
