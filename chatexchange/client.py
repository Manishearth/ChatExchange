import collections
import re
import time
import Queue
import threading
import logging
import warnings
import weakref

import requests

from . import browser, events, messages, rooms, users


TOO_FAST_RE = r"You can perform this action again in (\d+) seconds"


logger = logging.getLogger(__name__)


class Client(object):
    max_recent_events = 1000
    max_recently_gotten_objects = 5000

    def __init__(self, host='stackexchange.com', email=None, password=None):
        self.logger = logger.getChild('SEChatWraper')

        if email or password:
            assert email and password, (
                "must specify both email and password or neither")

        # any known instances
        self._messages = weakref.WeakValueDictionary()
        self._rooms = weakref.WeakValueDictionary()
        self._users = weakref.WeakValueDictionary()

        if host in self._deprecated_hosts:
            replacement = self._deprecated_hosts[host]
            warnings.warn(
                "host value %r is deprecated, use %r instead" % (
                    host, replacement
                ), DeprecationWarning, stacklevel=2)
            host = replacement

        if host not in self.valid_hosts:
            raise ValueError("invalid host: %r" % (host,))

        self.br = browser.Browser()
        self.br.host = host
        self.host = host
        self._previous = None
        self.request_queue = Queue.Queue()
        self.logged_in = False
        self.recent_events = collections.deque(maxlen=self.max_recent_events)
        self._recently_gotten_objects = collections.deque(maxlen=self.max_recently_gotten_objects)
        self._requests_served = 0
        self.thread = threading.Thread(target=self._worker, name="message_sender")
        self.thread.setDaemon(True)

        if email:
            self.login(email, password)

    def get_message(self, message_id, **attrs):
        """
        Gets the (possibly new) Message instance with the given message_id.

        Updates it will the specified attribute values.
        """
        return self._get_deduplicated(
            messages.Message, message_id, self._messages, attrs)

    def get_room(self, room_id, **attrs):
        return self._get_deduplicated(
            rooms.Room, room_id, self._rooms, attrs)

    def get_user(self, user_id, **attrs):
        return self._get_deduplicated(
            users.User, user_id, self._users, attrs)

    def _get_deduplicated(self, cls, id, instances, attrs):
        instance = instances.setdefault(id, cls(id, self))

        for key, value in attrs.items():
            setattr(instance, key, value)

        # we force a fixed number of recent objects to be cached
        self._recently_gotten_objects.appendleft(instance)

        return instance

    valid_hosts = {
        'stackexchange.com',
        'meta.stackexchange.com',
        'stackoverflow.com'
    }

    _deprecated_hosts = {
        'SE': 'stackexchange.com',
        'MSO': 'meta.stackexchange.com',
        'MSE': 'meta.stackexchange.com',
        'SO': 'stackexchange.com'
    }

    def get_me(self):
        assert self.br.user_id is not None
        return self.get_user(self.br.user_id, name=self.br.user_name)

    def login(self, email, password):
        assert not self.logged_in
        self.logger.info("Logging in.")

        self.br.login_se_openid(email, password)

        self.br.login_site(self.host)

        if self.host == 'stackexchange.com':
            self.br.login_se_chat()

        self.logged_in = True
        self.logger.info("Logged in.")
        self.thread.start()

    def logout(self):
        assert self.logged_in

        for watcher in self.br.sockets.values():
            watcher.killed = True

        for watcher in self.br.polls.values():
            watcher.killed = True

        self.request_queue.put(SystemExit)
        self.logger.info("Logged out.")
        self.logged_in = False

    def _send_message(self, room_id, text):
        """
        Queues a message for sending to a given room.
        """
        self.request_queue.put(('send', room_id, text))
        self.logger.info("Queued message %r for room_id #%r.", text, room_id)
        self.logger.info("Queue length: %d.", self.request_queue.qsize())

    def _edit_message(self, message_id, text):
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
            next_action = self.request_queue.get()  # blocking
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

            try:
                if action_type == 'send':
                    response = self.br.send_message(room_id, text)
                else:
                    assert action_type == 'edit'
                    response = self.br.edit_message(message_id, text)
            except requests.HTTPError as ex:
                if ex.response.status_code == 409:
                    # this could be a throttling message we know how to handle
                    response = ex.response
                else:
                    raise

            if isinstance(response, str):
                match = re.match(TOO_FAST_RE, response)
                if match:  # Whoops, too fast.
                    wait = int(match.group(1))
                    self.logger.debug(
                        "Attempt %d: denied: throttled, must wait %.1f seconds",
                        attempt, wait)
                    # Wait more than that, though.
                    wait *= self.BACKOFF_MULTIPLIER
                    wait += self.BACKOFF_ADDER
                else:  # Something went wrong. I guess that happens.
                    wait = self.BACKOFF_ADDER
                    logging.error(
                        "Attempt %d: denied: unknown reason %r",
                        attempt, response)
            elif isinstance(response, dict):
                if response["id"] is None:  # Duplicate message?
                    text += " "  # Append because markdown
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

    def _join_room(self, room_id):
        self.br.join_room(room_id)

    def _room_events(self, activity, room_id):
        """
        Returns a list of Events associated with a particular room,
        given an activity message from the server.
        """
        room_activity = activity.get('r%s' % (room_id,), {})
        room_events_data = room_activity.get('e', [])
        for room_event_data in room_events_data:
            if room_event_data:
                event = events.make(room_event_data, self)
                self.recent_events.appendleft(event)
                yield event

    def _watch_room(self, room_id, event_callback, interval):
        def on_activity(activity):
            for event in self._room_events(activity, room_id):
                event_callback(event, self)

        self.br.watch_room_http(room_id, on_activity, interval)

    def _watch_room_socket(self, room_id, event_callback):
        def on_activity(activity):
            for event in self._room_events(activity, room_id):
                event_callback(event, self)

        self.br.watch_room_socket(room_id, on_activity)
