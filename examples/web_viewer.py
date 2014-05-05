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
    room_id = '14219' # Charcoal Chatbot Sandbox

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

        self.chat.joinRoom(self.room_id)
        self.chat.watchRoomSocket(self.room_id, self.on_chat_event)

        self.state = {
            'room_id': self.room_id,
            'room_name': "Chat Room",
            'messages': [
                {
                    'owner': 'room',
                    'text_content': "You have joined chat."
                }
            ]
        }

        super(Server, self).__init__(*a, **kw)

    def on_chat_event(self, event, wrapper):
        self.state['messages'].append(str(event))


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

        messages = []

        for event in reversed(chat.recent_events):
            if isinstance(event, events.MessagePosted):
                messages.append({
                    'owner': event.user_name,
                    'text_content': event.text_content,
                })

        self.server.state['messages'] = messages
        body = json.dumps(self.server.state)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def send_page(self):
        body = json.dumps(self.server.state)
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
                {{room_name}} <small>#{{room_id}}</small>
            </h1>
            <div ng-repeat="message in messages">
                <strong>{{message.owner}}:</strong> {{message.text_content}}
            </div>
        </div>
        <script src="//ajax.googleapis.com/ajax/libs/angularjs/1.2.16/angular.js"></script>
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap-theme.min.css">
        </body>
        </html>''')


if __name__ == '__main__':
    main(*sys.argv[1:])
