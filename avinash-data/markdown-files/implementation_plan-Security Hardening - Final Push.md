# Security Hardening - Final Push

This plan addresses all P0, P1, and P2 security and stability vulnerabilities identified in the latest review to ensure the system is truly production-ready. 

## User Review Required
> [!WARNING]
> Please review the expanded RBAC definitions. The X-Forwarded-For item now involves concrete infra work (Nginx config + uvicorn flags), not just a code assumption.

## Proposed Changes

### P0: Startup Crash in Academic Service
#### [MODIFY] `academic-service/app/worker/outbox_relay.py`
- Change `from app.core.database import async_session_maker` to `from app.core.database import AsyncSessionLocal`
- Update the context manager call to use `AsyncSessionLocal()`.

---

### P1: Webhook Replay Protection & Idempotency
#### [MODIFY] `academic-service/app/worker/outbox_relay.py`
- Include an `x-webhook-timestamp` header (Unix timestamp).
- Update the HMAC signature to cover `f"{timestamp}.{payload_bytes}"`.

#### [MODIFY] `fee-service/app/models/authorization.py` (and Alembic)
- Create a `WebhookProcessedEvent` model to durably store every `event_id` and timestamp. The `event_id` must have a `UniqueConstraint`.

#### [MODIFY] `fee-service/app/api/v1/endpoints/webhooks.py`
- Require `x-webhook-timestamp`.
- Enforce a 5-minute replay window: `abs(time.time() - timestamp) < 300`.
- Verify HMAC using `f"{timestamp}.{body_bytes}"`.
- Enforce atomic database-level idempotency by using `INSERT ... ON CONFLICT DO NOTHING` into `WebhookProcessedEvent` in the same transaction as the state mutation. If 0 rows are affected, the event was already processed.
- Remove `expected_mac` from the error logs to prevent leaking signing material.
- Add handler for `PARENT_STUDENT_UNLINKED` to set `is_active=False` in `FeeParentStudentAuth`.

---

### P1: Parent Unlink & Reconciliation Revokes
#### [MODIFY] `academic-service/app/services/academic_service.py` & `students.py`
- Add a new `DELETE /students/{student_id}/parents/{parent_user_id}` endpoint (using `parent_user_id` for contract consistency).
- Implement `unlink_parent_from_student` to delete the `StudentParentMap` and emit a `PARENT_STUDENT_UNLINKED` outbox event.
- **Payload consistency**: The outbox event payload must use `parent_user_id` (not `parent_id`) to match the link API contract and prevent confusion between `Parent.id` and `User.id` downstream.

#### [MODIFY] `scripts/reconcile_authorizations.py`
- Enhance the script to not only push active mappings, but also cross-reference active `FeeParentStudentAuth` records in `fee-service`.
- **Implementation Note**: This script (running inside `academic-service`) will read the `fee-service` authorization tables directly via raw SQL on the shared database. This introduces a known cross-schema coupling solely for the purpose of operational reconciliation.
- If an active parent authorization exists in `fee-service` but not in `academic-service` (an orphaned relationship), the script will emit a `PARENT_STUDENT_UNLINKED` event to safely revoke access.

---

### P1: Login Rate Limit IP Spoofing
#### [MODIFY] `nginx.conf` — Overwrite `X-Forwarded-For`
- Add `proxy_set_header X-Forwarded-For $remote_addr;` inside the relevant `location` block (e.g. `location /` or the per-service proxy block) — **not** inside an `upstream` block, where the directive is invalid and would silently have no effect.

#### [MODIFY] `docker-compose.yml` (or service entrypoint)
- Add `--proxy-headers --forwarded-allow-ips="<gateway-network-CIDR>"` to the `auth-service` uvicorn startup command, ensuring that `request.client.host` is resolved from the trusted gateway IP only.

#### [MODIFY] `auth-service/app/api/v1/endpoints/auth.py`
- Remove the manual `X-Forwarded-For` parsing block entirely. Use `request.client.host` directly — uvicorn will have already resolved it from the trusted forwarded header.

---

### P1: IDOR and RBAC Fixes

#### [MODIFY] `fee-service/app/api/v1/endpoints/fees.py`
- Restrict `my_dues` and `my_payments` to `require_roles("student", "parent")` strictly. Remove the staff/admin fallback branch (staff will use explicit administrative routes).
- Properly import `HTTPException` to fix 500 errors.

#### [MODIFY] `academic-service/app/api/v1/endpoints/students.py`
- In `get_student_parents`, if `current_user.role == "parent"`, securely verify that the queried `student_id` is linked to `current_user.id` to prevent enumeration.

#### [MODIFY] `academic-service/app/api/v1/endpoints/phase5.py`
- Add `require_roles("admin", "super_admin")` (School-wide views) to:
  - `/teacher-attendance/summary`
  - `/teacher-attendance/trend`
  - `/exam-marks/school-overview`
- Add `require_roles("admin", "super_admin", "teacher", "class_incharge")` (Class-scoped views) to:
  - `/lesson-logs/summary`
  - `/exam-marks/class-summary`
- Add `require_roles("admin", "super_admin", "teacher", "class_incharge", "student", "parent")` to:
  - `/timetable`
  - `/exam-marks/student`
- Enforce strict ownership/authorization checks inside each handler:
  - **student**: can only access their own marks/timetable (their enrolled `class_id`).
  - **parent**: can only access marks/timetable for their linked children.
  - **teacher / class_incharge**: must be verified as the assigned teacher of the requested `class_id` or `student_id`'s class — not just any class-scoped route by role alone.

#### [MODIFY] `attendance-service/app/api/v1/endpoints/attendance.py`
- Add `require_roles("admin", "super_admin")` to the school-wide `/attendance/school-summary` and `/attendance/trend` endpoints.

#### [MODIFY] `communication-service/app/api/v1/endpoints/communication.py`
- Add `require_roles("admin", "super_admin", "teacher")` to the `POST /notices` endpoint.

---

### P1: Production Guardrails Bypass
#### [MODIFY] Scaffold service configuration & wiring
- Since some scaffold services completely lack configuration logic, we will **add `app/core/config.py`** modules with production validators to them.
- Update each service's `requirements.txt` (or `pyproject.toml`) to include the shared dependencies needed by the new config module (e.g. `pydantic-settings`, `structlog`) so they don't fail at boot.
- Apply the production guardrails (disabling docs, strict CORS, config validators) to all five services:
  - `communication-service` — `main.py`, `config.py`, `requirements.txt`
  - `school-ops-service` — `main.py`, `config.py`, `requirements.txt`
  - `ai-service` — `main.py`, `config.py`, `requirements.txt`
  - `analytics-service` — `main.py`, `config.py`, `requirements.txt`
  - `file-service` — `main.py`, `config.py`, `requirements.txt`

---

### P2: Leakage & Filters

#### [MODIFY] `auth-service/app/main.py`
- Catch `Exception as e` around Redis initialization and:
  - Log only a generic message `"Redis connection failed"` — no URLs, no `str(e)`.
  - Raise a generic `RuntimeError("Failed to connect to message store.")` — do not include `str(e)` or `settings.REDIS_URL` in the raised error body.

#### [MODIFY] `fee-service/app/services/fee_service.py`
- In `get_fee_records()`, update the SQLAlchemy query to actually apply the `class_id` filter when provided.

## Verification Plan

### Automated Tests
- **Webhooks**: Update `test_webhooks.py` to verify timestamp enforcement, atomic durable idempotency (via the new table), and HMAC signatures.
- **Unlink Propagation** (end-to-end critical path):
  - Call `DELETE /students/{student_id}/parents/{parent_user_id}` and confirm the `StudentParentMap` is removed.
  - Verify the `PARENT_STUDENT_UNLINKED` outbox event is written in the same transaction.
  - Trigger the relay worker and confirm the `fee-service` webhook handler sets `FeeParentStudentAuth.is_active = False`.
  - Confirm the parent can no longer access that student's fee records (should receive 403).
- **RBAC & Ownership Tests**: Add automated test suites for:
  - `get_student_parents` parent scoping / enumeration prevention.
  - `/exam-marks/student` student/parent ownership validation.
  - `/timetable` student/parent ownership validation.
  - `/attendance/school-summary` and `/attendance/trend` strict RBAC (admin/super_admin only).
  - `POST /notices` strict RBAC.
  - `/fees/my-*` rejecting admin/staff tokens with 403.

### Manual Verification
- Start `academic-service` to confirm the P0 crash is fixed.
- Check `auth-service` startup with a broken Redis URL to verify logs do not leak secrets.
