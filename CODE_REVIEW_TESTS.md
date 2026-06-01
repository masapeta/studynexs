# Regression Suite — harness design + skeletons (advise-only)

Goal: lock in the last three commits (upserts, cash idempotency, M6, active-year) and give M8 a net. Two buckets, because they have **different** requirements:

- **`tests/test_concurrency.py`** — service-level, real races, normal pytest process.
- **`tests/security/`** — needs the middleware/guards actually ON, so it runs as a **separate process** with a non-testing env.

---

## Two traps that make a green suite meaningless

**Trap A — you cannot re-enable the guards with a runtime flag.**
`app = create_app()` runs at *import*, and `create_app` only adds `Audit/Tenant/Metrics` middleware `if settings.ENVIRONMENT != TESTING`. Worse, `check_rate_limit`, `validate_tenant_school_match`, and `validate_refresh_origin` each early-`return` when `settings.ENVIRONMENT == "testing"`, and every module captured `settings = get_settings()` at import (lru-cached). So flipping `settings.ENVIRONMENT` mid-test does nothing — the app and the captured settings are already built. The clean fix is **process isolation**: a separate test dir whose env is set *before* import. Don't fight the cache in-process.

**Trap B — one shared session can't race.**
The existing `db_session`/`client` fixtures yield a *single* `AsyncSession` inside one rolled-back transaction. Two coroutines sharing it run in the *same* transaction on the *same* connection — `ON CONFLICT` can't fire (no second tx), no row-lock contention, and `AsyncSession` isn't concurrency-safe anyway. A race test built on it passes trivially and tests nothing. Race tests need **two independent sessions on two connections that actually `commit()`**, against a DB where the unique indexes exist (`create_all` builds them from the models).

---

## Bucket 1 — `tests/test_concurrency.py` (real races, service-level)

Self-contained engine; seed-and-commit first (so other sessions can see the rows), then race, then assert. No `client`/`db_session` override.

```python
import asyncio, uuid
from datetime import date

import pytest, pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.models.base import Base
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.academic import AcademicYear, Class
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.db.models.student import Student
from app.modules.attendance.services.attendance_service import AttendanceService
from app.modules.attendance.schemas.attendance import AttendanceEntry

_base = get_settings().DATABASE_URL.rsplit("/", 1)[0]
TEST_DB_URL = f"{_base}/studynexs_test"


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.create_all)   # builds the partial unique indexes too
    yield eng
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
    await eng.dispose()


def _sm(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed(engine):
    """Commit a school+class+student+teacher so concurrent sessions can see them."""
    async with _sm(engine)() as s:
        school = School(name="T", code="T", tenant_slug="t", board="CBSE",
                        contact_email="a@t.com", contact_phone="+910000000000", is_active=True)
        s.add(school); await s.flush()
        ay = AcademicYear(school_id=school.id, year_label="2026-2027",
                          start_date=date(2026,6,1), end_date=date(2027,5,31), is_active=True)
        s.add(ay); await s.flush()
        cls = Class(school_id=school.id, grade="1", section="A", academic_year_id=ay.id)
        teach = User(school_id=school.id, mobile="+910000000001", full_name="T",
                     role=UserRole.TEACHER, is_active=True)
        s.add_all([cls, teach]); await s.flush()
        suser = User(school_id=school.id, mobile="+910000000002", full_name="S",
                     role=UserRole.STUDENT, is_active=True)
        s.add(suser); await s.flush()
        stu = Student(school_id=school.id, user_id=suser.id, class_id=cls.id, admission_no="A1")
        s.add(stu); await s.commit()
        return school.id, cls.id, stu.id, teach.id


@pytest.mark.asyncio
async def test_attendance_concurrent_save_one_row(engine):
    school_id, class_id, stu_id, teacher_id = await _seed(engine)

    async def mark(status):
        async with _sm(engine)() as s:
            await AttendanceService(s).mark_bulk(
                school_id, class_id, date(2026, 6, 1),
                [AttendanceEntry(student_id=stu_id, status=status)], teacher_id)
            await s.commit()

    # 4 concurrent saves for the same student/date
    await asyncio.gather(*(mark(AttendanceStatus.PRESENT) for _ in range(4)))

    async with _sm(engine)() as s:
        n = await s.scalar(select(func.count()).select_from(Attendance)
                           .where(Attendance.student_id == stu_id,
                                  Attendance.date == date(2026, 6, 1)))
    assert n == 1     # upsert collapsed all four into one row, no IntegrityError
```

Same shape for the others (left as stubs — copy the fixture):
- **`test_exam_marks_concurrent_save_one_row`** — 4 concurrent `enter_marks` for one (exam, student) → 1 `ExamMark`. Add a sequential `test_enter_marks_rejects_over_max` (one entry > `total_marks` → `ValueError`).
- **`test_active_year_double_activate`** — two sessions each `SchoolService(s).create_year(is_active=True)` + commit, gathered. Assert exactly **one** active year and that exactly one coroutine raised `IntegrityError` (the partial unique index). *Note:* `create_year` does `UPDATE … is_active=False` then insert; under the index the loser's commit fails — verify your service/endpoint surfaces that as the 409 you expect.
- **`test_cash_idempotency_concurrent`** — two `process_payment` with the **same `idempotency_key`** (transaction_id=None) → exactly one `FeeReceipt`; loser raises `IntegrityError`. Plus a sequential `test_same_idem_key_returns_same_receipt` (pre-check path → same receipt id, no error).

> Collect IntegrityErrors from `gather` with `return_exceptions=True` and assert exactly one, e.g. `errs = [r for r in results if isinstance(r, IntegrityError)]; assert len(errs) == 1`.

---

## Bucket 2 — `tests/security/` (guards ON, separate process)

Its own `conftest.py` whose **first lines** set a non-testing env, *before* any app import:
```python
import os
os.environ["ENVIRONMENT"] = "development"     # not "testing" → guards/middleware active
os.environ["RATE_LIMIT_ENABLED"] = "true"
os.environ["TENANT_BASE_DOMAIN"] = "localhost"
from app.core.config import get_settings; get_settings.cache_clear()
# ...then import app, build client, seed two schools (tenant_slug "a" and "b")
```
Run as a distinct step so it can't share the cached testing settings:
```
ENVIRONMENT=development RATE_LIMIT_ENABLED=true pytest tests/security -p no:cacheprovider
```
Tests:
- **`test_rate_limit_429_and_ttl`** *(real Redis required — uses Lua `eval`)* — call `check_rate_limit(key, max=N, window=60, r)` N times (ok) then once more → `HTTPException(429)`; assert `await r.ttl(prefixed_key) > 0` after the first call (the no-lost-expire property). fakeredis Lua support is flaky — point CI at a real Redis service.
- **`test_tenant_mismatch_rejected`** — log in under tenant **a**, call any authed route with header `X-Tenant-Slug: b` → **403** ("not valid for this school tenant"). This is the cross-tenant control that `test_tenant_isolation.py` can't reach today.
- **`test_refresh_requires_allowed_origin`** — `POST /auth/refresh` with no/`evil.com` `Origin` → **403**; with an allowed origin → 200.

CI services needed: Postgres (`studynexs_test`) and Redis. Run bucket 1 in the normal `pytest` step; bucket 2 as the separate `ENVIRONMENT=development` step above.

---

## After it's green → M8 (own commit)
Implement off the sid-keyed design from the previous note (embed `sid` in the refresh token; Redis `refresh:{user_id}:{sid}` → current jti; rotate per session; reuse → revoke that sid; drop the `nx` lock; logout deletes one sid, logout-all scans `refresh:{user_id}:*`). Its tests belong in **bucket 2** (they need the real refresh/Redis path): two devices refresh independently (both 200); replay an old jti on one sid → that session 401s, the other still works.
```
```
Heads-up: the sid change touches `create_refresh_token` (claims), `issue_tokens`, `rotate_refresh_session`, and `logout` — keep it isolated from the test commit so a bisect stays clean.
```
