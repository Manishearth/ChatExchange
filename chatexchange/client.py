import sys
if sys.version_info[0] == 2:
    import Queue as queue
else:
    import queue
import logging
if sys.version_info[:2] <= (2, 6):
    logging.Logger.getChild = lambda self, suffix:\
        self.manager.getLogger('.'.join((self.name, suffix)) if self.root is not self else suffix)
import collections
import re
import time
import threading
import weakref
import requests

from . import browser, messages, rooms, users


TOO_FAST_RE = r"You can perform this action again in (\d+) second"


logger = logging.getLogger(__name__)


class PeekableQueue(queue.Queue):
    """
    A simple extension of the standard Queue object which allows inspection of the tail
    and manipulating the returned value.
    """
    def peek_latest(self):
        """
        Return the last object which was added to the queue without modifying the queue
        """
        if self.qsize() > 0:
            # Implementation detail: queue grows rightward, last element is [-1]
            return self.queue[-1]

    def poke_latest(self, oldvalue, newvalue):
        """
        Replace the lastest value if it is identical to the passed-in oldvalue.
        Otherwise, return False to signify failure.
        """
        if self.queue[-1] is oldvalue:
            self.queue[-1] = newvalue
            return True
        return False


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

    def __init__(
            self,
            host='stackexchange.com',
            email=None, password=None,
            send_aggressively=False
    ):
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
        self.on_message_sent = None
        self._request_queue = PeekableQueue()

        self._br = browser.Browser()
        self._br.host = host
        self._previous = None
        self._recently_gotten_objects = collections.deque(maxlen=self._max_recently_gotten_objects)
        self._requests_served = 0
        self._thread = threading.Thread(target=self._worker, name="ChatExchange: message_sender for chat.{}".format(host))
        self._thread.setDaemon(True)

        self.aggressive_sender = send_aggressively

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

    valid_hosts = ('stackexchange.com', 'meta.stackexchange.com', 'stackoverflow.com')

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

        cookies = self._br.login_site(self.host, email, password)

        self.logged_in = True
        self.logger.info("Logged in.")
        self._thread.start()

        return cookies

    def login_with_cookie(self, cookie_jar):
        """
        Authenticates using a pre-fetched (by the client application) `acct` cookie.
        """
        assert not self.logged_in
        self.logger.info("Logging in with acct cookie.")

        self._br.login_site_with_cookie(self.host, cookie_jar)

        self.logged_in = True
        self.logger.info("Logged in (cookie).")
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

    def set_websocket_recovery(self, on_ws_closed):
        self._br.set_websocket_recovery(on_ws_closed)

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
    _BACKOFF_ADDER = 5

    @staticmethod
    def _unpack_response(response):
        try:
            j = response.json()
            return j
        except ValueError:
            return response.text

    def _try_send(self, action_type, room_id, message_id, text):
        """
        Helper function for _do_action_despite_throttling: try to send
        the message
        """
        try:
            if action_type == 'send':
                return self._br.send_message(room_id, text)
            elif action_type == 'edit':
                return self._br.edit_message(message_id, text)
            else:
                assert action_type == 'delete'
                return self._br.delete_message(message_id)
        except requests.HTTPError as ex:
            if ex.response.status_code == 409:
                # this could be a throttling message we know how to handle
                return ex.response
            else:
                raise

    def _wait_for(self, response, attempt):
        """
        Helper function for _do_action_despite_throttling: Figure out
        how long to wait, depending on the type of the client response.
        """
        unpacked = Client._unpack_response(response)

        if isinstance(unpacked, str):
            ignored_messages = [
                "ok",
                "It is too late to delete this message",
                "It is too late to edit this message",
                "The message has been deleted and cannot be edited",
                "This message has already been deleted."
            ]
            if unpacked not in ignored_messages:
                # We received a text response, but it's not one of the ignored ones
                match = re.match(TOO_FAST_RE, unpacked)
                if match:
                    # Whoops, too fast. The response says we must wait N seconds.
                    wait = int(match.group(1))
                    self.logger.debug(
                        "Attempt %d: denied: throttled, must wait %.1f seconds",
                        attempt, wait)
                    # We don't need to wait any more than what the API tells us.
                    return wait

                else:  # Something went wrong. I guess that happens.
                    if attempt > 5:
                        raise ChatActionError(
                            "5 failed attempts to do chat action. "
                            "Unknown reason: %s" % unpacked)
                    wait = self._BACKOFF_ADDER
                    logging.error(
                        "Attempt %d: denied: unknown reason %r",
                        attempt, unpacked)
                    return wait
        elif isinstance(unpacked, dict):
            if unpacked["id"] is None:  # Duplicate message?
                wait = self._BACKOFF_ADDER
                self.logger.debug(
                    "Attempt %d: denied: duplicate, waiting %.1f seconds.",
                    attempt, wait)
                return wait, " "  # add padding because markdown

    def _do_action_despite_throttling(self, action):
        action_type = action[0]
        if action_type == 'send':
            action_type, room_id, text = action
            message_id = None
        else:
            assert action_type == 'edit' or action_type == 'delete'
            action_type, message_id, text = action

        sent = False
        attempt = 0
        if text == self._previous:
            text = " " + text
        response = None
        unpacked = None
        while not sent:
            wait = 0
            attempt += 1
            self.logger.debug("Attempt %d: start.", attempt)

            response = self._try_send(action_type, room_id, message_id, text)

            wait, padding = self._wait_for(response, attempt)
            dbg = "Attempt %d: waiting %.1f seconds", attempt, wait

            if padding:
                text += padding

            if not wait and action_type != 'send':
                # There's no reason to wait after sending a message.
                # At least for sending a message, SE chat responses make
                # it clear when a wait is needed.
                wait = self._BACKOFF_ADDER
                dbg = "Attempt %d: success. Waiting %.1f seconds", attempt, wait
                sent = True
                self._previous = text

            self.logger.debug(dbg)
            time.sleep(wait)

        if action_type == 'send' and isinstance(unpacked, dict) and self.on_message_sent is not None:
            self.on_message_sent(response.json()["id"], room_id)

        return response

    def _join_room(self, room_id):
        self._br.join_room(room_id)

    def _leave_room(self, room_id):
        self._br.leave_room(room_id)


class ChatActionError(Exception):
    pass
