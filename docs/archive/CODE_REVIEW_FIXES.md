# Apply-Ready Fixes (advise-only)

Diffs are against the code as reviewed. Order = your pilot priority. Each is independent unless noted.
`C1` (rotate the OpenAI key) is dashboard-only and yours.

---

## 1. M1 — Rate-limit + monthly per-school cap on AI generation  *(do first; live cost risk)*

**Scope note:** this caps abuse/cost. It does **not** move generation off the request thread — the endpoints still `await` the LLM while holding a DB connection (the 60 s / pool-exhaustion concern). Offloading to your existing Arq queue is a separate, larger change; this is the cheap risk-killer.

**`app/core/config.py`** — add near the AI section (after line ~144):
```python
    # ── AI quotas / abuse control ────────────────────────────────
    AI_GENERATE_RATE_PER_MIN: int = 10          # per user, per endpoint
    AI_MONTHLY_CAP_ENABLED: bool = True
    AI_MONTHLY_GENERATION_CAP: int = 1000       # papers + reports per school per calendar month
```

**`app/modules/ai/endpoints/ai.py`** — imports: add `Environment` and `rate_limit`:
```python
from app.core.config import Environment, get_settings          # add Environment
from app.core.rate_limit import rate_limit                      # new
```
Add the quota helper (top of file, after `settings = get_settings()`):
```python
async def _enforce_ai_quota(school_id: uuid.UUID, db: AsyncSession) -> None:
    if not settings.AI_MONTHLY_CAP_ENABLED or settings.ENVIRONMENT == Environment.TESTING:
        return
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    used = await db.scalar(
        select(func.count()).select_from(AIUsage).where(
            AIUsage.school_id == school_id,
            AIUsage.created_at >= month_start,
        )
    ) or 0
    if used >= settings.AI_MONTHLY_GENERATION_CAP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly AI generation limit reached for this school.",
        )
```
On **both** generate routes, add the rate-limit dependency to the decorator and the quota check as the first line:
```python
@router.post(
    "/question-papers/generate",
    response_model=QuestionPaperOut,
    dependencies=[rate_limit("ai:generate", max_requests=settings.AI_GENERATE_RATE_PER_MIN)],  # add
)
async def generate_question_paper(... , db: AsyncSession = Depends(get_db)) -> QuestionPaperOut:
    await _enforce_ai_quota(uuid.UUID(current_user.school_id), db)   # add (first line)
    ...
```
Same two lines for `@router.post("/report-cards/generate", ...)` → `generate_report_card`.
(`rate_limit` already no-ops in testing / when `RATE_LIMIT_ENABLED=false`, so tests are unaffected.)

---

## 2. H3 — Outbox traceback slice  *(1 char; latent but trivial)*

**`app/workers/outbox_worker.py:100`**
```diff
-            event.last_error = traceback.format_exc()[-500]
+            event.last_error = traceback.format_exc()[-500:]
```

---

## 3. H1 — Payment idempotency  *(constraint + catch → return existing)*

**(a) New Alembic migration.** Create `alembic/versions/<rev>_unique_txn_per_school.py`. Set `down_revision` to your current head (`alembic heads`); clean any existing duplicate `transaction_id`s first or the index build fails.
```python
"""unique transaction_id per school on fee_receipts"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"          # any unique id
down_revision = "<current head>"   # run: alembic heads
branch_labels = None
depends_on = None

def upgrade():
    op.create_index(
        "uq_receipt_txn_per_school", "fee_receipts",
        ["school_id", "transaction_id"], unique=True,
        postgresql_where=sa.text("transaction_id IS NOT NULL"),
    )

def downgrade():
    op.drop_index("uq_receipt_txn_per_school", table_name="fee_receipts")
```

**(b) Model** — keep metadata in sync. `app/db/models/fee.py`, `FeeReceipt.__table_args__` (line ~143); add `text` to the sqlalchemy import:
```python
        Index(
            "uq_receipt_txn_per_school", "school_id", "transaction_id",
            unique=True, postgresql_where=text("transaction_id IS NOT NULL"),
        ),
```

**(c) Service** — `app/modules/fees/services/fee_service.py`. Add `from sqlalchemy.exc import IntegrityError`, then wrap the **first** receipt flush (line 137):
```python
        self.db.add(receipt)
        try:
            await self.db.flush()
        except IntegrityError:
            # Concurrent duplicate of the same transaction_id — the winner already
            # created the receipt AND updated the fee record; roll back ours and return theirs.
            await self.db.rollback()
            existing = (await self.db.execute(
                select(FeeReceipt).where(
                    FeeReceipt.school_id == school_id,
                    FeeReceipt.transaction_id == transaction_id,
                )
            )).scalar_one_or_none()
            if existing:
                return existing
            raise
```
Why this is complete: the counter `FOR UPDATE` already serializes the two payments, and the fee-record mutation happens *after* this flush — so when the loser's INSERT trips the unique index, the rollback discards both the duplicate receipt **and** the double credit, and you hand back the winner's receipt. The pre-check at the top still covers sequential retries.
**Still open (note, not blocking):** cash payments (`transaction_id is None`) remain non-idempotent — add a client idempotency key later if double-submit on cash matters.

---

## 4. M3 — Global IntegrityError → 409  *(also fixes M2's 500s for dup attendance/marks/users)*

**`app/main.py`**, inside `create_app()` (after the app is created, before routers). Note: place this so H1's local catch still wins for the payment path (it does — local `try/except` runs first).
```python
from sqlalchemy.exc import IntegrityError
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(IntegrityError)
async def _on_integrity_error(request: Request, exc: IntegrityError):
    logger.warning("integrity_error", path=request.url.path,
                   error=str(getattr(exc, "orig", exc)))
    return JSONResponse(status_code=409,
                        content={"detail": "Resource already exists or violates a constraint."})
```
`get_db` already rolls back on exception before this handler returns, so the session is clean. Generic message by design; refine per-constraint later if you want friendlier text.

---

## 5. H4 — Role ceiling on user creation  *(stop admin minting super_admin)*

**`app/modules/users/endpoints/users.py`** — add above the routes:
```python
from fastapi import HTTPException
_ROLE_RANK = {"student": 0, "parent": 0, "teacher": 1, "class_incharge": 1,
              "operations": 2, "admin": 3, "super_admin": 4}

def _assert_can_assign(caller_role: str, target_role: str) -> None:
    if _ROLE_RANK.get(target_role, 99) >= _ROLE_RANK.get(caller_role, -1):
        raise HTTPException(status_code=403,
                            detail="You cannot create a user with equal or higher privileges.")
```
In `create_user`, before `service.create_user(...)`:
```python
    _assert_can_assign(current_user.role, body.role.value)
```
**Policy choice (yours):** as written, "equal-or-higher" blocks an `admin` from creating another `admin`/`super_admin`, and blocks a `super_admin` from creating a second `super_admin` (do that via seed/DB). If you need peer-admin creation, change `>=` to `>`. There's no role-change endpoint today, so this is the only escalation path to close.

---

## 6. H2 — Trust the proxy's real-client IP, not left-most XFF

nginx sets `X-Real-IP $remote_addr` (the real TCP peer, unspoofable) and *appends* to `X-Forwarded-For` (so its left-most entry is client-controlled). Fix **both** copies.

**`app/modules/auth/endpoints/auth.py:39-44`** and **`app/core/rate_limit.py:29-33`** — replace the body:
```python
def _get_client_ip(request: Request) -> str:   # _client_ip in rate_limit.py
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()   # right-most = nearest trusted hop
    return request.client.host if request.client else "unknown"
```
**Caveat:** this is only sound if the app is reachable *only* through that nginx (otherwise a client can set `X-Real-IP` too). Bind the API to the internal network, and/or run uvicorn with `--forwarded-allow-ips=<nginx ip>` (or Starlette `ProxyHeadersMiddleware`) so the platform validates proxy headers centrally. Consider de-duplicating these two identical helpers into one.

---

## 7. Report card — count missing exams as 0  *(your choice — read the scope note)*

**`app/modules/ai/services/report_card_service.py`**, `_consolidate_marks` (lines 41-66). Drive from `Exam` (all in-scope exams for the class) LEFT JOIN the student's marks, so un-marked exams contribute 0 obtained against their full `total_marks`:
```python
from datetime import date  # add

async def _consolidate_marks(
    db: AsyncSession, *, school_id: uuid.UUID, student_id: uuid.UUID,
    class_id: uuid.UUID, since: date | None = None, until: date | None = None,
) -> list[dict]:
    conds = [Exam.school_id == school_id, Exam.class_id == class_id,
             Exam.date <= date.today()]          # don't count future exams
    if since: conds.append(Exam.date >= since)
    if until: conds.append(Exam.date <= until)
    rows = (await db.execute(
        select(Subject.name,
               func.coalesce(func.sum(ExamMark.marks_obtained), 0),
               func.sum(Exam.total_marks))
        .select_from(Exam)
        .join(Subject, Exam.subject_id == Subject.id)
        .outerjoin(ExamMark, (ExamMark.exam_id == Exam.id) & (ExamMark.student_id == student_id))
        .where(*conds)
        .group_by(Subject.name)
        .order_by(Subject.name)
    )).all()
    return [{"subject": n, "marks_obtained": float(o or 0), "total_marks": float(t or 0)}
            for n, o, t in rows]
```
Update the call in `generate_report_for_student`:
```python
    subjects = await _consolidate_marks(
        db, school_id=school_id, student_id=student_id, class_id=student.class_id,
    )
```
**Scope note (important):** `Exam.date <= today` stops future exams counting as 0, but there's still no term concept — all past exams for the class count. To make a *term* report honest, pass `since`/`until` for the reporting period (or let the teacher pick exam IDs). Until you do, a unit test that haven't-been-graded ≠ absent is impossible to satisfy. Recommend wiring the period before relying on the %.
```
Each `outerjoin` row is unique per exam (ExamMark filtered to one student → ≤1 match per exam), so `sum(Exam.total_marks)` counts each exam exactly once.
```

---

### Suggested commit grouping
1. `feat(ai): cap + rate-limit generation` (M1)
2. `fix(fees): idempotent payments` (H1 migration+model+service) — needs `alembic upgrade head`
3. `fix(api): 409 on integrity errors; outbox slice` (M3 + H3)
4. `fix(auth): real client IP; role ceiling` (H2 + H4)
5. `feat(reports): count missing exams as zero within period` (report card)

Run after: `alembic upgrade head`, then `pytest`. Heads-up — current tests won't exercise M1/H2/H4 (rate-limit, tenant, CSRF, middleware are disabled under `ENVIRONMENT=testing`, per pass-2 N7), so add targeted tests or verify these manually.
