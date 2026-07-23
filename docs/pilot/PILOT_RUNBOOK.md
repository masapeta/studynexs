# StudyNexs Pilot Runbook — Release 0.3

> Operator guide for conducting the first Principal + Teacher pilot experience.

**Release baseline:** `v0.3.0`
**Pilot scope:** Principal + Teacher only
**Do not include:** Release 0.4 Student/Parent journeys, new feature work, architecture changes, or unreviewed demo paths.

---

## 1. Purpose

This runbook exists so the pilot operator can conduct the first school pilot without engineering assistance during the session.

The pilot should prove one simple story:

```text
StudyNexs learns the school curriculum
↓
Academic Intelligence becomes ready
↓
Teachers generate grounded lesson plans and question papers
↓
The principal can understand why this is worth piloting
```

The operator should not improvise workflows. Follow the preflight, script, and recovery paths exactly.

---

## 2. Roles

| Role | Purpose | Reference account |
|---|---|---|
| Principal | Understand value, readiness, and pilot fit | `principal` |
| Teacher 1 — subject teacher | Demonstrate grounded lesson plan and question paper flow | `teacher6` |
| Teacher 2 — academic lead / class incharge | Observe teacher workflow, governance, and handoff model | `teacher1` |
| Operator | Runs environment, preflight, demo, and incident response | Product / engineering operator |

Password for seeded reference accounts:

```text
Demo@1234
```

For a real customer tenant, replace seeded accounts with the school’s real pilot users and verify the same role/class/subject assumptions before the pilot.

---

## 3. Release boundary

Release 0.3 includes:

- Principal runtime proof.
- Teacher runtime proof.
- Principal browser walkthrough.
- Teacher browser walkthrough.
- Tenant isolation verification.
- Same-pack grounding verification for teacher-generated lesson plan and question paper.

Release 0.3 does not include:

- Student journey.
- Parent journey.
- Student/parent onboarding.
- Rich student practice engine.
- Advanced report cards.
- New architecture.
- New product modules.

If the school asks about student or parent experience, say:

> “The first pilot phase focuses on principal and teacher academic workflow. Student and parent experiences are planned for the next release phase after we validate teacher adoption.”

---

## 4. Operator timeline

### T-1 day

1. Confirm the release baseline.
2. Confirm API, database, Redis, Qdrant, and web build can run.
3. Confirm AI provider keys are configured.
4. Confirm the pilot tenant and users.
5. Confirm teacher class/subject assignments.
6. Run the full preflight checklist.
7. Run the runtime proof.
8. Run the browser walkthrough.
9. Record the canonical pack, lesson plan, and question paper IDs.
10. Rehearse the demo script once end to end.

### T-0, before joining the school call

1. Restart from a fresh production web build.
2. Confirm `/ready` is healthy.
3. Confirm AI credits or principal override.
4. Open the demo browser in a clean profile or incognito context.
5. Keep a second browser/session ready for teacher login.
6. Keep the preflight checklist open.
7. Keep the demo script open.

### During the pilot

1. Do not run unplanned scripts.
2. Do not switch into Student or Parent flows.
3. Do not explain internal architecture unless asked.
4. Do not expose API logs, terminal traces, or internal identifiers unless useful for trust.
5. If a live AI generation is slow, narrate the grounding process calmly and use the prevalidated generated artifact if needed.

### After the pilot

1. Record customer reactions.
2. Record objections and confusion.
3. Record whether success criteria were met.
4. Do not start Release 0.4 based on verbal enthusiasm alone.
5. Convert observations into a reviewed next-batch proposal.

---

## 5. Environment startup

From repository root:

```powershell
docker compose -f infra/docker/docker-compose.dev.yml up -d
```

API:

```powershell
cd apps/api
python -c "import app.main; print('api import ok')"
```

Use the configured API service if Docker is running the API. If running locally:

```powershell
cd apps/api
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Admin web production build:

```powershell
cd apps/admin-web
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
$env:NEXT_PUBLIC_TENANT_SLUG="reference"
npm run build
npx next start -p 3002
```

Use a fresh production server. Do not use a stale `next start` process from a previous build.

---

## 6. Mandatory preflight commands

API readiness:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/ready
```

Reference School smoke:

```powershell
cd apps/api
python scripts/smoke_reference_school.py
```

Batch 3 runtime proof:

```powershell
cd apps/api
python scripts/smoke_batch3_principal_teacher_pilot.py
```

Batch 3 browser walkthrough:

```powershell
cd apps/admin-web
$env:E2E_BASE_URL="http://127.0.0.1:3002"
$env:E2E_API_URL="http://127.0.0.1:8000"
$env:E2E_TENANT_SLUG="reference"
node e2e-batch3-principal-teacher.cjs
```

Expected results:

- Runtime proof: `BATCH 3 PRINCIPAL+TEACHER PILOT PROOF: PASS`
- Browser walkthrough: `ALL GREEN`
- Disallowed console/API errors: `0`

---

## 7. Pilot data to confirm

Before the session, record:

| Item | Expected / actual |
|---|---|
| Tenant | `reference` or customer pilot tenant |
| Principal account | |
| Teacher 1 account | |
| Teacher 2 account | |
| Canonical approved CurriculumPack | |
| KG ready | |
| RAG ready | |
| AI credits remaining or override active | |
| Canonical generated lesson plan | |
| Canonical generated question paper | |
| Browser walkthrough result | |
| Runtime proof result | |

For Release 0.3 reference validation, the canonical pack was:

```text
1bdfffc6-933d-4780-9de4-b7d6c92201bb
```

---

## 8. Pilot execution sequence

Use the detailed script in [`PILOT_DEMO_SCRIPT.md`](./PILOT_DEMO_SCRIPT.md).

High-level flow:

1. Open with the principal.
2. Explain the Release 0.3 pilot boundary.
3. Show dashboard and curriculum readiness.
4. Show Academic Intelligence Ready.
5. Switch to Teacher 1.
6. Show assigned class/subject context.
7. Generate or open a grounded lesson plan.
8. Generate or open a grounded question paper.
9. Invite Teacher 2 to react as academic lead.
10. Confirm pilot success criteria and next steps.

---

## 9. Incident response

### AI credit limit appears

Symptom:

```text
School AI credit limit reached for this month.
```

Action:

1. Do not troubleshoot live in front of the school.
2. Use the prevalidated generated artifact if available.
3. After the call, confirm AI budget or activate principal override.

Preflight prevention:

```powershell
cd apps/api
python scripts/smoke_batch3_principal_teacher_pilot.py
```

The proof explicitly checks AI credits or override availability.

### Browser route fails or chunks fail

Symptoms:

- white screen;
- route 500;
- `ChunkLoadError`;
- stale UI after recent build.

Action:

1. Stop the stale web server.
2. Run `npm run build`.
3. Restart `npx next start -p 3002`.
4. Rerun browser walkthrough.

### Teacher cannot see expected class or subject

Action:

1. Stop live workflow.
2. Switch to the preverified teacher account if available.
3. Record the mapping issue.
4. Do not change RBAC live unless explicitly planned.

### Login rate limit

Action:

1. Pause repeated login attempts.
2. Use a fresh browser context.
3. If local validation only, clear scoped local Redis login-rate keys.
4. Do not clear all Redis keys.

---

## 10. No-go conditions

Do not proceed with a live pilot session if any of these are true:

- API `/ready` is not healthy.
- Browser walkthrough fails.
- Runtime proof fails.
- Tenant header is wrong or missing.
- Principal login fails.
- Teacher login fails.
- Teacher class/subject mapping is wrong.
- Academic Intelligence is not ready.
- AI credits are exhausted and no override/prevalidated artifact exists.
- Any cross-tenant data appears.

---

## 11. Operator closeout

After the pilot, capture:

- whether the principal understood the value;
- whether both teachers understood where they fit;
- whether the school wants to proceed;
- what confused them;
- what they asked for next;
- what blocked trust;
- whether Release 0.4 should be proposed.

Use [`PILOT_SUCCESS_CRITERIA.md`](./PILOT_SUCCESS_CRITERIA.md) for the final assessment.
