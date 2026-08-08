# StudyNexs — Product State Assessment

**Date:** 2026-07-20  
**Assessor role:** Founding Principal Engineer (ownership handover)  
**Canonical repository:** `D:\Projects\studynexs-platform\studynexs-dev`  
**Branch:** `develop` (ahead of `origin/develop` by 7 commits)  
**Latest commit (verified):** `ce3d067` — *docs(product): add Reference-First Product Principle*  
**Method:** Documentation read as *intent*; every major claim cross-checked against code, routes, seeds, and tests. No code or governance docs were modified to produce this report.

---

## Executive summary

StudyNexs is a **substantially built** AI-first school operating system — not a greenfield prototype. The backend is a mature modular monolith (~182 HTTP handlers across 22 `/api/v1` prefixes, 43 Alembic migrations, 72 pytest modules). The admin web exposes **72 App Router pages** covering admin, teacher, parent, and student experiences in one Next.js app.

**The product is demo-capable on localhost today**, but **not yet demo-online** (no HTTPS URL). The shortest path to a compelling **Reference School** demonstration is to **finish and commit the in-progress Reference School seed/smoke/runbook work**, run **Demo v1 locally with a live AI key**, then execute **Gate 1A (HTTPS deploy)** — not to build new features.

**Biggest surprise:** More capability exists than the UI exposes. Parent Copilot, Student Copilot, curriculum intelligence, knowledge graph, document ingest, mastery digest, and answer-sheet evaluation are **implemented and tested** but partially hidden from primary navigation or absent from E2E smoke coverage.

---

## 1. Repository status

| Item | Verified state |
|------|----------------|
| **Canonical repo** | `D:\Projects\studynexs-platform\studynexs-dev` — matches constitution, AGENT_HANDOVER, and workspace rules |
| **Primary branch** | `develop` (never develop on `main` / `production`) |
| **Git state** | 7 commits ahead of remote; **significant uncommitted work** on Reference School demo assets (seeds, smokes, showcase docs) |
| **Working tree** | Modified: 14 seed/smoke scripts, `knowledge_graph.py`, `pack_service.py`, showcase READMEs. **Untracked:** `reference_school_config.py`, `seed_reference_school.py`, `seed_reference_school_curriculum.py`, `smoke_reference_school.py`, Demo v1 runbooks |
| **Tests (last verified)** | **340 passed, 2 skipped** per `docs/engineering/platform.json` (2026-07-15 isolated run). **Not re-run in this assessment.** 72 test files; ~340+ test functions |
| **Web build** | Last verified passing 2026-07-15 (`AGENT_HANDOVER`) |
| **CI** | `.github/workflows/ci.yml` — pytest + `next build` + Docker as hard gates; lint report-only |

### Documentation freshness (mismatches)

| Document | Issue |
|----------|-------|
| `docs/STATUS.md` | Dated **2026-07-12**; cites 305 tests, "Batch 16 uncommitted", "four portals don't exist" — partially stale |
| `docs/PLATFORM_STATUS.md` | Commit `45ed42a` vs actual `ce3d067`; otherwise aligned on capabilities |
| `docs/engineering/platform.json` | `last_commit: 8ed3a5f` — stale |
| `docs/pilot/GATE1_EXECUTION.md` | Step 5 still references deprecated `seed_demo_e2e_journey.py`; canonical seed is now `seed_reference_school.py` |
| `docs/PRODUCT.md` | Last updated 2026-06-15 — vision doc, not implementation status |

**Rule applied:** Where docs and code disagree, **implementation wins** (per engineering dashboard policy).

---

## 2. Architecture status

### Stack (verified in repo)

| Layer | Technology | Status |
|-------|------------|--------|
| Backend | FastAPI, Python 3.11, async SQLAlchemy + asyncpg | ✅ Production-shaped |
| Database | PostgreSQL 16, 43 migrations, single Alembic head | ✅ |
| Cache / auth | Redis 7 (OTP, blacklist, rate limits, user cache) | ✅ |
| Vector DB | Qdrant (RAG, tenant+pack scoped) | ✅ Implemented; required for grounded AI |
| Jobs | Arq (Redis) — answer-sheet vision eval async | ✅ Worker wired |
| Frontend | Next.js 16, React 19, Tailwind v4, App Router | ✅ |
| AI | Provider-agnostic LLM gateway + embeddings + RAG + metering/credits | ✅ |
| Deploy target | API → Azure Container Apps; Web → Cloudflare OpenNext | 🔧 Config exists; **HTTPS demo not deployed** |

### Modular monolith (22 HTTP-mounted domains)

```
auth · users · academic · attendance · examinations · fees · timetable
communications · school_ops · notifications · files · jobs · ai · school
mastery · curriculum (6 routers) · portal · tutor · parent_copilot
dashboard · platform · lesson-plans
```

**Internal-only (no HTTP router):** `knowledge_graph` (consumed by curriculum, tutor, copilots) — intentional.

**Skeleton only:** `analytics` module — empty `endpoints/`, `schemas/`, `services/`; **not mounted in `main.py`**.

### Architecture version

Engineering dashboard reports **v2.6** (Batches 1–28 complete). Batch **29 — Infrastructure Readiness** in progress (reserved subdomains, runtime tenant slug, Dockerfile `[rag]` extra, deploy docs).

### Tenancy & security (verified patterns)

- `school_id` derived from `CurrentUser`, not client — enforced in services
- `CommitOnSuccessRoute` on all 21+ module routers (test-guarded)
- Aadhaar encryption at rest (`EncryptedString`)
- Fee payment idempotency, Decimal money, tenant isolation tests
- AI credits: row-locked ledger, school pool + per-user quotas

---

## 3. Feature status

Legend: **✅ Implemented & verified** · **🟡 Partial** (works but thin UI, stub integration, or integration_pending) · **📄 Documented only** · **🔭 Future vision**

### 3.1 Four intelligence pillars

| Pillar | Backend | UI | Verified | Notes |
|--------|---------|-----|----------|-------|
| **Curriculum Intelligence** | ✅ Packs, approval, ingest, Concept Cards, content review, RAG index/retrieve | ✅ `/dashboard/teaching/curriculum`, document ingest | tests_passing / build_passing | Moat is real; Reference School seeds approved Class 10 Maths pack |
| **Assessment Intelligence** | ✅ Grounded QP, question bank, rubric eval, answer-sheet OCR+grading, HITL | ✅ AI Papers, exams, evaluate, corrections, gradebook | tests_passing | Hero workflow; ~₹0.13/paper on gpt-4o-mini (documented) |
| **Learning Intelligence** | ✅ Mastery compute, flags, digest, student/parent copilots, tutor | 🟡 Mastery/digest/copilots exist but not in E2E smoke | tests_passing | Analytics module **not started** |
| **School Operations Intelligence** | ✅ Students, staff, fees, attendance, admissions, payroll, expenses, library, transport, residential | 🟡 Core ops wired; transport/residential/library **read-only or stub UI** | tests_passing / partial | Razorpay/online pay **rejected** ("coming soon") |

### 3.2 Shared AI platform

| Capability | Status |
|------------|--------|
| LLM gateway (OpenAI, Gemini, Anthropic, Ollama, stub) | ✅ |
| Embeddings (OpenAI + stub) | ✅ |
| Vector store (Qdrant + in-memory) | ✅ |
| RAG (index, retrieve, citations, hybrid + re-rank) | ✅ |
| AI credits & metering | ✅ |
| Document Intelligence (OCR → chunk → embed → index) | ✅ |
| Knowledge Graph (spine, question→concept, student→weak concept, graph queries) | ✅ service layer |

**Config reality:** Default LLM provider is `gemini`; embeddings use OpenAI `text-embedding-3-small`. Production provider choice remains an open business decision (DECISION_LOG D5).

### 3.3 SMS / ERP modules

| Module | API | Admin UI | Demo seed |
|--------|-----|----------|-----------|
| Students, classes, enrollment | ✅ | ✅ Students hub | ✅ ~288 students, Grades 1–10 |
| Staff & HR | ✅ | ✅ | ✅ Teachers, incharges |
| Attendance | ✅ | ✅ | ✅ |
| Fees (offline pay, receipts) | ✅ | ✅ Finance hub | ✅ |
| Exams & marks | ✅ | ✅ Teaching hub | ✅ |
| Timetable | ✅ | ✅ | ✅ |
| Notices | ✅ | ✅ | ✅ |
| Admissions pipeline | ✅ | ✅ Admissions tab | ✅ |
| Payroll / expenses | ✅ | ✅ Finance hub | ✅ |
| Library | ✅ issue/return API | 🟡 List only; import "coming soon" | ✅ |
| Transport | ✅ CRUD API | 🟡 Read-only list; **module off by default** | Optional seed |
| Residential | ✅ allocate API | 🟡 Partial; **module off by default** | Optional seed |
| Notifications | ✅ in-app | ✅ | 🟡 SMS/email/push = TODO in service |

### 3.4 Portals

| Portal | Status | Routes |
|--------|--------|--------|
| **School Admin / Principal** | ✅ Built | `/dashboard/*` |
| **Teacher** | ✅ Inside admin-web | `/dashboard/teaching/*`, teacher persona on dashboard |
| **Parent** | 🟡 Built inside admin-web | `/parent/*` — fees, notices, children, **Parent Copilot** on child page |
| **Student** | 🟡 Built inside admin-web | `/student/*` — tutor, mastery, notices |
| **Platform operator** | 🔧 Engineering status only | `/dashboard/platform/engineering` |
| **Flutter mobile** | 📄 Planned | 0% — DECISION_LOG D4 deferred to tutor phase |

### 3.5 Documented but not implemented (or skeleton only)

- **Analytics module** — empty package, no routes
- **Online fee collection (Razorpay)** — explicitly rejected until signature-verified flow
- **External notification delivery** (SMS, email, FCM) — in-app only
- **Separate teacher-web / parent-web / platform-web apps** — vision in PRODUCT.md
- **Learning Analytics (Batch 30)** — deferred until Gate 1 exit
- **Smart Workbooks, marketplace, MCP agents** — PRODUCT.md future horizons
- **WeasyPrint PDF receipts** — HTML fallback today

---

## 4. Demo readiness

### 4.1 Reference School (canonical demo tenant)

**Defined in** `apps/api/scripts/reference_school_config.py` (uncommitted):

| Field | Value |
|-------|-------|
| Tenant slug | `reference` |
| School | ARM International School (SSC) |
| Password (all personas) | `Demo@1234` |
| Principal | `principal` |
| Class 10 incharge | `teacher1` |
| Maths teacher | `teacher6` |
| Parent | `parent_demo` |
| Student | `student_demo` |

**Seed chain:** `seed_reference_school.py` → idempotent chain of 9 scripts + curriculum pack + tutor misconception. **Uncommitted but present in working tree.**

**Smoke:** `smoke_demo_readiness.py` (updated for `reference` tenant) + new `smoke_reference_school.py` — hits principal login + all page-load APIs. E2E: `apps/admin-web/e2e-smoke.cjs` covers 11 staff pages + report card flow + student tutor.

**Runbook:** `docs/showcase/DEMO_V1_SCRIPT.md` (uncommitted) — 45–60 min "day in the life" narrative aligned to intelligence pillars.

### 4.2 Gate 1 status

| Sub-gate | Goal | Status |
|----------|------|--------|
| **1A — Demo Online** | HTTPS URL, login, seed, AI, smokes 100% | ⬜ **Blocked on cloud credentials** |
| **1B — Demo Reliable** | Fallbacks, polish, teacher/parent E2E, reliability targets | 🟡 Partial locally |
| **Gate 1 EXIT** | Principal demo + no critical issues | ⬜ Not done |

**Localhost demo:** Ready *after* running migrations + `seed_reference_school.py` + Docker stack (Postgres, Redis, Qdrant) + valid `GEMINI_API_KEY` (or fallback provider).

**HTTPS demo:** Not available. Batch 29 infra readiness in progress.

### 4.3 If a school principal came tomorrow — honest demo script

**What we can demonstrate credibly (localhost or deployed, with seed + AI key):**

1. **Principal morning briefing** — Dashboard with live student count, attendance rollup, fee stats, notices
2. **School operations** — Students, staff, classes, attendance, timetable, finance (fees/payroll/expenses), admissions pipeline, settings
3. **Curriculum moat** — Approved CurriculumPack for Class 10 Maths; curriculum management UI; document ingest path
4. **Teacher AI wedge** — Generate grounded question paper → review with citations → approve; lesson plans with pack grounding; Teacher Copilot QP review panel
5. **Exam loop** — Exams list, gradebook, report cards with AI-drafted remarks (HITL approve)
6. **Assessment depth** — Answer-sheet upload → async vision OCR → AI-suggested marks with rubric breakdown → teacher approve (needs prepared sheet + time)
7. **Learning loop** — Topic mastery flags, mastery digest, Mistake Recovery Tutor (student portal), Student Copilot ask
8. **Parent experience** — Parent portal: child progress, fees, notices; **Parent Copilot** Q&A on child page
9. **Trust signals** — Human-in-the-loop approvals, AI usage/credits visible, engineering dashboard for platform depth (admin only)

**What we should NOT claim or demo as production-ready:**

- Online fee payments / Razorpay
- SMS, email, or push notifications to parents
- Native mobile apps (Flutter)
- Full transport/residential/hostel operations (API exists; UI thin; modules often disabled)
- Library circulation (issue/return) — API only
- Learning analytics dashboards (Batch 30 not started)
- Multi-school platform operator console (beyond engineering status page)
- Guaranteed AI quality without live key and Qdrant indexing

**Recommended demo duration:** 45–60 minutes using `DEMO_V1_SCRIPT.md` narrative (curriculum-first story, not feature tour).

---

## 5. Technical debt

| Area | Severity | Detail |
|------|----------|--------|
| **Doc drift** | Medium | STATUS.md, platform.json commit hash, GATE1 seed script name out of sync |
| **Uncommitted demo assets** | High for GTM | Reference School seed/smoke/runbooks exist only in working tree |
| **Local full pytest flakiness** | Low | asyncpg event-loop contention; CI and isolated runs green |
| **Lint backlog** | Low | ruff/eslint report-only by ARM decision |
| **Notifications delivery** | Medium | In-app works; external channels stubbed |
| **Online payments** | Medium | Intentionally deferred pre-revenue |
| **Azure Blob vs local disk** | Low | Files module supports Azure; local disk in dev |
| **AI provider split** | Low | Gemini default LLM, OpenAI embeddings — needs demo env clarity |
| **Module toggles** | Low | Transport/residential hidden until `enabled_modules` set |
| **Empty analytics module** | Low | Dead skeleton; remove or implement after Gate 1 |

No open **Sev-1** issues identified in recent engineering batches (fee self-clearing closed Batch 1).

---

## 6. Missing integrations

| Integration | Status | Impact on demo |
|-------------|--------|----------------|
| **HTTPS deploy (Cloudflare + Azure)** | Not done | Cannot send a link to principal |
| **Razorpay** | Not integrated | Offline fee recording only |
| **MSG91 / SendGrid** | Stubbed in notifications | No SMS/email in demo |
| **FCM push** | Not built | No mobile push |
| **Azure Blob (prod files)** | Config-ready | Local disk sufficient for demo |
| **Production LLM benchmark lock** | Open decision | Demo needs working API key + fallback plan |
| **Ollama (self-host fallback)** | Adapter exists | Optional for cost/residency |
| **Real OTP SMS** | Stub/dev | Password login sufficient for demo |

---

## 7. Unused work — hidden value in the codebase

Features **implemented and tested** but **under-exposed** (quick wins for demo polish):

| Capability | Backend | UI exposure | Smoke covered? |
|------------|---------|-------------|----------------|
| **Parent Copilot** | `POST /api/v1/parent-copilot/*` | `/parent/child/[id]` — no bottom-nav tab | ❌ |
| **Student Copilot** | `/api/v1/tutor/copilot/*` | Student portal | ❌ |
| **Curriculum RAG search** | `GET .../curriculum/packs/{id}/rag/search` | No UI | ❌ |
| **Mastery heatmap** | `GET /api/v1/mastery/classes/{id}/heatmap` | No UI | ❌ |
| **Mastery recompute** | `POST /api/v1/mastery/recompute` | No UI | ❌ |
| **Exam corrections workflow** | Full API | Linked from exams/evaluate, **not in Teaching hub tabs** | ❌ |
| **Mastery digest** | API + page | Button from mastery page, **not in hub nav** | ❌ |
| **Teacher copilot feedback draft** | `POST /api/v1/ai/copilot/feedback-draft` | No UI | ❌ |
| **AI credit override / school report** | Admin API | No UI (principal emergency override) | ❌ |
| **Document ingest** | Full pipeline | Teaching hub tab | ❌ |
| **Content Review Queue** | API + tests | Inside curriculum UI | ❌ |
| **Library issue/return** | POST endpoints | Disabled "coming soon" | ❌ |
| **Transport assign / route CRUD** | POST endpoints | Read-only page | ❌ |
| **Residential allocate** | POST endpoint | Partial UI | ❌ |
| **Portal features teaser** | `GET /portal/features` | `/demo/roadmap` only | ❌ |

**Seed data not wired to default demo path:**

- `seed_pilot_naagarjuna.py` — minimal pilot tenant (superseded by Reference School for showcase)
- `seed_synthetic.py` — 3-school load test data
- `seed_transport.py`, `seed_residential.py` — require manual run + module flags
- Legacy `test` / `naagarjuna` tenant slugs documented as deprecated in `reference_school_config.py`

**Duplicate / dead patterns:**

- `seed_demo_e2e_journey.py` — deprecated wrapper pointing to reference school chain
- `analytics` module — empty placeholder directories
- `/teacher` route — redirects to `/dashboard` (legacy)
- Multiple legacy dashboard URL redirects (bookmarks preserved — not harmful)

**Estimate:** ~15–20% of backend surface area has **no admin-web consumer**; much of it is admin/diagnostic or ops-complete-but-UI-thin.

---

## 8. Shortest path to a compelling Reference School demonstration

### Phase A — Local Demo v1 (1–2 days, no new features)

Priority is **activation**, not construction.

1. **Commit Reference School assets** — `reference_school_config.py`, `seed_reference_school.py`, curriculum seed, smokes, showcase docs (currently uncommitted)
2. **Run validation** — `alembic upgrade head` → `seed_reference_school.py` → `smoke_reference_school.py` → `e2e-smoke.cjs` with `NEXT_PUBLIC_TENANT_SLUG=reference`
3. **Configure AI** — `GEMINI_API_KEY` (or OpenAI) + Qdrant up; run one live QP generation to confirm grounding
4. **Enable demo modules** — Set `enabled_modules.transport/residential` in seed or settings if those screens matter for the narrative
5. **Rehearse** — Follow `docs/showcase/DEMO_V1_SCRIPT.md` once end-to-end; note any 500s or empty states
6. **Prepare backup** — Pre-approved QP + report card in DB if live AI fails (Gate 1B requirement)

### Phase B — Demo Online / Gate 1A (3–5 days, blocked on credentials)

1. Complete **Batch 29** infra (runtime tenant slug, Dockerfile `[rag]` extra, deploy docs)
2. Deploy API + web with production env vars
3. Seed **reference** tenant on demo DB
4. Run smokes against **public URL** (not localhost)
5. Document login card in operator runbook (no secrets in git)

### Phase C — Demo Reliable / Gate 1B (3–5 days)

1. Add parent + teacher flows to E2E smoke
2. AI fallback coverage for QP, report card, copilot ask
3. Nav polish: Parent Copilot discoverability, corrections/digest in Teaching hub (optional, low code)
4. Hit reliability targets in GATE1_EXECUTION.md

**Explicitly defer:** Batch 30 Learning Analytics, analytics module, Flutter, Razorpay, new pillars — until Gate 1 exit.

---

## 9. Recommended priorities (for owner confirmation — not started)

These are **recommended defaults** pending your review. **No implementation will begin until you confirm.**

| Priority | Action | Rationale | Effort |
|----------|--------|-----------|--------|
| **P0** | Commit + validate Reference School seed/smoke/runbook | Unblocks any demo; work already done | S |
| **P0** | Gate 1A HTTPS deploy (when credentials available) | Principal needs a URL, not localhost | M (blocked) |
| **P1** | Rehearse Demo v1 script; fix only demo-breaking bugs | Confidence before external eyes | S |
| **P1** | Sync stale docs (STATUS, platform.json, GATE1 seed name) | Reduces agent/operator confusion | S |
| **P2** | E2E smoke: parent copilot + curriculum + evaluate path | Covers highest differentiators | M |
| **P2** | UI discoverability: Parent Copilot nav, Teaching hub tabs for corrections/digest | Surfaces existing value | S |
| **P3** | AI fallback / pre-seeded backup artifacts | Gate 1B reliability | M |
| **Defer** | Analytics module, Batch 30, mobile, payments, notification delivery | Post Gate 1 exit | — |

---

## 10. Doc vs implementation — key mismatches

| Claim (docs) | Reality (code) |
|--------------|----------------|
| "340 tests passing" | Last verified 2026-07-15; not re-run today; local full suite can be flaky |
| "Batch 16 Document Intelligence uncommitted" | Committed in later batches; STATUS.md stale |
| "~152 endpoints" | ~182 route handlers counted in endpoints |
| "Demo seed: seed_demo_e2e_journey.py" | Deprecated; use `seed_reference_school.py` |
| "Four of five portals don't exist" | Still true for *separate apps*; parent/student/teacher exist **inside admin-web** |
| "Curriculum Intelligence ~75%" | Backend+UI largely complete; RAG search UI missing |
| "Flutter 0%" | Accurate |
| "Gate 1A in progress" | Infra batch started; HTTPS still blocked |

---

## 11. Product vision (condensed)

**What StudyNexs is:** An AI-first school operating system for Indian K-12 — not a generic ERP with chat bolted on. The moat is **board-grounded Curriculum Intelligence** feeding Assessment, Learning, and Operations — always **human-in-the-loop** for authoritative output.

**Current business milestone:** Gate 1 — Demo Ready (1A Online → 1B Reliable → principal demo → stop polishing).

**Product Execution Phase:** Platform is "stable infrastructure"; new work should deliver **educational capability** consuming existing architecture (`PRODUCT_EXECUTION_CONSTITUTION.md` v1.0).

**North Star:** Teachers save time, students learn better, parents stay informed, administrators decide better — AI fades into the workflow.

---

## 12. Assessment conclusion

StudyNexs is **past the "does it work?" phase** for its core wedge: curriculum-grounded AI papers, exam/evaluation assist, mastery, and multi-portal experiences. The gap is not primarily **missing features** — it is **demo packaging, deployment, and surfacing hidden capability**.

The repository contains enough implemented value to run a **credible 45–60 minute Reference School demonstration today on localhost**, and a **shareable HTTPS demo** as soon as Gate 1A deploy credentials land — provided Reference School seeds are committed and validated.

---

**Next step:** Owner reviews this assessment → confirms priorities → then issue **"Build Demo v1"** instruction. No code changes should proceed before that confirmation.

---

*Assessment produced per Phase 1–3 handover protocol. Implementation source of truth: codebase + tests. Policy source of truth: `/CLAUDE.md`.*
