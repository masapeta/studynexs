"""Bucket 2 — guards/middleware ON.

Runs as a SEPARATE process so the env is set BEFORE any app import: settings are
lru-cached at import and the middleware/tenant/CSRF/rate-limit early-returns all key off
ENVIRONMENT == "testing", so flipping them in-process is a silent no-op.

Run:  ENVIRONMENT=development RATE_LIMIT_ENABLED=true pytest tests_security -p no:cacheprovider

This dir is intentionally a SIBLING of tests/ (not tests/security/): tests/conftest.py sets
ENVIRONMENT=testing and imports app at module top, which would build the app in testing mode
before our env takes effect. Needs a real Redis (the M6 test uses Lua eval; fakeredis is flaky).
"""
import os

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("RATE_LIMIT_ENABLED", "true")
os.environ.setdefault("TENANT_BASE_DOMAIN", "localhost")

import pytest_asyncio  # noqa: E402

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()


@pytest_asyncio.fixture(autouse=True)
async def reset_redis_pool():
    """Close the global Redis pool between tests — pytest-asyncio gives each test a fresh
    event loop, and the module-cached pool is bound to the loop that created it. Without this,
    the second test to touch Redis hits 'Event loop is closed' on the dead connection."""
    import app.core.dependencies as deps

    if deps._redis_pool is not None:
        await deps._redis_pool.aclose()
        deps._redis_pool = None
    yield
    if deps._redis_pool is not None:
        await deps._redis_pool.aclose()
        deps._redis_pool = None
