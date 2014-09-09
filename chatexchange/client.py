import collections
import re
import time
import Queue
import threading
import logging
import weakref

import requests

from . import browser, events, messages, rooms, users


TOO_FAST_RE = r"You can perform this action again in (\d+) seconds"


logger = logging.getLogger(__name__)


class Client(object):
    """
    A high-level interface for interacting with Stack Exchange chat.

    @ivar logged_in:   Whether this client is currently logged-in.
                       If False, attempting requests will result in errors.
    @type logged_in:   L{bool}
    @ivar host:        Hostname of associated Stack Exchange site.
    @type host:        L{str}
    @cvar valid_hosts: Set of valid/real Stack Exchange hostnames with chat.
    @type valid_hosts: L{set}
    """

    _max_recently_gotten_objects = 5000

    def __init__(self, host='stackexchange.com', email=None, password=None):
        """
        Initializes a client for a specific chat host.

        If email and password are provided, the client will L{login}.
        """
        self.logger = logger.getChild('Client')

        if email or password:
            assert email and password, (
                "must specify both email and password or neither")

        # any known instances
        self._messages = weakref.WeakValueDictionary()
        self._rooms = weakref.WeakValueDictionary()
        self._users = weakref.WeakValueDictionary()

        if host not in self.valid_hosts:
            raise ValueError("invalid host: %r" % (host,))

        self.host = host
        self.logged_in = False
        self._request_queue = Queue.Queue()

        self._br = browser.Browser()
        self._br.host = host
        self._previous = None
        self._recently_gotten_objects = collections.deque(maxlen=self._max_recently_gotten_objects)
        self._requests_served = 0
        self._thread = threading.Thread(target=self._worker, name="message_sender")
        self._thread.setDaemon(True)

        if email or password:
            assert email and password
            self.login(email, password)

    def get_message(self, message_id, **attrs_to_set):
        """
        Returns the Message instance with the given message_id.
        Any keyword arguments will be assigned as attributes of the Message.

        @rtype: L{chatexchange.messages.Message}
        """
        return self._get_and_set_deduplicated(
            messages.Message, message_id, self._messages, attrs_to_set)

    def get_room(self, room_id, **attrs_to_set):
        """
        Returns the Room instance with the given room_id.
        Any keyword arguments will be assigned as attributes of the Room.

        @rtype: L{rooms.Room}
        """
        return self._get_and_set_deduplicated(
            rooms.Room, room_id, self._rooms, attrs_to_set)

    def get_user(self, user_id, **attrs_to_set):
        """
        Returns the User instance with the given room_id.
        Any keyword arguments will be assigned as attributes of the Room.

        @rtype: L{users.User}
        """
        return self._get_and_set_deduplicated(
            users.User, user_id, self._users, attrs_to_set)

    def _get_and_set_deduplicated(self, cls, id, instances, attrs):
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

    def get_me(self):
        """
        Returns the currently-logged-in User.

        @rtype: L{users.User}
        """
        assert self._br.user_id is not None
        return self.get_user(self._br.user_id, name=self._br.user_name)

    def login(self, email, password):
        """
        Authenticates using the provided Stack Exchange OpenID credentials.
        If successful, blocks until the instance is ready to use.
        """
        assert not self.logged_in
        self.logger.info("Logging in.")

        self._br.login_se_openid(email, password)

        self._br.login_site(self.host)

        if self.host == 'stackexchange.com':
            self._br.login_se_chat()

        self.logged_in = True
        self.logger.info("Logged in.")
        self._thread.start()

    def logout(self):
        """
        Logs out this client once all queued requests are sent.
        The client cannot be logged back in/reused.
        """
        assert self.logged_in

        for watcher in self._br.sockets.values():
            watcher.killed = True

        for watcher in self._br.polls.values():
            watcher.killed = True

        self._request_queue.put(SystemExit)
        self.logger.info("Logged out.")
        self.logged_in = False

    def __del__(self):
        if self.logged_in:
            self._request_queue.put(SystemExit)
            assert False, "You forgot to log out."

    def _worker(self):
        assert self.logged_in
        self.logger.info("Worker thread reporting for duty.")
        while True:
            next_action = self._request_queue.get()  # blocking
            if next_action == SystemExit:
                self.logger.info("Worker thread exits.")
                return
            else:
                self._requests_served += 1
                self.logger.info(
                    "Now serving customer %d, %r",
                    self._requests_served, next_action)

                self._do_action_despite_throttling(next_action)

            self._request_queue.task_done()

    # Appeasing the rate limiter gods is hard.
    _BACKOFF_MULTIPLIER = 2
    _BACKOFF_ADDER = 5

    # When told to wait n seconds, wait n * BACKOFF_MULTIPLIER + BACKOFF_ADDER

    def _do_action_despite_throttling(self, action):
        action_type = action[0]
        if action_type == 'send':
            action_type, room_id, text = action
        else:
            assert action_type == 'edit' or action_type == 'delete'
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
                    response = self._br.send_message(room_id, text)
                elif action_type == 'edit':
                    response = self._br.edit_message(message_id, text)
                else:
                    assert action_type == 'delete'
                    response = self._br.delete_message(message_id)
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
                    wait *= self._BACKOFF_MULTIPLIER
                    wait += self._BACKOFF_ADDER
                else:  # Something went wrong. I guess that happens.
                    wait = self._BACKOFF_ADDER
                    logging.error(
                        "Attempt %d: denied: unknown reason %r",
                        attempt, response)
            elif isinstance(response, dict):
                if response["id"] is None:  # Duplicate message?
                    text += " "  # Append because markdown
                    wait = self._BACKOFF_ADDER
                    self.logger.debug(
                        "Attempt %d: denied: duplicate, waiting %.1f seconds.",
                        attempt, wait)

            if wait:
                self.logger.debug("Attempt %d: waiting %.1f seconds", attempt, wait)
            else:
                wait = self._BACKOFF_ADDER
                self.logger.debug("Attempt %d: success. Waiting %.1f seconds", attempt, wait)
                sent = True
                self._previous = text

            time.sleep(wait)

    def _join_room(self, room_id):
        self._br.join_room(room_id)
