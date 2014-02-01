import SEChatBrowser
import re
import time
import Queue
import threading

TOO_FAST_RE = "You can perform this action again in (\d+) seconds"


class SEChatAsyncWrapper(object):

  def __init__(self, site="SE"):
    self.br = SEChatBrowser.SEChatBrowser()
    self.site = site
    self.previous = None
    self.message_queue = Queue.Queue()
    self.thread = threading.Thread(target=self._worker, name="message_sender")
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
    self.thread.start()

  def logout(self):
    assert self.logged_in
    self.message_queue.push(SystemExit)

  def sendMessage(self, room, text):
    self.message_queue.push((room, text))

  def __del__(self):
    if self.logged_in:
      self.message_queue.push(SystemExit) # todo: underscore everything used by
                                          # the thread so this is guaranteed
                                          # to work.
      assert False, "You forgot to log out."

  def _worker(self):
    assert self.logged_in
    while True:
      next = self.message_queue.get() # blocking
      if next == SystemExit:
        return
      else:
        room, text = next
        self._actuallySendMessage(room, text) # also blocking.
      self.message_queue.task_done()

  def _actuallySendMessage(self, room, text):
    room = str(room)
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
