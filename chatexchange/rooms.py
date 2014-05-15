import logging

from . import _utils


logger = logging.getLogger(__name__)


class Room(object):
    def __init__(self, id, client):
        self.logger = logger.getChild('Room')
        self.id = id
        self.client = client

    name = _utils.LazyFrom('scrape_info')
    description = _utils.LazyFrom('scrape_info')
    message_count = _utils.LazyFrom('scrape_info')
    user_count = _utils.LazyFrom('scrape_info')
    parent_site_name = _utils.LazyFrom('scrape_info')
    owners = _utils.LazyFrom('scrape_info')
    tags = _utils.LazyFrom('scrape_info')

    def scrape_info(self):
        raise NotImplementedError()

    def join(self):
        return self.client._join_room(self.id)

    def watch(self, event_callback, interval):
        return self.client._watch_room(self.id, event_callback, interval)

    def watch_socket(self, event_callback):
        return self.client._watch_room_socket(self.id, event_callback)

    def send_message(self, text):
        self.client._send_message(self.id, text)
