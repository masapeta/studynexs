"""M6 — atomic rate limiter. Proves the Lua INCR+EXPIRE blocks at the limit AND sets a TTL
on the first hit (the no-lost-expire / no-permanent-lockout property). Real Redis required.
"""
import os

import pytest
import redis.asyncio as redis
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.dependencies import check_rate_limit

settings = get_settings()


@pytest.mark.asyncio
async def test_rate_limit_blocks_and_sets_ttl():
    # If guards are off (ENVIRONMENT=testing) check_rate_limit early-returns → this would
    # pass while testing nothing. Assert we're really in a guards-on process.
    assert settings.ENVIRONMENT != "testing", "run bucket 2 with ENVIRONMENT=development"

    r = redis.from_url(settings.REDIS_URL)
    key = "m6test:" + os.urandom(6).hex()
    prefixed = f"{settings.REDIS_RATE_LIMIT_PREFIX}{key}"
    try:
        for _ in range(3):
            await check_rate_limit(key, 3, 60, r)          # 3 allowed
        # The atomic Lua set the TTL on the first INCR — no permanent-lockout window.
        assert await r.ttl(prefixed) > 0
        with pytest.raises(HTTPException) as ei:
            await check_rate_limit(key, 3, 60, r)          # 4th → blocked
        assert ei.value.status_code == 429
    finally:
        await r.delete(prefixed)
        await r.aclose()
