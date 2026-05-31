# End-to-End Code Review & Analysis (Refined)

This document summarizes the architectural, security, and performance review of the Academix School Management System (modular monolith). It incorporates corrections from a static trace against the current codebase.

## 1. Architectural Overview

The project has consolidated previous microservices into a modular monolith.

- **Backend:** FastAPI with **13** primary functional routers mounted under `/api/v1`: Auth, Users, Academic, Timetable, Examinations, Attendance, Fees, Files, AI, Communications, Notifications, School Ops, and Analytics (`app/main.py` — one `include_router` per domain).
- **Frontend:** Next.js (App Router) using a central API client with a hybrid authentication strategy.
- **Shared logic:** Centralized in `app.core` and `app.db` on the backend, and `src/lib/api.ts` (staff-web) for HTTP clients.

### Key strengths

- **Outbox pattern:** `OutboxEvent` (and related processing) supports cross-module consistency (e.g. Academic → Fees) without distributed transactions.
- **Secure auth lifecycle:** Short-lived Bearer access tokens plus HttpOnly, rotated refresh tokens. The refresh cookie is **path-scoped** to `/api/v1/auth/refresh`, which limits where the browser sends it.
- **Concurrency controls:** `with_for_update()` on fee payment (`StudentFeeRecord`) and on the **School** row for receipt-number allocation reduces race conditions on concurrent payments.
- **Per-OTP vertical limits:** `verify_otp` enforces attempt counting and invalidates the OTP after `OTP_MAX_ATTEMPTS` (default 3).

## 2. Security analysis

| Severity | Area | Description |
|----------|------|-------------|
| Low | CSRF | Refresh uses `SameSite=Lax` and a narrow cookie path. Defense-in-depth (e.g. custom header on mutations, or stricter SameSite where acceptable) can further harden edge cases. |
| Low | Rate limiting (horizontal) | `/auth/verify-otp` has **vertical** protection (per-OTP guesses, invalidation after max attempts) but not obvious **IP/user** throttling for bursty traffic across many mobiles. |
| Low | Tenant probing | With tenant context present, unknown `X-Tenant-Slug` (or host-derived slug) can yield **404**, which can act as a coarse existence oracle for slugs. |
| Low | Audit logs | Failed “Forgot password” validation (invalid student/parent pairing) returns a generic **400** without a dedicated security audit entry; successful OTP send is logged (`Forgot password OTP sent`). |

## 3. Latency & performance

| Area | Issue | Impact / nuance |
|------|--------|-------------------|
| Database | Auth path | `get_current_user` performs a **full `User` row load** on every authenticated request — **one extra DB round-trip** for freshness (`is_active`, `school_id`, tenant alignment). Caching trades latency for staleness; wording “unnecessary” is misleading. |
| Database | Bulk exam marks | `exam_marks_bulk_upsert` calls `await db.flush()` **inside** the per-student loop, causing sequential round-trips. A single flush (or batched insert strategy) would reduce chatter if response shape allows. |
| API | Pagination | **GET /students** and **GET /teachers** return full lists (with optional class filter on students). **GET /users** is paginated. Other academic lists (e.g. **GET /classes**, **GET /subjects**) are also unpaginated — same scaling concern as roster lists. |
| Product / UX | OTP timing | **OTP_COOLDOWN_SECONDS** and **OTP_EXPIRE_MINUTES** both default to **5 minutes**. **Cooldown** mainly affects **resending** OTP after `send_otp`. **Wrong entry** is governed by **OTP_MAX_ATTEMPTS** on verify, not by the 5-minute cooldown — distinguish these in runbooks. |

## 4. End-to-end testing readiness

- **Playwright:** Staff-web includes E2E specs (golden paths where implemented, plus roster smoke such as no `/api/v1/users` on key pages). CI can run targeted smoke with seeded users (see `.github/workflows/staff-web-e2e-smoke.yml` and `apps/api/scripts/ci_e2e_seed.py`).
- **Local DB URL:** `scripts/update_admin.py` defaults to **localhost:5432**. If Postgres listens on **5433**, set **DATABASE_URL** (or equivalent) so the script and API `POSTGRES_URL` stay aligned.
- **Synthetic admin password login:** `scripts/update_admin.py` sets the **oldest** admin/super_admin row to **admin.synthetic** with password **Admin@123** by default (**SYNTHETIC_ADMIN_PASSWORD** overrides). Mirror these in **apps/staff-web/.env.local** as **E2E_ADMIN_USERNAME** / **E2E_ADMIN_PASSWORD** for Playwright. That script does **not** create a teacher account; teacher flows need **E2E_TEACHER_USERNAME** / **E2E_TEACHER_PASSWORD** (CI seed script, fixtures, or manual user).

## 5. Recommendations (hardening)

1. **Auth read path:** Optional Redis (or JWT claims) cache for **User** with short TTL and invalidation on role/status change — document staleness rules.
2. **Bulk writes:** Refactor **exam_marks_bulk_upsert** (and similar loops) toward **one flush** or set-based operations where IDs and constraints allow.
3. **Pagination:** Extend **/users**-style pagination to **/students**, **/teachers**, **/classes**, **/subjects**, and other large lists as schools grow.
4. **Horizontal limits:** Redis-backed **IP / fingerprint** throttles on **/verify-otp** and other abuse-prone **unauthenticated** endpoints, complementing existing per-OTP vertical limits.
5. **Audit:** Structured security audit events for repeated **forgot-password** failures and optional rate limits on that flow.

---

*Last updated from review feedback: router count (13), auth DB wording, OTP cooldown vs verify attempts, pagination scope, E2E credential and port notes.*
