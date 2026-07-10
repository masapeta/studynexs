# Academix / StudyNexs — Second-Pass Code Review (brutally honest)

**Date:** 2026-06-01 · **Scope:** everything I didn't read closely the first time — `academic`, `files`, `notices`, `notifications`, the three PDF renderers, the Dockerfile/`.dockerignore`, dependency manifest, migrations, and the test suite. This document only covers **new findings and corrections**; the items in `CODE_REVIEW.md` (pass 1) still stand.

---

## Verdict first

This is a **well-architected skeleton that is not production-ready** — and that gap is wider than pass 1 implied. The module layout, tenant-scope helpers, and auth scaffolding are genuinely good. But several load-bearing pieces are **unimplemented**, **insecure**, or **untested**, and at least one is a real data-exposure hole I missed the first time:

- 🔴 Any logged-in student or parent can read **every student's full profile** in the school — parent phone numbers, home transport stop, hostel room. (New — N1.)
- 🔴 The live `.env` (OpenAI key) and `.git` get **baked into the Docker image** (`COPY . .`, no `.dockerignore`), which also runs as **root** and ships dev/test tooling. (Extends pass-1 C1.)
- 🟠 **File storage is local-disk only** — the Azure Blob path is a comment, not code. Uploads disappear on redeploy and 404 across replicas.
- 🟠 **PDFs never generate** — WeasyPrint isn't a dependency, so every `/pdf` endpoint silently returns HTML.
- 🟠 The **receipt** renderer does **no HTML escaping** (the other two do) → template/stored-XSS.
- 🟡 The **entire delivery layer is stubbed** (SMS/email/push = `pass # TODO`; outbox handlers log and no-op). The product records intent to notify and sends nothing.
- 🟡 The **tests disable the security middleware**, so the controls that matter most are unverified.

Honestly: pass 1 was too kind in calling tenant scoping "consistent" and the tests reassuring. See the retractions at the bottom.

---

## New findings

### 🔴 N1 — Broken object-level authorization: student PII readable by any user in the tenant
**`app/modules/academic/endpoints/academic.py:95-122, 153-182`** (service: `academic_service.py:223-346`)

`GET /academic/students`, `GET /academic/students/{id}/parents`, and `GET /academic/students/{id}/profile` are gated by **`get_current_user` only — no role check, no ownership check.** Any authenticated principal in the school, **including `student` and `parent` accounts**, can call them.

`student_profile` returns, for *any* `student_id`:
- student name, mobile, email, DOB, blood group, **APAAR national ID**;
- **every linked parent's name, mobile, and email**;
- fee totals; **transport route + boarding stop + driver + vehicle number**; **hostel block + room number + warden contact**.

And `GET /academic/students` hands any user the full roster (UUIDs + names + admission numbers), so the IDs needed to enumerate `/profile` are free. Net: one parent login can harvest the home pickup point and parents' phone numbers for **every child in the school**. For a K-12 product that's a child-safety issue, not just a privacy one (OWASP A01).

The damning part: the **fees** module already does this correctly — `fees/endpoints/fee.py:44-53` calls `assert_can_access_student`. The academic endpoints simply forgot.

**Fix:** Gate the list/roster endpoints to staff (`require_roles("admin","super_admin","teacher","class_incharge","operations")`) and run every per-student academic endpoint through `assert_can_access_student` (the helper already encodes parent-linked / self / staff rules). Add an isolation test that a `parent` token gets 403 on a non-linked child.

### 🔴 N2 — Live secret and repo metadata baked into the Docker image
**`apps/api/Dockerfile`** + **no `apps/api/.dockerignore`**

`COPY . .` with no `.dockerignore` copies `apps/api/.env` (the real `OPENAI_API_KEY` from pass-1 C1), `.git/`, `.venv/`, `.mypy_cache/`, `.pytest_cache/`, and `uploads/` into the image. The key then lives in an image layer **even if the file is later deleted**, and anyone who can pull the image gets it. Additionally:
- `pip install -e ".[dev]"` ships pytest, locust, faker, ruff, mypy into the **production** image (bloat + attack surface).
- **No `USER` directive → the container runs as root.**
- No base-image digest pin, no `HEALTHCHECK`.

**Fix:** Add a `.dockerignore` (`.env*`, `.git`, `.venv`, `__pycache__`, `*_cache`, `uploads`, `tests`); install prod deps only (`pip install .` against a locked set); add a non-root `USER`; pin the base image by digest. Then rotate the key (again) since it has been in build context.

### 🟠 N3 — File storage is local-disk only; Azure Blob is unimplemented
**`app/modules/files/services/file_service.py:16-63`**

`upload()` always does `open(storage_path, "wb")` under a local `uploads/` dir; the "in prod: upload to Azure Blob" is a comment. `download_file` then serves `FileResponse(path=record.storage_path)`. Consequences in any real deployment:
- Containers have ephemeral filesystems → **uploaded files vanish on redeploy/restart.**
- With more than one replica, a file written on pod A **404/500s when downloaded via pod B** (it's on A's disk).
- `AZURE_STORAGE_CONNECTION_STRING` / `AZURE_STORAGE_CONTAINER` config exists but is dead.

This is a functional showstopper for the documented Azure deployment. **Fix:** implement the Blob backend (or mount shared storage) before any multi-replica/container rollout; until then it only works as a single-node dev server.

Related, same file/endpoint:
- **10 MB limit is enforced *after* `await file.read()`** (`file.py:40-42`) — the whole body is buffered into RAM first, so a large body is a memory-DoS. Mitigated only by nginx `client_max_body_size 12m`; gone if hit directly or if that cap is raised. Check `Content-Length` / stream instead.
- **`content_type` is taken from the client** and echoed on download with **no `X-Content-Type-Options: nosniff`** → MIME-confusion. No file-type allow-list.
- `get_file(school_id=None)` makes cross-tenant fetch a one-arg mistake away; make `school_id` mandatory.

### 🟠 N4 — PDF generation never runs (WeasyPrint isn't a dependency)
**`pyproject.toml`** (no `weasyprint`) vs **`fees/services/receipt_pdf.py:94-100`**, **`ai/services/paper_pdf.py:98-103`**, **`ai/services/report_card_pdf.py:99-104`**

All three renderers do `try: from weasyprint import HTML … except ImportError: return html`. WeasyPrint is in **none** of the dependency groups, so the import always fails and every `/pdf` endpoint returns **HTML with a `text/html` content type** while the UI/users believe they're getting a PDF. Either add `weasyprint` (and its system libs — note it needs `libpango`, which your `slim` image doesn't install) or rename these "print-ready HTML" and stop advertising PDF.

### 🟠 N5 — Receipt renderer is injectable (no HTML escaping)
**`app/modules/fees/services/receipt_pdf.py:16-84`**

`render_receipt_html` interpolates `school_name`, `school_address`, `school_contact`, `student_name`, `class_name`, `fee_type`, `transaction_id`, and **`school_logo_url` straight into `src="…"`** with **zero escaping**. `report_card_pdf.py` and `paper_pdf.py` correctly use `html.escape` everywhere — this file is the outlier. Because N4 means the output is served **as HTML**, this is live template injection:
- `school_logo_url` (set via school-profile update) can break out of the `src` attribute: `https://x"><script>…` → script in the receipt document.
- `student_name` is a user's `full_name`; the `generate_receipt_html` preview/email helper (`:103-105`) returns the raw string with no attachment disposition, so anywhere a receipt is previewed inline becomes stored XSS.

**Fix:** `html.escape` every interpolated value and validate/′escape the logo URL (scheme allow-list). Mirror what the other two renderers already do.

### 🟡 N6 — The notification/communication delivery layer is entirely stubbed
**`app/modules/notifications/services/notification_service.py:32-39`** and **`app/workers/outbox_worker.py:38-61`**

`NotificationService.send` writes an in-app row, then:
```python
if channel == SMS:   pass  # TODO: MSG91
elif channel == EMAIL: pass  # TODO: SendGrid / SES
elif channel == PUSH:  pass  # TODO: Firebase FCM
```
and every outbox handler (`fee_paid`, `attendance_marked`, `notice_published`, `exam_marks_entered`) just calls `logger.info(...)`. So the platform's headline "notify parents on fees / attendance / marks" **sends nothing** — no SMS, email, or push is wired. MSG91/SendGrid keys in config are unused. This is a missing core feature, not a bug, but it's openly `TODO` and worth stating plainly.

Also: `NotificationService` queries by `user_id` with **no `school_id` filter** (`:45,53,61,69`). Not exploitable today (UUIDs are unique and single-tenant per user), but it breaks the scoping invariant the rest of the codebase follows — add `school_id` for defense-in-depth.

### 🟡 N7 — The tests don't exercise the security-critical paths
**`tests/conftest.py`** + **`tests/test_tenant_isolation.py`**

Tests run with `ENVIRONMENT=testing` and `RATE_LIMIT_ENABLED=false`, which means:
- `check_rate_limit` early-returns → **rate limiting/lockout untested.**
- `validate_tenant_school_match` and `validate_refresh_origin` early-return → **token-vs-subdomain tenant binding and CSRF untested.**
- `main.py` skips `AuditMiddleware`/`TenantMiddleware`/`MetricsMiddleware` under testing → **the whole middleware stack is untested.**
- Each test runs in one rolled-back transaction → **no concurrency/idempotency coverage** (so the fee double-pay and attendance/marks races can't be caught here).

`test_tenant_isolation.py` is good as far as it goes — it proves the **service-layer `school_id` filtering** returns 404 for a foreign class/exam — but that's the part that was never really in doubt. The actual cross-tenant control (a valid School-A token replayed against School-B's subdomain, enforced by `validate_tenant_school_match`) is **disabled in the test environment**, so it has zero coverage. Three isolation tests, covering only subjects + exam marks; nothing for fees, students, files, users, notifications, attendance, or AI artifacts.

Net: the suite is real (DB-backed, not mocked — good) but gives **false confidence** precisely on the controls a reviewer cares about.

### 🟡 N8 — Whole tables have no indexes; loading strategy is ad hoc
**Models with zero `Index`/no `__table_args__`:** `outbox.py`, `communication.py`, `school_ops.py`, `school.py`, `question_paper.py`, `timetable.py`.

Postgres doesn't auto-index foreign keys, so:
- **Outbox** is polled every 2 s with `WHERE status=PENDING ORDER BY created_at LIMIT 20 FOR UPDATE SKIP LOCKED` and **no index on `status`/`created_at`** → a sequential scan on every poll, degrading as the table grows. Add `Index(..., "status", "created_at")`.
- **`NoticeReadReceipt`** is looked up by `(notice_id, user_id)` with no index or unique constraint → seq scan + the check-then-insert race.
- **`StudentTransport`** is queried by `route_id` and `student_id` (both unindexed) in `ops_service.list_route_students` / `assign_student_transport`.

Separately, `grep` shows **zero** `selectinload`/`joinedload` in the codebase. Relationship loading is either `lazy="selectin"` on the model or hand-rolled per-row queries — e.g. `academic_service.student_profile` fires ~8 + 2×(#parents) sequential queries for **one** profile view (compounding N1's exposure with a latency cost). This is the same N+1 family flagged in pass 1 (attendance/marks/fees), and it's systemic.

### 🟡 N9 — `enroll_student` / `link_parent` lack role and duplicate guards
**`academic_service.py:153-202`**

- `enroll_student` doesn't check the target user's role is `student`, and a second enroll of the same user hits `Student.user_id`'s unique constraint → `IntegrityError` → **500** (no handler anywhere — pass-1 M3).
- `link_parent` will link **any** in-school user as a "parent" (no role check) and a duplicate link hits `uq_student_parent` → 500.

Validate roles; map conflicts to 409.

---

## Corrections to pass 1 (being honest about my own report)

- **"Consistent `school_id` scoping on virtually every query" — overstated.** It's consistent for *cross-entity writes* via `TenantScope`, but **read-side object authorization is inconsistent**: the academic student endpoints (N1) have a real PII hole, and notifications drop `school_id` (N6). I should have caught N1 in pass 1; it's arguably the single most important issue in the codebase.
- **"Tests … keep it" — too generous.** They're DB-backed (good) but disable the rate limiter, tenant-match, CSRF, and the entire middleware stack, and can't see concurrency (N7). Treat current green tests as *not* evidence that the security controls work.
- **"Outbox uses FOR UPDATE SKIP LOCKED — good."** True for concurrency, but the handlers are no-ops (N6), the table is unindexed (N8), and the error path is broken (pass-1 H3). It's scaffolding, not a working outbox.
- **PDF/receipts** were listed neutrally in pass 1; they actually (a) never produce PDFs (N4) and (b) include an injectable renderer (N5).

## Still outstanding from pass 1 (unchanged, not re-detailed)
C1 secret rotation · H1 payment idempotency / no `transaction_id` unique constraint · H2 spoofable `X-Forwarded-For` rate-limit · H3 outbox `[-500]` slice bug · H4 admin→super_admin escalation · M1 unthrottled/synchronous AI endpoints · M2/M3 N+1 + missing `IntegrityError`→409 · M4 per-request tenant DB lookup · M5 receipt-counter seeding · M6 Redis fail-mode · M8 single-session refresh.

## Honest priority call
1. **N1** (student PII access control) and **N2** (`.dockerignore` + rotate key) — before any pilot touches real student data.
2. **N3** (file storage) and **N4/N5** (PDF + receipt escaping) — these are "the feature doesn't work / is injectable," not polish.
3. **N7** — turn the security middleware *on* in a test profile and add real cross-tenant + authz tests; otherwise you can't trust any of the above is fixed.
4. Then N6/N8/N9 and the pass-1 backlog.

If you want, I'll start with N1 (smallest, highest-impact: route the academic endpoints through `assert_can_access_student`) and the `.dockerignore`, and add the failing isolation tests that should have caught them.
