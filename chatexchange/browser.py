import json
import logging
import re
import sys
import threading
import time

from BeautifulSoup import BeautifulSoup
import requests
import websocket


logger = logging.getLogger(__name__)


class SEChatBrowser(object):
    user_agent = ('ChatExchange/0.dev '
                  '(+https://github.com/Manishearth/ChatExchange)')

    def __init__(self):
        self.logger = logger.getChild('SEChatBrowser')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })
        self.rooms = {}
        self.sockets = {}
        self.polls = {}
        self.chatfkey = ""
        self.chatroot = "http://chat.stackexchange.com"

    def loginSEOpenID(self, user, password):
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

    def loginSECOM(self):
        """
        Logs the browser into StackExchange.com.
        """
        return self._se_openid_login_with_fkey(
            'http://stackexchange.com/users/login?returnurl = %2f',
            'http://stackexchange.com/users/authenticate',
            {
                'oauth_version': '',
                'oauth_server': '',
                'openid_identifier': 'https://openid.stackexchange.com/'
            })

    def loginMSOOld(self):
        """
        (OBSOLETE) Logs the browser into Meta Stack Overflow.
        """
        self._se_openid_login_with_fkey(
            'http://meta.stackoverflow.com/users/login?returnurl = %2f',
            'http://meta.stackoverflow.com/users/authenticate',
            {
                'oauth_version': '',
                'oauth_server': '',
                'openid_identifier': 'https://openid.stackexchange.com/'
            })

        self.chatroot = "http://chat.meta.stackoverflow.com"
        self.updateChatFkey()

    def loginMSE(self):
        """
        Logs the browser into Meta Stack Exchange.
        """
        self._se_openid_login_with_fkey(
            'http://meta.stackexchange.com/users/login?returnurl = %2f',
            'http://meta.stackexchange.com/users/authenticate',
            {
                'oauth_version': '',
                'oauth_server': '',
                'openid_identifier': 'https://openid.stackexchange.com/'
            })

        self.chatroot = "http://chat.meta.stackexchange.com"
        self.updateChatFkey()

    def loginSO(self):
        """
        Logs the browser into Stack Overflow.
        """
        self._se_openid_login_with_fkey(
            'http://stackoverflow.com/users/login?returnurl = %2f',
            'http://stackoverflow.com/users/authenticate',
            {
                'oauth_version': '',
                'oauth_server': '',
                'openid_identifier': 'https://openid.stackexchange.com/'
            })

        self.chatroot = "http://chat.stackoverflow.com"
        self.updateChatFkey()

    def _se_openid_login_with_fkey(self, fkey_url, post_url, data=()):
        """
        POSTs the specified login data to post_url, after retrieving an
        'fkey' value from an element named 'fkey' at fkey_url.

        Also handles SE OpenID prompts to allow login to a site.
        """
        fkey_soup = self.getSoup(fkey_url)
        fkey_input = fkey_soup.find('input', {'name': 'fkey'})
        if fkey_input is None:
            raise LoginError("fkey input not found")
        fkey = fkey_input['value']

        data = dict(data)
        data['fkey'] = fkey

        response = self.session.post(
            post_url, data=data, allow_redirects=True)

        # treat HTTP errors as Python errors
        response.raise_for_status()

        response = self._handle_se_openid_prompt_if_neccessary(response)

        return response

    def _handle_se_openid_prompt_if_neccessary(self, prompt_response):
        if not prompt_response.url.startswith('https://openid.stackexchange.com/account/prompt'):
            return prompt_response

        prompt_soup = BeautifulSoup(prompt_response.content)

        data = {
            'session': prompt_soup.find('input', {'name': 'session'})['value'],
            'fkey': prompt_soup.find('input', {'name': 'fkey'})['value']
        }

        response = self.session.post(
            'https://openid.stackexchange.com/account/prompt/submit',
            data=data)
        response.raise_for_status()

        return response

    def loginChatSE(self):
        chatlogin = self.getSoup("http://stackexchange.com/users/chat-login")
        authToken = chatlogin.find('input', {"name": "authToken"})['value']
        nonce = chatlogin.find('input', {"name": "nonce"})['value']
        data = {"authToken": authToken, "nonce": nonce}
        referer_header = {"Referer": "http://stackexchange.com/users/chat-login"}
        rdata = self.session.post(
            "http://chat.stackexchange.com/login/global-fallback",
            data=data, allow_redirects=True, headers=referer_header
        ).content
        fkey = BeautifulSoup(rdata).find('input', {"name": "fkey"})['value']
        self.chatfkey = fkey
        self.chatroot = "http://chat.stackexchange.com"
        return rdata

    def updateChatFkey(self):
        try:
            fkey = self.getSoup(self.getURL("chats/join/favorite")) \
                             .find('input', {"name": "fkey"})['value']
            if fkey is not None and fkey != "":
                self.chatfkey = fkey
                return True
        except Exception as e:
                self.logger.error("Error updating fkey: %s", e)
        return False

    def postSomething(self, relurl, data):
        data['fkey'] = self.chatfkey
        req = self.post(self.getURL(relurl), data)
        try:
            return req.json()
        except Exception:
            return req.content

    def getSomething(self, relurl):
        return self.session.get(self.getURL(relurl)).content

    def getSoup(self, url):
        return BeautifulSoup(self.session.get(url).content)

    def post(self, url, data):
        return self.session.post(url,data)

    def joinRoom(self, room_id):
        room_id = str(room_id)
        self.rooms[room_id] = {}
        result = self.postSomething(
            "/chats/"+str(room_id)+"/events",
            {"since": 0, "mode": "Messages", "msgCount": 100})
        eventtime = result['time']
        self.rooms[room_id]["eventtime"] = eventtime

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

    def getURL(self, rel):
        if rel[0] != "/":
            rel = "/"+rel
        return self.chatroot+rel


class RoomSocketWatcher(object):
    def __init__(self, browser, room_id, on_activity):
        self.logger = logger.getChild('RoomSocketWatcher')
        self.browser = browser
        self.room_id = str(room_id)
        self.thread = None
        self.on_activity = on_activity

    def start(self):
        events_data = self.browser.postSomething(
            '/chats/%s/events' % (self.room_id,),
            {'since': 0, 'mode': 'Messages', 'msgCount': 100}
        )
        if events_data['events']:
            eventtime = events_data['events'][0]['time_stamp']
            self.logger.debug('eventtime == %r', eventtime)
        else:
            self.logger.debug("No previous events in room %s", self.room_id)
            eventtime = 0

        ws_auth_data = self.browser.postSomething(
            '/ws-auth',
            {'roomid': self.room_id}
        )
        wsurl = ws_auth_data['url'] + '?l=%s' % (eventtime,)
        self.logger.debug('wsurl == %r', wsurl)

        self.ws = websocket.create_connection(
            wsurl, origin=self.browser.chatroot)

        self.thread = threading.Thread(target=self._runner)
        self.thread.setDaemon(True)
        self.thread.start()

    def _runner(self):
        #look at wsdump.py later to handle opcodes
        while True:
            a = self.ws.recv()

            if a != None and a != "":
                self.on_activity(json.loads(a))


class RoomPollingWatcher(object):
    def __init__(self, browser, room_id, on_activity, interval):
        self.logger = logger.getChild('RoomPollingWatcher')
        self.browser = browser
        self.room_id = str(room_id)
        self.thread = None
        self.on_activity = on_activity
        self.interval = interval

    def start(self):
        self.thread = threading.Thread(target=self._runner)
        self.thread.setDaemon(True)
        self.thread.start()

    def _runner(self):
        while(True):
            last_event_time = self.browser.rooms[self.room_id]['eventtime']

            activity = self.browser.postSomething(
                '/events',
                {'r' + self.room_id: last_event_time})

            try:
                room_result = activity['r' + self.room_id]
                eventtime = room_result['t']
                self.browser.rooms[self.room_id]['eventtime'] = eventtime
            except KeyError as ex:
                pass # no updated time from room

            self.on_activity(activity)

            time.sleep(self.interval)


class LoginError(Exception):
    pass
