# StudyNexs Pilot Preflight Checklist — Release 0.3

> Complete this checklist before every Principal + Teacher pilot session.

**Release baseline:** `v0.3.0`
**Scope:** Principal + two teachers
**Out of scope:** Student/Parent Release 0.4 journeys

---

## Sign-off

| Role | Name | Status |
|---|---|---|
| Pilot operator | | ☐ Ready |
| Product owner / ARM | | ☐ Ready |
| Engineering on-call | | ☐ Ready |
| School principal contact | | ☐ Ready |

Go / no-go:

- ☐ Go
- ☐ Go with conditions
- ☐ No-go

Conditions:

---

## A. Release and change control

| # | Check | Status | Notes |
|---|---|---|---|
| A1 | Release tag is `v0.3.0` | ☐ | |
| A2 | Release 0.3 is Accepted / Frozen | ☐ | |
| A3 | No Release 0.4 work is included | ☐ | |
| A4 | No unreviewed product changes are being demoed | ☐ | |
| A5 | Working tree dirty files, if any, are unrelated and not part of pilot | ☐ | |

Commands:

```powershell
git describe --tags --exact-match HEAD
git status --short
```

---

## B. Environment

| # | Check | Status | Notes |
|---|---|---|---|
| B1 | Docker Desktop / container runtime running | ☐ | |
| B2 | PostgreSQL running | ☐ | |
| B3 | Redis running | ☐ | |
| B4 | Qdrant running | ☐ | |
| B5 | API imports cleanly | ☐ | |
| B6 | API `/ready` returns DB + Redis OK | ☐ | |
| B7 | Admin web is freshly built | ☐ | |
| B8 | Admin web is running on an API-allowed origin | ☐ | |
| B9 | No stale `next start` process is serving old chunks | ☐ | |

Commands:

```powershell
docker ps
cd apps/api
python -c "import app.main; print('api import ok')"
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/ready
cd ../admin-web
npm run build
npx next start -p 3002
```

---

## C. AI readiness

| # | Check | Status | Notes |
|---|---|---|---|
| C1 | Real AI provider key configured | ☐ | |
| C2 | AI gateway is not using stub provider for pilot generation | ☐ | |
| C3 | School AI credits are sufficient | ☐ | |
| C4 | Principal emergency override active if credits are exhausted | ☐ | |
| C5 | Runtime proof confirms AI generation works | ☐ | |

Required command:

```powershell
cd apps/api
python scripts/smoke_batch3_principal_teacher_pilot.py
```

Expected:

```text
BATCH 3 PRINCIPAL+TEACHER PILOT PROOF: PASS
```

No-go if teacher lesson-plan or question-paper generation returns 429 and there is no validated fallback artifact.

---

## D. Tenant and users

| # | Check | Status | Notes |
|---|---|---|---|
| D1 | Correct tenant selected | ☐ | |
| D2 | Principal login works | ☐ | |
| D3 | Teacher 1 login works | ☐ | |
| D4 | Teacher 2 login works | ☐ | |
| D5 | Principal has curriculum visibility | ☐ | |
| D6 | Teacher 1 has assigned class/subject | ☐ | |
| D7 | Teacher 2 role is understood before live use | ☐ | |
| D8 | No teacher sees unauthorized tenant data | ☐ | |

Reference accounts:

| Role | Username | Password | Use |
|---|---|---|---|
| Principal | `principal` | `Demo@1234` | Principal walkthrough |
| Teacher 1 | `teacher6` | `Demo@1234` | Class 10 Mathematics generation |
| Teacher 2 | `teacher1` | `Demo@1234` | Class incharge / academic lead discussion |

For real school pilots, verify actual accounts instead of using reference credentials.

---

## E. Curriculum and grounding

| # | Check | Status | Notes |
|---|---|---|---|
| E1 | Approved `CurriculumPack` exists | ☐ | |
| E2 | Pack belongs to pilot tenant | ☐ | |
| E3 | Pack is for the demonstrated class/subject | ☐ | |
| E4 | KG ready | ☐ | |
| E5 | RAG ready | ☐ | |
| E6 | Vector/topic counts are greater than zero | ☐ | |
| E7 | Lesson-plan generation uses same pack | ☐ | |
| E8 | Question-paper generation uses same pack | ☐ | |

Release 0.3 reference pack:

```text
1bdfffc6-933d-4780-9de4-b7d6c92201bb
```

---

## F. Runtime proof

| # | Check | Status | Notes |
|---|---|---|---|
| F1 | API `/ready` passes | ☐ | |
| F2 | Principal runtime proof passes | ☐ | |
| F3 | Teacher runtime proof passes | ☐ | |
| F4 | Same-pack grounding proof passes | ☐ | |
| F5 | Reference School smoke passes | ☐ | |

Commands:

```powershell
cd apps/api
python scripts/smoke_batch3_principal_teacher_pilot.py
python scripts/smoke_reference_school.py
```

Expected:

```text
BATCH 3 PRINCIPAL+TEACHER PILOT PROOF: PASS
ALL GREEN (32 checks)
```

---

## G. Browser walkthrough

| # | Check | Status | Notes |
|---|---|---|---|
| G1 | Fresh production web server running | ☐ | |
| G2 | Principal dashboard route renders | ☐ | |
| G3 | Principal curriculum route renders | ☐ | |
| G4 | Principal lesson-plan route renders | ☐ | |
| G5 | Principal question-paper route renders | ☐ | |
| G6 | Teacher home route renders | ☐ | |
| G7 | Teacher teaching hub renders | ☐ | |
| G8 | Teacher lesson-plan route renders | ☐ | |
| G9 | Teacher question-paper route renders | ☐ | |
| G10 | Teacher exams route renders | ☐ | |
| G11 | 0 disallowed console/API errors | ☐ | |

Command:

```powershell
cd apps/admin-web
$env:E2E_BASE_URL="http://127.0.0.1:3002"
$env:E2E_API_URL="http://127.0.0.1:8000"
$env:E2E_TENANT_SLUG="reference"
node e2e-batch3-principal-teacher.cjs
```

Expected:

```text
ALL GREEN
0 disallowed console/API errors
```

---

## H. Demo materials

| # | Check | Status | Notes |
|---|---|---|---|
| H1 | Pilot demo script open | ☐ | |
| H2 | Canonical pack ID recorded | ☐ | |
| H3 | Canonical generated lesson plan recorded | ☐ | |
| H4 | Canonical generated question paper recorded | ☐ | |
| H5 | Backup browser session ready | ☐ | |
| H6 | Screen share tested | ☐ | |
| H7 | School participants and roles confirmed | ☐ | |

---

## No-go triggers

Stop the pilot if any of these occur before the session:

- `/ready` is not healthy.
- Runtime proof fails.
- Browser walkthrough fails.
- AI credits/override unavailable.
- Principal login fails.
- Teacher 1 login fails.
- Teacher class/subject mapping is wrong.
- Academic Intelligence is not ready.
- Any cross-tenant data appears.
- Web server shows stale chunks or route 500s.
