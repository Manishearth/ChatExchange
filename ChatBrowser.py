#from mechanize import *
import json
from BeautifulSoup import *
import requests
siteroot="http://chat.stackexchange.com"
import sys
import re

def getURL(rel):
  if(rel[0]!="/"):
    rel="/"+rel
  return siteroot+rel

class ChatBrowser:
  def __init__(self):
    #self.b=Browser()
    #self.b.set_handle_robots(False)
    #self.b.set_proxies({})
    self.session=requests.session()

  def loginSEOpenID(self,user,password):
    fkey=self.getSoup("https://openid.stackexchange.com/account/login").find('input',{"name":"fkey"})['value']
    print fkey    
    logindata={"email":user,"password":password,"fkey":fkey}
    self.post("https://openid.stackexchange.com/account/login/submit",logindata)
  
  def loginSECOM(self):
    fkey=self.getSoup("http://stackexchange.com/users/login?returnurl=%2f").find('input',{"name":"fkey"})['value']
    data={"fkey":fkey,"oauth_version":"","oauth_server":"","openid_identifier":"https://openid.stackexchange.com/"}
    self.post("http://stackexchange.com/users/authenticate",data)
  
  def getSoup(self,url):
    return BeautifulSoup(self.session.get(url).content)
  
  def getHTM(self,url):
    return self.session.get(url).content
  
  def post(self,url,data):
    return self.session.post(url,data)
