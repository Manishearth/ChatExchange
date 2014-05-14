import logging

from . import _utils


logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, id, client):
        self.logger = logger.getChild('User')
        self.id = id
        self.client = client

    name = _utils.LazyFrom('scrape_profile')
    about = _utils.LazyFrom('scrape_profile')
    is_moderator = _utils.LazyFrom('scrape_profile')
    parent_user_url = _utils.LazyFrom('scrape_profile')

    def scrape_profile(self):
        raise NotImplementedError()
