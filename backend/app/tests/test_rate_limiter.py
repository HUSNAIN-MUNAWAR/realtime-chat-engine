import pytest
from app.services.rate_limiter import RedisRateLimiter

class FakeRedis:
    def __init__(self): self.data = {}
    async def incr(self, key):
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]
    async def expire(self, key, ttl): return True

@pytest.mark.asyncio
async def test_limiter_blocks_after_limit():
    limiter = RedisRateLimiter(FakeRedis(), limit=2, window_seconds=60)
    assert (await limiter.allow("u1"))[0]
    assert (await limiter.allow("u1"))[0]
    assert not (await limiter.allow("u1"))[0]
