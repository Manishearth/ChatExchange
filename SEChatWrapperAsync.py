import SEChatBrowser
import re
import time
import Queue
import threading
import logging
import logging.handlers

TOO_FAST_RE = "You can perform this action again in (\d+) seconds"


def _getLogger():
  logHandler = logging.handlers.TimedRotatingFileHandler(
    filename='async-wrapper.log',
    when="midnight", delay=True, utc=True, backupCount=7,
  )
  logHandler.setFormatter(logging.Formatter(
    "%(asctime)s: %(levelname)s: %(threadName)s: %(message)s"
  ))
  logger = logging.Logger(__name__)
  logger.addHandler(logHandler)
  logger.setLevel(logging.DEBUG)
  return logger


class SEChatAsyncWrapper(object):

  def __init__(self, site="SE"):
    self.logger = _getLogger()
    self.br = SEChatBrowser.SEChatBrowser()
    self.site = site
    self._previous = None
    self.message_queue = Queue.Queue()
    self.thread = threading.Thread(target=self._worker, name="message_sender")
    self.logged_in = False

  def login(self, username, password):
    assert not self.logged_in
    self.logger.info("Logging in.")

    self.br.loginSEOpenID(username, password)
    if self.site == "SE":
      self.br.loginSECOM()
      self.br.loginChatSE()
    elif self.site == "SO":
      self.br.loginSO()
    elif self.site == "MSO":
      self.br.loginMSO()

    self.logged_in = True
    logging.self.logger.info("Logged in.")
    self.thread.start()

  def logout(self):
    assert self.logged_in
    self.message_queue.push(SystemExit)
    self.logger.info("Logged out.")

  def sendMessage(self, room, text):
    self.message_queue.push((room, text))
    self.logger.info("Queued message %r for room #%r.", text, room)
    self.logger.info("Queue length: %d.", self.message_queue.qsize())

  def __del__(self):
    if self.logged_in:
      self.message_queue.push(SystemExit) # todo: underscore everything used by
                                          # the thread so this is guaranteed
                                          # to work.
      assert False, "You forgot to log out."

  def _worker(self):
    assert self.logged_in
    self.logger.info("Worker thread reporting for duty.")
    while True:
      next = self.message_queue.get() # blocking
      if next == SystemExit:
        self.logger.info("Worker thread exits.")
        return
      else:
        room, text = next
        self.logger.info("Now serving %r for room #%r." % (text, room))
        self._actuallySendMessage(room, text) # also blocking.
      self.message_queue.task_done()

  def _actuallySendMessage(self, room, text):
    room = str(room)
    sent = False
    attempt = 0
    if text == self._previous:
      text = " " + text
    while not sent:
      wait = 0
      attempt += 1
      self.logger.debug("Attempt %d start.")
      response = self.br.postSomething("/chats/"+room+"/messages/new",
                                       {"text": text})
      if isinstance(response, str):
        match = re.match(TOO_FAST_RE, response)
        if match: # Whoops, too fast.
          wait = int(match.group(1))
          self.logger.debug("Attempt %d: denied: throttled, must wait %.1f seconds",
                            attempt, wait)
          # Wait more than that, though.
          wait *= 1.5
        else: # Something went wrong. I guess that happens.
          wait = 5
          logging.error("Attempt %d: denied: unknown reason %r",
                        attempt, response, wait)
      elif isinstance(response, dict):
        if response["id"] is None: # Duplicate message?
          text = text + " " # Let's not risk turning the message
          wait = 5          # into a codeblock accidentally.
          self.logger.debug("Attempt %d: denied: duplicate, waiting %.1f seconds.",
                            attempt, wait)

      if wait:
        self.logger.debug("Attempt %d: waiting %.1f seconds", attempt, wait)
        time.sleep(wait)
      else:
        self.logger.debug("Attempt %d: success", attempt)
        sent = True
        self._previous = text

    time.sleep(5)
