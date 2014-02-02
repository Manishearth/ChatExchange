#from mechanize import *
from BeautifulSoup import *
import requests


class SEChatBrowser(object):
  def __init__(self):
    #self.b = Browser()
    #self.b.set_handle_robots(False)
    #self.b.set_proxies({})
    self.session = requests.Session()
    self.chatfkey = ""
    self.chatroot = "http://chat.stackexchange.com"

  def loginSEOpenID(self, user, password):
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
    try:
      self.post(self.getURL(relurl), data).json()
    except Exception:
      return self.post(self.getURL(relurl), data).content

  def getSomething(self, relurl):
    return self.session.get(self.getURL(relurl)).content

  def getSoup(self, url):
    return BeautifulSoup(self.session.get(url).content)

  def post(self, url, data):
    return self.session.post(url, data)

  def getURL(self, rel):
    if rel[0] != "/":
      rel = "/"+rel
    return self.chatroot+rel
