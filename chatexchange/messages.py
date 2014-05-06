from . import _utils


class Message(object):
    def __init__(self, id, wrapper):
        self.id = id
        self.wrapper = wrapper

    room_id = _utils.LazyFrom('scrape_transcript')
    room_name = _utils.LazyFrom('scrape_transcript')
    content = _utils.LazyFrom('scrape_transcript')
    owner_user_id = _utils.LazyFrom('scrape_transcript')
    owner_user_name = _utils.LazyFrom('scrape_transcript')
    _parent_message_id = _utils.LazyFrom('scrape_transcript')

    editor_user_id = _utils.LazyFrom('scrape_history')
    editor_user_name = _utils.LazyFrom('scrape_history')
    content_source = _utils.LazyFrom('scrape_history')
    edits = _utils.LazyFrom('scrape_history')
    stars = _utils.LazyFrom('scrape_history')
    pins = _utils.LazyFrom('scrape_history')
    pinner = _utils.LazyFrom('scrape_history')
    time_stamp = _utils.LazyFrom('scrape_history')

    def scrape_history(self):
        # TODO: move request logic to Browser or Wrapper
        history_soup = self.wrapper.br.getSoup(
            self.wrapper.br.getURL(
                '/messages/%s/history' % (self.id)))

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
        # self.edits = ...
        # self.stars = ...
        # self.pins = ...
        # self.editor_user_id = ...
        # self.editor_user_name = ...
        # self.pinner = ...
        # self.time_stamp = ...

    def scrape_transcript(self):
        # TODO: move request logic to Browser or Wrapper
        transcript_soup = self.wrapper.br.getSoup(
            self.wrapper.br.getURL(
                '/transcript/message/%s' % (self.id)))

        room_soup, = transcript_soup.select('.room-name a')
        room_id = int(room_soup['href'].split('/')[2])
        room_name = room_soup.text

        monologues_soups = transcript_soup.select(
            '#transcript .monologue')
        for monologue_soup in monologues_soups:
            user_link, = monologue_soup.select('.signature .username a')
            user_id = int(user_link['href'].split('/')[2])
            user_name = user_link.text

            message_soups = monologue_soup.select('.message')
            for message_soup in message_soups:
                message_id = int(message_soup['id'].split('-')[1])
                message = self.wrapper.get_message(message_id)

                message.room_id = room_id
                message.room_name = room_name
                message.owner_user_id = user_id
                message.owner_user_name = user_name

                message.content = str(
                    message_soup.select('.content')[0]
                ).partition('>')[2].rpartition('<')[0].strip()

                parent_info_soups = message_soup.select('.reply-info')

                if parent_info_soups:
                    parent_info_soup, = parent_info_soups
                    message._parent_message_id = int(
                        parent_info_soup['href'].partition('#')[2])
                else:
                    message._parent_message_id = None


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
