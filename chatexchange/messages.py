import logging

from . import _utils


logger = logging.getLogger(__name__)


class Message(object):
    def __init__(self, id, client):
        self.id = id
        self._logger = logger.getChild('Message')
        self._client = client

    room = _utils.LazyFrom('scrape_transcript')
    content = _utils.LazyFrom('scrape_transcript')
    owner = _utils.LazyFrom('scrape_transcript')
    _parent_message_id = _utils.LazyFrom('scrape_transcript')
    stars = _utils.LazyFrom('scrape_transcript')
    starred_by_you = _utils.LazyFrom('scrape_transcript')
    pinned = _utils.LazyFrom('scrape_transcript')

    content_source = _utils.LazyFrom('scrape_history')
    editor = _utils.LazyFrom('scrape_history')
    edited = _utils.LazyFrom('scrape_history')
    edits = _utils.LazyFrom('scrape_history')
    pins = _utils.LazyFrom('scrape_history')
    pinners = _utils.LazyFrom('scrape_history')
    time_stamp = _utils.LazyFrom('scrape_history')

    def scrape_history(self):
        data = self._client._br.get_history(self.id)

        self.owner = self._client.get_user(
            data['owner_user_id'], name=data['owner_user_name'])
        self.room = self._client.get_room(data['room_id'])
        self.content = data['content']
        self.content_source = data['content_source']
        self.edits = data['edits']
        self.edited = data['edited']
        if data['editor_user_id'] is not None:
            self.editor = self._client.get_user(
                data['editor_user_id'], name=data['editor_user_name'])
        else:
            self.editor = None

        self._scrape_stars(data)

        self.pinned = data['pinned']
        self.pins = data['pins']
        self.pinners = [
            self._client.get_user(user_id, name=user_name)
            for user_id, user_name
            in zip(data['pinner_user_ids'], data['pinner_user_names'])
        ]

        # TODO: self.time_stamp = ...

    def scrape_transcript(self):
        data = self._client._br.get_transcript_with_message(self.id)

        self.room = self._client.get_room(
            data['room_id'], name=data['room_name'])

        for message_data in data['messages']:
            message_id = message_data['id']

            message = self._client.get_message(message_id)

            message.owner = self._client.get_user(
                message_data['owner_user_id'], name=message_data['owner_user_name'])
            message.room = self._client.get_room(
                message_data['room_id'], name=message_data['room_name'])

            if message_data['edited']:
                if not Message.edited.values.get(message):
                    # If it was edited but not previously known to be edited,
                    # these might have cached outdated None/0 no-edit values.
                    del message.editor
                    del message.edits

            if 'editor_user_id' in message_data:
                if message_data['editor_user_id'] is not None:
                    message.editor = self._client.get_user(
                        message_data['editor_user_id'], name=message_data['editor_user_name'])
                else:
                    message.editor = None
            if 'edits' in message_data:
                message.edits = message_data['edits']

            message.edited = message_data['edited']
            message.content = message_data['content']
            message._scrape_stars(message_data)

            message._parent_message_id = message_data['parent_message_id']

            # TODO: message.time_stamp = ...

    def _scrape_stars(self, data):
        self.starred = data['starred']
        self.stars = data['stars']

        if 'starred_by_you' in data:
            self.starred_by_you = data['starred_by_you']

        if data['pinned'] and not Message.pinned.values.get(self):
            # If it just became pinned but was previously known unpinned,
            # these cached pin details will be stale if set.
            del self.pinners
            del self.pins

        self.pinned = data['pinned']

        if 'pinner_user_ids' in data:
            self.pinners = [
                self._client.get_user(user_id, name=user_name)
                for user_id, user_name
                in zip(data['pinner_user_ids'], data['pinner_user_names'])
            ]
        if 'pins' in data:
            self.pins = data['pins']

    @property
    def parent(self):
        if self._parent_message_id is not None:
            return self._client.get_message(self._parent_message_id)

    @property
    def text_content(self):
        if self.content is not None:
            return _utils.html_to_text(self.content)

    def reply(self, text, length_check=True):
        self.room.send_message(
            ":%s %s" % (self.id, text), length_check)

    def edit(self, text):
        self._client._request_queue.put(('edit', self.id, text))
        self._logger.info("Queued edit %r for message_id #%r.", text, self.id)
        self._logger.info("Queue length: %d.", self._client._request_queue.qsize())
        
    def delete(self):
        self._client._request_queue.put(('delete', self.id, ''))
        self._logger.info("Queued deletion for message_id #%r.", self.id)
        self._logger.info("Queue length: %d.", self._client._request_queue.qsize())

    def star(self, value=True):
        del self.starred_by_you  # don't use cached value
        if self.starred_by_you != value:
            self._client._br.toggle_starring(self.id)
            # we assume this was successfully

            self.starred_by_you = value

            if self in Message.stars.values:
                if value:
                    self.stars += 1
                else:
                    self.stars -= 1

                self.starred = bool(self.stars)
            else:
                # bust potential stale cached values
                del self.starred
        else:
            self._logger.info(".starred_by_you is already %r", value)

    def pin(self, value=True):
        del self.pinned  # don't used cached value
        if self.pinned != value:
            self._client._br.toggle_pinning(self.id)
            # we assume this was successfully

            if self in Message.pins.values:
                assert self in Message.pinners.values
                me = self._client.get_me()

                if value:
                    self.pins += 1
                    self.pinners.append(me)
                else:
                    self.pins -= 1
                    self.pinners.remove(me)

                self.pinned = bool(self.pinned)
            else:
                # bust potential stale cached values
                del self.pinned
                del self.pinners
        else:
            self._logger.info(".pinned is already %r", value)

    def cancel_stars(self):
        del self.stars  # don't used cached value
        if self.stars:
            self._client._br.cancel_stars(self.id)
            # we assume this was successfully

            self.starred_by_you = False
            self.stars = 0
            self.starred = False
            self.pinned = False
            self.pins = 0
            self.pinners = []
        else:
            self._logger.info(".stars is already 0")
