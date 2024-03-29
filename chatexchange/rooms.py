import sys
if sys.version_info[0] == 2:
    import Queue as queue
else:
    import queue
import logging

from . import _utils, events, markdown_detector


logger = logging.getLogger(__name__)


class Room(object):
    def __init__(self, id, client):
        self.id = id
        self._logger = logger.getChild('Room')
        self._client = client
        self.send_aggressively = client.aggressive_sender

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

    def leave(self):
        return self._client._leave_room(self.id)

    def _mergeable_pair(self, message1, message2):
        """
        Helper for self.send_aggressively: determine if two messages can be merged
        """
        if message1 is None or message2 is None:
            return False
        op1, room1, msg1 = message1
        op2, room2, msg2 = message2
        if op1 != 'send':
            return False
        if op2 != 'send':
            return False
        if room1 != room2:
            return False
        # If one starts with four spaces, the other also needs to start with four spaces
        indent1 = msg1.startswith('    ')
        indent2 = msg2.startswith('    ')
        if indent1 != indent2:
            return False
        if indent1 and indent2:
            return True

        if markdown_detector.markdown(msg1):
            return False
        if markdown_detector.markdown(msg2):
            return False
        return True

    def send_message(self, text, length_check=True):
        """
        Sends a message (queued, to avoid getting throttled)
        @ivar text: The message to send
        @type text: L{str}
        """
        if len(text) > 500 and length_check and '\n' not in text:
            self._logger.info("Could not send message because it was longer than 500 characters.")
            return
        if len(text) == 0:
            self._logger.info("Could not send message because it was empty.")
            return
        if self.send_aggressively:
            previous_request = self._client._request_queue.peek_latest()
            if self._mergeable_pair(previous_request, ('send', self.id, text)):
                merged_text = '\n'.join([previous_request[2], text])
                if (not length_check or len(merged_text) <= 500) and \
                    self._client._request_queue.poke_latest(previous_request, (
                        tuple(list(previous_request[0:2]) + [merged_text]))):
                    self._logger.info(
                        "Merging message %r for room_id #%r to previous queued message",
                        text, self.id)
                    return
        self._client._request_queue.put(('send', self.id, text))
        self._logger.info("Queued message %r for room_id #%r.", text, self.id)
        self._logger.info("Queue length: %d.", self._client._request_queue.qsize())

    def watch(self, event_callback):
        return self.watch_polling(event_callback, 3)

    def watch_polling(self, event_callback, interval):
        def on_activity(activity):
            for event in self._events_from_activity(activity, self.id):
                event_callback(event, self._client)

        return self._client._br.watch_room_http(self.id, on_activity, interval)

    def watch_socket(self, event_callback):
        def on_activity(activity):
            for event in self._events_from_activity(activity, self.id):
                event_callback(event, self._client)

        return self._client._br.watch_room_socket(self.id, on_activity)

    def _events_from_activity(self, activity, room_id):
        """
        Returns a list of Events associated with a particular room,
        given an activity message from the server.
        """
        room_activity = activity.get('r%s' % (room_id,), {})
        room_events_data = room_activity.get('e', [])
        for room_event_data in room_events_data:
            if room_event_data:
                event = events.make(room_event_data, self._client)
                self._client._recently_gotten_objects.appendleft(event)
                yield event

    def new_events(self, types=events.Event):
        return FilteredEventIterator(self, types)

    def new_messages(self):
        return MessageIterator(self)

    def get_pingable_users(self):
        return [
            self._client.get_user(user_id, name=name)
            for (user_id, name, _1, _2)
            in self._client._br.get_pingable_users_in_room(self.id)
        ]

    def get_current_users(self):
        return [
            self._client.get_user(user_id, name=name)
            for (user_id, name)
            in self._client._br.get_current_users_in_room(self.id)
        ]

    def get_pingable_user_ids(self):
        return self._client._br.get_pingable_user_ids_in_room(self.id)

    def get_pingable_user_names(self):
        return self._client._br.get_pingable_user_names_in_room(self.id)

    def get_current_user_ids(self):
        return self._client._br.get_current_user_ids_in_room(self.id)

    def get_current_user_names(self):
        return self._client._br.get_current_user_names_in_room(self.id)


class FilteredEventIterator(object):
    def __init__(self, room, types):
        self.types = types
        self._queue = queue.Queue()

        room.join()
        self._watcher = room.watch(self._on_event)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tracback):
        self._watcher.close()

    def __iter__(self):
        while True:
            yield self._queue.get()

    def _on_event(self, event, client):
        if isinstance(event, self.types):
            self._queue.put(event)


class MessageIterator(object):
    def __init__(self, room):
        self._event_iter = FilteredEventIterator(room, events.MessagePosted)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tracback):
        self._event_iter._watcher.close()

    def __iter__(self):
        for event in self._event_iter:
            yield event.message

    def _on_event(self, event, client):
        return self._event_iter._on_event(event)
