import re
import time
import Queue
import threading
import logging
import logging.handlers
import warnings

import BeautifulSoup

from . import browser, events


TOO_FAST_RE = r"You can perform this action again in (\d+) seconds"


logger = logging.getLogger(__name__)


class SEChatWrapper(object):
    def __init__(self, site="SE"):
        self.logger = logger.getChild('SEChatWraper')

        if site == 'MSO':
            self.logger.warn("'MSO' should no longer be used, use 'MSE' instead.")
            site = 'MSE'
        self.br = browser.SEChatBrowser()
        self.site = site
        self._previous = None
        self.request_queue = Queue.Queue()
        self.logged_in = False
        self._requests_served = 0
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
        elif self.site == "MSE":
            self.br.loginMSE()
        else:
            raise ValueError("Unable to login to site: %r" % (self.site,))


        self.logged_in = True
        self.logger.info("Logged in.")
        self.thread.start()

    def logout(self):
        assert self.logged_in
        self.request_queue.put(SystemExit)
        self.logger.info("Logged out.")
        self.logged_in = False

    def sendMessage(self, room_id, text):
        warnings.warn(
            "Use send_message instead of sendMessage",
            DeprecationWarning, stacklevel=1)
        return self.send_message(room_id, text)

    def send_message(self, room_id, text):
        """
        Queues a message for sending to a given room.
        """
        self.request_queue.put(('send', room_id, text))
        self.logger.info("Queued message %r for room_id #%r.", text, room_id)
        self.logger.info("Queue length: %d.", self.request_queue.qsize())

    def edit_message(self, message_id, text):
        """
        Queues an edit to be made to a message.
        """
        self.request_queue.put(('edit', message_id, text))
        self.logger.info("Queued edit %r for message_id #%r.", text, message_id)
        self.logger.info("Queue length: %d.", self.request_queue.qsize())

    def __del__(self):
        if self.logged_in:
            self.request_queue.put(SystemExit)
            # todo: underscore everything used by
            # the thread so this is guaranteed
            # to work.
            assert False, "You forgot to log out."

    def _worker(self):
        assert self.logged_in
        self.logger.info("Worker thread reporting for duty.")
        while True:
            next_action = self.request_queue.get() # blocking
            if next_action == SystemExit:
                self.logger.info("Worker thread exits.")
                return
            else:
                action_type = next_action[0]

                self._requests_served += 1
                self.logger.info(
                    "Now serving customer %d, %r",
                    self._requests_served, next_action)

                self._do_action_despite_throttling(next_action)

            self.request_queue.task_done()


    # Appeasing the rate limiter gods is hard.
    BACKOFF_MULTIPLIER = 2
    BACKOFF_ADDER = 5

    # When told to wait n seconds, wait n * BACKOFF_MULTIPLIER + BACKOFF_ADDER

    def _do_action_despite_throttling(self, action):
        action_type = action[0]
        if action_type == 'send':
            action_type, room_id, text = action
        else:
            assert action_type == 'edit'
            action_type, message_id, text = action

        sent = False
        attempt = 0
        if text == self._previous:
            text = " " + text
        while not sent:
            wait = 0
            attempt += 1
            self.logger.debug("Attempt %d: start.", attempt)

            if action_type == 'send':
                response = self.br.postSomething(
                    '/chats/%s/messages/new' % (room_id,),
                    {'text': text})
            else:
                assert action_type == 'edit'
                response = self.br.postSomething(
                    '/messages/%s' % (message_id,),
                    {'text': text})

            if isinstance(response, str):
                match = re.match(TOO_FAST_RE, response)
                if match: # Whoops, too fast.
                    wait = int(match.group(1))
                    self.logger.debug(
                        "Attempt %d: denied: throttled, must wait %.1f seconds",
                        attempt, wait)
                    # Wait more than that, though.
                    wait *= self.BACKOFF_MULTIPLIER
                    wait += self.BACKOFF_ADDER
                else: # Something went wrong. I guess that happens.
                    wait = self.BACKOFF_ADDER
                    logging.error(
                        "Attempt %d: denied: unknown reason %r",
                        attempt, response)
            elif isinstance(response, dict):
                if response["id"] is None: # Duplicate message?
                    text = text + " " # Append because markdown
                    wait = self.BACKOFF_ADDER
                    self.logger.debug(
                        "Attempt %d: denied: duplicate, waiting %.1f seconds.",
                        attempt, wait)

            if wait:
                self.logger.debug("Attempt %d: waiting %.1f seconds", attempt, wait)
            else:
                wait = self.BACKOFF_ADDER
                self.logger.debug("Attempt %d: success. Waiting %.1f seconds", attempt, wait)
                sent = True
                self._previous = text

            time.sleep(wait)

    def joinRoom(self, room_id):
        self.br.joinRoom(room_id)

    def _room_events(self, activity, room_id):
        """
        Returns a list of Events associated with a particular room,
        given an activity message from the server.
        """
        room_activity = activity.get('r' + room_id, {})
        room_events_data = room_activity.get('e', [])
        room_events = [
            events.make(data, self) for data in room_events_data if data]
        return room_events

    def watchRoom(self, room_id, on_event, interval):
        def on_activity(activity):
            for event in self._room_events(activity, room_id):
                on_event(event, self)

        self.br.watch_room_http(room_id, on_activity, interval)

    def watchRoomSocket(self, room_id, on_event):
        def on_activity(activity):
            for event in self._room_events(activity, room_id):
                on_event(event, self)

        self.br.watch_room_socket(room_id, on_activity)
