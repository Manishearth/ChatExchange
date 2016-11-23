import logging

from . import _utils


logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, id, client):
        self.id = id
        self._logger = logger.getChild('User')
        self._client = client

    name = _utils.LazyFrom('scrape_profile')
    about = _utils.LazyFrom('scrape_profile')
    is_moderator = _utils.LazyFrom('scrape_profile')
    message_count = _utils.LazyFrom('scrape_profile')
    room_count = _utils.LazyFrom('scrape_profile')
    reputation = _utils.LazyFrom('scrape_profile')
    last_seen = _utils.LazyFrom('scrape_profile')

    def scrape_profile(self):
        data = self._client._br.get_profile(self.id)

        self.name = data['name']
        self.is_moderator = data['is_moderator']
        self.message_count = data['message_count']
        self.room_count = data['room_count']
        self.reputation = data['reputation']
        self.last_seen = data['last_seen']
