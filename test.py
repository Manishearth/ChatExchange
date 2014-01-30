from ChatBrowser import *
import getpass
import os

a=ChatBrowser()
if("ChatExchangeU" in os.environ):
  username=os.environ["ChatExchangeU"]
else:
  print "Username: "
  username=raw_input()
if("ChatExchangeP" in os.environ):
  password=os.environ["ChatExchangeP"]
else:
  print "Username: "
  password=getpass.getpass("Password: ")

a.loginSEOpenID(username,password)
a.loginSECOM()
