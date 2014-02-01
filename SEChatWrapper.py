import SEChatBrowser
import re
import time

TOO_FAST_RE = "You can perform this action again in (\d+) seconds"


class SEChatWrapper(object):

  def __init__(self, site="SE"):
    self.br = SEChatBrowser.SEChatBrowser()
    self.site = site
    self.previous = None

  def login(self, username, password):
    self.br.loginSEOpenID(username, password)
    if self.site == "SE":
      self.br.loginSECOM()
      self.br.loginChatSE()
    elif self.site == "SO":
      self.br.loginSO()
    elif self.site == "MSO":
      self.br.loginMSO()

  def sendMessage(self, room, text):
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
