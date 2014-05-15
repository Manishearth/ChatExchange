import logging

from . import _utils


logger = logging.getLogger(__name__)


class Message(object):
    def __init__(self, id, client):
        self.logger = logger.getChild('Message')
        self.id = id
        self.client = client

    room_id = _utils.LazyFrom('scrape_transcript')
    room_name = _utils.LazyFrom('scrape_transcript')
    content = _utils.LazyFrom('scrape_transcript')
    owner_user_id = _utils.LazyFrom('scrape_transcript')
    owner_user_name = _utils.LazyFrom('scrape_transcript')
    _parent_message_id = _utils.LazyFrom('scrape_transcript')
    stars = _utils.LazyFrom('scrape_transcript')
    starred_by_you = _utils.LazyFrom('scrape_transcript')
    pinned = _utils.LazyFrom('scrape_transcript')

    editor_user_id = _utils.LazyFrom('scrape_history')
    editor_user_name = _utils.LazyFrom('scrape_history')
    content_source = _utils.LazyFrom('scrape_history')
    edited = _utils.LazyFrom('scrape_history')
    edits = _utils.LazyFrom('scrape_history')
    pins = _utils.LazyFrom('scrape_history')
    pinner_user_ids = _utils.LazyFrom('scrape_history')
    pinner_user_names = _utils.LazyFrom('scrape_history')
    time_stamp = _utils.LazyFrom('scrape_history')

    def scrape_history(self):
        data = self.client.br.get_history(self.id)

        self.room_id = data['room_id']
        self.content = data['content']
        self.content_source = data['content_source']
        self.edits = data['edits']
        self.edited = data['edited']
        self.editor_user_id = data['editor_user_id']
        self.editor_user_name = data['editor_user_name']

        self._scrape_stars(data)

        self.pinned = data['pinned']
        self.pins = data['pins']
        self.pinner_user_ids = data['pinner_user_ids']
        self.pinner_user_names = data['pinner_user_names']

        # TODO: self.time_stamp = ...

    def scrape_transcript(self):
        data = self.client.br.get_transcript_with_message(self.id)

        self.room_id = data['room_id']
        self.room_name = data['room_name']

        for message_data in data['messages']:
            message_id = message_data['id']

            message = self.client.get_message(message_id)

            message.room_id = message_data['room_id']
            message.room_name = message_data['room_name']
            message.owner_user_id = message_data['owner_user_id']
            message.owner_user_name = message_data['owner_user_name']

            if message_data['edited']:
                if not Message.edited.values.get(message):
                    # If it was edited but not previously known to be edited,
                    # these might have cached outdated None/0 no-edit values.
                    del message.editor_user_id
                    del message.editor_user_name
                    del message.edits

            if 'editor_user_id' in message_data:
                message.editor_user_id = message_data['editor_user_id']
            if 'editor_user_name' in message_data:
                message.editor_user_name = message_data['editor_user_name']
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
            # these cached pin details will be stale.
            del self.pinner_user_ids
            del self.pinner_user_names
            del self.pins

        self.pinned = data['pinned']

        if 'pinner_user_ids' in data:
            self.pinner_user_ids = data['pinner_user_ids']
        if 'pinner_user_names' in data:
            self.pinner_user_names = data['pinner_user_names']
        if 'pins' in data:
            self.pins = data['pins']

    @property
    def parent(self):
        if self._parent_message_id is not None:
            return self.client.get_message(self._parent_message_id)

    @property
    def text_content(self):
        if self.content is not None:
            return _utils.html_to_text(self.content)

    def reply(self, text):
        self.client._send_message(
            self.room_id,
            ":%s %s" % (self.id, text))

    def edit(self, text):
        self.client._edit_message(self.id, text)

    def star(self, value=True):
        del self.starred_by_you  # don't use cached value
        if self.starred_by_you != value:
            self.client.br.toggle_starring()
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
            self.logger.info(".starred_by_you is already %r", value)

    def pin(self, value=True):
        del self.pinned  # don't used cached value
        if self.pinned != value:
            self.client.br.toggle_pinning()
            # we assume this was successfully

            if self in Message.pins.values:
                assert self in Message.pinner_user_ids.values
                assert self in Message.pinner_user_names.values

                if value:
                    self.pins += 1
                    self.pinner_user_ids.append(self.client.br.user_id)
                    self.pinner_user_names.append(self.client.br.user_name)
                else:
                    self.pins -= 1
                    index = self.pinner_user_ids.index(self.client.br.user_id)
                    del self.pinner_user_ids[index]
                    del self.pinner_user_names[index]

                self.pinned = bool(self.pinned)
            else:
                # bust potential stale cached values
                del self.pinned
                del self.pinner_user_ids
                del self.pinner_user_names
        else:
            self.logger.info(".pinned is already %r", value)
