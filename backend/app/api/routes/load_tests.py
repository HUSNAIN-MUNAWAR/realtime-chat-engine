from datetime import timedelta
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_session
from app.models import LoadTestRun, Room, RoomMembership, User, Workspace
from app.schemas.chat import ProvisionLoadTestRequest
from app.security.jwt import create_access_token
from app.security.passwords import hash_password

router = APIRouter()

@router.post("/provision")
async def provision_load_test(payload: ProvisionLoadTestRequest, x_load_test_secret: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    if not settings.enable_load_test_endpoints or x_load_test_secret != settings.load_test_secret:
        raise HTTPException(403, "Load-test provisioning disabled or invalid secret")
    run = LoadTestRun(name=payload.run_name, users=payload.users, rooms=payload.rooms, message_rate=payload.message_rate, status="provisioned")
    session.add(run); await session.flush()
    ws = Workspace(name=f"Load Test {run.id[:8]}", slug=f"load-test-{run.id[:8]}", owner_id=None)
    session.add(ws); await session.flush()
    rooms = []
    for i in range(payload.rooms):
        room = Room(workspace_id=ws.id, name=f"lt-room-{i}", room_type="channel", created_by_id=None)
        session.add(room); rooms.append(room)
    await session.flush()
    users, password_hash = [], hash_password("LoadTest12345!")
    for i in range(payload.users):
        u = User(email=f"lt-{run.id}-{i}@example.com", username=f"lt_{run.id[:8]}_{i}", hashed_password=password_hash, role="load_tester")
        session.add(u); users.append(u)
        if i and i % 1000 == 0:
            await session.flush()
    await session.flush()
    memberships = [{"room_id": rooms[i % len(rooms)].id, "user_id": u.id, "role": "member"} for i, u in enumerate(users)]
    if memberships:
        await session.execute(pg_insert(RoomMembership), memberships)
    await session.commit()
    tokens = [create_access_token(u.id, "load_tester", expires_delta=timedelta(hours=12)) for u in users]
    return {"run_id": run.id, "workspace_id": ws.id, "rooms": [{"id": r.id, "name": r.name} for r in rooms], "users": [{"id": u.id, "username": u.username, "token": tokens[i], "room_id": rooms[i % len(rooms)].id} for i, u in enumerate(users)]}
