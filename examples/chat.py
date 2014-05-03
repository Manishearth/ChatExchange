#!/usr/bin/env python
import getpass
import logging
import os
import random
import sys
import threading
import time

import chatexchange.wrapper
import chatexchange.events


logger = logging.getLogger(__name__)


def main():
    setup_logging()

    # Run `. setp.sh` to set the below testing environment variables

    host_id = 'SE'
    room_id = '14219' # Charcoal Chatbot Sandbox

    if 'ChatExchangeU' in os.environ:
        username = os.environ['ChatExchangeU']
    else:
        sys.stderr.write("Username: ")
        sys.stderr.flush()
        username = raw_input()
    if 'ChatExchangeP' in os.environ:
        password = os.environ['ChatExchangeP']
    else:
        password = getpass.getpass("Password: ")

    wrapper = chatexchange.wrapper.SEChatWrapper(host_id)
    wrapper.login(username,password)

    wrapper.joinRoom(room_id)
    wrapper.watchRoom(room_id, on_message, 1)

    # If WebSockets are available, one could instead use:
    #     wrapper.watchRoomSocket(room, on_message)

    print "(You are now in room #%s on %s.)" % (room_id, host_id)
    while True:
        message = raw_input("<< ")
        wrapper.sendMessage(room_id, message)

    wrapper.logout()


def on_message(message, wrapper):
    if not isinstance(message, chatexchange.events.MessagePosted):
        # Ignore non-message_posted events.
        logger.debug("event: %r", message)
        return

    print ""
    print ">> (%s) %s" % (message.user_name, message.text_content)
    if message.content.startswith('!!/random'):
        print message
        print "Spawning thread"
        message.reply(str(random.random()))


def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)

    # In addition to the basic stderr logging configured globally
    # above, we'll use a log file for chatexchange.wrapper.
    wrapper_logger = logging.getLogger('chatexchange.wrapper')
    wrapper_handler = logging.handlers.TimedRotatingFileHandler(
        filename='wrapper.log',
        when='midnight', delay=True, utc=True, backupCount=7,
    )
    wrapper_handler.setFormatter(logging.Formatter(
        "%(asctime)s: %(levelname)s: %(threadName)s: %(message)s"
    ))
    wrapper_logger.addHandler(wrapper_handler)


if __name__ == '__main__':
    main(*sys.argv[1:])
