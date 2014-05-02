import logging
import logging.handlers
import Queue
import re
import threading
import time
import warnings

from . import browser


warnings.warn("Deprecated class, use SEChatWrapper", DeprecationWarning)


TOO_FAST_RE = "You can perform this action again in (\d+) seconds"


logger = logging.getLogger(__name__)


class SEChatAsyncWrapper(object):
    def __init__(self, site="SE"):
        self.logger = logger
        self.br = browser.SEChatBrowser()
        self.site = site
        self._previous = None
        self.message_queue = Queue.Queue()
        self.logged_in = False
        self.messages = 0
        self.thread = threading.Thread(target=self._worker, name="message_sender")
        self.thread.setDaemon(True)

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
        self.logger.info("Logged in.")
        self.thread.start()

    def logout(self):
        assert self.logged_in
        self.message_queue.put(SystemExit)
        self.logger.info("Logged out.")
        self.logged_in = False

    def sendMessage(self, room, text):
        self.message_queue.put((room, text))
        self.logger.info("Queued message %r for room #%r.", text, room)
        self.logger.info("Queue length: %d.", self.message_queue.qsize())

    def __del__(self):
        if self.logged_in:
            self.message_queue.put(SystemExit) # todo: underscore everything used by
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
                self.messages += 1
                room, text = next
                self.logger.info("Now serving customer %d, %r for room #%s.",
                                                    self.messages, text, room)
                self._actuallySendMessage(room, text) # also blocking.
            self.message_queue.task_done()

    # Appeasing the rate limiter gods is hard.
    BACKOFF_MULTIPLIER = 2
    BACKOFF_ADDER = 5

    # When told to wait n seconds, wait n * BACKOFF_MULTIPLIER + BACKOFF_ADDER

    def _actuallySendMessage(self, room, text):
        room = str(room)
        sent = False
        attempt = 0
        if text == self._previous:
            text = " " + text
        while not sent:
            wait = 0
            attempt += 1
            self.logger.debug("Attempt %d: start.", attempt)
            response = self.br.postSomething("/chats/"+room+"/messages/new",
                                                                             {"text": text})
            if isinstance(response, str):
                match = re.match(TOO_FAST_RE, response)
                if match: # Whoops, too fast.
                    wait = int(match.group(1))
                    self.logger.debug("Attempt %d: denied: throttled, must wait %.1f seconds",
                                                        attempt, wait)
                    # Wait more than that, though.
                    wait *= self.BACKOFF_MULTIPLIER
                    wait += self.BACKOFF_ADDER
                else: # Something went wrong. I guess that happens.
                    wait = self.BACKOFF_ADDER
                    logging.error("Attempt %d: denied: unknown reason %r",
                                                attempt, response)
            elif isinstance(response, dict):
                if response["id"] is None: # Duplicate message?
                    text = text + " " # Append because markdown
                    wait = self.BACKOFF_ADDER
                    self.logger.debug("Attempt %d: denied: duplicate, waiting %.1f seconds.",
                                                        attempt, wait)

            if wait:
                self.logger.debug("Attempt %d: waiting %.1f seconds", attempt, wait)
            else:
                wait = self.BACKOFF_ADDER
                self.logger.debug("Attempt %d: success. Waiting %.1f seconds", attempt, wait)
                sent = True
                self._previous = text

            time.sleep(wait)

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
        thethread = threading.Thread(target=pokeMe)
        thethread.setDaemon(True)
        thethread.start()
        return thethread
