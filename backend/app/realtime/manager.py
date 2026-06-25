from __future__ import annotations
import asyncio, json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from fastapi import WebSocket
from redis.asyncio import Redis
from app.observability.metrics import ACTIVE_ROOMS, ACTIVE_USERS, WS_ACTIVE_CONNECTIONS

@dataclass
class ClientConnection:
    websocket: WebSocket
    user_id: str
    username: str
    connection_id: str
    rooms: set[str] = field(default_factory=set)

class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, ClientConnection] = {}
        self.user_connections: dict[str, set[str]] = defaultdict(set)
        self.room_connections: dict[str, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, connection: ClientConnection) -> None:
        await websocket.accept()
        async with self._lock:
            self.connections[connection.connection_id] = connection
            self.user_connections[connection.user_id].add(connection.connection_id)
            self._set_gauges()

    async def disconnect(self, connection_id: str) -> ClientConnection | None:
        async with self._lock:
            connection = self.connections.pop(connection_id, None)
            if not connection:
                self._set_gauges()
                return None
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                self.user_connections.pop(connection.user_id, None)
            for room_id in list(connection.rooms):
                self.room_connections[room_id].discard(connection_id)
                if not self.room_connections[room_id]:
                    self.room_connections.pop(room_id, None)
            self._set_gauges()
            return connection

    async def join_room(self, connection_id: str, room_id: str) -> None:
        async with self._lock:
            if connection_id in self.connections:
                self.connections[connection_id].rooms.add(room_id)
                self.room_connections[room_id].add(connection_id)
                self._set_gauges()

    async def leave_room(self, connection_id: str, room_id: str) -> None:
        async with self._lock:
            if connection_id in self.connections:
                self.connections[connection_id].rooms.discard(room_id)
                self.room_connections[room_id].discard(connection_id)
                if not self.room_connections[room_id]:
                    self.room_connections.pop(room_id, None)
                self._set_gauges()

    async def send_to_connection(self, connection_id: str, event: dict[str, Any]) -> bool:
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        try:
            await connection.websocket.send_json(event)
            return True
        except Exception:
            await self.disconnect(connection_id)
            return False

    async def broadcast_room_local(self, room_id: str, event: dict[str, Any]) -> int:
        delivered = 0
        for cid in list(self.room_connections.get(room_id, set())):
            if await self.send_to_connection(cid, event):
                delivered += 1
        return delivered

    async def broadcast_user_local(self, user_id: str, event: dict[str, Any]) -> int:
        delivered = 0
        for cid in list(self.user_connections.get(user_id, set())):
            if await self.send_to_connection(cid, event):
                delivered += 1
        return delivered

    def _set_gauges(self) -> None:
        WS_ACTIVE_CONNECTIONS.set(len(self.connections))
        ACTIVE_USERS.set(len(self.user_connections))
        ACTIVE_ROOMS.set(len(self.room_connections))

manager = ConnectionManager()

async def redis_listener(redis: Redis, stop_event: asyncio.Event) -> None:
    pubsub = redis.pubsub()
    await pubsub.subscribe("chat:events")
    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not message:
                continue
            try:
                envelope = json.loads(message["data"])
                target = envelope.get("target", {})
                event = envelope.get("event", {})
                if target.get("type") == "room":
                    await manager.broadcast_room_local(target["room_id"], event)
                elif target.get("type") == "user":
                    await manager.broadcast_user_local(target["user_id"], event)
            except Exception:
                continue
    finally:
        await pubsub.unsubscribe("chat:events")
        await pubsub.close()
