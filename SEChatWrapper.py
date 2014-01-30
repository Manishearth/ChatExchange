import SEChatBrowser

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
