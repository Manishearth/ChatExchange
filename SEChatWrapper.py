import SEChatBrowser
import threading
import time
class SEChatWrapper:
  def __init__(self,site="SE"):
    self.br=SEChatBrowser.SEChatBrowser()
    self.site=site
  def login(self,username,password):
    self.br.loginSEOpenID(username,password)
    if(self.site == "SE"):
      self.br.loginSECOM()
      self.br.loginChatSE()
    elif (self.site =="SO"):
      self.br.loginSO()
    elif (self.site=="MSO"):
      self.br.loginMSO()
  def sendMessage(self,room,text):
    return  self.br.postSomething("/chats/"+room+"/messages/new",{"text":text})
  def joinRoom(self,roomid):
    self.br.joinRoom(roomid)
  def watchRoom(self,roomid,func,interval):
    def pokeMe():
      while(True):
        try:
          pokeresult=self.br.pokeRoom(roomid)
          events=pokeresult["r"+str(roomid)]["e"]
          func(events)
        except KeyError:
          "NOP"
        finally:
          time.sleep(interval)
    thethread=threading.Thread(target=pokeMe)
    thethread.setDaemon(True)
    thethread.start()
    return thethread

"""
[{"event_type":1,"time_stamp":1391324366,"content":"boooo","id":25123259,"user_id":31768,"user_name":"ManishEarth","room_id":11540,"room_name":"Charcoal HQ","message_id":13536215}]
"""
