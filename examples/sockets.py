#!/usr/bin/env python
import logging
import os

import chatexchange.wrapper


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#Run `. setp.sh` to set the below testing environment variables


def on_socket_activity(activity):
    logger.info('activity == %r', activity)

wrapper = chatexchange.wrapper.SEChatWrapper('SE')
wrapper.login(os.environ['ChatExchangeU'], os.environ['ChatExchangeP'])
wrapper.joinWatchSocket('11540', on_socket_activity)

logger.info("Waiting for socket activity.")
wrapper.br.sockets['11540'].thread.join()
