#!/usr/bin/python

import SEChatWrapper,SEChatWrapperAsync
import getpass
import os
import time,threading
import random
#Run `. setp.sh` to set the below testing environment variables

host="MSO"
room="651"
if("ChatExchangeU" in os.environ):
  username=os.environ["ChatExchangeU"]
else:
  print "Username: "
  username = raw_input()
if("ChatExchangeP" in os.environ):
  password = os.environ["ChatExchangeP"]
else:
  password = getpass.getpass("Password: ")

a=SEChatWrapperAsync.SEChatAsyncWrapper(host)
a.login(username,password)
def omsg(msg,wrap):
  print ""
  print ">> ("+msg['user_name']+") ",msg['content']
  print ""
  if(msg['content'].startswith("!!/random")):
    print msg
    ret = "@"+msg['user_name']+" "+str(random.random())
    print "Spawning thread"
    wrap.sendMessage(msg["room_id"],ret)


a.joinRoom(room)

a.watchRoom(room,omsg,1)
#print a.sendMessage("11540","Manish is still testing the wrapper --the wrapper, ca 15 milliseconds ago")
print "Ready"
while(True):
  b=raw_input("<< ")
  a.sendMessage(room,b)
a.logout()
