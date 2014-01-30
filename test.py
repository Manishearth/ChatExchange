import SEChatBrowser
import SEChatWrapper
import getpass
import os

a=SEChatWrapper.SEChatWrapper("SE")
if("ChatExchangeU" in os.environ):
  username=os.environ["ChatExchangeU"]
else:
  print "Username: "
  username=raw_input()
if("ChatExchangeP" in os.environ):
  password=os.environ["ChatExchangeP"]
else:
  password=getpass.getpass("Password: ")

a.login(username,password)


print a.br.sendMessage("11540","This was sent by ChatExchange")
