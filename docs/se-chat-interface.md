Incomplete unofficial documentation of Stack Exchange chat interface.

All POST methods require an `fkey` POST form data argument. It won't be
specifically listed for each of them.

## Event JSON Objects

Chat events are represented by JSON objects with at least the following
fields:

- `room_id` - integer
- `room_name` - string
- `event_type` - integer, possible values enumerated below
- `time_stamp` - integer

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
- `message_owner_stars` - integer or missing if message not pinned.
- `target_user_id` - integer or missing
- `show_parent` - boolean or missing

They also contain the following fields, which may refer to the owner of
the most in some cases (e.g. for an id=1 message posted event), but
others may refer to the user taking the action triggering the event
(e.g. for an id=6 message starred or unstarred event).

- `user_id` - integer
- `user_name` - string

## Reading

### POST `/chats/ROOM_ID/events?mode=Messages`

Returns the most available recent event_type=1 (MessagePosted) Events
for the given ROOM_ID.

#### URL Query String Arguments

##### `before`

Optional. Limits results to events with a `message_id` less than
`before`.

##### `after`

Optional. Limits results to events with a `message_id` greater than or
equal to `after`.

##### `msgCount`

Optional. Number of events to return.  
Maximum: 500  
Default: 100

### POST `/events`

Returns a list of recent events for a room.

#### POST form data arguments

##### `rROOM_ID`

The name specifies the room we are interested in (e.g. `'r14219'`), and
the value specifies the `time_stamp` we would like to see messages
since.

### GET `/message/MESSAGE_ID`

Returns the text of the specified message.

#### URL Query String Arguments

##### `plain`

Optional. If false or missing, the rendered HTML of the message will be
returned. If true, the original markdown source of the message will be.

### POST `/ws-auth`

Authenticates a websocket connection to listen for events in a given
room. This returns a JSON Object with a `url` field, identifying the URL
to be used for the websocket connection. The `l` query string paramter
should be used with websocket URL to specify the time_stamp after which
we are interested in events.

#### POST form data arguments

##### `roomid`

### GET `/rooms/thumbs/ROOM_ID`

Returns a JSON object with information about the specified room.
Includes the following fields:

- `id` - integer
- `name` - string
- `description` - string
- `isFavorite` - boolean
- `usage` - null or string with HTML displaying graph of room activity
- `tags` - string with HTML displays tags associated with room

#### URL Query String Arguments

##### `showUsage`

Optional Whether the `usage` field should be populated, else null.  
Default: false

### POST `/user/info/`

Returns information about users in the context of a given room.

The result is a JSON object with a single field, `users`, a list of
objects each of which has the following keys:

- `id` - integer
- `name` - string
- `reputation` - integer
- `is_moderator` - boolean
- `is_owner` - boolean
- `email_hash` - an hex MD5 hash digest used to identify a gravatar,
  or a `!`-prefixed avatar URL.

#### POST form data arguments

##### `ids`

The ID (comma-seperated list of IDs?) of the users in question.

##### `roomId`

The ID of the room in question.

## Writing

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

### POST `/messages/MESSAGE_ID/star`

Stars or unstars the specified message. You can't specify whether you
want to have starred the message or not, you can just toggle whether
you have.

### POST `/messages/MESSAGE_ID/owner-star`

Pins or unpins the specified message. This is a toggle, like starring.

### POST `/messages/MESSAGE_ID/delete`

Removes `content` of the specified message.

### POST `/admin/movePosts/ROOM_ID`

Moves posts from the specified room to another room.

#### POST form data arguments

- `ids` - comma-seperated list of message_ids
- `to` - room_id of room the messages should be moved to
