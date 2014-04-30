#!/usr/bin/env python
import getpass
import logging
import os
import random
import sys
import threading
import time

import chatexchange.wrapper


logging.basicConfig(level=logging.INFO)

#Run `. setp.sh` to set the below testing environment variables

host_id = "SE"
room_id = "11540"

if "ChatExchangeU" in os.environ:
    username = os.environ["ChatExchangeU"]
else:
    sys.stderr.write("Username: ")
    sys.stderr.flush()
    username = raw_input()
if "ChatExchangeP" in os.environ:
    password = os.environ["ChatExchangeP"]
else:
    password = getpass.getpass("Password: ")

wrapper = chatexchange.wrapper.SEChatWrapper(host_id)
wrapper.login(username,password)

def on_message(msg, wrapper):
    if msg.type != msg.Types.message_posted:
        return

    print ""
    print ">> ("+msg.user_name+")", msg.content
    print ""
    if msg.content.startswith('!!/random'):
        print msg
        ret = "@%s %s" % (msg.user_name, random.random())
        print "Spawning thread"
        wrapper.sendMessage(msg.room_id, ret)


wrapper.joinRoom(room_id)
wrapper.watchRoom(room_id, on_message, 1)

# If WebSockets are available, one could instead use:
#     wrapper.watchRoomSocket(room, on_message)

print "(You are now in room #%s on %s.)" % (room_id, host_id)
while True:
    message = raw_input("<< ")
    wrapper.sendMessage(room_id, message)

wrapper.logout()
