from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.security.jwt import create_access_token
from app.security.passwords import hash_password, verify_password

router = APIRouter()

def public_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "username": user.username, "role": user.role, "created_at": user.created_at.isoformat() if user.created_at else None}

@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)):
    existing = await session.scalar(select(User).where((User.email == str(payload.email).lower()) | (User.username == payload.username.lower())))
    if existing:
        raise HTTPException(status_code=409, detail="Email or username already exists")
    user = User(email=str(payload.email).lower(), username=payload.username.lower(), hashed_password=hash_password(payload.password), role="user")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, user.role), user=public_user(user))

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    user = await session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id, user.role), user=public_user(user))
