import json
from BeautifulSoup import BeautifulSoup
import requests
import sys
import re
import websocket


class SEChatBrowser:
  def __init__(self):
    self.session = requests.Session()
    self.rooms={}
    self.sockets={}
    self.chatfkey = ""
    self.chatroot = "http://chat.stackexchange.com"

  def loginSEOpenID(self, user, password):
    self.userlogin=user
    self.userpass=password
    fkey = self.getSoup("https://openid.stackexchange.com/account/login") \
             .find('input', {"name": "fkey"})['value']
    logindata = {"email": user,
                 "password": password,
                 "fkey": fkey}
    return self.session.post("https://openid.stackexchange.com/account/login/submit",
                             data=logindata,
                             allow_redirects=True)

  def loginSECOM(self):
    fkey = self.getSoup("http://stackexchange.com/users/login?returnurl = %2f") \
             .find('input', {"name": "fkey"})['value']
    data = {"fkey": fkey,
            "oauth_version": "",
            "oauth_server": "",
            "openid_identifier": "https://openid.stackexchange.com/"}
    return self.session.post("http://stackexchange.com/users/authenticate",
                             data=data,
                             allow_redirects=True)

  def loginMSOOld(self):
    fkey = self.getSoup("http://meta.stackoverflow.com/users/login?returnurl = %2f") \
             .find('input', {"name": "fkey"})['value']
    data = {"fkey": fkey,
            "oauth_version": "",
            "oauth_server": "",
            "openid_identifier": "https://openid.stackexchange.com/"}
    self.session.post("http://meta.stackoverflow.com/users/authenticate",
                      data=data,
                      allow_redirects=True)
    self.chatroot = "http://chat.meta.stackoverflow.com"
    self.updateFkey()

  def loginMSO(self):
    fkey = self.getSoup("http://meta.stackoverflow.com/users/login?returnurl = %2f") \
             .find('input', {"name": "fkey"})['value']
    data = {"fkey": fkey,
            "oauth_version": "",
            "oauth_server": "",
            "openid_identifier": "https://openid.stackexchange.com/"}
    self.session.post("http://meta.stackoverflow.com/users/authenticate",
                      data=data,
                      allow_redirects=True)
    self.chatroot = "http://chat.meta.stackoverflow.com"
    self.updateFkey()
  def loginSO(self):
    fkey = self.getSoup("http://stackoverflow.com/users/login?returnurl = %2f") \
             .find('input', {"name": "fkey"})['value']
    data = {"fkey": fkey,
            "oauth_version": "",
            "oauth_server": "",
            "openid_identifier": "https://openid.stackexchange.com/"}
    self.session.post("http://stackoverflow.com/users/authenticate",
                      data=data,
                      allow_redirects=True)
    self.chatroot = "http://chat.stackoverflow.com"
    self.updateFkey()

  def loginChatSE(self):
    chatlogin = self.getSoup("http://stackexchange.com/users/chat-login")
    authToken = chatlogin.find('input', {"name": "authToken"})['value']
    nonce = chatlogin.find('input', {"name": "nonce"})['value']
    data = {"authToken": authToken, "nonce": nonce}
    referer_header = {"Referer": "http://stackexchange.com/users/chat-login"}
    rdata = self.session.post("http://chat.stackexchange.com/login/global-fallback",
                              data=data,
                              allow_redirects=True,
                              headers=referer_header).content
    fkey = BeautifulSoup(rdata).find('input', {"name": "fkey"})['value']
    self.chatfkey = fkey
    self.chatroot = "http://chat.stackexchange.com"
    return rdata

  def updateFkey(self):
    try:
      fkey = self.getSoup(self.getURL("chats/join/favorite")) \
               .find('input', {"name": "fkey"})['value']
      if fkey is not None and fkey != "":
        self.chatfkey = fkey
        return True
    except Exception as e:
        print "Error updating fkey:", e
    return False

  def postSomething(self, relurl, data):
    data['fkey'] = self.chatfkey
    req=self.post(self.getURL(relurl), data)
    try:
      return req.json()
    except Exception:
      return req.content

  def getSomething(self, relurl):
    return self.session.get(self.getURL(relurl)).content

  def getSoup(self, url):
    return BeautifulSoup(self.session.get(url).content)
  def initSocket(self,roomno,func):
    """
    Does not work. Use polling of /events
    """
    eventtime=self.postSomething("/chats/"+str(roomno)+"/events",{"since":0,"mode":"Messages","msgCount":100})['time']
    print eventtime
    wsurl=self.postSomething("/ws-auth",{"roomid":roomno})['url']+"?l="+str(eventtime)
    print wsurl
    self.sockets[roomno]={"url":wsurl}
    #return
    self.sockets[roomno]['ws']=websocket.create_connection(wsurl,origin=self.chatroot)
    #self.sockets[roomno]['ws']=websocket.create_connection(wsurl)
    def runner():
        print "start"
        print roomno
        #look at wsdump.py later to handle opcodes
        while (True):
            a=self.sockets[roomno]['ws'].recv()
            print "a",a
            if(a != None and a!=""):
                func(a)
    print "ready"
    self.sockets[roomno]['thread']=threading.Thread(target=runner)
    self.sockets[roomno]['thread'].setDaemon(True)
    self.sockets[roomno]['thread'].start()
    print "r2"
  def post(self,url,data):
    return self.session.post(url,data)
  def joinRoom(self,roomid):
    roomid=str(roomid)
    self.rooms[roomid]={}
    result=self.postSomething("/chats/"+str(roomid)+"/events",{"since":0,"mode":"Messages","msgCount":100})
    eventtime=result['time']
    self.rooms[roomid]["eventtime"]=eventtime
  def pokeRoom(self,roomid):
    roomid=str(roomid)
    if(not self.rooms[roomid]):
        return false
    pokeresult=self.postSomething("/events",{"r"+roomid:self.rooms[roomid]['eventtime']})
    try:
        roomresult=pokeresult["r"+str(roomid)]
        newtime=roomresult["t"]
        self.rooms[roomid]["eventtime"]=newtime
    except KeyError:
        "NOP"
    return pokeresult
  def getURL(self,rel):
    if(rel[0]!="/"):
      rel="/"+rel
    return self.chatroot+rel
