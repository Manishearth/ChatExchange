from chatexchange.wrapper import SEChatWrapper, Event


def test_message_posted_event_initialization():
    """
    Tests that Event is initialized with message_posted data correctly.
    """
    wrapper = SEChatWrapper()

    room_name = "Charcoal Chatbot Sandbox"
    content = 'hello <b>world</b>'
    intended_text_content = 'hello world'
    event_type = 1
    event_id = 28258802
    message_id = 15249005
    room_id = 14219
    time_stamp = 1398822427
    user_id = 97938
    user_name = "bot"

    event_data = {
        "content": content,
        "event_type": event_type,
        "id": event_id,
        "message_id": message_id,
        "room_id": room_id,
        "room_name": room_name,
        "time_stamp": time_stamp,
        "user_id": user_id,
        "user_name": user_name
    }

    event = Event(wrapper, event_data)

    assert event.type == Event.Types.message_posted
    # we want to make sure it's an Event.Types, not just a plain int
    assert type(event.type) == type(Event.Types.message_posted)

    assert event.event_id == event_id
    assert event.room_id == room_id
    assert event.room_name == room_name

    assert event.content == content
    assert event.text_content == intended_text_content
    assert event.message_id == message_id
    assert event.user_id == user_id
    assert event.user_name == user_name
