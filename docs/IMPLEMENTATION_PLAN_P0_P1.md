# StudyNexs — Phase 0 + Phase 1 Implementation Plan

> **⚠️ SUPERSEDED (2026-06-15)** — Do not edit. Use [PRODUCT.md](./PRODUCT.md) + [STATUS.md](./STATUS.md) instead.

> Owner: Avinash Reddy Masapeta (ARM) · Status: **DRAFT v0.1** · 2026-05-31
> Derives from [MASTER_PLAN.md](./MASTER_PLAN.md). Phase 1 flagship = **Teacher AI on web**.

---

## 0. Assumptions & decisions (override any before I build)

| # | Decision | Status |
|---|----------|--------|
| 1 | **Evolve** the existing FastAPI + Next.js core; solo build; target a thin pilot in weeks. | ✅ confirmed |
| 2 | **Provider-agnostic LLM gateway**; benchmark Gemini/Claude/OpenAI on real Phase-1 tasks; **no provider committed yet**. | ✅ confirmed (option B) |
| 3 | Keep **PostgreSQL** (no MongoDB). | default — say if wrong |
| 4 | **Defer UI-library** decision; Phase-1 UI reuses existing admin-web styling. | default |
| 5 | Async job queue = **Arq** (Redis-backed; Redis already in stack). | default |
| 6 | Phase-1 web surface = **reuse admin-web**, role-gated to `teacher`/`class_incharge`/`admin` (separate teacher portal deferred). | default |
| 7 | **Pilot grade range + board** (drives demo data + prompt context). Assuming **CBSE**, grades present in seed (1–8). | ⚠️ TO CONFIRM |
| 8 | **Subjective grading in P1** as teacher-approved *suggestions* (human gate de-risks it), vs. defer to P1.5. | ⚠️ TO CONFIRM (I lean: include in P1) |

---

## Phase 0 — Foundation & AI platform primitives (prereq for P1)

Goal: fix the compliance-critical bugs and stand up the minimum AI plumbing. Each task lists target files + acceptance.

### 0.1 Fix audit logging (compliance-critical) 🐞
- **Problem:** `app/core/audit_middleware.py` passes `user_agent=` to `AuditLog`, which has no such column → every prod audit write throws (swallowed) → **no audit rows persist**.
- **Fix:** add a `user_agent` column to `AuditLog` (useful for compliance) via a new Alembic migration; keep the middleware. Also capture `resource_id` where available.
- **Files:** `app/db/models/audit.py`, `alembic/versions/<new>.py`, (verify) `app/core/audit_middleware.py`.
- **Acceptance:** a mutating request in a non-test run inserts an audit row incl. user_agent; add a regression test that exercises the middleware path.

### 0.2 Fix money handling 🐞
- **Problem:** `fee_service.process_payment` casts `Decimal → float` before persisting to `Numeric(10,2)`.
- **Fix:** keep `Decimal` end-to-end (`amount_paid`, `paid_amount`).
- **Files:** `app/modules/fees/services/fee_service.py`. **Acceptance:** existing fee test still green; values stored as exact Decimal.

### 0.3 Async job queue (Arq)
- Add Arq worker + a `jobs` table (`id, school_id, type, status[queued/running/done/failed], params JSONB, result JSONB, error, created_at, updated_at`) for status the UI can poll.
- **Files:** `app/core/jobs/` (arq settings, enqueue helper, worker entrypoint), `app/db/models/job.py`, migration; wire worker into Docker (`docker-compose.dev.yml`) and/or a `python -m app.core.jobs.worker` entrypoint. Optionally retire the dead outbox later (out of scope now).
- **Acceptance:** enqueue a trivial job, worker runs it, status + result persist; one integration test.

### 0.4 LLM Gateway (provider-agnostic) + metering + feedback
- **Interface:** `LLMProvider.generate(messages, *, model, response_schema=None, **opts) -> LLMResult{text, json, tokens_in, tokens_out, model, provider, latency_ms}`.
- **Adapters:** Gemini, Anthropic (Claude), OpenAI — each behind the same interface, selected by config; only the ones with API keys present are active (others raise a clear "no key" error). Centralized: timeouts, retries/backoff, structured logging, **token + cost accounting**, optional JSON-schema-constrained output.
- **Metering:** `ai_usage` table (`school_id, feature, provider, model, tokens_in, tokens_out, cost_usd, latency_ms, created_at`).
- **Feedback:** `ai_feedback` table (`school_id, feature, ref_id, rating[up/down], note, user_id, created_at`) for quality tracking from day 1.
- **Semantic cache:** define the interface (Qdrant-backed) but implementation can wait until volume matters.
- **Config/env:** `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `AI_DEFAULT_PROVIDER`, `AI_DEFAULT_MODEL` (+ production guardrails).
- **Files:** new `app/modules/ai/gateway/` (`base.py`, `gemini.py`, `anthropic.py`, `openai.py`, `factory.py`, `metering.py`), models + migration, `app/core/config.py`.
- **Acceptance:** unit test drives the gateway with a fake "echo" provider; a live smoke test per configured provider records a row in `ai_usage`.

### 0.5 `ai` module skeleton
- Flesh out the empty `app/modules/ai/` with `endpoints/`, `schemas/`, `services/`; mount router at `/api/v1/ai` in `app/main.py`.
- **Acceptance:** `GET /api/v1/ai/health` (or similar) returns ok; router wired; no regressions to existing tests.

---

## Phase 1 — Teacher AI on web (the pilot flagship)

All three features run as **Arq jobs through the gateway**, are **metered + feedback-enabled**, gated to `teacher`/`class_incharge`/`admin`, scoped via `TenantScope`, and **human-approved before anything leaves the teacher**.

### 1A. Auto question-paper generation (difficulty-based)
- **Data:** `question_paper` (`id, school_id, class_id, subject_id, created_by, title, status[draft/approved], total_marks, difficulty_mix JSONB, topics JSONB, questions JSONB[{text,type,marks,options?,answer_key?}], created_at`) + migration.
- **Flow:** `POST /ai/question-papers/generate` (enqueue job; inputs: class, subject, topics/syllabus text, total marks, difficulty mix) → `GET /ai/jobs/{id}` poll → draft → `PUT` edit → `POST approve` → `GET export` (PDF; reuse the WeasyPrint/HTML approach already in `fees/services/receipt_pdf.py`).
- **Service:** build prompt → gateway (JSON-schema output) → validate/persist draft. Optional syllabus grounding deferred (P1 generates from topic list; RAG grounding = P1.5/P2).
- **Acceptance:** generate a paper for a real class+subject in < ~2 min, edit, approve, export PDF; usage metered.

### 1B. AI-assisted grading (human-in-the-loop)
- **Objective:** given exam + answer key + student responses → auto-score → write `exam_marks` (`marks_obtained`).
- **Subjective (pending decision #8):** AI proposes `marks_obtained` + `ai_feedback` → teacher reviews/edits/approves → only on approval persist with `ai_graded=true`. (Reuses the existing `ExamMark.ai_feedback` / `ai_graded` columns.)
- **Endpoints:** `POST /ai/grading/objective`, `POST /ai/grading/subjective/suggest`, `POST /ai/grading/approve`.
- **Acceptance:** objective auto-grade matches a key; subjective suggestions are editable and persist only on approval; nothing visible outside teacher (no parent/student portal in P1).

### 1C. 1-click student summary report
- **Data:** light `ai_report` (`id, school_id, student_id, type, content, status[draft/approved], created_by, created_at`).
- **Flow:** `POST /ai/students/{id}/summary` (job) → narrative from existing marks + attendance → teacher reviews before any share/export. `assert_can_access_student` enforced.
- **Acceptance:** returns a coherent, reviewable summary grounded in the student's real data; metered.

### Phase-1 UI (admin-web, role-gated)
- New "AI Tools" area: **Question Paper Generator**, **Grading Assistant**, **Student Summary** — each with a job-progress state and an approve/edit step + thumbs up/down feedback control.
- ⚠️ Frontend is **Next.js 16** — per `apps/admin-web/AGENTS.md`, consult `node_modules/next/dist/docs/` before writing components (APIs differ from older Next).

---

## Cost / provider benchmark (the deliverable I owe — option B)
Run **after 0.4** (gateway exists) so we measure real calls:
1. Build a small representative prompt+input set for each Phase-1 task (paper gen, objective grade, subjective grade, summary).
2. Run each through **Gemini 1.5 Flash & Pro**, **Claude Haiku & Sonnet**, **OpenAI** candidates.
3. Capture tokens, latency, $/call, and a small **quality eval** (rubric scoring of outputs).
4. Project **cost per teacher-action** → **per-student/month** at pilot + 10-school scale.
5. Recommendation + the provider/model routing default. → You decide.

---

## Sequencing (solo; weeks — realistic, will flex)
- **W1:** Phase 0 (audit fix, money fix, Arq, gateway + 3 adapters, metering, `ai` skeleton).
- **W2:** Feature 1A end-to-end + minimal UI; run first benchmark on paper-gen.
- **W3:** Features 1B + 1C + UI; complete the benchmark; metering dashboards.
- **Then:** pilot hardening (DPDP consent basics, AI-transparency labels), demo data for the pilot school.
- *Caveat:* 3 weeks solo is aggressive; 1B subjective or RAG grounding are the first things to defer if time is tight.

## Risks & open items
- Decisions #7 (grade/board) and #8 (subjective in P1) — please settle.
- Provider **API keys** must be available to run the benchmark.
- PDF export quality (WeasyPrint already a dependency — reuse).
- Next 16 frontend caveat (above).
- Keep human-approval gates strict — no AI grade/summary leaves the teacher in P1.

## Definition of done (pilot-ready)
A teacher at the pilot school can, inside the web app: generate & export a question paper; auto-grade objective + get approve-gated subjective suggestions; one-click a student summary — all metered, feedback-enabled, within existing auth/tenant isolation, with no regression to the current test suite, and with audit logging actually persisting.

---

## Phase 0 — BUILD STATUS (2026-05-31)

**Implemented on branch `phase-0-foundation`** (verified offline: ruff-clean, app imports without provider SDKs/arq, `/api/v1/ai/health` registered, audit regression test passes):
- **0.1** `audit_logs.user_agent` column (`app/db/models/audit.py`) + migration `c3a1f0d2e4b6` + regression test `tests/test_audit.py`.
- **0.2** Decimal-safe money in `app/modules/fees/services/fee_service.py`.
- **0.3** Arq queue: `app/db/models/job.py` (+migration `e7b9c1d3f5a2`), `app/core/jobs/{queue,worker}.py` (lazy arq imports).
- **0.4** LLM gateway: `app/modules/ai/gateway/{base,factory,pricing,metering,gemini,anthropic,openai}.py` + `ai_usage`/`ai_feedback` models (+migration `f1c3a5b7d9e0`) + config keys. `arq` + `[ai]` extra (anthropic/openai/google-genai) added to `pyproject.toml`.
- **0.5** `app/modules/ai/endpoints/ai.py` (`GET /ai/health`, admin-only) mounted at `/api/v1/ai`.

### ⚠️ Cannot be verified without infra — OWNER must run (Docker was down this session)
```bash
# 1. Recreate local DB under the new 'studynexs' name/user (also covers the rename)
docker compose -f infra/docker/docker-compose.dev.yml down -v
docker compose -f infra/docker/docker-compose.dev.yml up -d

# 2. Reinstall deps (gets arq + provider SDKs; regenerates egg-info)
cd apps/api && pip install -e ".[dev,ai]"

# 3. Apply migrations (audit user_agent, jobs, ai_usage/ai_feedback)
alembic upgrade head

# 4. Run the test suite (needs Postgres up)
python create_test_db.py && pytest -q

# 5. Run the Arq worker (separate terminal; needs Redis up)
arq app.core.jobs.worker.WorkerSettings

# 6. (When benchmarking) set GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY in .env,
#    then smoke-test each adapter — google-genai/anthropic/openai SDK call shapes need a live check.
```

### Known caveats to validate
- Provider adapter SDK call shapes (esp. `google-genai`) are written to spec but **need a live smoke test** — they couldn't be exercised offline.
- `enqueue` flushes the Job row then enqueues; `run_job` raises (→ Arq retry) if the row isn't committed yet — fine for dev, revisit if races appear.
- Pre-existing lint in `fee_service.get_fee_stats` and `db/models/__init__.py` was left untouched (predates this work) to keep diffs focused.
