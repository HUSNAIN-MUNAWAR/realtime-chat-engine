# WebSocket Protocol

Endpoint:

```text
ws://localhost:8000/ws?token=<JWT>
```

All messages use this envelope:

```json
{
  "type": "message.send",
  "request_id": "client-generated-id",
  "payload": {}
}
```

## Client to server events

| Type | Required payload | Effect |
|---|---|---|
| `room.join` | `room_id` | Subscribes this connection to room events. Membership is checked in PostgreSQL. |
| `room.leave` | `room_id` | Unsubscribes this connection locally. |
| `message.send` | `room_id`, `content`, `client_message_id` | Persists a message, scores risk, publishes `message.created`. |
| `thread.reply` | `room_id`, `content`, `client_message_id`, `parent_message_id` | Persists a threaded reply. |
| `message.delivered` | `room_id`, `message_id` | Stores delivery receipt and broadcasts status. |
| `message.read` | `room_id`, `message_id` | Stores read receipt and broadcasts status. |
| `typing.start` | `room_id` | Publishes typing indicator. |
| `typing.stop` | `room_id` | Publishes typing stop indicator. |
| `presence.heartbeat` | none | Refreshes Redis/DB presence TTL. |

## Server to client events

| Type | Meaning |
|---|---|
| `connection.init` | Authentication succeeded and connection ID is assigned. |
| `room.joined` | Room join accepted. |
| `message.ack` | Server accepted or de-duplicated a client message. |
| `message.created` | Durable message created and fanned out by Redis pub/sub. |
| `message.delivered` | A user delivered a message. |
| `message.read` | A user read a message. |
| `typing.start` / `typing.stop` | Typing state for a user in a room. |
| `user.presence` | Presence status update. |
| `error.rate_limited` | User exceeded message limit. |
| `error.validation` | Payload failed validation or membership checks. |

## Idempotency

The tuple `(sender_id, client_message_id)` has a unique database constraint. If a client retries after reconnect, the server returns an ack for the existing message instead of storing a duplicate.

## Ordering

Messages are ordered by PostgreSQL `created_at` and indexed by `(room_id, created_at)`. For stricter global ordering across regions, add monotonic sequence allocation or per-room Kafka/Redis Stream partitions.
