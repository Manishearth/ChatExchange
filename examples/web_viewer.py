#!/usr/bin/env python
import BaseHTTPServer
import collections
import getpass
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

    chat = wrapper.SEChatWrapper('stackexchange.com')
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
        self.messages = collections.deque(maxlen=25)

        self.chat.joinRoom(self.room_id)
        self.chat.watchRoomSocket(self.room_id, self.on_chat_event)

        self.chat.sendMessage(self.room_id, "Hello, world!")

        super(Server, self).__init__(*a, **kw)

    def get_state(self):
        return {
            'host': self.chat.host,
            'room': {
                'id': self.room_id,
                'name': self.room_name
            },
            'messages': [{
                'id': message.id,
                'owner_user_id': message.owner_user_id,
                'owner_user_name': message.owner_user_name,
                'text_content': message.text_content,
                'stars': message.stars,
                'owner_stars': message.owner_stars,
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

    def do_POST(self):
        assert self.path == '/action'

        length = int(self.headers.getheader('content-length'))
        json_data = self.rfile.read(length)
        data = json.loads(json_data)

        if data['action'] == 'create':
            self.server.chat.send_message(
                self.server.room_id,
                data['text'])
        elif data['action'] == 'edit':
            message = self.server.chat.get_message(data['target'])
            message.edit(data['text'])
        elif data['action'] == 'reply':
            message = self.server.chat.get_message(data['target'])
            message.reply(data['text'])
        elif data['action'] == 'set-starring':
            message = self.server.chat.get_message(data['target'])
            message.star(data['value'])
        elif data['action'] == 'set-pinning':
            message = self.server.chat.get_message(data['target'])
            message.pin(data['value'])
        else:
            assert False

        self.send_response(200)
        self.end_headers()
        self.wfile.write("queued!")
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
        self.wfile.write('''<!doctype html ng-cloak>
        <html ng-app ng-controller="WebViewerPageController">
        <head>
        <title>ChatExchange Web Viewer Example</title>
        </head>
        <body>
        <script src="//ajax.googleapis.com/ajax/libs/angularjs/1.2.16/angular.js"></script>
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">
        <script>
            'use strict';

            function WebViewerPageController(
                $scope,
                $interval,
                $http
            ) {
                var input = document.querySelector('input');
                input.focus();

                $scope.action = 'create';
                $scope.target = null;
                $scope.text = "";

                $scope.room = {
                    name: "Loading room...",
                    id: "???"
                };

                $scope.sendAction = function() {
                    $http.post('/action', {
                        action: $scope.action,
                        text: $scope.text,
                        target: $scope.target
                    });
                    
                    $scope.text = "";
                    $scope.action = 'create';
                    $scope.target = '';
                }

                $scope.prepareToReply = function(id) {
                    $scope.action = 'reply';
                    $scope.target = id;
                    input.focus();
                }

                $scope.prepareToEdit = function(message) {
                    $scope.action = 'edit';
                    $scope.target = message.id;
                    $scope.text = message.text_content;
                    input.focus();
                }

                $scope.setMessageStarred = function(id, value) {
                    $http.post('/action', {
                        action: 'set-starring',
                        target: id,
                        value: value
                    });
                }

                $scope.setMessagePinned = function(id, value) {
                    $http.post('/action', {
                        action: 'set-pinning',
                        target: id,
                        value: value
                    });
                }

                $interval(update, 500);
                update();

                function update() {
                    $http.get('/state').then(function(response) {
                        angular.extend($scope, response.data);
                    });
                };
            }
        </script>
        <div class="container">
            <h1 class="text-center">
                <a href="http://chat.{{host}}/rooms/{{room.id}}">
                    {{room.name}} <small>#{{room.id}}</small>
                </a>
            </h1>
            <div ng-hide="messages.length">
                <em>There have been no new messages.</em>
            </div>

            <div class="messages"><div class="row" ng-repeat="message in messages">
                <div class="col-xs-2 text-right">
                    <a href="http://chat.{{host}}/users/{{message.owner_user_id}}/"
                    >{{message.owner_user_name}}</a>:
                </div>

                <div class="col-xs-5">
                    <span>
                        {{message.text_content}}
                    </span>
                </div>

                <div class="col-xs-5">
                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="prepareToReply(message.id)"
                    >
                        Reply
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="prepareToEdit(message)"
                    >
                        Edit
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="setMessageStarred(message.id, true)"
                    >
                        Star
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="setMessageStarred(message.id, false)"
                    >
                        Unstar
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="setMessagePinned(message.id, true)"
                    >
                        Pin
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="setMessagePinned(message.id, false)"
                    >
                        Unpin
                    </button>

                    <span class="label label-info" ng-if="message.edits">
                        edited
                        <span ng-if="message.edits > 1">x{{message.edits}}</span>
                    </span>

                    <span class="label label-primary" ng-if="message.stars">
                        starred
                        <span ng-if="message.stars > 1">x{{message.stars}}</span>
                    </span>

                    <span class="label label-primary" ng-if="message.owner_stars">
                        pinned
                    </span>
                </div>
            </div></div>

            <form ng-submit="sendAction()" class="row">
                <div class="col-xs-2 text-right">
                    <code>{{action}}</code>
                </div>
                <div class="col-xs-5">
                    <input ng-model="text" class="form-control" />
                </div>
                <div class="col-xs-5">
                    <button type="submit" class="btn btn-primary btn-sm">
                        Submit
                    </button>
                </div>
            </form>
            <style>
            .row { margin-top: .5em; }
            .label { vertical-align: middle; }
            body { background: #BBB; }
            .messages {
                min-height: 10em;
            }
            .container {
                border: 1px solid #888;
                background: white;
                border-top: none;
                padding: 1em;
            }
            </style>
        </div>
        </body>
        </html>''')


if __name__ == '__main__':
    main(*sys.argv[1:])
