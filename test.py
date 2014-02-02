import SEChatBrowser
import SEChatWrapper
import getpass
import os
import time

#Run `. setp.sh` to set the below testing environment variables
if("ChatExchangeU" in os.environ):
  username=os.environ["ChatExchangeU"]
else:
  print "Username: "
  username=raw_input()
if("ChatExchangeP" in os.environ):
  password=os.environ["ChatExchangeP"]
else:
  password=getpass.getpass("Password: ")

a=SEChatWrapper.SEChatWrapper("MSO")
a.login(username,password)
def omsg(msg):
  print "\n>> ("+msg[0]['user_name']+") ",msg[0]['content']
a.joinRoom("89")

a.watchRoom("89",omsg,1)
#print a.sendMessage("11540","Manish is still testing the wrapper --the wrapper, ca 15 milliseconds ago")
print "Ready"
while(True):
  b=raw_input("<< ")
  a.sendMessage("89",b)
