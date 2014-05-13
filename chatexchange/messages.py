import logging

from . import _utils


logger = logging.getLogger(__name__)


class Message(object):
    def __init__(self, id, wrapper):
        self.logger = logger.getChild('Message')
        self.id = id
        self.wrapper = wrapper

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
        # TODO: move request and soup logic to Browser
        history_soup = self.wrapper.br.getSoup(
            self.wrapper.br.getURL(
                '/messages/%s/history' % (self.id,)))

        latest = history_soup.select('.monologue')[0]
        history = history_soup.select('.monologue')[1:]

        message_id = int(latest.select('.message a')[0]['name'])
        assert message_id == self.id

        self.room_id = int(latest.select('.message a')[0]['href']
                           .rpartition('/')[2].partition('?')[0])

        self.content = str(
            latest.select('.content')[0]
        ).partition('>')[2].rpartition('<')[0].strip()

        self.content_source = (
            history[0].select('.content b')[0].next_sibling.strip())

        edits = 0
        has_editor_name = False

        for item in history:
            if item.select('b')[0].text != 'edited:':
                continue

            edits += 1

            if not has_editor_name:
                has_editor_name = True
                user_soup = item.select('.username a')[0]
                self.editor_user_id = self._user_id_from_user_link(user_soup)
                self.editor_user_name = user_soup.text

        assert (edits > 0) == has_editor_name

        if not edits:
            self.editor_user_id = None
            self.editor_user_name = None

        self.edits = edits
        self.edited = bool(self.edits)

        self._scrape_stars(history_soup, scrape_starred_by_you=False)

        if self.pinned:
            pins = 0
            pinner_user_ids = []
            pinner_user_names = []

            for p_soup in history_soup.select('#content p'):
                if not p_soup.select('.stars.owner-star'):
                    break

                a_soup = p_soup.select('a')[0]

                pins += 1
                pinner_user_ids.append(self._user_id_from_user_link(a_soup))
                pinner_user_names.append(a_soup.text)

            self.pins = pins
            self.pinner_user_ids = pinner_user_ids
            self.pinner_user_names = pinner_user_names

        # TODO: self.time_stamp = ...

    def scrape_transcript(self):
        # TODO: move request and soup logic to Browser
        transcript_soup = self.wrapper.br.getSoup(
            self.wrapper.br.getURL(
                '/transcript/message/%s' % (self.id,)))

        room_soup, = transcript_soup.select('.room-name a')
        room_id = int(room_soup['href'].split('/')[2])
        room_name = room_soup.text

        monologues_soups = transcript_soup.select(
            '#transcript .monologue')
        for monologue_soup in monologues_soups:
            user_link, = monologue_soup.select('.signature .username a')
            user_id = self._user_id_from_user_link(user_link)
            user_name = user_link.text

            message_soups = monologue_soup.select('.message')
            for message_soup in message_soups:
                message_id = int(message_soup['id'].split('-')[1])
                message = self.wrapper.get_message(message_id)

                message.room_id = room_id
                message.room_name = room_name
                message.owner_user_id = user_id
                message.owner_user_name = user_name

                edited = bool(message_soup.select('.edits'))
                if edited:
                    if not Message.edited.values.get(self):
                        # XXX: generalize all instances of this?
                        # if its state was previously edited, then we don't
                        # need to worry about deleting stale `None` values. We
                        # preserve the possibly-existing values.
                        del self.editor_user_id
                        del self.editor_user_name
                        del self.edits
                else:
                    self.editor_user_id = None
                    self.editor_user_name = None
                    self.edits = 0

                self.edited = edited

                message.content = str(
                    message_soup.select('.content')[0]
                ).partition('>')[2].rpartition('<')[0].strip()

                message._scrape_stars(message_soup, scrape_starred_by_you=True)

                # TODO: message.time_stamp = ...

                parent_info_soups = message_soup.select('.reply-info')

                if parent_info_soups:
                    parent_info_soup, = parent_info_soups
                    message._parent_message_id = int(
                        parent_info_soup['href'].partition('#')[2])
                else:
                    message._parent_message_id = None

    def _user_id_from_user_link(self, user_link):
        return int(user_link['href'].split('/')[2])

    def _scrape_stars(self, soup, scrape_starred_by_you):
        stars_soup = soup.select('.stars')

        if stars_soup:
            times_soup = soup.select('.times')
            if times_soup and times_soup[0].text:
                self.stars = int(times_soup[0].text)
            else:
                self.stars = 1

            if scrape_starred_by_you:
                # some pages never show user-star, so we have to skip
                self.starred_by_you = bool(
                    soup.select('.stars.user-star'))

            pinned = bool(
                soup.select('.stars.owner-star'))

            if pinned:
                if not Message.pinned.values.get(self):
                    # XXX: generalize all instances of this?
                    # if its state was already pinned, then we don't need
                    # to worry about deleting stale `[]` values. We preserve
                    # the possibly-existing values.
                    del self.pinner_user_ids
                    del self.pinner_user_names
                    del self.pins
            else:
                self.pinner_user_ids = []
                self.pinner_user_names = []
                self.pins = 0

            self.pinned = pinned
        else:
            self.stars = 0
            if scrape_starred_by_you:
                self.starred_by_you = False
            self.pinned = False
            self.pins = 0
            self.pinner_user_ids = []
            self.pinner_user_names = []

    @property
    def parent(self):
        if self._parent_message_id is not None:
            return self.wrapper.get_message(self._parent_message_id)

    @property
    def text_content(self):
        if self.content is not None:
            return _utils.html_to_text(self.content)

    def reply(self, text):
        self.wrapper.send_message(
            self.room_id,
            ":%s %s" % (self.id, text))

    def edit(self, text):
        self.wrapper.edit_message(self.id, text)

    def star(self, value=True):
        del self.starred_by_you  # don't use cached value
        if self.starred_by_you != value:
            self._toggle_starring()

            self.starred_by_you = value  # assumed valid

            # bust staled cache
            del self.stars
        else:
            self.logger.info(".starred_by_you is already %r", value)

    def pin(self, value=True):
        del self.pinned  # don't used cached value
        if self.pinned != value:
            self._toggle_pinning()

            # bust staled cache
            del self.pinned
            del self.pins
            del self.pinner_user_ids
            del self.pinner_user_names
        else:
            self.logger.info(".pinned is already %r", value)

    def _toggle_starring(self):
        # TODO: move request logic to Browser or Wrapper
        self.wrapper.br.postSomething(
            '/messages/%s/star' % (self.id,))

    def _toggle_pinning(self):
        # TODO: move request logic to Browser or Wrapper
        self.wrapper.br.postSomething(
            '/messages/%s/owner-star' % (self.id,))
