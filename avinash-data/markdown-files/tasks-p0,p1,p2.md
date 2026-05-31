## P0: Startup Crash
- [x] `academic-service/app/worker/outbox_relay.py` — fix `async_session_maker` → `AsyncSessionLocal`

## P1: Webhook Replay & Atomic Idempotency
- [x] `academic-service/app/worker/outbox_relay.py` — add `x-webhook-timestamp` header + sign `timestamp.payload`
- [x] `fee-service/app/models/authorization.py` — add `WebhookProcessedEvent` model with `UniqueConstraint(event_id)`
- [x] Alembic migration for `WebhookProcessedEvent`
- [x] `fee-service/app/api/v1/endpoints/webhooks.py` — timestamp validation, atomic idempotency, `PARENT_STUDENT_UNLINKED` handler, remove HMAC log leak

## P1: Parent Unlink End-to-End
- [x] `academic-service/app/services/academic_service.py` — add `unlink_parent_from_student` (delete map + emit `PARENT_STUDENT_UNLINKED` outbox event with `parent_user_id`)
- [x] `academic-service/app/api/v1/endpoints/students.py` — add `DELETE /students/{student_id}/parents/{parent_user_id}` + parent ownership on GET
- [ ] `scripts/reconcile_authorizations.py` — add revoke path for orphaned fee auth records (shared-DB cross-schema query)

## P1: Login Rate Limit IP Spoofing
- [x] `nginx.conf` — overwrite `X-Forwarded-For` with `$remote_addr` in all `location` blocks
- [x] `docker-compose.dev.yml` — add `--proxy-headers --forwarded-allow-ips` to auth-service uvicorn command
- [x] `auth-service/app/api/v1/endpoints/auth.py` — remove manual `X-Forwarded-For` parsing

## P1: IDOR and RBAC
- [x] `fee-service/app/api/v1/endpoints/fees.py` — restrict `my_dues`/`my_payments` to `student`/`parent` only; fix missing `HTTPException` import
- [x] `academic-service/app/api/v1/endpoints/students.py` — parent ownership check in `get_student_parents`
- [x] `academic-service/app/api/v1/endpoints/phase5.py` — RBAC on all routes + student/parent/teacher ownership checks
- [x] `attendance-service/app/api/v1/endpoints/attendance.py` — RBAC on `school-summary` and `trend`
- [x] `communication-service/app/api/v1/endpoints/communication.py` — RBAC on `POST /notices`

## P1: Scaffold Guardrails
- [x] `communication-service` — `config.py` (already existed), `main.py` wired to settings, `requirements.txt` added
- [x] `school-ops-service` — `config.py`, `main.py`, `requirements.txt` added
- [x] `ai-service` — `config.py`, `main.py`, `requirements.txt` added
- [x] `analytics-service` — `config.py`, `main.py`, `requirements.txt` added
- [x] `file-service` — `config.py`, `main.py`, `requirements.txt` added

## P2: Leakage & Filters
- [x] `auth-service/app/main.py` — generic Redis failure message in both log and RuntimeError
- [x] `fee-service/app/services/fee_service.py` — apply `class_id` filter in `get_fee_records()`

## Verification
- [x] Updated `test_webhooks.py` — timestamp enforcement, atomic idempotency, PARENT_STUDENT_UNLINKED (7/7 ✅)
- [x] `test_fees_rbac.py` — my-dues/my-payments RBAC (9/9 ✅)
- [x] `test_rbac.py` — parent enumeration, unlink ownership, unauth (8/8 ✅)
- [x] `test_attendance_rbac.py` — school-summary and trend admin-only written
- [ ] 5 pre-existing `test_students.py` enrollment schema failures remain (not introduced here — enrollment API schema changed to require apaar_number etc)
