#!/usr/bin/env python
import BaseHTTPServer
import json
import logging
import os
import sys
import webbrowser


from chatexchange import wrapper, events


"""
Opens a web page displaying a simple updating view of a chat room.

This is not meant for unauthenticated, remote, or multi-client use.
"""


logger = logging.getLogger(__name__)


def main(port='8462'):
    port = int(port)

    logging.basicConfig(level=logging.INFO)

    host_id = 'SE'
    room_id = 14219 # Charcoal Chatbot Sandbox

    if 'ChatExchangeU' in os.environ:
        username = os.environ['ChatExchangeU']
    else:
        sys.stderr.write("Username: ")
        sys.stderr.flush()
        username = raw_input()
    if 'ChatExchangeP' in os.environ:
        password = os.environ['ChatExchangeP']
    else:
        password = getpass.getpass("Password: ")

    chat = wrapper.SEChatWrapper(host_id)
    chat.login(username, password)

    httpd = Server(
        ('127.0.0.1', 8462), Handler, chat=chat, room_id=room_id)
    webbrowser.open('http://localhost:%s/' % (port,))
    httpd.serve_forever()


class Server(BaseHTTPServer.HTTPServer, object):
    def __init__(self, *a, **kw):
        self.chat = kw.pop('chat')
        self.room_id = kw.pop('room_id')
        self.room_name = "Chat Room"
        self.messages = []

        self.chat.joinRoom(self.room_id)
        self.chat.watchRoomSocket(self.room_id, self.on_chat_event)

        self.chat.sendMessage(self.room_id, "Hello, world!")

        super(Server, self).__init__(*a, **kw)

    def get_state(self):
        return {
            'room': {
                'id': self.room_id,
                'name': self.room_name
            },
            'messages': [{
                'owner': message.owner_user_name,
                'text_content': message.text_content,
                'stars': message.stars,
                'edits': message.edits,
            } for message in self.messages]
        }

    def on_chat_event(self, event, wrapper):
        if (isinstance(event, events.MessagePosted)
            and event.room_id == self.room_id):
            self.room_name = event.room_name
            self.messages.append(event.message)


class Handler(BaseHTTPServer.BaseHTTPRequestHandler, object):
    logger = logging.getLogger(__name__).getChild('Handler')

    def do_GET(self):
        if self.path == '/':
            self.send_page()
        elif self.path == '/state':
            self.send_state()
        else:
            self.send_error(404)

        self.wfile.close()

    def send_state(self):
        chat = self.server.chat
        body = json.dumps(self.server.get_state())
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def send_page(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write('''<!doctype html>
        <html ng-app ng-controller="WebViewerPageController">
        <head>
        <title>ChatExchange Web Viewer Example</title>
        </head>
        <body>
        <script>
            'use strict';

            function WebViewerPageController(
                $scope,
                $interval,
                $http
            ) {
                $interval(update, 500);

                function update() {
                    $http.get('/state').then(function(response) {
                        angular.extend($scope, response.data);
                    });
                };
            }
        </script>
        <div class="container">
            <h1>
                {{room.name}} <small>#{{room.id}}</small>
            </h1>
            <div ng-repeat="message in messages">
                <strong>{{message.owner}}:</strong> {{message.text_content}}
                <em ng-if="message.edits">
                    (edited {{message.edits}} times)
                </em>
                <em ng-if="message.stars">
                    (starred {{message.stars}} times)
                </em>
            </div>
        </div>
        <script src="//ajax.googleapis.com/ajax/libs/angularjs/1.2.16/angular.js"></script>
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap-theme.min.css">
        </body>
        </html>''')


if __name__ == '__main__':
    main(*sys.argv[1:])
