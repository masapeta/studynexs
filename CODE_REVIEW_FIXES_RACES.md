# Apply-Ready Fixes — Race Conditions (round 2, advise-only)

Closes the genuine remaining races after `9f4e03d`: M2 (attendance + marks), cash idempotency, M6 (rate-limit atomicity). M8 (refresh) outlined, not diffed — it's a design change. Plus the academic-year double-activation race.

Two traps the naive `on_conflict` upsert misses — both handled below:
1. **Duplicate target rows in one payload** → Postgres errors `ON CONFLICT DO UPDATE command cannot affect row a second time`. Must de-dupe the batch by the conflict key first.
2. **`updated_at` won't auto-set** on a Core upsert (the model's `onupdate=func.now()` only fires on ORM updates) → set it explicitly in `set_`.

---

## M2a — Attendance bulk → single race-safe upsert (also kills the N+1)

**`app/modules/attendance/services/attendance_service.py`** — replace the `mark_bulk` loop (lines 19-55):
```python
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

async def mark_bulk(
    self, school_id: uuid.UUID, class_id: uuid.UUID,
    att_date: date, entries: list[AttendanceEntry], marked_by: uuid.UUID,
) -> int:
    scope = TenantScope(self.db, school_id)
    await scope.school_class(class_id)
    await scope.students_in_class(class_id, [e.student_id for e in entries])

    # Trap #1: last write wins if a student appears twice in the payload
    by_student = {e.student_id: e for e in entries}
    if not by_student:
        return 0

    rows = [{
        "school_id": school_id, "student_id": sid, "class_id": class_id,
        "date": att_date, "status": e.status, "marked_by": marked_by, "remarks": e.remarks,
    } for sid, e in by_student.items()]

    stmt = pg_insert(Attendance).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_attendance_student_date",
        set_={
            "status": stmt.excluded.status,
            "remarks": stmt.excluded.remarks,
            "marked_by": stmt.excluded.marked_by,
            "updated_at": func.now(),          # Trap #2
        },
    )
    await self.db.execute(stmt)
    await self.db.flush()
    return len(rows)
```
Concurrent marks for the same class/date now resolve atomically at the DB (no lost update, no 409, no N+1).

## M2b — Exam marks → same pattern

**`app/modules/examinations/services/exam_service.py`** — replace `enter_marks` loop (lines 45-71):
```python
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

async def enter_marks(self, school_id: uuid.UUID, exam_id: uuid.UUID, entries: list[MarkEntry]) -> int:
    scope = TenantScope(self.db, school_id)
    exam = await scope.exam(exam_id)
    by_student = {e.student_id: e for e in entries}
    await scope.students_in_class(exam.class_id, list(by_student))
    if not by_student:
        return 0
    # Optional but recommended: reject marks above the exam max (data integrity, not a race)
    for e in by_student.values():
        if e.marks_obtained > exam.total_marks:
            raise ValueError("marks_obtained exceeds exam total_marks")

    rows = [{
        "school_id": school_id, "exam_id": exam_id, "student_id": sid,
        "marks_obtained": e.marks_obtained, "grade_letter": e.grade_letter, "remarks": e.remarks,
    } for sid, e in by_student.items()]

    stmt = pg_insert(ExamMark).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_exam_student",
        set_={
            "marks_obtained": stmt.excluded.marks_obtained,
            "grade_letter": stmt.excluded.grade_letter,
            "remarks": stmt.excluded.remarks,
            "updated_at": func.now(),
        },
    )
    await self.db.execute(stmt)
    await self.db.flush()
    return len(rows)
```

---

## Cash payment idempotency (the `transaction_id IS NULL` gap)

The H1 index is partial, so cash receipts get none. Give **every** payment a client idempotency key; it also strengthens the gateway path.

**Migration** — `alembic/versions/<rev>_fee_receipt_idempotency_key.py` (`down_revision` = current head = `d1a4f6c8e2b3` unless you've added more):
```python
def upgrade():
    op.add_column("fee_receipts", sa.Column("idempotency_key", sa.String(64), nullable=True))
    op.create_index(
        "uq_receipt_idem_per_school", "fee_receipts",
        ["school_id", "idempotency_key"], unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

def downgrade():
    op.drop_index("uq_receipt_idem_per_school", table_name="fee_receipts")
    op.drop_column("fee_receipts", "idempotency_key")
```

**Model** `app/db/models/fee.py` — column on `FeeReceipt` + index in `__table_args__`:
```python
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    # in __table_args__:
    Index("uq_receipt_idem_per_school", "school_id", "idempotency_key",
          unique=True, postgresql_where=text("idempotency_key IS NOT NULL")),
```

**Schema** `app/modules/fees/schemas/fee.py` — `PayFeeRequest`:
```python
    idempotency_key: str | None = Field(None, max_length=64)
```

**Service** `process_payment` — pre-check (covers cash too) near the top, alongside the transaction_id check:
```python
    if idempotency_key:
        existing = (await self.db.execute(
            select(FeeReceipt).where(
                FeeReceipt.school_id == school_id,
                FeeReceipt.idempotency_key == idempotency_key,
            )
        )).scalar_one_or_none()
        if existing:
            return existing
    ...
    receipt = FeeReceipt(..., idempotency_key=idempotency_key)   # set on create
```
**Endpoint** `fees/endpoints/fee.py` `pay_fee` — pass `idempotency_key=body.idempotency_key` into `process_payment(...)` and add the param to the service signature.

Frontend: generate a UUID per payment attempt, reuse it on retry, and disable the submit button on click (defense-in-depth). The partial index makes truly-concurrent cash dups a 409 (same trade-off as H1); add the rollback→return-existing catch when you want idempotent 200s on both paths.

---

## M6 — Atomic rate-limit counter (kill the permanent-lockout window)

**`app/core/dependencies.py`** — define the script once at module top:
```python
# INCR + first-hit EXPIRE, atomically (no lost-expire → no permanent lockout)
_RATE_LIMIT_LUA = """
local c = redis.call('INCR', KEYS[1])
if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return c
"""
```
In `check_rate_limit`, replace the separate INCR/EXPIRE (lines 249-251):
```python
    redis_key = f"{settings.REDIS_RATE_LIMIT_PREFIX}{key}"
    current = await r.eval(_RATE_LIMIT_LUA, 1, redis_key, window_seconds)
```
Atomic, so the process can't die between INCR and EXPIRE. Still a fixed window (fine for abuse control); a true sliding window (sorted-set / token bucket) is a separate enhancement, not a correctness fix.

---

## Bonus — Academic-year double-activation (silent; M3 can't catch it)

**Migration** — enforce one active year per school at the DB:
```python
op.create_index("uq_one_active_year_per_school", "academic_years",
                ["school_id"], unique=True, postgresql_where=sa.text("is_active"))
```
**Model** `app/db/models/academic.py` `AcademicYear.__table_args__`:
```python
    Index("uq_one_active_year_per_school", "school_id",
          unique=True, postgresql_where=text("is_active")),
```
After this, the concurrent-activate race becomes a clean 409 (via the M3 handler) instead of two active years. `create_year`'s "deactivate others then insert" stays, but the DB now guarantees the invariant. (Backfill check: ensure no school currently has >1 active year before migrating, or the index build fails.)

---

## M8 — Refresh concurrency (schedule, don't batch)

Bigger change; outline only:
- Replace the single `REDIS_REFRESH_JTI_PREFIX{user_id}` value with a **set of valid JTIs per user** (or embed a `sid` device/session id in the refresh token and key by `{user_id}:{sid}`), each with its own TTL.
- On refresh: valid iff presented jti ∈ set → rotate (remove old, add new). Reuse = a jti that's neither current nor a known predecessor → revoke that session (or all, your policy).
- Drop the hard `nx` "refresh already in progress" lock that currently 401s concurrent refreshes; per-session rotation removes the cross-tab/device contention.

This fixes both multi-device logout and the concurrent-refresh spurious logout, but it touches the token model and `rotate_refresh_session` — worth its own commit + tests.

---

### Order / verify
`alembic upgrade head` after the two migrations. Backfill-check the active-year index. Then for each upsert, a quick concurrency test (two `asyncio.gather` saves for the same class/date → one row, no error). As noted in pass-2 N7, the current suite runs with rate-limiting/tenant/CSRF/middleware off, so M6 needs manual verification or a dedicated test that flips `RATE_LIMIT_ENABLED` on.
