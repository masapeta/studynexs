"""Guards-ON integration tests: cross-tenant rejection + refresh-origin (CSRF) check.

These need the real middleware/dependencies active (dev mode), a client against the app,
and two seeded schools. They run in the bucket-2 separate process (see conftest).
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.db.models.base import Base
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.main import app

settings = get_settings()
TEST_DB_URL = f"{settings.DATABASE_URL.rsplit('/', 1)[0]}/studynexs_test"


@pytest_asyncio.fixture
async def client():
    eng = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(eng, expire_on_commit=False)
    async with sm() as s:
        a = School(name="A", code="A", tenant_slug="a", is_active=True,
                   contact_email="a@a.com", contact_phone="+910000000001")
        b = School(name="B", code="B", tenant_slug="b", is_active=True,
                   contact_email="b@b.com", contact_phone="+910000000002")
        s.add_all([a, b])
        await s.flush()
        s.add(User(school_id=a.id, username="adm", mobile="+910000000003", full_name="Adm",
                   role=UserRole.SUPER_ADMIN, password_hash=hash_password("Pw@12345"),
                   is_active=True))
        await s.commit()

    async def _override():
        async with sm() as s:
            yield s

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
    await eng.dispose()


async def _login(client) -> str:
    r = await client.post("/api/v1/auth/login", headers={"X-Tenant-Slug": "a"},
                          json={"username": "adm", "password": "Pw@12345"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body.get("access_token") or body.get("data", {}).get("access_token")


@pytest.mark.asyncio
async def test_tenant_mismatch_rejected(client):
    token = await _login(client)
    # Token is for tenant "a"; calling with tenant "b" must 403.
    r = await client.get("/api/v1/users?page_size=1",
                         headers={"Authorization": f"Bearer {token}", "X-Tenant-Slug": "b"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_refresh_requires_allowed_origin(client):
    await _login(client)  # sets the refresh cookie
    bad = await client.post("/api/v1/auth/refresh",
                            headers={"X-Tenant-Slug": "a", "Origin": "http://evil.com"})
    assert bad.status_code == 403
