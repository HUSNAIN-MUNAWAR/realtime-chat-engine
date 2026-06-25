from __future__ import annotations
import json, time
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy import select
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.ml.risk_model import risk_scorer
from app.models import PresenceSession, User
from app.observability.metrics import MESSAGE_LATENCY, MESSAGES_RECEIVED, MESSAGES_SENT, RATE_LIMIT_EVENTS, REDIS_PUBLISH_LATENCY, WS_CONNECTIONS_TOTAL, WS_ERRORS
from app.realtime.manager import ClientConnection, manager
from app.realtime.protocol import ClientEvent
from app.security.jwt import decode_token
from app.services.message_service import add_delivery_receipt, add_read_receipt, create_message, get_message_by_client_id, is_member, message_to_event
from app.services.rate_limiter import RedisRateLimiter

router = APIRouter()
redis_client: Redis | None = None

def set_redis(redis: Redis) -> None:
    global redis_client
    redis_client = redis

async def publish_event(target: dict, event: dict) -> None:
    if redis_client is None:
        return
    start = time.perf_counter()
    await redis_client.publish("chat:events", json.dumps({"target": target, "event": event}, default=str))
    REDIS_PUBLISH_LATENCY.observe(time.perf_counter() - start)

async def authenticate_ws(token: str | None) -> User | None:
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    async with AsyncSessionLocal() as session:
        return await session.get(User, payload["sub"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None):
    user = await authenticate_ws(token)
    if not user:
        await websocket.close(code=4401)
        WS_CONNECTIONS_TOTAL.labels(result="auth_failed").inc()
        return
    connection_id = str(uuid4())
    await manager.connect(websocket, ClientConnection(websocket=websocket, user_id=user.id, username=user.username, connection_id=connection_id))
    WS_CONNECTIONS_TOTAL.labels(result="accepted").inc()
    limiter = RedisRateLimiter(redis_client, settings.message_rate_limit_per_minute) if redis_client else None
    await websocket.send_json({"type": "connection.init", "payload": {"connection_id": connection_id, "user": {"id": user.id, "username": user.username, "role": user.role}}})
    try:
        await update_presence(user.id, connection_id, "online")
        async for raw in websocket.iter_text():
            if len(raw.encode("utf-8")) > settings.max_message_bytes + 2048:
                await websocket.send_json({"type": "error.validation", "payload": {"detail": "Event is too large"}})
                continue
            try:
                event = ClientEvent.model_validate_json(raw)
            except Exception as exc:
                WS_ERRORS.labels(type="validation").inc()
                await websocket.send_json({"type": "error.validation", "payload": {"detail": str(exc)}})
                continue
            MESSAGES_RECEIVED.inc()
            await handle_event(event, user, connection_id, websocket, limiter)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(connection_id)
        await update_presence(user.id, connection_id, "offline")
        await publish_event({"type": "user", "user_id": user.id}, {"type": "user.presence", "payload": {"user_id": user.id, "status": "offline"}})

async def handle_event(event: ClientEvent, user: User, connection_id: str, websocket: WebSocket, limiter: RedisRateLimiter | None) -> None:
    if event.type == "room.join":
        room_id = event.payload.get("room_id")
        if not room_id:
            await websocket.send_json({"type": "error.validation", "payload": {"detail": "room_id required"}})
            return
        async with AsyncSessionLocal() as session:
            if not await is_member(session, room_id, user.id):
                await websocket.send_json({"type": "error.validation", "payload": {"detail": "You are not a room member"}})
                return
        await manager.join_room(connection_id, room_id)
        await websocket.send_json({"type": "room.joined", "request_id": event.request_id, "payload": {"room_id": room_id}})
        return

    if event.type == "room.leave":
        room_id = event.payload.get("room_id")
        if room_id:
            await manager.leave_room(connection_id, room_id)
        await websocket.send_json({"type": "room.left", "request_id": event.request_id, "payload": {"room_id": room_id}})
        return

    if event.type in {"typing.start", "typing.stop"}:
        room_id = event.payload.get("room_id")
        if room_id:
            await publish_event({"type": "room", "room_id": room_id}, {"type": event.type, "payload": {"room_id": room_id, "user_id": user.id, "username": user.username}})
        return

    if event.type == "presence.heartbeat":
        await update_presence(user.id, connection_id, "online")
        await websocket.send_json({"type": "presence.heartbeat.ack", "request_id": event.request_id, "payload": {"status": "online"}})
        return

    if event.type == "message.delivered":
        message_id, room_id = event.payload.get("message_id"), event.payload.get("room_id")
        if message_id and room_id:
            async with AsyncSessionLocal() as session:
                await add_delivery_receipt(session, message_id, user.id)
            await publish_event({"type": "room", "room_id": room_id}, {"type": "message.delivered", "payload": {"message_id": message_id, "user_id": user.id}})
        return

    if event.type == "message.read":
        message_id, room_id = event.payload.get("message_id"), event.payload.get("room_id")
        if message_id and room_id:
            async with AsyncSessionLocal() as session:
                await add_read_receipt(session, message_id, user.id)
            await publish_event({"type": "room", "room_id": room_id}, {"type": "message.read", "payload": {"message_id": message_id, "user_id": user.id}})
        return

    if event.type in {"message.send", "thread.reply"}:
        start = time.perf_counter()
        allowed, remaining = True, settings.message_rate_limit_per_minute
        if limiter:
            allowed, remaining = await limiter.allow(f"message:{user.id}")
        if not allowed:
            RATE_LIMIT_EVENTS.inc()
            await websocket.send_json({"type": "error.rate_limited", "request_id": event.request_id, "payload": {"remaining": remaining}})
            return
        room_id = event.payload.get("room_id")
        content = str(event.payload.get("content", "")).strip()
        client_message_id = event.payload.get("client_message_id") or str(uuid4())
        parent_id = event.payload.get("parent_message_id")
        if not room_id or not content:
            await websocket.send_json({"type": "error.validation", "request_id": event.request_id, "payload": {"detail": "room_id and content required"}})
            return
        if len(content.encode("utf-8")) > settings.max_message_bytes:
            await websocket.send_json({"type": "error.validation", "request_id": event.request_id, "payload": {"detail": "Message exceeds size limit"}})
            return
        async with AsyncSessionLocal() as session:
            if not await is_member(session, room_id, user.id):
                await websocket.send_json({"type": "error.validation", "request_id": event.request_id, "payload": {"detail": "You are not a room member"}})
                return
            existing = await get_message_by_client_id(session, user.id, client_message_id)
            if existing:
                message = existing
            else:
                message = await create_message(session, room_id, user.id, client_message_id, content, parent_id, risk_scorer.predict(content))
        await websocket.send_json({"type": "message.ack", "request_id": event.request_id, "payload": {"client_message_id": client_message_id, "message_id": message.id, "status": "sent"}})
        await publish_event({"type": "room", "room_id": room_id}, {"type": "message.created", "payload": message_to_event(message, user.username)})
        MESSAGES_SENT.inc()
        MESSAGE_LATENCY.observe(time.perf_counter() - start)
        return

    await websocket.send_json({"type": "error.validation", "request_id": event.request_id, "payload": {"detail": f"Unsupported event type {event.type}"}})

async def update_presence(user_id: str, connection_id: str, status: str) -> None:
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.presence_ttl_seconds)
    if redis_client:
        if status == "online":
            await redis_client.setex(f"presence:{user_id}:{connection_id}", settings.presence_ttl_seconds, status)
        else:
            await redis_client.delete(f"presence:{user_id}:{connection_id}")
    async with AsyncSessionLocal() as session:
        presence = await session.scalar(select(PresenceSession).where(PresenceSession.connection_id == connection_id))
        now = datetime.now(timezone.utc)
        if presence:
            presence.status, presence.last_seen_at, presence.expires_at = status, now, expires
        else:
            session.add(PresenceSession(user_id=user_id, connection_id=connection_id, status=status, last_seen_at=now, expires_at=expires))
        await session.commit()
