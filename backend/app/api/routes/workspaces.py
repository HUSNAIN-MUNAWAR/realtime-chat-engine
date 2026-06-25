from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models import Room, RoomMembership, User, Workspace
from app.schemas.chat import WorkspaceCreate
from app.security.dependencies import get_current_user

router = APIRouter()

@router.get("")
async def list_workspaces(session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    rows = (await session.scalars(select(Workspace).order_by(Workspace.created_at))).all()
    return [{"id": w.id, "name": w.name, "slug": w.slug, "owner_id": w.owner_id} for w in rows]

@router.post("")
async def create_workspace(payload: WorkspaceCreate, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    if await session.scalar(select(Workspace).where(Workspace.slug == payload.slug)):
        raise HTTPException(409, "Workspace slug already exists")
    ws = Workspace(name=payload.name, slug=payload.slug, owner_id=user.id)
    session.add(ws); await session.flush()
    general = Room(workspace_id=ws.id, name="general", room_type="channel", created_by_id=user.id)
    session.add(general); await session.flush()
    session.add(RoomMembership(room_id=general.id, user_id=user.id, role="owner"))
    await session.commit()
    return {"id": ws.id, "name": ws.name, "slug": ws.slug, "default_room_id": general.id}
