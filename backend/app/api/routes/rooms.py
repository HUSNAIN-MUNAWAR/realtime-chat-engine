from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models import DirectConversation, Room, RoomMembership, User
from app.schemas.chat import DirectConversationCreate, RoomCreate
from app.security.dependencies import get_current_user

router = APIRouter()

@router.get("")
async def list_rooms(workspace_id: str | None = None, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    stmt = select(Room).join(RoomMembership, Room.id == RoomMembership.room_id).where(RoomMembership.user_id == user.id).order_by(Room.name)
    if workspace_id:
        stmt = stmt.where(Room.workspace_id == workspace_id)
    rooms = (await session.scalars(stmt)).all()
    return [{"id": r.id, "workspace_id": r.workspace_id, "name": r.name, "room_type": r.room_type} for r in rooms]

@router.post("")
async def create_room(payload: RoomCreate, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    room = Room(workspace_id=payload.workspace_id, name=payload.name, room_type=payload.room_type, created_by_id=user.id)
    session.add(room); await session.flush()
    session.add(RoomMembership(room_id=room.id, user_id=user.id, role="owner"))
    await session.commit()
    return {"id": room.id, "workspace_id": room.workspace_id, "name": room.name, "room_type": room.room_type}

@router.post("/{room_id}/join")
async def join_room(room_id: str, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    stmt = pg_insert(RoomMembership).values(room_id=room_id, user_id=user.id, role="member").on_conflict_do_nothing(index_elements=["room_id", "user_id"])
    await session.execute(stmt)
    await session.commit()
    return {"status": "joined", "room_id": room_id}

@router.post("/direct")
async def create_direct(payload: DirectConversationCreate, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    other = await session.get(User, payload.other_user_id)
    if not other:
        raise HTTPException(404, "User not found")
    a, b = sorted([user.id, other.id])
    existing = await session.scalar(select(DirectConversation).where(and_(DirectConversation.workspace_id == payload.workspace_id, DirectConversation.user_a_id == a, DirectConversation.user_b_id == b)))
    if existing:
        room = await session.get(Room, existing.room_id)
        return {"id": room.id, "workspace_id": room.workspace_id, "name": room.name, "room_type": room.room_type}
    room = Room(workspace_id=payload.workspace_id, name=f"dm-{user.username}-{other.username}", room_type="direct", created_by_id=user.id)
    session.add(room); await session.flush()
    session.add(DirectConversation(workspace_id=payload.workspace_id, room_id=room.id, user_a_id=a, user_b_id=b))
    session.add(RoomMembership(room_id=room.id, user_id=user.id, role="member"))
    session.add(RoomMembership(room_id=room.id, user_id=other.id, role="member"))
    await session.commit()
    return {"id": room.id, "workspace_id": room.workspace_id, "name": room.name, "room_type": room.room_type}
