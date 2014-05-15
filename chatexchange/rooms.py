import logging

from . import _utils, events


logger = logging.getLogger(__name__)


class Room(object):
    def __init__(self, id, client):
        self.id = id
        self._logger = logger.getChild('Room')
        self._client = client

    name = _utils.LazyFrom('scrape_info')
    description = _utils.LazyFrom('scrape_info')
    message_count = _utils.LazyFrom('scrape_info')
    user_count = _utils.LazyFrom('scrape_info')
    parent_site_name = _utils.LazyFrom('scrape_info')
    owners = _utils.LazyFrom('scrape_info')
    tags = _utils.LazyFrom('scrape_info')

    def scrape_info(self):
        data = self._client._br.get_room_info(self.id)

        self.name = data['name']
        self.description = data['description']
        self.message_count = data['message_count']
        self.user_count = data['user_count']
        self.parent_site_name = data['parent_site_name']
        self.owners = [
            self._client.get_user(user_id, name=user_name)
            for user_id, user_name
            in zip(data['owner_user_ids'], data['owner_user_names'])
        ]
        self.tags = data['tags']

    @property
    def text_description(self):
        if self.description is not None:
            return _utils.html_to_text(self.description)

    def join(self):
        return self._client._join_room(self.id)

    def send_message(self, text):
        self._client._request_queue.put(('send', self.id, text))
        self._logger.info("Queued message %r for room_id #%r.", text, self.id)
        self._logger.info("Queue length: %d.", self._client._request_queue.qsize())

    def watch(self, event_callback):
        return self.watch_polling(event_callback, 3)

    def watch_polling(self, event_callback, interval):
        return self._client._watch_room_polling(self.id, event_callback, interval)

    def watch_socket(self, event_callback):
        return self._client._watch_room_socket(self.id, event_callback)

    def new_events(self, types=events.Event):
        raise NotImplementedError()
        events = FilteredEventIterator()

        self.watch_socket()

        return events

    def new_messages(self):
        raise NotImplementedError()


class FilteredEventIterator(object):
    pass


class MessageIterator(object):
    pass
