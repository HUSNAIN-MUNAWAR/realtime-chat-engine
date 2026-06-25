from collections.abc import AsyncGenerator
from redis.asyncio import Redis
from app.core.config import settings

redis: Redis | None = None

async def init_redis() -> Redis:
    global redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.ping()
    return redis

async def close_redis() -> None:
    if redis:
        await redis.close()

async def get_redis() -> AsyncGenerator[Redis, None]:
    if redis is None:
        raise RuntimeError("Redis not initialized")
    yield redis
