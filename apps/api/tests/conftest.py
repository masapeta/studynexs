import os
import uuid
from typing import AsyncGenerator
from datetime import date

os.environ["ENVIRONMENT"] = "testing"
os.environ["OUTBOX_WORKER_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.core.config import get_settings

get_settings.cache_clear()

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import get_db
from app.core.dependencies import get_redis
from app.core.security import hash_password, create_access_token
from app.db.models.academic import AcademicYear, Class
from app.db.models.base import Base
from app.db.models.fee import FeeFrequency, FeeStructure, FeeType, ReceiptCounter
from app.db.models.school import School
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User, UserRole
from app.main import app

settings = get_settings()

db_url = settings.DATABASE_URL
base_url = db_url.rsplit("/", 1)[0]
TEST_DB_NAME = "studynexs_test"
TEST_DB_URL = f"{base_url}/{TEST_DB_NAME}"


async def _ensure_test_database() -> None:
    """Create studynexs_test if missing (connect via postgres maintenance DB)."""
    import asyncpg

    conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


class _FakeRedis:
    """Minimal in-memory Redis for tests — no server required."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def setex(self, key: str, _ttl: int, value: str) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    async def eval(self, _script: str, _numkeys: int, _key: str, *_args) -> int:
        return 1

    async def aclose(self) -> None:
        return None


@pytest_asyncio.fixture
async def engine():
    """Function-scoped engine — avoids asyncpg 'different loop' errors with httpx."""
    await _ensure_test_database()
    _engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Fresh session per test.
    Each test runs in a transaction that is rolled back.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        yield session

        await session.close()
        await transaction.rollback()

@pytest_asyncio.fixture(autouse=True)
async def reset_redis_pool():
    """Close global Redis pool between tests (avoids 'Event loop is closed')."""
    import app.core.dependencies as deps

    if deps._redis_pool is not None:
        await deps._redis_pool.aclose()
        deps._redis_pool = None
    yield
    if deps._redis_pool is not None:
        await deps._redis_pool.aclose()
        deps._redis_pool = None


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with DB override."""
    fake_redis = _FakeRedis()

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Tenant-Slug": "test"},
    ) as c:
        yield c
    app.dependency_overrides.clear()

# ── Helpers ──────────────────────────────────────────────────────────────────

async def get_auth_token(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]

def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def access_token_for(user: User, *, tenant_slug: str = "test") -> str:
    """Issue a bearer token without hitting /auth/login (avoids Redis in unit tests)."""
    return create_access_token(
        user_id=str(user.id),
        school_id=str(user.school_id),
        role=user.role.value,
        tenant_slug=tenant_slug,
    )

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_school(db_session: AsyncSession) -> School:
    school = School(
        name="Test School", code="TST", tenant_slug="test", board="CBSE",
        contact_email="admin@test.com", contact_phone="+911234567890", is_active=True
    )
    db_session.add(school)
    await db_session.flush()
    return school

@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, test_school: School) -> User:
    user = User(
        school_id=test_school.id, username="test_admin", mobile="+919876543210",
        full_name="Test Admin", role=UserRole.SUPER_ADMIN,
        password_hash=hash_password("Admin@123"), is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    return user

@pytest_asyncio.fixture
async def teacher_user(db_session: AsyncSession, test_school: School) -> User:
    user = User(
        school_id=test_school.id, username="test_teacher", mobile="+919876543211",
        full_name="Test Teacher", role=UserRole.TEACHER,
        password_hash=hash_password("Teacher@123"), is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    return user

@pytest_asyncio.fixture
async def academic_year(db_session: AsyncSession, test_school: School) -> AcademicYear:
    ay = AcademicYear(
        school_id=test_school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True
    )
    db_session.add(ay)
    await db_session.flush()
    return ay

@pytest_asyncio.fixture
async def test_class(db_session: AsyncSession, test_school: School, academic_year: AcademicYear) -> Class:
    cls = Class(
        school_id=test_school.id, grade="Grade 1", section="A", academic_year_id=academic_year.id
    )
    db_session.add(cls)
    await db_session.flush()
    return cls

@pytest_asyncio.fixture
async def fee_setup(
    db_session: AsyncSession, test_school: School, test_class: Class, academic_year: AcademicYear
) -> FeeStructure:
    counter = ReceiptCounter(
        school_id=test_school.id,
        prefix="TST",
        last_sequence=0,
    )
    db_session.add(counter)
    structure = FeeStructure(
        school_id=test_school.id,
        class_id=test_class.id,
        fee_type=FeeType.TUITION,
        amount=5000.00,
        frequency=FeeFrequency.MONTHLY,
        academic_year_id=academic_year.id,
        due_day=5,
    )
    db_session.add(structure)
    await db_session.flush()
    return structure


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession, test_school: School, test_class: Class) -> User:
    user = User(
        school_id=test_school.id, username="test_student", mobile="+919876543212",
        full_name="Test Student", role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"), is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    student = Student(
        school_id=test_school.id, user_id=user.id, class_id=test_class.id,
        admission_no="ADM001", roll_no="1"
    )
    db_session.add(student)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def parent_user(
    db_session: AsyncSession, test_school: School, student_user: User
) -> User:
    """A parent linked to `student_user` (via StudentParentMap)."""
    user = User(
        school_id=test_school.id, username="test_parent", mobile="+919876543213",
        full_name="Test Parent", role=UserRole.PARENT,
        password_hash=hash_password("Parent@123"), is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    parent = Parent(
        school_id=test_school.id, user_id=user.id,
        relationship_type=Relationship.FATHER,
    )
    db_session.add(parent)
    await db_session.flush()

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    db_session.add(
        StudentParentMap(student_id=student.id, parent_id=parent.id, is_primary=True)
    )
    await db_session.flush()
    return user
