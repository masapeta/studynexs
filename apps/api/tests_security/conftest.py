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
# Login rate-limit counters live in the real (shared dev) Redis and aren't user-scoped, so
# repeated logins across tests would otherwise trip it. The M6 test exercises the limiter
# directly with its own max, so it's unaffected by this ceiling.
os.environ.setdefault("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "1000")

import pytest_asyncio  # noqa: E402

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

ALLOWED_ORIGIN = "http://localhost:3000"  # in settings.ALLOWED_ORIGINS for dev


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


@pytest_asyncio.fixture
async def make_client():
    """Yield a factory of independent AsyncClients against the dev-mode app, each with its
    own cookie jar (= a separate device/session). Seeds one school + one admin user in a
    fresh test schema; overrides get_db. Returns (factory, info-dict)."""
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.database import get_db
    from app.core.security import hash_password
    from app.db.models.base import Base
    from app.db.models.school import School
    from app.db.models.user import User, UserRole
    from app.main import app

    settings = get_settings()
    test_db = f"{settings.DATABASE_URL.rsplit('/', 1)[0]}/studynexs_test"
    eng = create_async_engine(test_db, poolclass=NullPool)
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(eng, expire_on_commit=False)
    async with sm() as s:
        school = School(name="A", code="A", tenant_slug="a", is_active=True,
                        contact_email="a@a.com", contact_phone="+910000000001")
        s.add(school)
        await s.flush()
        s.add_all([
            User(school_id=school.id, username="adm", mobile="+910000000003", full_name="Adm",
                 role=UserRole.SUPER_ADMIN, password_hash=hash_password("Pw@12345"),
                 is_active=True),
            User(school_id=school.id, username="adm2", mobile="+910000000004", full_name="Adm2",
                 role=UserRole.ADMIN, password_hash=hash_password("Pw@12345"), is_active=True),
        ])
        await s.commit()

    async def _override():
        async with sm() as s:
            yield s

    app.dependency_overrides[get_db] = _override
    opened: list = []

    def _factory():
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        opened.append(c)
        return c

    yield _factory, {
        "slug": "a",
        "username": "adm", "password": "Pw@12345",          # super_admin
        "admin_username": "adm2", "admin_password": "Pw@12345",  # admin
    }

    for c in opened:
        await c.aclose()
    app.dependency_overrides.clear()
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
    await eng.dispose()
