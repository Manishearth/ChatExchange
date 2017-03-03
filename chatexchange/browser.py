# encoding: utf-8
import sys
import logging
if sys.version_info[:2] <= (2, 6):
    logging.Logger.getChild = lambda self, suffix:\
        self.manager.getLogger('.'.join((self.name, suffix)) if self.root is not self else suffix)
import json
import threading
import time

from bs4 import BeautifulSoup
import requests
import websocket
from . import _utils
import socket
import re


logger = logging.getLogger(__name__)


class Browser(object):
    """
    An interface for scraping and making requests to Stack Exchange chat.
    """
    user_agent = ('ChatExchange/0.dev '
                  '(+https://github.com/Manishearth/ChatExchange)')

    chat_fkey = _utils.LazyFrom('_update_chat_fkey_and_user')
    user_name = _utils.LazyFrom('_update_chat_fkey_and_user')
    user_id = _utils.LazyFrom('_update_chat_fkey_and_user')

    request_timeout = 30.0

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
        self.on_websocket_closed = self._default_ws_recovery

    def _default_ws_recovery(self, room_id):
        on_activity = self.sockets[room_id].on_activity
        try:
            self.leave_room(room_id)
        except websocket.WebSocketConnectionClosedException:
            pass
        self.join_room(room_id)
        self.watch_room_socket(room_id, on_activity)

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

        # Try again if we fail. We're blaming "the internet" for weirdness.
        MAX_HTTP_RETRIES = 5                # EGAD! A MAGIC NUMBER!
        attempt = 0
        response = None

        while attempt <= MAX_HTTP_RETRIES:
            attempt += 1
            try:
                response = method_method(
                    url, data=data, headers=headers, timeout=self.request_timeout)
                break
            except requests.exceptions.ConnectionError as e:          # We want to try again, so continue
                                                                    # BadStatusLine throws this error
                print("Connection Error -> Trying again...")
                time.sleep(0.1)                                     # short pause before retrying
                if attempt == MAX_HTTP_RETRIES:                     # Only show exception if last try
                    raise
                continue

            except (requests.exceptions.Timeout, socket.timeout) as e:                  # Timeout occurred, retry
                                                                # Catching both because of this bug in requests
                                                                # https://github.com/kennethreitz/requests/issues/1236
                print("Timeout -> Trying again...")
                time.sleep(1.0)     # Longer pause because it was a time out. Assume overloaded and give them a second
                if attempt == MAX_HTTP_RETRIES:                     # Only show exception if last try
                    raise
                continue

        response.raise_for_status()

        # XXX: until throttling is implemented everywhere in Client, at least add some delay here.
        time.sleep(0.1)

        return response

    def get(self, url, data=None, headers=None, with_chat_root=True):
        return self._request('get', url, data, headers, with_chat_root)

    def post(self, url, data=None, headers=None, with_chat_root=True):
        return self._request('post', url, data, headers, with_chat_root)

    def get_soup(self, url, data=None, headers=None, with_chat_root=True):
        response = self.get(url, data, headers, with_chat_root)
        return BeautifulSoup(response.text, "html.parser")

    def post_soup(self, url, data=None, headers=None, with_chat_root=True):
        response = self.post(url, data, headers, with_chat_root)
        return BeautifulSoup(response.text, "html.parser")

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
                "failed to get `usr` cookie from Stack Exchange OpenID, "
                "check credentials provided for accuracy")

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

        prompt_soup = BeautifulSoup(prompt_response.text, "html.parser")

        data = {
            'session': prompt_soup.find('input', {'name': 'session'})['value'],
            'fkey': prompt_soup.find('input', {'name': 'fkey'})['value']
        }

        url = 'https://openid.stackexchange.com/account/prompt/submit'

        response = self.post(url, data, with_chat_root=False)

        return response

    def _load_fkey(self, soup):
        chat_fkey = soup.find('input', {'name': 'fkey'})['value']
        if not chat_fkey:
            raise BrowserError('fkey missing')

        self.chat_fkey = chat_fkey

    def _load_user(self, soup):
        user_link_soup = soup.select('.topbar-menu-links a')[0]
        user_id, user_name = self.user_id_and_name_from_link(user_link_soup)

        self.user_id = user_id
        self.user_name = user_name

    @staticmethod
    def user_id_and_name_from_link(link_soup):
        user_name = link_soup.text
        user_id = int(link_soup['href'].split('/')[-2])
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

    def leave_room(self, room_id):
        room_id = str(room_id)
        if room_id in self.rooms:
            self.rooms.pop(room_id)
        if room_id in self.sockets:
            self.sockets[room_id].close()
            self.sockets.pop(room_id)
        if room_id in self.polls:
            self.polls[room_id].close()
            self.polls.pop(room_id)
        self.post_fkeyed('/chats/leave/%s' % (room_id,))

    def watch_room_socket(self, room_id, on_activity):
        """
        Watches for raw activity in a room using WebSockets.

        This starts a new daemon thread.
        """
        room_id = str(room_id)
        socket_watcher = RoomSocketWatcher(self, room_id, on_activity)
        socket_watcher.on_websocket_closed = self.on_websocket_closed
        self.sockets[room_id] = socket_watcher
        socket_watcher.start()
        return socket_watcher

    def watch_room_http(self, room_id, on_activity, interval):
        """
        Watches for raw activity in a room using HTTP polling.

        This starts a new daemon thread.
        """
        room_id = str(room_id)
        http_watcher = RoomPollingWatcher(self, room_id, on_activity, interval)
        self.polls[room_id] = http_watcher
        http_watcher.start()
        return http_watcher

    def toggle_starring(self, message_id):
        return self.post_fkeyed(
            'messages/%s/star' % (message_id,))

    def toggle_pinning(self, message_id):
        return self.post_fkeyed(
            'messages/%s/owner-star' % (message_id,))

    def cancel_stars(self, message_id):
        return self.post_fkeyed(
            'messages/%s/unstar' % (message_id,))

    def send_message(self, room_id, text):
        return self.post_fkeyed(
            'chats/%s/messages/new' % (room_id,),
            {'text': text})

    def edit_message(self, message_id, text):
        return self.post_fkeyed(
            'messages/%s' % (message_id,),
            {'text': text})

    def delete_message(self, message_id):
        return self.post_fkeyed('messages/%s/delete' % (message_id, ))

    def get_history(self, message_id):
        """
        Returns the data from the history page for message_id.
        """
        history_soup = self.get_soup(
            'messages/%s/history' % (message_id,))

        latest_soup = history_soup.select('.monologue')[0]
        previous_soup = history_soup.select('.monologue')[1:]

        page_message_id = int(latest_soup.select('.message a')[0]['name'])
        assert message_id == page_message_id

        room_id = int(latest_soup.select('.message a')[0]['href']
                      .rpartition('/')[2].partition('?')[0])

        latest_content = str(
            latest_soup.select('.content')[0]
        ).partition('>')[2].rpartition('<')[0].strip()

        latest_content_source = (
            previous_soup[0].select('.content b')[0].next_sibling.strip())

        owner_soup = latest_soup.select('.username a')[0]
        owner_user_id, owner_user_name = (
            self.user_id_and_name_from_link(owner_soup))

        edits = 0
        has_editor_name = False

        for item in previous_soup:
            if item.select('b')[0].text != 'edited:':
                continue

            edits += 1

            if not has_editor_name:
                has_editor_name = True
                user_soup = item.select('.username a')[0]
                latest_editor_user_id, latest_editor_user_name = (
                    self.user_id_and_name_from_link(user_soup))

        assert (edits > 0) == has_editor_name

        if not edits:
            latest_editor_user_id = None
            latest_editor_user_name = None

        star_data = self._get_star_data(
            latest_soup, include_starred_by_you=False)

        if star_data['pinned']:
            pins = 0
            pinner_user_ids = []
            pinner_user_names = []

            for p_soup in history_soup.select('#content p'):
                if not p_soup.select('.stars.owner-star'):
                    break

                a_soup = p_soup.select('a')[0]

                pins += 1
                user_id, user_name = self.user_id_and_name_from_link(a_soup)
                pinner_user_ids.append(user_id)
                pinner_user_names.append(user_name)
        else:
            pins = 0
            pinner_user_ids = []
            pinner_user_names = []

        data = {}

        data.update(star_data)

        data.update({
            'room_id': room_id,
            'content': latest_content,
            'content_source': latest_content_source,
            'owner_user_id': owner_user_id,
            'owner_user_name': owner_user_name,
            'editor_user_id': latest_editor_user_id,
            'editor_user_name': latest_editor_user_name,
            'edited': bool(edits),
            'edits': edits,
            'pinned': bool(pins),
            'pins': pins,
            'pinner_user_ids': pinner_user_ids,
            'pinner_user_names': pinner_user_names,
            # TODO: 'time_stamp': ...
        })

        return data

    def get_transcript_with_message(self, message_id):
        """
        Returns the data from the transcript page associated with message_id.
        """
        transcript_soup = self.get_soup(
            'transcript/message/%s' % (message_id,))

        room_soups = transcript_soup.select('.room-name a')
        room_soup = room_soups[-1]
        room_id = int(room_soup['href'].split('/')[-2])
        room_name = room_soup.text

        messages_data = []

        monologues_soups = transcript_soup.select(
            '#transcript .monologue')

        for monologue_soup in monologues_soups:
            user_link, = monologue_soup.select('.signature .username a')
            user_id, user_name = self.user_id_and_name_from_link(user_link)

            message_soups = monologue_soup.select('.message')

            for message_soup in message_soups:
                message_id = int(message_soup['id'].split('-')[1])

                edited = bool(message_soup.select('.edits'))

                content = str(
                    message_soup.select('.content')[0]
                ).partition('>')[2].rpartition('<')[0].strip()

                star_data = self._get_star_data(
                    message_soup, include_starred_by_you=True)

                parent_info_soups = message_soup.select('.reply-info')

                if parent_info_soups:
                    parent_info_soup, = parent_info_soups
                    parent_message_id = int(
                        parent_info_soup['href'].partition('#')[2])
                else:
                    parent_message_id = None

                message_data = {
                    'id': message_id,
                    'content': content,
                    'room_id': room_id,
                    'room_name': room_name,
                    'owner_user_id': user_id,
                    'owner_user_name': user_name,
                    'edited': edited,
                    'parent_message_id': parent_message_id,
                    # TODO: 'time_stamp': ...
                }

                message_data.update(star_data)

                if not edited:
                    message_data['editor_user_id'] = None
                    message_data['editor_user_name'] = None
                    message_data['edits'] = 0

                messages_data.append(message_data)

        data = {
            'room_id': room_id,
            'room_name': room_name,
            'messages': messages_data
        }

        return data

    def _get_star_data(self, root_soup, include_starred_by_you):
        """
        Gets star data indicated to the right of a message from a soup.
        """

        stars_soups = root_soup.select('.stars')

        if stars_soups:
            stars_soup, = stars_soups

            times_soup = stars_soup.select('.times')
            if times_soup and times_soup[0].text:
                stars = int(times_soup[0].text)
            else:
                stars = 1

            if include_starred_by_you:
                # some pages never show user-star, so we have to skip
                starred_by_you = bool(
                    root_soup.select('.stars.user-star'))

            pinned = bool(
                root_soup.select('.stars.owner-star'))

            if pinned:
                pins_known = False
            else:
                pins_known = True
                pinner_user_ids = []
                pinner_user_names = []
                pins = 0
        else:
            stars = 0
            if include_starred_by_you:
                starred_by_you = False

            pins_known = True
            pinned = False
            pins = 0
            pinner_user_ids = []
            pinner_user_names = []

        data = {
            'stars': stars,
            'starred': bool(stars),
            'pinned': pinned,
        }

        if pins_known:
            data['pinner_user_ids'] = pinner_user_ids
            data['pinner_user_names'] = pinner_user_names
            data['pins'] = pins

        if include_starred_by_you:
            data['starred_by_you'] = starred_by_you

        return data

    def get_profile(self, user_id):
        """
        Returns the data from the profile page for user_id.
        """
        profile_soup = self.get_soup('users/%s' % (user_id,))

        name = profile_soup.find('h1').text

        is_moderator = bool(u'♦' in profile_soup.select('.user-status')[0].text)
        message_count = int(profile_soup.select('.user-message-count-xxl')[0].text)
        room_count = int(profile_soup.select('.user-room-count-xxl')[0].text)
        reputation_elements = profile_soup.select('.reputation-score')
        if len(reputation_elements) > 0:
            reputation = int(profile_soup.select('.reputation-score')[0]['title'])
        else:
            reputation = -1

        stats_elements = profile_soup.select('.user-valuecell')
        if len(stats_elements) >= 4:
            last_seen = _utils.parse_last_seen(stats_elements[2].text)
        else:
            last_seen = -1

        return {
            'name': name,
            'is_moderator': is_moderator,
            'message_count': message_count,
            'room_count': room_count,
            'reputation': reputation,
            'last_seen': last_seen
        }

    def get_room_info(self, room_id):
        """
        Returns the data from the room info page for room_id.
        """
        info_soup = self.get_soup('rooms/info/%s' % (room_id,))

        name = info_soup.find('h1').text

        description = str(
            info_soup.select('.roomcard-xxl p')[0]
        ).partition('>')[2].rpartition('<')[0].strip()

        message_count = int(info_soup.select('.room-message-count-xxl')[0].text)
        user_count = int(info_soup.select('.room-user-count-xxl')[0].text)

        parent_image_soups = info_soup.select('.roomcard-xxl img')
        if parent_image_soups:
            parent_site_name = parent_image_soups[0]['title']
        else:
            parent_site_name = None

        owner_user_ids = []
        owner_user_names = []

        for card_soup in info_soup.select('#room-ownercards .usercard'):
            user_id, user_name = self.user_id_and_name_from_link(card_soup.find('a'))
            owner_user_ids.append(user_id)
            owner_user_names.append(user_name)

        tags = []

        for tag_soup in info_soup.select('.roomcard-xxl .tag'):
            tags.append(tag_soup.text)

        return {
            'name': name,
            'description': description,
            'message_count': message_count,
            'user_count': user_count,
            'parent_site_name': parent_site_name,
            'owner_user_ids': owner_user_ids,
            'owner_user_names': owner_user_names,
            'tags': tags
        }

    def get_pingable_user_ids_in_room(self, room_id):
        url = "rooms/pingable/{0}".format(room_id)
        resp_json = self.get(url).json()
        user_ids = []
        for user in resp_json:
            user_ids.append(user[0])
        return user_ids

    def get_pingable_user_names_in_room(self, room_id):
        url = "rooms/pingable/{0}".format(room_id)
        resp_json = self.get(url).json()
        user_names = []
        for user in resp_json:
            user_names.append(user[1])
        return user_names

    def get_current_user_ids_in_room(self, room_id):
        url = "/rooms/{0}/".format(room_id)
        soup = self.get_soup(url)
        script_tag = soup.body.script
        users_js = re.compile(r"(?s)CHAT\.RoomUsers\.initPresent\(\[.+\]\);").findall(script_tag.text)[0]
        user_data = [x.strip() for x in users_js.split('\n') if len(x.strip()) > 0][1:-1]
        user_ids = []
        for ud in user_data:
            user_ids.append(int(re.compile("id: (\d+),").search(ud).group(1)))
        return user_ids

    def get_current_user_names_in_room(self, room_id):
        url = "/rooms/{0}/".format(room_id)
        soup = self.get_soup(url)
        script_tag = soup.body.script
        users_js = re.compile(r"(?s)CHAT\.RoomUsers\.initPresent\(\[.+\]\);").findall(script_tag.text)[0]
        user_data = [x.strip() for x in users_js.split('\n') if len(x.strip()) > 0][1:-1]
        user_names = []
        for ud in user_data:
            user_names.append(re.compile("name: \(\"(.+?)\"\),").search(ud).group(1))
        return user_names


    def set_websocket_recovery(self, on_ws_closed):
        self.on_websocket_closed = on_ws_closed
        for s in self.sockets:
            s.on_websocket_closed = self.on_websocket_closed


class RoomSocketWatcher(object):
    def __init__(self, browser, room_id, on_activity):
        self.logger = logger.getChild('RoomSocketWatcher')
        self.browser = browser
        self.room_id = str(room_id)
        self.thread = None
        self.on_activity = on_activity
        self.on_websocket_closed = None
        self.killed = False

    def close(self):
        self.killed = True
        if hasattr(self, 'ws'):
            self.ws.close()

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
            try:
                a = self.ws.recv()
            except websocket.WebSocketConnectionClosedException as e:
                if self.on_websocket_closed is not None:
                    self.on_websocket_closed(self.room_id)
                else:
                    raise e
                self.killed = True
                break

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

    def close(self):
        self.killed = True

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
