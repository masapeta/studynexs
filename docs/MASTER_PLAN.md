# StudyNexs — Master Plan

> Single source of truth for the AI-native School Management product.
> Status: **DRAFT v0.1** · Last updated: 2026-05-31 · Owner: Avinash Reddy Masapeta (ARM)
> This is a living document — expect changes as development progresses.

---

## 1. Vision & Business Model

**StudyNexs** is an AI-native School Management System (SMS) for the Indian K-12 market, sold on **subscription to both schools and parents**. Every SMS module is paired with an AI capability that *assesses, predicts, or automates*. The product's eventual centerpiece is an interactive **AI Tutor Bot** (text → voice → image → video) plus structured teacher↔parent↔student communication.

- **Who pays:** schools (per-school/per-seat) and parents (per-child tiers).
- **Market:** India first — multilingual, board-aligned (CBSE/ICSE/State, NEP 2020), low-bandwidth and compliance-sensitive (minors' data).
- **Moat:** the AI layer + the structured pedagogy data that accrues over time (doubt memory, skill-gap history, per-student learning paths).

## 2. Guiding Principles

1. **Evolve, don't restart.** Build on the existing, proven multi-tenant FastAPI core; add AI as additive layers. (Decision 2026-05-31.)
2. **Provider-agnostic AI.** All LLM access goes through one internal gateway; no vendor lock-in. Pick provider(s) *after* a unit-economics cost analysis.
3. **Human-in-the-loop for anything consequential.** AI grades, risk flags, and reports are *suggestions a human approves* before a student/parent sees them. Protects against liability and false labeling of children.
4. **Security & compliance first.** Multi-tenant isolation is sacred; DPDP/children's-data compliance is a Phase-0 concern, not an afterthought.
5. **Cost-aware by design.** Model routing + semantic caching + per-tenant token budgets, because AI cost is the subscription margin.
6. **Ship thin, real slices.** Solo builder + weeks-to-pilot ⇒ one flagship at a time, each genuinely usable.
7. **Mobile = Flutter**, introduced when the tutor bot phase begins (not Phase 1).

## 3. Current State (what we're building on)

**Reused as-is (the valuable foundation):**
- Multi-tenant isolation (`school_id` + composite uniques + tenant middleware + post-login school match).
- Auth/session: access-token-in-memory + HttpOnly refresh cookie, rotation, reuse detection, blacklist, OTP, 3-layer rate limiting (WAF → Nginx → Redis).
- Fee payment concurrency (atomic receipt counter, idempotency, partial pay, immutable snapshots).
- Data model (schools, users/roles, students, parents, classes, subjects, exams, **exam_marks with `ai_feedback`/`ai_graded`**, attendance, fees, notices, etc.), Alembic migrations, Docker/Nginx/Azure-WAF infra, ~28 tests.
- Next.js admin web (Dashboard, Students, Staff, Classes, Attendance, Finance, Notices wired).

**Must fix in Phase 0 (known issues):**
- 🐞 **Audit logging is broken in production** — `audit_middleware` passes a non-existent `user_agent` column to `AuditLog`; no audit rows are written. Compliance-critical, fix first.
- 🐞 **Outbox/event system is dead code** — `emit_event()` never called; handlers only log. Replace with a real async job system (we need one for AI anyway).
- 🐞 Money cast `Decimal→float` in `fee_service` before persisting to `Numeric(10,2)`.
- Notifications not school-scoped (defense-in-depth).

**Not yet built (becomes roadmap):** 4 of 5 portals, mobile app, any AI, realtime chat, billing automation, `ai`/`analytics` modules (empty).

## 4. Target Architecture (the evolution)

```
                 ┌─────────────────────────────────────────────────────────┐
 Clients         │  Next.js web (admin/teacher)   Flutter app (P2+)         │
                 └───────────────┬─────────────────────────────────────────┘
                                 │  HTTPS (Azure Front Door + WAF → Nginx)
                 ┌───────────────▼─────────────────────────────────────────┐
 API (FastAPI)   │  Auth · Tenant · RBAC · existing SMS modules             │
                 │  + NEW: ai/ module (endpoints + services)                │
                 └───┬───────────────┬───────────────┬─────────────────────┘
                     │               │               │
        ┌────────────▼───┐  ┌────────▼────────┐  ┌───▼──────────────┐
        │ LLM Gateway    │  │ Async Job Queue │  │ RAG / Vector     │
        │ (provider-     │  │ (Redis-backed   │  │ (Qdrant — already│
        │  agnostic,     │  │  workers; AI    │  │  in infra)       │
        │  cost-metered, │  │  generation,    │  │                  │
        │  cached)       │  │  grading jobs)  │  │                  │
        └───────┬────────┘  └─────────────────┘  └──────────────────┘
                │
   ┌────────────▼─────────────┐   Cross-cutting (all phases):
   │ Anthropic / OpenAI /     │   • AI usage metering (tokens, cost/school)
   │ open-source (pluggable)  │   • Eval + feedback capture (thumbs up/down)
   └──────────────────────────┘   • Object storage (media: P2+)  • Realtime (chat: P3+)
```

**New platform primitives** (built incrementally, starting in Phase 0/1):
- **LLM Gateway** — one internal interface; pluggable providers; centralized prompts, retries, timeouts, token/cost logging, semantic cache (Qdrant), per-tenant budget guards.
- **Async Job Queue** — Redis-backed worker (recommend **Arq**: async, lightweight, already have Redis). Replaces the dead outbox for AI generation/grading and future notifications. *Decision to confirm.*
- **RAG pipeline** — curriculum/syllabus ingestion → embeddings → Qdrant, per-tenant namespaces (no cross-school leakage). Needed for tutor (P2) and optionally question-paper grounding (P1).
- **AI metering + eval** — every LLM call logged with tokens/cost/latency + a feedback hook; foundation for the cost analysis and quality improvement.

## 5. Feature Catalog → Phase Map

| Capability | Phase | Notes |
|---|---|---|
| **Teacher AI: question-paper gen, assisted grading, student summary** | **P1 (pilot)** | Web; reuses exam data |
| Foundation hardening + LLM gateway + job queue + metering | **P0** | Prereq for everything |
| Student Text Tutor (RAG) + Flutter app shell | P2 | Tutor phase 1; mobile begins |
| Parent Intelligence dashboard + weekly auto reports | P2/P3 | Parents are paying users |
| Risk & early-warning alerts (fail/attendance/behavior) | P3 | Human-reviewed before parent-facing |
| Structured 1:1 chat (student×parent×subject-teacher threads) + realtime | P3 | Not group chat — isolated threads |
| Personalized learning engine (adaptive plans, recommendations) | P3/P4 | |
| Voice Tutor (STT/TTS/translate) | P4 | Indian-language (AI4Bharat/Bhashini) |
| Gamification (XP, leaderboards, badges, skill tree) | P4 | |
| Vision & Video Tutor | P5 | Multimodal |
| AI School Brain (admin predictive/optimization), smart scheduling, buffer-teacher auto-assign | P5+ | |
| Plagiarism / AI-content "signals" (NOT verdicts), peer benchmarking, emotion recognition | P5+ | Treat detectors as advisory only |
| Subscription billing automation, self-serve onboarding, platform-operator console | Parallel track | When monetizing beyond pilot |
| Multi-language UI, offline/low-bandwidth, SMS/WhatsApp parent fallback | Parallel track | India go-to-market |

## 6. Phase 0 — Foundation Hardening (prereq, ~days)

Minimal, only what Phase 1 needs + the compliance-critical bugs:
1. Fix the **audit logging** bug (drop/match `user_agent`); add a migration if we want the column. Verify rows persist.
2. Stand up the **LLM Gateway** service (provider-agnostic interface, env-driven provider/model, token+cost logging, timeout/retry, basic semantic cache).
3. Stand up the **async job queue** (Arq worker) + a `jobs` table for status; retire the dead outbox or fold it in.
4. **AI metering** table (per call: school_id, feature, provider, model, tokens_in/out, cost, latency) + **feedback** capture.
5. Fix money `Decimal` handling (quick).

**Acceptance:** an LLM call can be made through the gateway from a background job, fully metered, with a unit test; audit rows persist in a non-test run.

## 7. Phase 1 — Pilot MVP: Teacher AI on Web (the "weeks" slice)

**Goal:** a real teacher at a pilot school saves hours using three AI tools inside the existing web app. Everything is human-approved before it leaves the teacher's hands.

### 7A. Auto question-paper generation (difficulty-based)
- Teacher selects class + subject + topics/syllabus + total marks + difficulty mix → AI drafts a paper (sections, question types, mark allocation) → teacher edits/approves → export PDF.
- New: a lightweight `question_paper` entity (draft/approved, JSONB questions). Optional RAG grounding on uploaded syllabus.

### 7B. AI-assisted grading (human-in-the-loop)
- **Objective:** auto-grade against an answer key.
- **Subjective:** AI proposes marks + written feedback → teacher reviews/edits/approves. Writes to existing `exam_marks` (`marks_obtained`, `grade_letter`, `ai_feedback`, `ai_graded=true` only after approval).
- Nothing is visible to students/parents in P1 (no parent portal yet) — output stays teacher-side.

### 7C. 1-click student summary report
- From existing marks + attendance, AI generates a coherent narrative ("strong in X, needs work on Y, attendance trend Z") → teacher reviews before any sharing/export.

### Cross-cutting in P1
- Runs as **async jobs** through the gateway; UI shows progress.
- **Guardrails:** human approval on all outputs; "AI-generated, review before use" labels; PII minimization in prompts; prompt-injection hygiene on uploaded syllabus text.
- **Metering + feedback** on every generation.
- Reuses existing auth/RBAC/tenant isolation; teacher/admin roles only.

### Explicitly OUT of Phase 1
Mobile app, tutor bot, voice/vision, realtime chat, parent/student portals, gamification, predictive risk, billing automation, multi-language. All are later roadmap.

### Phase 1 acceptance criteria
- Teacher generates a class+subject question paper in < 2 min, edits, exports PDF.
- Objective auto-grading works against a key; subjective grading produces editable AI suggestions that persist only on approval.
- 1-click student summary returns a coherent, reviewable report.
- All AI calls metered (tokens/cost) and feedback-capturable.
- No regression to multi-tenant isolation or auth (tests green).

## 8. Phase 2+ Roadmap (sequenced, not scheduled)

P2: Flutter app shell + **Student Text Tutor (RAG, curriculum-grounded, child-safety guardrails, doubt memory)**; Parent dashboard + weekly auto reports.
P3: Structured 1:1 realtime chat; risk/early-warning (human-reviewed); personalized learning engine.
P4: Voice tutor (Indian languages); gamification.
P5+: Vision/video tutor; AI School Brain (predictive/optimization, smart scheduling, buffer-teacher auto-assign); advisory plagiarism/benchmarking/emotion features.
Parallel: subscription billing, self-serve onboarding, platform-operator console, multi-language, offline/low-bandwidth, SMS/WhatsApp parent fallback.

## 9. AI Cost & Provider Strategy

- Design **provider-agnostic** now (gateway). Decide provider(s) after a cost analysis.
- **Cost analysis I owe you:** per-feature token estimates × expected usage × price across candidate models → **cost per student / per school / per teacher-action** → informs subscription pricing and margin. Plus India **data-residency** comparison per provider. *Deliverable once we pick 2–3 candidate models to benchmark.*
- Levers baked into the gateway: model routing (cheap model first, escalate), semantic caching (Qdrant), per-tenant token budgets, batching.

## 10. Compliance & Security Plan

- **DPDP Act 2023:** verifiable parental consent for minors, consent artifacts/records, data-subject rights, breach notification, retention limits (esp. future chat/voice transcripts).
- **Data residency in India**; encryption at rest + in transit; field-level encryption for sensitive PII; key management.
- **Audit logging fixed** (P0) and tamper-evident.
- **AI transparency:** disclose AI involvement in grades/reports; human approval gate.
- **Child safety (from tutor phase):** content moderation, age-appropriate filters, no PII leakage, refusal behavior.
- **Multi-tenant AI isolation:** per-tenant RAG namespaces; never mix one school's data into another's context.

## 11. Risks & Open Questions

- **Solo + weeks is tight even for P1.** Mitigation: ruthless scope; subjective grading could slip to P1.5 if needed.
- **AI quality/hallucination** in grading/summaries → human-in-the-loop + eval harness from day 1.
- **Open decisions to confirm:** (a) job queue = Arq? (b) is subjective grading in P1 or P1.5? (c) RAG grounding for question papers in P1 or keep P1 ungrounded? (d) pilot school's board/curriculum + do we have its syllabus content? (e) which 2–3 models to benchmark for the cost analysis?

## 12. Immediate Next Steps (after you review this plan)

1. You review/adjust this Master Plan (especially §11 open decisions).
2. I write a detailed **Phase 0 + Phase 1 implementation plan** (file-level tasks, schema/migrations, endpoints, gateway design) for your approval.
3. We build Phase 0 (foundation) → Phase 1 (Teacher AI) → pilot.
4. In parallel, I produce the **AI cost analysis** once we pick candidate models.
