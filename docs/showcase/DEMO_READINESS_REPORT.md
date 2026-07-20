# Demo v1 — Readiness Report

**Date:** 2026-07-20  
**Tenant:** ARM International School · `reference`  
**Goal:** A principal experiences StudyNexs and asks *"When can we start our pilot?"*

---

## Verdict

**Demo v1 is ready for localhost rehearsal and principal walkthrough** (after operator pre-flight below).

Not yet ready for **shareable HTTPS URL** — Gate 1A deploy still blocked on cloud credentials (unchanged from assessment).

---

## What was implemented (this batch)

| Change | Journey | Why |
|--------|---------|-----|
| `seed_reference_school_demo_v1.py` | 2, 3, 4, 5 | Closes P1 seed gaps: approved grounded QP, pending QP for principal queue, unit test + **suggested** AI eval, class-work notice |
| Wired into `seed_reference_school.py` chain | All | One command seeds full demo |
| Extended `smoke_demo_readiness.py` (+7 checks → **32 total**) | 0, 2, 3/4 | Automated proof curriculum + eval + notice exist |
| Teaching hub **Review** tab | 2 | Surfaces corrections/eval path in nav |
| Principal briefing quick links → Curriculum, AI papers, Exam review | 0, 2, 5 | Connected story from dashboard |
| Parent home **Parent Copilot** CTA per child | 4 | Discoverability without new module |
| Evaluate page auto-opens **suggested** eval + review banner | 2 | Demo-ready AI marking without live OCR |

**No new platform modules.** No architecture changes. Integration and seed data only.

---

## What was reused (existing capabilities)

- CurriculumPack approval, KG spine, RAG grounding (Batch 1 + curriculum seeds)
- Question paper HITL workflow + question bank ingest
- Answer-sheet evaluation engine (objective + rubric suggestions, teacher approve)
- Morning Briefing / dashboard aggregation
- Parent Copilot briefing + ask API
- Student tutor recommendations (misconception from prior seed)
- Full SMS ops data (288 students, fees, attendance, exams, timetable)
- Reference School seed chain + login personas

---

## Operator pre-flight (required before every demo)

```powershell
cd D:\Projects\studynexs-platform\studynexs-dev\apps\api
docker compose -f ../../infra/docker/docker-compose.dev.yml up -d
python scripts/seed_reference_school.py
python scripts/smoke_reference_school.py   # expect ALL GREEN (32 checks)
```

**Admin-web** (`apps/admin-web/.env.local`):

```
NEXT_PUBLIC_TENANT_SLUG=reference
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Logins:** see [`REFERENCE_SCHOOL_LOGIN_CARD.md`](./REFERENCE_SCHOOL_LOGIN_CARD.md) · password `Demo@1234`

**Walkthrough script:** [`DEMO_V1_SCRIPT.md`](./DEMO_V1_SCRIPT.md)  
**Human checklist:** [`DEMO_V1_JOURNEY_CHECKLIST.md`](./DEMO_V1_JOURNEY_CHECKLIST.md)

---

## Demo story (connected, not feature tour)

| Act | Role | Route | Payoff |
|-----|------|-------|--------|
| 0 | Principal | Dashboard → Curriculum | School is alive; **approved Class 10 Maths pack** with spine + audit |
| 1 | teacher6 | Lesson plans | Lesson grounded to curriculum |
| 3 | teacher6 + student | Attendance → Notices → Student tutor | Same school day; class work notice visible |
| 2a | teacher6 | AI papers | **Pre-seeded approved** Quadratic Equations paper |
| 2b | teacher6 | Exams → Unit Test → **Evaluate** | **Suggested AI marks** ready for review (no live OCR needed) |
| 5 | Principal | Dashboard | Priority queue shows **1 paper pending approval** + school health KPIs |
| 4 | parent_demo | Parent home → Copilot | Child summary + scripted ask |

**Live AI optional:** Generate a new QP if `GEMINI_API_KEY` (or fallback) is configured; demo works without it using seeded artifacts.

---

## Validation run (2026-07-20)

| Check | Result |
|-------|--------|
| `seed_reference_school_demo_v1.py` | ✅ Pass (idempotent re-run safe) |
| `smoke_reference_school.py` | ✅ **32/32 ALL GREEN** |
| `pytest tests/test_answer_sheet_eval.py tests/test_question_paper.py` | ✅ 17 passed |
| Web lint (changed files) | ✅ No diagnostics |

Full backend suite and E2E browser smoke not re-run this batch.

---

## Remaining known limitations (honest)

| Limitation | Demo impact | Mitigation |
|------------|-------------|------------|
| No HTTPS URL | Cannot email a link | Gate 1A deploy when credentials available |
| Online fees / Razorpay | Offline fees only | Narrate; show fee stats |
| No homework module | Use class-work **notice** | Seeded |
| Live OCR eval | Optional wow | Seeded **suggested** eval; narrate OCR path |
| Parent Copilot needs AI key | Briefing may fallback | Script prompt; pre-loaded briefing often works from API |
| Transport/residential UI thin | Out of demo scope | Skip or settings-only |
| Analytics product module | Widgets only | Principal briefing + gradebook |
| Flutter mobile | Web portals only | Frame as pilot PWA |

---

## Risks during customer demonstrations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Stale local uvicorn on :8000 (Windows) | Medium | Smoke uses `localhost:8000`; kill stale process if smoke fails |
| Missing seed / wrong tenant slug | High | Run full seed + smoke before demo |
| AI provider outage during **live** generation | Medium | Use pre-seeded QP + eval; don't depend on live gen |
| Principal focuses on feature count | Medium | Stick to **day-in-the-life** script, not module tour |
| Overselling KG/RAG internals | Low | Show curriculum UI outcomes, not backend jargon |
| Approve eval without reviewing | Low | Demo script emphasizes teacher authority / HITL |

---

## Why Demo v1 is ready

1. **One tenant, one story** — Reference School chains curriculum → assessment → learning → parent → principal in ≤60 minutes.
2. **No empty states** on critical paths after seed (verified by 32 API checks).
3. **AI differentiation is visible** — grounded paper, suggested marking with rubric breakdown, copilot surfaces — without requiring risky live generation.
4. **Human-in-the-loop is demonstrable** — pending QP approval + eval review + incharge approve narrative.
5. **Reuse-first** — zero new modules; activated existing backend with seed + minor UX wiring.

---

## Recommended next step (post-review)

1. **Human rehearsal** — ARM walks [`DEMO_V1_SCRIPT.md`](./DEMO_V1_SCRIPT.md) once; note friction only.
2. **Gate 1A** — HTTPS deploy when cloud credentials land (no feature work until URL works).
3. **Gate 1B** — Pre-approved QP backup if live AI fails; parent/teacher E2E in browser smoke.
4. **First principal demo** — Stop polishing after successful walkthrough (Gate 1 exit).

**Do not start** Batch 30 Learning Analytics or new intelligence modules until after Gate 1 exit.

---

*Report produced at Demo v1 completion. Baseline: [`PRODUCT_STATE_ASSESSMENT.md`](../../PRODUCT_STATE_ASSESSMENT.md).*
