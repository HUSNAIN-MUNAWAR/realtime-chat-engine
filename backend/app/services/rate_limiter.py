import time
from redis.asyncio import Redis

class RedisRateLimiter:
    def __init__(self, redis: Redis, limit: int, window_seconds: int = 60) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    async def allow(self, key: str) -> tuple[bool, int]:
        now = int(time.time())
        bucket = f"rate:{key}:{now // self.window_seconds}"
        count = await self.redis.incr(bucket)
        if count == 1:
            await self.redis.expire(bucket, self.window_seconds + 5)
        remaining = max(self.limit - int(count), 0)
        return int(count) <= self.limit, remaining
