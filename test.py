#!/usr/bin/python

import SEChatWrapper
import getpass
import os

#Run `. setp.sh` to set the below testing environment variables
if "ChatExchangeU" in os.environ:
  username = os.environ["ChatExchangeU"]
else:
  print "Username: "
  username = raw_input()
if("ChatExchangeP" in os.environ):
  password = os.environ["ChatExchangeP"]
else:
  password = getpass.getpass("Password: ")

a = SEChatWrapper.SEChatWrapper("SE")
a.login(username, password)
#print a.sendMessage("11540","Manish is still testing the wrapper --the wrapper, ca 15 milliseconds ago")
