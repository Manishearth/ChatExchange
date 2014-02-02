import SEChatBrowser
import SEChatWrapper
import getpass
import os
import time
import random
#Run `. setp.sh` to set the below testing environment variables

host="MSO"
room="89"
if("ChatExchangeU" in os.environ):
  username=os.environ["ChatExchangeU"]
else:
  print "Username: "
  username=raw_input()
if("ChatExchangeP" in os.environ):
  password=os.environ["ChatExchangeP"]
else:
  password=getpass.getpass("Password: ")

a=SEChatWrapper.SEChatWrapper(host)
a.login(username,password)
def omsg(msg,wrap):
  print ""
  print ">> ("+msg['user_name']+") ",msg['content']
  print ""
  if(msg['content'].startswith("!!/random")):
    wrap.sendMessage(str(msg["room_id"]),"@"+msg['user_name']+" "+str(random.random()))
a.joinRoom(room)

a.watchRoom(room,omsg,1)
#print a.sendMessage("11540","Manish is still testing the wrapper --the wrapper, ca 15 milliseconds ago")
print "Ready"
while(True):
  b=raw_input("<< ")
  a.sendMessage(room,b)
