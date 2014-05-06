import logging


logger = logging.getLogger(__name__)


def make(data, wrapper):
    """
    Instantiates an instance of Event or a subclass, for the given
    event data and (optional) wrapper.
    """
    type_id = data['event_type']
    cls = types.get(type_id, Event)
    return cls(data, wrapper)


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
    def __init__(self, data, wrapper):
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
    """
    Base class for events about Messages.
    """
    def _init_from_data(self):
        self.user_id = self.data['user_id']
        self.user_name = self.data['user_name']
        self.content = self.data.get('content', None)
        self.message_id = self.data['message_id']
        self.message_edits = self.data.get('message_edits', 0)
        self.show_parent = self.data.get('show_parent', False)
        self.message_stars = self.data.get('message_stars', 0)
        self.message_owner_stars = self.data.get('message_owner_stars', 0)
        self.target_user_id = self.data.get('target_user_id', None)
        self.parent_message_id = self.data.get('parent_id', None)

        self.message = self.wrapper.get_message(self.message_id)

        self._update_message()

    def _update_message(self):
        # XXX: assuming Event has newer information than Message.
        message = self.message
        message.content = self.content
        message.deleted = self.content is None
        message.edits = self.message_edits
        message.stars = self.message_stars
        message.pins = self.message_owner_stars
        message.target_user_id = self.target_user_id
        message._parent_message_id = self.parent_message_id

        # this is ugly
        if not isinstance(self, MessageMovedOut):
            message.room_id = self.room_id
            message.room_name = self.room_name


@register_type
class MessagePosted(MessageEvent):
    type_id = 1

    def _update_message(self):
        super(MessagePosted, self)._update_message()
        self.message.owner_user_id = self.user_id
        self.message.owner_user_name = self.user_name
        self.message.time_stamp = self.time_stamp


@register_type
class MessageEdited(MessageEvent):
    type_id = 2

    def _update_message(self):
        super(MessageEdited, self)._update_message()
        # XXX: I need to test with a moderator to determine whether the
        # XXX: user information associate with an edit is the owner
        # XXX: of the post or the user doing the editing. If it's the
        # XXX: user doing the editing, then we should add a new
        # XXX: editor field to Message. For now, we'll ignore the user.


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


@register_type
class UserMentioned(MessageEvent):
    type_id = 8


@register_type
class MessageFlagged(Event):
    type_id = 9


@register_type
class MessageDeleted(MessageEvent):
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
class MessageReply(MessageEvent):
    type_id = 18


@register_type
class MessageMovedOut(MessageEvent):
    type_id = 19


@register_type
class MessagedMovedIn(MessageEvent):
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
