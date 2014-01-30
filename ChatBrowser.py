#from mechanize import *
import json
from BeautifulSoup import *
import requests
siteroot="http://chat.stackexchange.com"
import sys
import re



class ChatBrowser:
  def __init__(self):
    #self.b=Browser()
    #self.b.set_handle_robots(False)
    #self.b.set_proxies({})
    self.session=requests.session()
    self.chatfkey=""

  def loginSEOpenID(self,user,password):
    fkey=self.getSoup("https://openid.stackexchange.com/account/login").find('input',{"name":"fkey"})['value'] 
    logindata={"email":user,"password":password,"fkey":fkey}
    self.session.post("https://openid.stackexchange.com/account/login/submit",data=logindata,allow_redirects=True)
  
  def loginSECOM(self):
    fkey=self.getSoup("http://stackexchange.com/users/login?returnurl=%2f").find('input',{"name":"fkey"})['value']
    data={"fkey":fkey,"oauth_version":"","oauth_server":"","openid_identifier":"https://openid.stackexchange.com/"}
    self.session.post("http://stackexchange.com/users/authenticate",data=data,allow_redirects=True)
  
  def loginChat(self):
    chatlogin=self.getSoup("http://stackexchange.com/users/chat-login")
    authToken=chatlogin.find('input',{"name":"authToken"})['value']
    nonce=chatlogin.find('input',{"name":"nonce"})['value']
    data={"authToken":authToken,"nonce":nonce}
    rdata=self.session.post("http://chat.stackexchange.com/login/global-fallback",data=data,,allow_redirects=True,headers={"Referer":"http://stackexchange.com/users/chat-login"}).content
    fkey=BeautifulSoup(rdata).find('input',{"name":"fkey"})['value']
    self.chatfkey=fkey
  
  def updateFkey(self):
    try:
      fkey=getSoup("http://chat.stackexchange.com/chats/join/favorite").find('input',{"name":"fkey"})['value']
      if(fkey!=None and fkey!=""):
        self.chatfkey=fkey
        return true
    except(e):
      return false
    return false
  
  def postSomething(self,relurl,data):
    data['fkey']=self.chatfkey
    return self.post(self.getURL(relurl),data).content
  def getSomething(self,relurl):
    return self.get(self.getURL(relurl)).content
  def sendMessage(self,room,message):
    return self.postSomething("/chats/"+room+"/messages/new",{"text":message})
  def getSoup(self,url):
    return BeautifulSoup(self.session.get(url).content)
  
  def getHTM(self,url):
    return self.session.get(url).content
  
  def post(self,url,data):
    return self.session.post(url,data)
  def getURL(self,rel):
    if(rel[0]!="/"):
      rel="/"+rel
    return siteroot+rel
