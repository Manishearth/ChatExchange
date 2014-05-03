import logging

from . import _utils


logger = logging.getLogger(__name__)


def make(data, wrapper=None, **kwargs):
    """
    Instantiates an instance of Event or a subclass, for the given
    event data and (optional) wrapper.
    """
    type_id = data['event_type']
    cls = types.get(type_id, Event)
    return cls(data, wrapper, **kwargs)


# Event subclasses by type_id
types = {}


def register_type(event_type):
    """
    Registers an Event subclass for use with events.make().
    """
    type_id = event_type.type_id
    assert type_id not in types
    types.setdefault(type_id, event_type)
    return event_type


class Event(object):
    def __init__(self, data, wrapper=None):
        self.logger = logger.getChild(type(self).__name__)

        assert data, "empty data passed to Event constructor"

        self.wrapper = wrapper
        self.data = data

        if hasattr(self, 'type_id'):
            assert self.type_id == data['event_type']
        else:
            self.type_id = data['event_type']

        self.event_id = data['id']
        self.room_id = data['room_id']
        self.room_name = data['room_name']
        self.time_stamp = data['time_stamp']

        self._init_from_data()

    def _init_from_data(self):
        """
        Initializes any type-specific fields from self.data.
        """
        pass

    def __repr__(self):
        return '{0!s}({1!r}, {2!r})'.format(
            type(self).__name__, self.data, self.wrapper)


class MessageEvent(Event):
    # common initialization for MessagePosted and MessageEdited
    def _init_from_data(self):
        self.content = self.data['content']
        self.text_content = _utils.html_to_text(self.content)
        self.user_name = self.data['user_name']
        self.user_id = self.data['user_id']
        self.message_id = self.data['message_id']

    def reply(self, message):
        assert self.wrapper
        self.wrapper.sendMessage(
            self.room_id,
            ":%s %s" % (self.message_id, message))


@register_type
class MessagePosted(MessageEvent):
    type_id = 1


@register_type
class MessageEdited(MessageEvent):
    type_id = 2

    def _init_from_data(self):
        super(MessageEdited, self)._init_from_data()
        self.message_edits = self.data['message_edits']


@register_type
class UserEntered(Event):
    type_id = 3


@register_type
class UserLeft(Event):
    type_id = 4


@register_type
class RoomNameChanged(Event):
    type_id = 5


@register_type
class MessageStarred(MessageEvent):
    type_id = 6

    def _init_from_data(self):
        super(MessageStarred, self)._init_from_data()
        self.message_stars = self.data['message_stars']


@register_type
class DebugMessage(Event):
    type_id = 7


class MentioningMessageEvent(MessageEvent):
    def _init_from_data(self):
        super(MentioningMessageEvent, self)._init_from_data()
        self.target_user_id = self.data['target_user_id']
        self.parent_message_id = self.data['parent_id']


@register_type
class UserMentioned(MentioningMessageEvent):
    type_id = 8


@register_type
class MessageFlagged(Event):
    type_id = 9


@register_type
class MessageDeleted(Event):
    type_id = 10


@register_type
class FileAdded(Event):
    type_id = 11


@register_type
class ModeratorFlag(Event):
    type_id = 12


@register_type
class UserSettingsChanged(Event):
    type_id = 13


@register_type
class GlobalNotification(Event):
    type_id = 14


@register_type
class AccountLevelChanged(Event):
    type_id = 15


@register_type
class UserNotification(Event):
    type_id = 16


@register_type
class Invitation(Event):
    type_id = 17


@register_type
class MessageReply(MentioningMessageEvent):
    type_id = 18

    def _init_from_data(self):
        super(MessageReply, self)._init_from_data()
        self.show_parent = self.data['show_parent']


@register_type
class MessageMovedIn(Event):
    type_id = 19


@register_type
class MessagedMovedOut(Event):
    type_id = 20


@register_type
class TimeBreak(Event):
    type_id = 21


@register_type
class FeedTicker(Event):
    type_id = 22


@register_type
class UserSuspended(Event):
    type_id = 29


@register_type
class UserMerged(Event):
    type_id = 30
