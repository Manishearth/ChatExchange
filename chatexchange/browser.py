import json
import logging
import threading
import time

from bs4 import BeautifulSoup
import requests
import websocket
import _utils


logger = logging.getLogger(__name__)


class Browser(object):
    user_agent = ('ChatExchange/0.dev '
                  '(+https://github.com/Manishearth/ChatExchange)')

    chat_fkey = _utils.LazyFrom('_update_chat_fkey_and_user')
    user_name = _utils.LazyFrom('_update_chat_fkey_and_user')
    user_id = _utils.LazyFrom('_update_chat_fkey_and_user')

    request_timeout = 10.0

    def __init__(self):
        self.logger = logger.getChild('Browser')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })
        self.rooms = {}
        self.sockets = {}
        self.polls = {}
        self.host = None

    @property
    def chat_root(self):
        assert self.host, "browser has no associated host"
        return 'http://chat.%s' % (self.host,)

    # request helpers

    def _request(
        self, method, url,
        data=None, headers=None, with_chat_root=True
    ):
        if with_chat_root:
            url = self.chat_root + '/' + url

        method_method = getattr(self.session, method)
        # using the actual .post method causes data to be form-encoded,
        # whereas using .request with method='POST' would create a query string
        response = method_method(
            url, data=data, headers=headers, timeout=self.request_timeout)

        response.raise_for_status()

        return response

    def get(self, url, data=None, headers=None, with_chat_root=True):
        return self._request('get', url, data, headers, with_chat_root)

    def post(self, url, data=None, headers=None, with_chat_root=True):
        return self._request('post', url, data, headers, with_chat_root)

    def get_soup(self, url, data=None, headers=None, with_chat_root=True):
        response = self.get(url, data, headers, with_chat_root)
        return BeautifulSoup(response.content)

    def post_soup(self, url, data=None, headers=None, with_chat_root=True):
        response = self.post(url, data, headers, with_chat_root)
        return BeautifulSoup(response.content)

    def post_fkeyed(self, url, data=None, headers=None):
        if data is None:
            data = {}
        elif not isinstance(data, dict):
            raise TypeError("data must be a dict")
        else:
            data = dict(data)

        data['fkey'] = self.chat_fkey

        return self.post(url, data, headers)

    # authentication

    def login_se_openid(self, user, password):
        """
        Logs the browser into Stack Exchange's OpenID provider.
        """
        self.userlogin = user
        self.userpass = password

        self._se_openid_login_with_fkey(
            'https://openid.stackexchange.com/account/login',
            'https://openid.stackexchange.com/account/login/submit',
            {
                'email': user,
                'password': password,
            })

        if not self.session.cookies.get('usr', None):
            raise LoginError(
                "failed to get `usr` cookie from Stack Exchange OpenID")

    def login_site(self, host):
        """
        Logs the browser into a Stack Exchange site.
        """
        assert self.host is None or self.host is host

        self._se_openid_login_with_fkey(
            'http://%s/users/login?returnurl = %%2f' % (host,),
            'http://%s/users/authenticate' % (host,),
            {
                'oauth_version': '',
                'oauth_server': '',
                'openid_identifier': 'https://openid.stackexchange.com/'
            })

        self.host = host

    def _se_openid_login_with_fkey(self, fkey_url, post_url, data=()):
        """
        POSTs the specified login data to post_url, after retrieving an
        'fkey' value from an element named 'fkey' at fkey_url.

        Also handles SE OpenID prompts to allow login to a site.
        """
        fkey_soup = self.get_soup(fkey_url, with_chat_root=False)
        fkey_input = fkey_soup.find('input', {'name': 'fkey'})
        if fkey_input is None:
            raise LoginError("fkey input not found")
        fkey = fkey_input['value']

        data = dict(data)
        data['fkey'] = fkey

        response = self.post(post_url, data, with_chat_root=False)

        response = self._handle_se_openid_prompt_if_neccessary(response)

        return response

    def _handle_se_openid_prompt_if_neccessary(self, prompt_response):
        prompt_prefix = 'https://openid.stackexchange.com/account/prompt'

        if not prompt_response.url.startswith(prompt_prefix):
            # no prompt for us to handle
            return prompt_response

        prompt_soup = BeautifulSoup(prompt_response.content)

        data = {
            'session': prompt_soup.find('input', {'name': 'session'})['value'],
            'fkey': prompt_soup.find('input', {'name': 'fkey'})['value']
        }

        url = 'https://openid.stackexchange.com/account/prompt/submit'

        response = self.post(url, data, with_chat_root=False)

        return response

    def login_se_chat(self):
        start_login_url = 'http://stackexchange.com/users/chat-login'
        start_login_soup = self.get_soup(start_login_url, with_chat_root=False)

        auth_token = start_login_soup.find('input', {'name': 'authToken'})['value']
        nonce = start_login_soup.find('input', {'name': 'nonce'})['value']
        data = {'authToken': auth_token, "nonce": nonce}
        referer_header = {'Referer': start_login_url}

        login_url = 'http://chat.stackexchange.com/login/global-fallback'
        login_request = self.post(login_url, data, referer_header, with_chat_root=False)
        login_soup = BeautifulSoup(login_request.content)

        self._load_fkey(login_soup)

        return login_request

    def _load_fkey(self, soup):
        chat_fkey = soup.find('input', {'name': 'fkey'})['value']
        if not chat_fkey:
            raise BrowserError('fkey missing')

        self.chat_fkey = chat_fkey

    def _load_user(self, soup):
        user_link_soup, = soup.select('.topbar-menu-links a')
        user_id, user_name = self.user_id_and_name_from_link(user_link_soup)

        self.user_id = user_id
        self.user_name = user_name

    @staticmethod
    def user_id_and_name_from_link(link_soup):
        user_name = link_soup.text
        user_id = int(link_soup['href'].split('/')[2])
        return user_id, user_name

    def _update_chat_fkey_and_user(self):
        """
        Updates the fkey used by this browser, and associated user name/id.
        """
        favorite_soup = self.get_soup('chats/join/favorite')
        self._load_fkey(favorite_soup)
        self._load_user(favorite_soup)

    # remote requests

    def join_room(self, room_id):
        room_id = str(room_id)
        self.rooms[room_id] = {}
        response = self.post_fkeyed(
            'chats/%s/events' % (room_id,),
            {
                'since': 0, 
                'mode': 'Messages',
                'msgCount': 100
            })
        eventtime = response.json()['time']
        self.rooms[room_id]['eventtime'] = eventtime

    def watch_room_socket(self, room_id, on_activity):
        """
        Watches for raw activity in a room using WebSockets.

        This starts a new daemon thread.
        """
        socket_watcher = RoomSocketWatcher(self, room_id, on_activity)
        self.sockets[room_id] = socket_watcher
        socket_watcher.start()

    def watch_room_http(self, room_id, on_activity, interval):
        """
        Watches for raw activity in a room using HTTP polling.

        This starts a new daemon thread.
        """
        http_watcher = RoomPollingWatcher(self, room_id, on_activity, interval)
        self.polls[room_id] = http_watcher
        http_watcher.start()

    def toggle_starring(self, message_id):
        return self.post_fkeyed(
            'messages/%s/star' % (message_id,))

    def toggle_pinning(self, message_id):
        return self.post_fkeyed(
            'messages/%s/owner-star' % (message_id,))

    def send_message(self, room_id, text):
        return self.post_fkeyed(
            'chats/%s/messages/new' % (room_id,),
            {'text': text})

    def edit_message(self, message_id, text):
        return self.post_fkeyed(
            'messages/%s' % (message_id,),
            {'text': text})


class RoomSocketWatcher(object):
    def __init__(self, browser, room_id, on_activity):
        self.logger = logger.getChild('RoomSocketWatcher')
        self.browser = browser
        self.room_id = str(room_id)
        self.thread = None
        self.on_activity = on_activity
        self.killed = False

    def start(self):
        last_event_time = self.browser.rooms[self.room_id]['eventtime']

        ws_auth_data = self.browser.post_fkeyed(
            'ws-auth',
            {'roomid': self.room_id}
        ).json()
        wsurl = ws_auth_data['url'] + '?l=%s' % (last_event_time,)
        self.logger.debug('wsurl == %r', wsurl)

        self.ws = websocket.create_connection(
            wsurl, origin=self.browser.chat_root)

        self.thread = threading.Thread(target=self._runner)
        self.thread.setDaemon(True)
        self.thread.start()

    def _runner(self):
        #look at wsdump.py later to handle opcodes
        while not self.killed:
            a = self.ws.recv()

            if a is not None and a != "":
                self.on_activity(json.loads(a))


class RoomPollingWatcher(object):
    def __init__(self, browser, room_id, on_activity, interval):
        self.logger = logger.getChild('RoomPollingWatcher')
        self.browser = browser
        self.room_id = str(room_id)
        self.thread = None
        self.on_activity = on_activity
        self.interval = interval
        self.killed = False

    def start(self):
        self.thread = threading.Thread(target=self._runner)
        self.thread.setDaemon(True)
        self.thread.start()

    def _runner(self):
        while not self.killed:
            last_event_time = self.browser.rooms[self.room_id]['eventtime']

            activity = self.browser.post_fkeyed(
                'events', {'r' + self.room_id: last_event_time}).json()

            try:
                room_result = activity['r' + self.room_id]
                eventtime = room_result['t']
                self.browser.rooms[self.room_id]['eventtime'] = eventtime
            except KeyError as ex:
                pass  # no updated time from room

            self.on_activity(activity)

            time.sleep(self.interval)


class BrowserError(Exception):
    pass


class LoginError(BrowserError):
    pass
