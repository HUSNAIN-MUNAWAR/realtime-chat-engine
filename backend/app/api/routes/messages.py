from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models import User
from app.security.dependencies import get_current_user
from app.services.message_service import is_member, list_messages, message_to_event

router = APIRouter()

@router.get("/{room_id}")
async def history(room_id: str, limit: int = Query(default=50, ge=1, le=100), before: str | None = None, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    if not await is_member(session, room_id, user.id):
        raise HTTPException(403, "Not a room member")
    messages, next_cursor = await list_messages(session, room_id, limit, before)
    return {"items": [message_to_event(m) for m in messages], "next_cursor": next_cursor}
