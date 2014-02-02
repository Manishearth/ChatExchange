import SEChatBrowser
import re
import time

TOO_FAST_RE = "You can perform this action again in (\d+) seconds"


class SEChatWrapper(object):

  def __init__(self, site="SE"):
    self.br = SEChatBrowser.SEChatBrowser()
    self.site = site
    self.previous = None
    self.logged_in = False

  def login(self, username, password):
    assert not self.logged_in

    self.br.loginSEOpenID(username, password)
    if self.site == "SE":
      self.br.loginSECOM()
      self.br.loginChatSE()
    elif self.site == "SO":
      self.br.loginSO()
    elif self.site == "MSO":
      self.br.loginMSO()

    self.logged_in = True

  def logout(self):
    assert self.logged_in
    self.logged_in = False
    pass # There are no threads to stop

  def __del__(self):
    assert not self.logged_in, "You forgot to log out."

  def sendMessage(self, room, text):
    assert self.logged_in
    sent = False
    if text == self.previous:
      text = " " + text
    while not sent:
      wait = 0
      response = self.br.postSomething("/chats/"+room+"/messages/new",
                                       {"text": text})
      if isinstance(response, str): # Whoops, too fast.
        match = re.match(TOO_FAST_RE, response)
        if match:
          wait = int(match.group(1)) * 1.5
      elif isinstance(response, dict):
        if response["id"] is None: # Duplicate message?
          text = text + " " # Let's not risk turning the message
          wait = 1          # into a codeblock accidentally.

      if wait:
        print "Waiting %.1f seconds" % wait
        time.sleep(wait)
      else:
        sent = True
        self.previous = text
    time.sleep(5)
    return response
  def sendMessageOld(self,room,text):
    room=str(room)
    data=self.br.postSomething("/chats/"+room+"/messages/new",{"text":text})
    try:
      data=json.loads(data)
      self.br.rooms[room]["eventtime"]=data["time"]
      return data
    except ValueError,KeyError:
      return False
  def forceMessage(self,room,text,pad=1):
    """
    forceMessage(room,text)
    Sends a message whenever possible, if it's being ratelimited
    """
    status=self.sendMessage(room,text)
    if(status):
      return True
    mat=re.match("You can perform this action again in (\d)+ seconds","You can perform this action again in 3 seconds")
    if(mat):
      print "Waiting for ratelimit",mat.group(1)
      time.sleep(int(mat.group(1))+pad)
      self.forceMessage(room,text)
  def joinRoom(self,roomid):
    self.br.joinRoom(roomid)
  def watchRoom(self,roomid,func,interval):
    def pokeMe():
      while(True):
        try:
          pokeresult=self.br.pokeRoom(roomid)
          events=pokeresult["r"+str(roomid)]["e"]
          for event in events:
            func(event,self)
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

