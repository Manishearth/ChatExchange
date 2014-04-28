import logging
import time
import uuid
import os

import pytest

from chatexchange.wrapper import SEChatWrapper

import live_testing


logger = logging.getLogger(__name__)


if (os.environ.get('TRAVIS_BUILD_ID') and
    os.environ.get('TRAVIS_REPO_SLUG')):
    TEST_MESSAGE_PREFIX = (
        "[ [ChatExchange@Travis](https://travis-ci.org/"
        "{0[TRAVIS_REPO_SLUG]}/builds/{0[TRAVIS_BUILD_ID]}) ] "
    ).format(os.environ)
else:
    TEST_MESSAGE_PREFIX = (
        "[ [ChatExchange@localhost](https://github.com/Manishearth/ChatExchange/) ] ")


if live_testing.enabled:
    def test_se_message_echo():
        """
        Tests that we are able to send a message, and recieve it back
        within a reasonable amount of time, on Stack Exchange chat.
        """

        host_id = 'SE'
        room_id = '11540' # Charcoal HQ

        wrapper = SEChatWrapper(host_id)
        wrapper.login(
            live_testing.username,
            live_testing.password)

        test_message_code = uuid.uuid4().hex
        test_message = "%s `%s`" % (TEST_MESSAGE_PREFIX, test_message_code)

        replied = [False]

        def on_message(message, wrapper):
            if test_message_code in message['content']:
                replied[0] = True
                logger.debug("Saw expected echoed test chat message!")
            else:
                logger.debug(
                    "Ignoring unexpected message: %s", message)

        logger.debug("Joining chat")
        wrapper.joinRoom(room_id)

        wrapper.watchRoom(room_id, on_message, 1)
        time.sleep(2) # Avoid race conditions
        logger.debug("Sending test message")
        wrapper.sendMessage(room_id, test_message)

        timeout_time = time.time() + 30

        while time.time() < timeout_time and replied[0] == False:
            time.sleep(1)

        if not replied[0]:
            raise Exception("did not see expected chat reply in time")

        wrapper.logout()
