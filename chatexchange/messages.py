from . import _utils


class Message(object):
    def __init__(self, message_id, wrapper):
        self.message_id = message_id
        self.wrapper = wrapper

        self.room_id = None
        self.room_name = None
        self.content = None
        self.owner_user_id = None
        self.owner_user_name = None
        self.target_user_id = None
        self.edits = None
        self.stars = None
        self.owner_stars = None
        self._parent_message_id = None

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
            ":%s %s" % (self.message_id, text))

    def edit(self, text):
        self.wrapper.edit_message(self.message_id, text)
