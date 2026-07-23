# Stage 1 / Gate 1 — Validation Addendum (Final)

**Date:** 2026-07-22  
**Scope:** Stage 1 operational baseline + browser validation harness (Reference School tenant `reference`)  
**Status:** Stage 1 **COMPLETE** · Gate 1 **localhost validation COMPLETE** · Gate 1A HTTPS **not in scope**  
**Stage 2 (Academic Onboarding MVP):** **Not authorized** — stop for review after this addendum

This addendum is the authoritative evidence record for Stage 1 / Gate 1 localhost validation. It supplements [`DEMO_EXPERIENCE_GAP_ANALYSIS.md`](./DEMO_EXPERIENCE_GAP_ANALYSIS.md) (strategic target) and [`DEMO_READINESS_REPORT.md`](./DEMO_READINESS_REPORT.md).

---

## 1. Executive summary

| Layer | Verdict |
|-------|---------|
| **API health/readiness** | **200** on `127.0.0.1:8000` and `localhost:8000` |
| **CORS (config + preflight)** | **Resolved** — `http://localhost:3002` allowed on Docker API |
| **DB migrations** | **At head** (`x9a8b7c6d5e4`) — applied 2026-07-22 |
| **Reference School seed** | **Idempotent exit 0** |
| **Demo readiness API smoke** | **32/32 green** |
| **Focused pytest regressions** | **57/57 passed** |
| **Browser smoke (`e2e-smoke.cjs`)** | **18/18 ALL GREEN · 0 disallowed console errors** |
| **Four-persona journeys (`e2e-reference-journeys.cjs`)** | **18/18 ALL GREEN · 0 disallowed console errors · tenant `reference` on every persona** |
| **Gate 1A (HTTPS demo URL)** | **Not started** — separate deployment gate |

**Guided Reference School demo (presenter-led, localhost):** **Viable** with pre-flight checklist (§7).  
**Self-guided / public demo:** **Not ready** (unchanged from gap analysis).

---

## 2. Root cause & fix (API 500 on health)

**Problem:** `GET /health` and `/ready` returned **HTTP 500** on `http://127.0.0.1:8000`.

**Cause:** Orphaned local uvicorn worker bound exclusively to `127.0.0.1:8000` while Docker API served correctly on `0.0.0.0:8000`.

**Fix (operational):** `taskkill /PID <stale-pid> /F /T`

**Pre-flight (mandatory on Windows):** `netstat -ano | findstr ":8000"` — only Docker (`studynexs-api`, PID varies) should listen. Kill any local Python/uvicorn on `[::1]:8000` or `127.0.0.1:8000`.

---

## 3. Final validation sequence (2026-07-22)

Executed in order after ARM authorization to apply pending migration.

### 3.1 Database migration

```powershell
docker exec studynexs-api alembic upgrade head
```

| Before | After |
|--------|-------|
| `f4a5b6c7d8e9` | `x9a8b7c6d5e4` (head) — lesson plan template fields |

### 3.2 API health and readiness

```
GET http://127.0.0.1:8000/health  → 200  {"status":"healthy","service":"StudyNexs API"}
GET http://127.0.0.1:8000/ready   → 200  {"status":"ready","checks":{"database":"ok","redis":"ok"}}
```

### 3.3 Reference School seed

```powershell
cd apps\api
python scripts/seed_reference_school.py
```

Exit code **0** · tenant `reference` (ARM International School) · idempotent.

### 3.4 Demo readiness smoke

```powershell
python scripts/smoke_demo_readiness.py
```

**32/32 ALL GREEN**

### 3.5 Focused pytest regressions

```powershell
pytest tests/test_health.py `
  tests/test_lesson_plan_authz.py tests/test_lesson_plan_template.py `
  tests/test_concept_card.py tests/test_tutor.py `
  tests/test_parent_copilot.py tests/test_student_copilot.py `
  tests/test_curriculum_pack.py tests/test_question_paper.py `
  tests/test_answer_sheet_eval.py tests/test_mastery_api.py -q
```

| Result | Duration |
|--------|----------|
| **57 passed** | 265.5s |

Coverage: health · lesson plans · concept cards · tutor · parent/student copilot · curriculum pack · question papers · answer-sheet evaluation · mastery.

### 3.6 Previously failing endpoints (no 500s)

| Endpoint | Status |
|----------|--------|
| `GET /api/v1/ops/events` | **200** |
| `GET /api/v1/lesson-plans/next` | **200** (was 500 — schema drift, fixed by migration) |
| `GET /api/v1/tutor/students/{id}/lessons/fractions` | **200** |

### 3.7 Production web build

```powershell
cd apps\admin-web
$env:NEXT_PUBLIC_TENANT_SLUG='reference'
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8000'
npm run build
npx next start -p 3002
```

Build **green** · served on `http://localhost:3002`.

### 3.8 Browser smoke (`e2e-smoke.cjs`)

```powershell
$env:E2E_BASE_URL='http://localhost:3002'
$env:E2E_TENANT_SLUG='reference'
$env:E2E_API_URL='http://127.0.0.1:8000'
node e2e-smoke.cjs
```

| Result | Checks | Tenant tracker | Console |
|--------|--------|----------------|---------|
| **ALL GREEN** | **18/18** | `reference` on 15 API calls | **0 disallowed** (1 allowed pre-auth refresh 401) |

### 3.9 Four-persona journeys (`e2e-reference-journeys.cjs`)

```powershell
$env:E2E_LOGIN_GAP_MS='20000'
node e2e-reference-journeys.cjs
```

| Result | Checks | Tenant tracker | Console |
|--------|--------|----------------|---------|
| **ALL GREEN** | **18/18** | `reference` on every persona (5 calls each) | **0 disallowed** (1 allowed pre-auth refresh 401) |

**Persona breakdown (18 checks = 4 logins + 4 tenant assertions + 10 route renders):**

| Persona | Login | Tenant | Routes | Subtotal |
|---------|-------|--------|--------|----------|
| **Principal** | OK | reference | dashboard, curriculum, exams (3/3) | 5 |
| **Teacher** (`teacher6`) | OK | reference | hub, lesson-plans, ai-papers, exams (4/4) | 6 |
| **Parent** (`parent_demo`) | OK | reference | parent home (1/1) | 3 |
| **Student** (`student_demo`) | OK | reference | home, tutor (2/2) | 4 |
| **Total** | **4/4** | **4/4** | **10/10** | **18/18** |

**Screenshots:** `%TEMP%\sn-e2e\` · `%TEMP%\sn-reference-journeys\`

---

## 4. Validation harness (infrastructure)

| File | Purpose |
|------|---------|
| `apps/admin-web/e2e-harness-utils.cjs` | `requireReferenceTenant()` · `attachTenantTracker()` · `attachConsoleGuard()` |
| `apps/admin-web/e2e-smoke.cjs` | Principal dashboard smoke + report card + student tutor flows |
| `apps/admin-web/e2e-reference-journeys.cjs` | Four-persona UI login journeys |

**Console policy:** fail on any disallowed error; allow only pre-auth refresh **401** (no URL in Chrome generic message). CORS and `net::ERR_FAILED` always fail.

**Validation-blocking API fixes applied during harness hardening (not Stage 2):**

| Fix | File | Effect |
|-----|------|--------|
| `EventOut.event_time` coercion | `school_ops/schemas/ops.py` | `/api/v1/ops/events` 200 |
| `ConceptCardStatus` `values_callable` | `db/models/concept_card.py` | tutor lesson 200 |

---

## 5. Browser console errors

| Error | Status |
|-------|--------|
| Pre-auth refresh **401** | **Allowed** (expected before login) |
| CORS on `/api/v1/ops/events` | **Resolved** (underlying 500 fixed) |
| CORS on tutor lesson | **Resolved** (enum binding fixed) |
| CORS on `/api/v1/lesson-plans/next` | **Resolved** (migration applied) |
| **429** on rapid re-login | **Operator discipline** — use `E2E_LOGIN_GAP_MS=20000` or wait ~5 min |

Final run: **0 disallowed console errors** in both suites.

---

## 6. Remaining blockers (post–Stage 1)

| # | Blocker | Severity | Gate |
|---|---------|----------|------|
| B1 | **No HTTPS demo URL** | High for external send | Gate 1A |
| B2 | **Stale uvicorn on 127.0.0.1:8000** | High if uncaught | Pre-flight |
| B3 | **Login rate limit** on rapid persona switching | Low | Operator discipline |
| B4 | **Report card live AI** needs GEMINI key | Low (fallback exists) | Gate 1B |
| B5 | **Curriculum-first onboarding** not built | Strategic | Stage 2 |
| B6 | **Self-guided / public demo tenant** not built | Strategic | Post–Stage 2 |

CORS origin mismatch (formerly B3) is **closed**.

---

## 7. Operator pre-flight (Reference School demo)

```powershell
# 1. Kill stale uvicorn if present
netstat -ano | findstr ":8000"

# 2. Docker stack healthy
docker ps

# 3. Migrations at head
docker exec studynexs-api alembic current   # expect x9a8b7c6d5e4 (head)

# 4. API probes
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready

# 5. Seed + smoke
cd apps\api
python scripts/seed_reference_school.py
python scripts/smoke_demo_readiness.py   # 32/32

# 6. Web (production build)
cd ..\admin-web
$env:NEXT_PUBLIC_TENANT_SLUG='reference'
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8000'
npm run build
npx next start -p 3002

# 7. Optional browser validation
$env:E2E_BASE_URL='http://localhost:3002'
$env:E2E_TENANT_SLUG='reference'
node e2e-smoke.cjs                        # 18/18
$env:E2E_LOGIN_GAP_MS='20000'
node e2e-reference-journeys.cjs           # 18/18
```

**Demo logins:** `principal`, `teacher6`, `parent_demo`, `student_demo` · password `Demo@1234`

---

## 8. Stage 1 / Gate 1 verdict

| Criterion | Met? |
|-----------|------|
| API `/health` + `/ready` restored | **Yes** |
| CORS allows `localhost:3002` | **Yes** |
| DB at migration head | **Yes** |
| Reference School seed idempotent | **Yes** |
| API smoke 32/32 | **Yes** |
| Pytest regressions 57/57 | **Yes** |
| No new API 500s on validation paths | **Yes** |
| Browser smoke 18/18, 0 disallowed console | **Yes** |
| Four-persona journeys 18/18, tenant proved | **Yes** |
| Screenshots captured | **Yes** |
| Stage 2 authorized | **No** |

**Stage 1 localhost baseline: COMPLETE.**  
**Gate 1 localhost validation: COMPLETE.**  
**Gate 1A (HTTPS): NOT STARTED** — see [`GATE1_EXECUTION.md`](../pilot/GATE1_EXECUTION.md).

---

## 9. Next step (not started)

Stage 2 (Academic Onboarding MVP) remains **not authorized** in this batch. ARM may authorize separately after reviewing this addendum.

---

*Validation complete. Stop for review. Do not begin Stage 2 until explicitly authorized.*
