#!/usr/bin/env python
"""
Opens a web page displaying a simple updating view of a chat room.

This is not meant for unauthenticated, remote, or multi-client use.
"""

import sys
if sys.version_info[0] == 2:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
else:
    from http.server import HTTPServer, BaseHTTPRequestHandler
import collections
import getpass
import json
import logging
import os
import webbrowser

import chatexchange
from chatexchange import events


logger = logging.getLogger(__name__)


def main(port='8462'):
    port = int(port)

    logging.basicConfig(level=logging.INFO)

    room_id = 1  # Sandbox

    if 'ChatExchangeU' in os.environ:
        email = os.environ['ChatExchangeU']
    else:
        sys.stderr.write("Username: ")
        sys.stderr.flush()
        email = input()
    if 'ChatExchangeP' in os.environ:
        password = os.environ['ChatExchangeP']
    else:
        password = getpass.getpass("Password: ")

    client = chatexchange.Client('stackexchange.com')
    client.login(email, password)

    httpd = Server(
        ('127.0.0.1', 8462), Handler, client=client, room_id=room_id)
    webbrowser.open('http://localhost:%s/' % (port,))
    httpd.serve_forever()


class Server(HTTPServer, object):
    def __init__(self, *a, **kw):
        self.client = kw.pop('client')
        self.room = self.client.get_room(kw.pop('room_id'))
        self.room.name = "Chat Room"  # prevent request
        self.messages = collections.deque(maxlen=25)

        self.room.join()
        self.room.watch_socket(self.on_chat_event)

        self.room.send_message("Hello, world!")

        super(Server, self).__init__(*a, **kw)

    def get_state(self):
        return {
            'host': self.client.host,
            'room': {
                'id': self.room.id,
                'name': self.room.name
            },
            'recent_events':
                map(str, self.client._recently_gotten_objects),
            'messages': [{
                'id': message.id,
                'owner_user_id': message.owner.id,
                'owner_user_name': message.owner.name,
                'text_content': message.text_content,
                'stars': message.stars,
                'starred_by_you': message.starred_by_you,
                'pinned': message.pinned,
                'pinner_user_name': message.pinners and message.pinners[0].name,
                'pinner_user_id': message.pinners and message.pinners[0].id,
                'edits': message.edits,
            } for message in self.messages]
        }

    def on_chat_event(self, event, client):
        if isinstance(event, events.MessagePosted) and event.room is self.room:
            self.messages.append(event.message)


class Handler(BaseHTTPRequestHandler, object):
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
            self.server.room.send_message(data['text'])
        elif data['action'] == 'edit':
            message = self.server.client.get_message(data['target'])
            message.edit(data['text'])
        elif data['action'] == 'reply':
            message = self.server.client.get_message(data['target'])
            message.reply(data['text'])
        elif data['action'] == 'set-starring':
            message = self.server.client.get_message(data['target'])
            message.star(data['value'])
        elif data['action'] == 'set-pinning':
            message = self.server.client.get_message(data['target'])
            message.pin(data['value'])
        elif data['action'] == 'scrape-transcript':
            message = self.server.client.get_message(data['target'])
            message.scrape_transcript()
        elif data['action'] == 'scrape-history':
            message = self.server.client.get_message(data['target'])
            message.scrape_history()
        else:
            assert False

        self.send_response(200)
        self.end_headers()
        self.wfile.write("queued!")
        self.wfile.close()

    def send_state(self):
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

                $scope.prepareToReply = function(message) {
                    $scope.action = 'reply';
                    $scope.target = message.id;
                    input.focus();
                };

                $scope.prepareToEdit = function(message) {
                    $scope.action = 'edit';
                    $scope.target = message.id;
                    $scope.text = message.text_content;
                    input.focus();
                };

                $scope.setMessageStarred = function(message, value) {
                    $http.post('/action', {
                        action: 'set-starring',
                        target: message.id,
                        value: value
                    });
                };

                $scope.setMessagePinned = function(message, value) {
                    $http.post('/action', {
                        action: 'set-pinning',
                        target: message.id,
                        value: value
                    });
                };

                $scope.scrapeMessageHistory = function(message) {
                    $http.post('/action', {
                        action: 'scrape-history',
                        target: message.id
                    });
                };

                $scope.scrapeMessageTranscript = function(message) {
                    $http.post('/action', {
                        action: 'scrape-transcript',
                        target: message.id
                    });
                };

                $interval(update, 500);
                update();

                function update() {
                    $http.get('/state').then(function(response) {
                        angular.extend($scope, response.data);
                    });
                };
            }
        </script>
        <div class="container main">
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
                        ng-click="prepareToReply(message)"
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
                        ng-click="setMessageStarred(message, true)"
                        ng-hide="message.starred_by_you"
                    >
                        Star
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="setMessageStarred(message, false)"
                        ng-show="message.starred_by_you"
                    >
                        Unstar
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="setMessagePinned(message, true)"
                        ng-hide="message.pinned"
                    >
                        Pin
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="setMessagePinned(message, false)"
                        ng-show="message.pinned"
                    >
                        Unpin
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs"
                        ng-click="scrapeMessageHistory(message)"
                    >
                        Scrape History
                    </button>

                    <button
                        type="button" class="btn btn-default btn-xs""
                        ng-click="scrapeMessageTranscript(message)"
                    >
                        Scrape Transcript
                    </button>

                    <span class="label label-info" ng-show="message.edits">
                        edited
                        <span ng-show="message.edits > 1">x{{message.edits}}</span>
                    </span>

                    <span class="label label-primary" ng-if="message.stars">
                        starred
                        <span ng-if="message.stars > 1">x{{message.stars}}</span>
                        <span ng-if="message.starred_by_you">by you</span>
                    </span>

                    <span class="label label-primary" ng-show="message.pinned">
                        pinned by {{message.pinner_user_name}} (#{{message.pinner_user_id}})
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
        </div>
        <div class="events container">
            <pre ng-repeat="event in recent_events">{{event}}</pre>
        </div>
        <style>
            .row { margin-top: .5em; }
            .label { vertical-align: middle; }
            body { background: #BBB; }
            .messages {
                min-height: 10em;
            }
            .container.main {
                border: 1px solid #888;
                background: white;
                border-top: none;
                padding: 1em;
            }
            .events {
                margin-top: 2em;
            }
        </style>
        </body>
        </html>''')


if __name__ == '__main__':
    main(*sys.argv[1:])
