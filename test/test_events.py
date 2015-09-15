from chatexchange import events, client


def test_message_posted_event_initialization():
    event_type = 1
    room_name = "Charcoal Chatbot Sandbox"
    content = 'hello <b>world</b>'
    intended_text_content = 'hello world'
    id = 28258802
    message_id = 15249005
    room_id = 14219
    time_stamp = 1398822427
    user_id = 97938
    user_name = "bot"

    event_data = {
        "content": content,
        "event_type": event_type,
        "id": id,
        "message_id": message_id,
        "room_id": room_id,
        "room_name": room_name,
        "time_stamp": time_stamp,
        "user_id": user_id,
        "user_name": user_name
    }

    event = events.make(event_data, client.Client())

    assert isinstance(event, events.MessagePosted)
    assert type(event) == events.MessagePosted
    assert event.type_id == event_type

    assert event.id == id
    assert event.room.id == room_id
    assert event.room.name == room_name

    assert event.content == content
    assert event.message.text_content == intended_text_content
    assert event.message.id == message_id
    assert event.user.id == user_id
    assert event.user.name == user_name


def test_message_edited_event_initialization():
    event_type = 2
    room_name = "Charcoal Chatbot Sandbox"
    content = 'hello <b>world</b>'
    intended_text_content = 'hello world'
    id = 28258802
    message_id = 15249005
    message_edits = 2
    room_id = 14219
    time_stamp = 1398822427
    user_id = 97938
    user_name = "bot"

    event_data = {
        "content": content,
        "event_type": event_type,
        "id": id,
        "message_id": message_id,
        "message_edits": message_edits,
        "room_id": room_id,
        "room_name": room_name,
        "time_stamp": time_stamp,
        "user_id": user_id,
        "user_name": user_name
    }

    event = events.make(event_data, client.Client())

    assert isinstance(event, events.MessageEdited)
    assert type(event) == events.MessageEdited
    assert event.type_id == event_type

    assert event.id == id
    assert event.room.id == room_id
    assert event.room.name == room_name

    assert event.content == content
    assert event.message.text_content == intended_text_content
    assert event.message.id == message_id
    assert event.message.edits == message_edits
    assert event.user.id == user_id
    assert event.user.name == user_name


def test_message_starred_event_initialization():
    event_type = 6
    room_name = "Charcoal Chatbot Sandbox"
    content = 'hello <b>world</b>'
    intended_text_content = 'hello world'
    id = 28258802
    message_id = 15249005
    message_stars = 3
    room_id = 14219
    time_stamp = 1398822427
    user_id = 97938
    user_name = "bot"

    event_data = {
        "content": content,
        "event_type": event_type,
        "id": id,
        "message_id": message_id,
        "message_stars": message_stars,
        "room_id": room_id,
        "room_name": room_name,
        "time_stamp": time_stamp,
        "user_id": user_id,
        "user_name": user_name
    }

    event = events.make(event_data, client.Client())

    assert isinstance(event, events.MessageStarred)
    assert type(event) == events.MessageStarred
    assert event.type_id == event_type

    assert event.id == id
    assert event.room.id == room_id
    assert event.room.name == room_name

    assert event.content == content
    assert event.message.text_content == intended_text_content
    assert event.message.id == message_id
    assert event.message.stars == message_stars
    assert event.user.id == user_id
    assert event.user.name == user_name
