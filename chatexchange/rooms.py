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

    def scrape_info(self):
        raise NotImplementedError()
