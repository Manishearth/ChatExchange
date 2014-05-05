# Stack Exchange Chat API

Unofficial documentation of the private HTTP APIs used by Stack Exchange chat.

## Event JSON Objects

Chat events are represented by JSON objects.

- `room_id`
- `room_name`
- `event_type` - possible values enumerated below
- `time_stamp` - UTC time stamp


### `event_type` values

#### Message Events

- `1` - message posted
- `2` - message edited
- `6` - message starred or unstarred

All message events contain the the following fields based on the message
they refer to:

- `message_id` - integer
- `content` - string or missing if the user deleted the message
- `message_edits` - integer or missing if message hasn't been edited.
- `message_stars` - integer or missing if message has no stars.
- `target_user_id` - integer or missing
- `show_parent` - boolean or missing

They also contain the following fields, which may refer to the owner of
the most in some cases (e.g. for an id=1 message posted event), but
others may refer to the user taking the action triggering the event
(e.g. for an id=6 message starred or unstarred event).

- `user_id` - integer
- `user_name` - string

## HTTP Methods

All POST methods require an `fkey` POST form data argument.

### POST `/chats/ROOM_ID/messages/new`

Attempts to post a message to the specified chat room.

#### POST form data arguments

##### `text`

The content of the message.

### POST `/messages/MESSAGE_ID`

Attempts to edit a message.

#### POST form data arguments

##### `text`

The new content of the message.

### POST `/chats/ROOM_ID/events?mode=Messages`

Returns the most available recent event_type=1 (MessagePosted) Events
for the given ROOM_ID.

#### URL Query String Arguments

##### `before`

Optional. Limits results to events with a `message_id` less than `before`.

##### `after`

Optional. Limits results to events with a `message_id` greater than or equal to `after`.

##### `msgCount`

Optional. Number of events to return.
Maximum: 500
Default: 100

### POST `/ws-auth`

Authenticates a websocket connection to listen for events in a given
room. This returns a JSON Object with a `url` field, identifying the URL
to be used for the websocket connection. The `l` query string paramter
should be used with websocket URL to specify the time_stamp after which
we are interested in events.

#### POST form data arguments

##### `roomid`
