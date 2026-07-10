# Academix / StudyNexs Platform — End-to-End Code Review

**Reviewer:** Automated code review
**Date:** 2026-06-01
**Scope:** `apps/api` (FastAPI backend, ~8k LoC), `apps/admin-web` (Next.js frontend), `infra/` (nginx, docker-compose, Azure WAF). Focus: security, correctness bugs, missing logic, concurrency, and latency.

---

## Summary

The architecture is sound and notably mature for the stage: clean module boundaries, multi-tenant scoping helpers (`TenantScope`), object-level authz, JWT + refresh rotation with reuse detection, an outbox pattern, an Arq job queue, audit logging, production config guardrails, and tests. Most queries are correctly scoped by `school_id`, which is the hardest thing to get right in multi-tenant SaaS and is done consistently.

The issues below are concentrated in a few areas: **a live secret in `.env`**, **payment idempotency**, **rate-limit spoofing**, **a worker bug**, and several **N+1 / synchronous-call latency** patterns.

| Severity | Count | Headline items |
|---|---|---|
| 🔴 Critical | 1 | Live OpenAI API key present in `apps/api/.env` |
| 🟠 High | 4 | Payment idempotency race; spoofable IP rate-limit; outbox worker crash bug; privilege escalation in user creation |
| 🟡 Medium | 10 | Unprotected/synchronous AI endpoints; N+1 + race on attendance/marks; no IntegrityError→409; per-request tenant DB lookup; receipt-counter seeding; Redis fail-mode inconsistency; weak password policy; multi-device refresh; audit write latency; login spray key |
| 🟢 Low | ~8 | CORS/tenant origin model; non-constant-time OTP; numeric precision; provider client per request; etc. |

---

## 🔴 Critical

### C1. Live OpenAI API key committed to the working tree
**`apps/api/.env`** (last line) contains a real, usable key:
```
OPENAI_API_KEY=sk-proj-…redacted…
```
`.env` is correctly in `.gitignore` and is **not** tracked by git, so it is not in history — good. But the key is sitting in plaintext on disk, is mounted into the API container (`docker-compose.dev.yml` → `volumes: ../../apps/api:/app`), and has now been exposed in this review context.

**Action:** Rotate this key immediately in the OpenAI dashboard — assume it is compromised. Going forward, load provider keys from a secret manager (Azure Key Vault / environment injected at deploy), never a file in the repo tree. Add a pre-commit secret scanner (e.g. `gitleaks`) and verify the key never reached any branch/stash (`git log -p -S 'sk-proj'`).

---

## 🟠 High

### H1. Fee payment idempotency is racy and has no backing constraint → duplicate receipts / over-credit
**`app/modules/fees/services/fee_service.py:48-57`**, model **`app/db/models/fee.py:143-147`**

Idempotency relies solely on a non-atomic "SELECT a receipt with this `transaction_id`, return it if found" check. `FeeReceipt` has unique constraints on `receipt_number` and `receipt_sequence` but **none on `transaction_id`** (nor on `razorpay_payment_id`).

- *Sequential* duplicate webhooks (retry seconds later) are handled — the second SELECT sees the first receipt.
- *Concurrent* duplicates (gateway callback + webhook arriving together) both pass the SELECT before either commits. The `with_for_update()` row lock on the fee record + re-read mitigates **full** payments (the second sees `remaining == 0` and is rejected by the balance check), but **partial** payments are not protected: total ₹1000, txn X pays ₹400 twice concurrently → `paid_amount` becomes ₹800 and **two** receipts exist for one real ₹400 payment.
- Cash payments (`transaction_id is None`) have **no idempotency at all** — a double-click creates two receipts.

**Fix:** Add `UniqueConstraint("school_id", "transaction_id")` (partial index where `transaction_id IS NOT NULL`) and let the DB enforce it; catch the `IntegrityError` and return the existing receipt. Optionally also unique `razorpay_payment_id`.

### H2. App-level IP rate limiting is bypassable via spoofed `X-Forwarded-For`
**`app/modules/auth/endpoints/auth.py:39-44`** (and the duplicate in `app/core/rate_limit.py:29-33`)

`_get_client_ip` takes the **left-most** value of `X-Forwarded-For`. nginx sets `X-Forwarded-For $proxy_add_x_forwarded_for` (**`infra/nginx/nginx.conf:26`**), which *appends* the real IP to whatever the client sent. So a request with `X-Forwarded-For: 1.2.3.4` reaches the app as `1.2.3.4, <real-ip>` and the app keys the limiter on the attacker-controlled `1.2.3.4`. Rotating that header per request gives a fresh bucket every time → login/OTP brute-force and OTP-flood limits are defeated at the application layer.

Mitigation that exists: nginx's own `limit_req` uses `$binary_remote_addr` (the real TCP peer, not spoofable) at 30 r/m for `/auth/`. So you are not wide open *today behind this nginx*, but the app-level control is effectively decorative, and any other ingress (direct pod access, a different gateway, future LB) loses the protection.

**Fix:** Trust only `X-Real-IP` (nginx sets it to `$remote_addr`) or take the **right-most** XFF entry, and make the count of trusted proxy hops explicit. Don't parse the left-most XFF value.

### H3. Outbox worker crashes its own error handler (`[-500]` instead of `[-500:]`)
**`app/workers/outbox_worker.py:100`**
```python
event.last_error = traceback.format_exc()[-500]   # indexes ONE char; IndexError if traceback < 500 chars
```
This should be a slice `[-500:]`. As written, on any handler exception it either stores a single character or (when the traceback is shorter than 500 chars, which is common) raises `IndexError` **inside the `except` block**. That secondary exception propagates out of `process_pending_events`, skipping `session.commit()` (line 111), so the batch's status updates roll back and the loop logs `outbox_worker_error`. Net effect: the retry/dead-letter bookkeeping never persists and a poison event can stall the batch repeatedly.

**Fix:** `traceback.format_exc()[-500:]`. Consider also wrapping per-event handling so one bad event can't abort the batch, and add backoff between retries.

### H4. Privilege escalation: an `admin` can mint `super_admin` / `admin` accounts
**`app/modules/users/schemas/user.py:28-34`** + **`app/modules/users/endpoints/users.py:88-97`**

`UserCreate.role: UserRole` accepts any role, and `POST /users` is gated by `require_roles("admin", "super_admin")`. A regular `admin` can therefore create a `super_admin` (or another `admin`/`operations`) user and escalate privileges within the tenant. There is no role ceiling enforced relative to the caller.

**Fix:** Restrict assignable roles by caller (e.g. only `super_admin` may create `admin`/`super_admin`); reject attempts to create a role ≥ the caller's. (Good news: `UserUpdate` does **not** expose `role`/`is_active`/`school_id`, so the `setattr` mass-assignment in `update_user` is safe — keep it that way.)

---

## 🟡 Medium

### M1. AI generation endpoints: no rate limit, no budget cap, and synchronous LLM calls
**`app/modules/ai/endpoints/ai.py:145, 295`**, **`app/modules/ai/services/question_paper_service.py:158`**

The two most expensive endpoints (`/ai/question-papers/generate`, `/ai/report-cards/generate`) have **no `rate_limit(...)` dependency** and **no per-school usage quota**, even though `fees:pay` and `users:list` do. `record_usage` tracks spend but nothing blocks a school (or a script) from spamming generations → unbounded LLM cost and a DoS on your provider budget.

They also `await provider.generate(...)` **inside the request**, holding the DB connection for up to `AI_REQUEST_TIMEOUT_SECONDS` (60s) per call. Under modest concurrency this exhausts the connection pool (`pool_size=20`). You already have an Arq job queue (`app/core/jobs/`) that is unused here.

**Fix:** Add `rate_limit("ai:generate", max_requests=…)`, enforce a monthly per-school cap from `AIUsage`, and move generation to a background job (return a job id; poll/stream the result). Don't hold the DB session across the network call.

### M2. N+1 + check-then-insert race on attendance and exam marks (hot paths)
**`app/modules/attendance/services/attendance_service.py:28-54`** and **`app/modules/examinations/services/exam_service.py:51-70`**

Both loop over entries and run **one SELECT per student** to decide insert-vs-update (40 students → ~80 round-trips per class), then write. Beyond latency, the check-then-insert is **not atomic**: two concurrent bulk-marks for the same class/date both miss and both insert, hitting `uq_attendance_student_date` / `uq_exam_student` → `IntegrityError` → 500 (see M3).

**Fix:** Batch-fetch existing rows in one query keyed by `student_id`, or use PostgreSQL upsert: `insert(...).on_conflict_do_update(index_elements=[...], set_={...})`. One statement, race-safe, no N+1.

### M3. No `IntegrityError` → 409 handling anywhere
Grep shows **zero** `IntegrityError` handlers in `app/`. Every unique-constraint violation becomes a 500: duplicate user mobile/username (`create_user`, `uq_users_school_mobile`), concurrent attendance/marks (M2), etc.

**Fix:** Add a global exception handler mapping `sqlalchemy.exc.IntegrityError` to `409 Conflict` with a clean message, and/or catch locally where conflicts are expected.

### M4. Tenant is re-resolved from the DB on every authenticated request
**`app/core/dependencies.py:148, 194`** → **`app/core/tenant.py:87-102`**

`validate_tenant_school_match` calls `resolve_tenant(slug)` — a DB query — on **every** request, even though the JWT already carries both `school_id` and `tenant_slug`. That's an extra round-trip per request on top of the user-cache lookup.

**Fix:** Compare the request slug against the JWT's `tenant_slug` claim directly, or cache `slug → school_id` in Redis with a TTL. Reserve the DB hit for cache misses.

### M5. `ReceiptCounter` is only created by seed scripts → first payment crashes for un-seeded schools
**`app/modules/fees/services/fee_service.py:104-109`** (`scalar_one()`), seeding only in `scripts/seed_demo_ssc.py` / `seed_synthetic.py`

`process_payment` does `select(ReceiptCounter)…with_for_update()` then `scalar_one()`. There is no onboarding code path that creates a counter row, so a school created outside the seed scripts has none → `NoResultFound` → 500 on its first payment. The function also issues 5 sequential SELECTs (student, user, school, fee_structure, class) while holding the counter/fee-record locks, lengthening the locked critical section.

**Fix:** Create the `ReceiptCounter` on school creation, or upsert-on-demand (`scalar_one_or_none()` → create with a unique-constraint-safe insert). Load the snapshot data with a single joined query before taking the lock.

### M6. Redis failure mode is inconsistent; rate-limit counter is non-atomic
**`app/core/dependencies.py:130, 235-257`**

`get_current_user` deliberately tolerates Redis being down for the *user cache* ("never blocks on Redis failure") but the **blacklist check** (`_is_token_blacklisted`, line 130) and OTP/refresh logic are **not** wrapped — if Redis is down, auth throws 500. Decide fail-open vs fail-closed deliberately and apply it consistently.

`check_rate_limit` does `INCR` then a separate `EXPIRE` only when `current == 1`. It's labelled a "sliding window" but is a fixed window, and the two ops aren't atomic: if the process dies between them, the key never expires and the user is **locked out permanently**. Use a pipeline/Lua, or `SET key 1 EX <w> NX` + `INCR`.

### M7. Weak password policy, no account lockout
**`app/modules/users/schemas/user.py:34`** — `password: min_length=6`, no complexity rule. Combined with H2 (spoofable IP limiter) and M10 (per-username limiter key), online password guessing is realistic for staff/admin accounts.

**Fix:** Require ≥10–12 chars, check against a breached-password list, and add per-account lockout/backoff independent of IP.

### M8. Single-session refresh model logs users out across devices/tabs
**`app/modules/auth/services/auth_service.py:162-192`**

Only one refresh JTI is stored per user (`REDIS_REFRESH_JTI_PREFIX{user_id}`). Logging in on device B overwrites device A's JTI; when device A next refreshes, its JTI ≠ stored → "reuse detected" → A is blacklisted and logged out. Concurrent refreshes also fail with "Refresh already in progress" (the `nx` lock), and the client then `clear_refresh_cookie` → spurious logout. The frontend's single-flight (`api.ts:94-103`) only de-dupes within one tab.

**Fix:** Store a *set* of valid refresh JTIs per user (per device/session), or key the stored JTI by a session id embedded in the refresh token. Treat a *missing* prior JTI as "first login", not reuse.

### M9. Audit log writes synchronously on every mutation and swallows failures
**`app/core/audit_middleware.py:67-81`**

Each mutating request opens a **second** DB session and commits an audit row before returning → an extra connection + round-trip on every POST/PUT/PATCH/DELETE. Failures are logged at `warning` and dropped (silent loss of the audit trail). `resource_type` is derived by `path.split("/")[-2]`, a fragile heuristic. Login (a mutating POST) has no `current_user`, so it's skipped by the `if user_id and school_id` guard → logins aren't persisted.

**Fix:** Emit audit events through the existing outbox (async, durable), or batch them. Don't silently drop; at least dead-letter. If audit has compliance weight, make persistence failures loud.

### M10. Login limiter key includes the username → password spraying isn't capped per IP
**`app/modules/auth/endpoints/auth.py:154-159`** — key is `login:{ip}:{username}`. An attacker trying many usernames from one IP gets a fresh 5-attempt bucket per username. Add a second limiter on `login:{ip}` (and see H2 about the IP itself).

---

## 🟢 Low / polish

- **CORS + tenant origin model** — `main.py:61-67` uses a static `ALLOWED_ORIGINS` with `allow_credentials=True`, and the frontend pins `X-Tenant-Slug` from a build-time env (`apps/admin-web/src/lib/api.ts:3-4`, default `"test"`). For subdomain-per-tenant in prod, every tenant origin must be enumerated and you effectively get one tenant per frontend build. Confirm this matches the intended deployment (one build per tenant?) or derive the slug from `window.location` and support wildcard-subdomain CORS.
- **Production config validator gaps** — `config.py:173` `unsafe_origins` misses `localhost:3002/3003` and doesn't reject non-HTTPS (`http://`) origins in prod.
- **OTP compare not constant-time** — `auth_service.py:97` uses `!=`; use `secrets.compare_digest`. `send_otp` will also SMS arbitrary numbers (cost) — fine while rate-limited, but consider verifying the mobile exists first.
- **Numeric precision mismatch** — `PayFeeRequest.amount` allows `max_digits=12` but the column is `Numeric(10,2)` (`fee.py:80`); a 11–12 digit amount passes validation then overflows the column → 500. Money is also returned as `float` in responses (`fee_service.py:181-183`) — fine for display, lossy for math.
- **Provider client created per request** — `factory.get_provider()` builds a new `AsyncAnthropic`/OpenAI client each call → no connection reuse. Provider exceptions aren't caught (only `ValueError` is) so a timeout/429 from the LLM surfaces as 500. And because the endpoint converts the post-`record_usage` parse failure into an `HTTPException`, `get_db` rolls back — so **billed-but-failed** generations aren't recorded. Cache the client; catch provider errors → 502/503; record usage in a way that survives the error path.
- **`get_db` commits on every request** including GETs (`database.py:39`). Harmless but unnecessary.
- **No user reactivation path** — `deactivate_user` sets `is_active=False` but `UserUpdate` can't set it back to `True`.
- **Report-card percentage ignores un-taken exams** — `report_card_service.py:_consolidate_marks` only sums exams that have a mark row, so a missed exam isn't counted as 0; this can overstate a struggling student's percentage. Confirm that's intended.
- **Dev compose exposes unauthenticated services** — `docker-compose.dev.yml` publishes Postgres/Redis/Qdrant to the host with weak/no auth (Redis none, Qdrant no API key). Fine on localhost; dangerous if ever run on a shared host.

---

## What's done well (keep it)
- Consistent `school_id` scoping on virtually every query; `TenantScope` centralizes cross-entity ownership checks.
- Fee receipt counter uses `SELECT … FOR UPDATE` correctly; receipts store immutable snapshots.
- Refresh-token rotation with reuse detection and an HttpOnly, path-scoped cookie; access token kept in memory on the client (not `localStorage`).
- Outbox uses `FOR UPDATE SKIP LOCKED` for safe multi-worker draining.
- Production config guardrails crash on unsafe boot; `bcrypt` cost 12; fail-secure password verify.
- `MetricsMiddleware` normalizes UUIDs so metric cardinality stays bounded.

## Suggested priority order
1. **Rotate the OpenAI key** (C1) — today.
2. Add the `transaction_id` unique constraint + conflict handling (H1) and fix the outbox slice (H3) — small, high-impact.
3. Fix IP extraction (H2) and the role ceiling (H4).
4. Rate-limit + offload the AI endpoints (M1); convert attendance/marks to upserts (M2); add the global `IntegrityError` handler (M3).
5. Work through the remaining Medium items.
