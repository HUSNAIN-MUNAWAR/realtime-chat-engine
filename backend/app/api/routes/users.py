from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models import User
from app.security.dependencies import get_current_user

router = APIRouter()

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "username": user.username, "role": user.role}

@router.get("")
async def list_users(session: AsyncSession = Depends(get_session), _: User = Depends(get_current_user)):
    users = (await session.scalars(select(User).order_by(User.username).limit(100))).all()
    return [{"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in users]
