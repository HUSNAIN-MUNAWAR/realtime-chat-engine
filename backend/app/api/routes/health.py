from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.realtime.manager import manager
from app.services.redis import get_redis

router = APIRouter()

@router.get("/health")
async def health(session: AsyncSession = Depends(get_session), redis: Redis = Depends(get_redis)):
    await session.execute(text("SELECT 1"))
    pong = await redis.ping()
    return {"status": "ok", "database": "ok", "redis": "ok" if pong else "error", "active_connections": len(manager.connections)}

@router.get("/ready")
async def ready():
    return {"status": "ready"}
