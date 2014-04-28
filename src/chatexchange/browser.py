import json
import re
import sys

from BeautifulSoup import BeautifulSoup
import requests
try:
    import websocket
except:
    "Websockets not available. Please don't use initSocket()"


class SEChatBrowser(object):
    def __init__(self):
        self.session = requests.Session()
        self.rooms = {}
        self.sockets = {}
        self.chatfkey = ""
        self.chatroot = "http://chat.stackexchange.com"

    def loginSEOpenID(self, user, password):
        """
        Logs the browser into Stack Exchange's OpenID provider.
        """
        self.userlogin = user
        self.userpass = password

        return self._post_with_fkey(
            'https://openid.stackexchange.com/account/login',
            'https://openid.stackexchange.com/account/login/submit',
            {
                'email': user,
                'password': password,
            })

    def loginSECOM(self):
        """
        Logs the browser into StackExchange.com.
        """
        return self._post_with_fkey(
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
        self._post_with_fkey(
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
        self._post_with_fkey(
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
        self._post_with_fkey(
            'http://stackoverflow.com/users/login?returnurl = %2f',
            'http://stackoverflow.com/users/authenticate',
            {
                'oauth_version': '',
                'oauth_server': '',
                'openid_identifier': 'https://openid.stackexchange.com/'
            })

        self.chatroot = "http://chat.stackoverflow.com"
        self.updateChatFkey()

    def _post_with_fkey(self, fkey_url, post_url, data=()):
        """
        POSTs the specified data to post_url, after retrieving an 'fkey'
        value from an element named 'fkey' at fkey_url.
        """
        fkey_soup = self.getSoup(fkey_url)
        fkey_input = fkey_soup.find('input', {'name': 'fkey'})
        if fkey_input is None:
            raise LoginError("fkey input not found")
        fkey = fkey_input['value']

        data = dict(data)
        data['fkey'] = fkey

        return self.session.post(
            post_url, data=data, allow_redirects=True)

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
                print "Error updating fkey:", e
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

    def initSocket(self, roomno, func):
        """
        Experimenta. Use polling of /events
        """
        eventtime = self.postSomething(
            "/chats/"+str(roomno)+"/events",
            {"since": 0, "mode": "Messages", "msgCount": 100})['time']
        print eventtime

        wsurl = self.postSomething(
            "/ws-auth",
            {"roomid":roomno}
        )['url']+"?l="+str(eventtime)
        print wsurl

        self.sockets[roomno] = {"url":wsurl}
        self.sockets[roomno]['ws'] = websocket.create_connection(
            wsurl, origin=self.chatroot)

        def runner():
            print roomno
            #look at wsdump.py later to handle opcodes
            while True:
                a = self.sockets[roomno]['ws'].recv()
                print "a", a
                if a != None and a != "":
                    func(a)

        self.sockets[roomno]['thread']=threading.Thread(target=runner)
        self.sockets[roomno]['thread'].setDaemon(True)
        self.sockets[roomno]['thread'].start()

    def post(self, url, data):
        return self.session.post(url,data)

    def joinRoom(self, roomid):
        roomid = str(roomid)
        self.rooms[roomid] = {}
        result = self.postSomething(
            "/chats/"+str(roomid)+"/events",
            {"since": 0, "mode": "Messages", "msgCount": 100})
        eventtime = result['time']
        self.rooms[roomid]["eventtime"] = eventtime

    def pokeRoom(self, roomid):
        roomid = str(roomid)
        if not self.rooms[roomid]:
            return false

        pokeresult = self.postSomething("/events",{"r"+roomid:self.rooms[roomid]['eventtime']})

        try:
            roomresult = pokeresult["r"+str(roomid)]
            newtime = roomresult["t"]
            self.rooms[roomid]["eventtime"]=newtime
        except KeyError:
            "NOP"
        return pokeresult

    def getURL(self, rel):
        if rel[0] != "/":
            rel = "/"+rel
        return self.chatroot+rel


class LoginError(Exception):
    pass
