# StudyNexs — Build Status

> Owner: Avinash Reddy Masapeta (ARM) · **As of: 2026-06-15**  
> **What's true in the repo today.** Complete product definition: [PRODUCT.md](./PRODUCT.md).  
> **AI-intelligent OS roadmap:** [PRODUCT.md §23](./PRODUCT.md#23-ai-intelligent-school-os) · phase map below.

---

## Snapshot

- **SMS core + admin portal** are substantially built; backend APIs cover most school-ops modules.
- **IA consolidation (2026-06):** Finance, Students, and Teaching **module hubs** with tab nav; sidebar ~12 items; legacy URL redirects; Reports merged into dashboard analytics; `/teacher` → dashboard.
- **AI wedge is live in demo:** question paper generation (full + from-bank), report cards, answer-sheet vision eval, mastery narratives — proven end-to-end (~₹0.13/paper on OpenAI gpt-4o-mini).
- **AI hardening (2026-06):** input guards, eval rate limits, answer-sheet file access, metrics token gate, tutor lesson-key validation — see `apps/api/tests/test_ai_hardening.py`.
- **Exam loop (partial):** snap/upload → vision OCR → heuristic marks + HITL approve → corrections history; misconception library API exists.
- **Mistake Recovery Tutor (MVP):** template lessons + Azure/Web Speech TTS in `admin-web` student portal; recommendations from mastery + exam mistakes.
- **Lesson plans:** CRUD + **template-based** generation (`template-v1`) — **not LLM-grounded yet**; AI lesson plans are Phase **A-OS** below.
- **Topic mastery** module built (compute, flags, heatmap, digest, parent narratives on approve).
- **Pilot school** is interested; no signed deal yet. Demand and pricing not validated.
- **Binding constraint:** solo builder on branch `phase-0-foundation`. Scope discipline is survival.
- **Four of five planned portals** do not exist yet — student/parent experiences live inside `admin-web` (`/student`, `/parent`) until Flutter Phase 2.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Done — implemented and verified (tests and/or E2E smoke) |
| 🟡 | Built — works in demo; needs hardening, polish, or production wiring |
| 🔧 | Partial — backend or UI exists; other side missing or stubbed |
| ⬜ | Not started |
| 🔭 | Future / exploratory — do not build until validated |

---

## ✅ Completed & Verified

### Backend platform
- Multi-tenant isolation (`school_id` on all tenant tables; middleware + post-login school match)
- Auth: password + OTP, JWT access (in-memory) + HttpOnly refresh cookie, rotation, reuse detection, Redis blacklist
- RBAC with role assignment guards
- 3-layer rate limiting (WAF → Nginx → Redis); AI generate routes have additional caps
- ~**105 backend test functions** across `apps/api/tests/` (23 files) and `apps/api/tests_security/` (4 files)
- Alembic migrations (14 versions); ~30 entity models
- Audit logging (fixed — was silently broken in production)
- Fee payment idempotency (unique constraints on transaction/idempotency keys)
- Object-level authorization on fees + academic endpoints (`assert_can_access_student`, `require_roles`)
- Receipt HTML escaping; hardened Dockerfile + `.dockerignore`

### SMS modules (API)
- **users** — CRUD, `/me`
- **academic** — classes, subjects, students, enrollment, parents, profiles, teacher mappings
- **attendance** — bulk mark, class view, summaries
- **examinations** — exams CRUD, question schema, marks, class performance
- **fees** — stats, student fees, pay, atomic receipts, receipt HTML
- **timetable** — class/teacher slots CRUD
- **communications** — notices create/list/read
- **school-operations** — library, events, transport, residential
- **school** — profile, academic years
- **notifications** — in-app list, read, count
- **files** — upload/download (local disk)
- **mastery** — student profile, class heatmap, recompute, flags, digest, notify

### AI platform (Phase 0)
- Provider-agnostic LLM gateway (OpenAI, Anthropic, Gemini adapters)
- Usage metering (`ai_usage`) and feedback capture (`ai_feedback`)
- Async job infrastructure (Arq + `jobs` table) — **present but AI generation still runs synchronously on request thread**
- `/api/v1/ai/health`, `/api/v1/ai/usage`

### AI features (Phase 1)
- **Question paper generator** — generate, edit, approve (HITL), export; `generate-from-bank` compose mode; SSC Class 10 Maths verified (100 marks, 33 Qs)
- **Report card generator** — consolidate marks + attendance, AI-drafted remark, edit, approve (HITL), export
- **Mastery flag narratives** — LLM-generated parent-facing note on flag approval (teacher edits before send)
- **Answer-sheet evaluation v1** — upload image → vision OCR (async job) → heuristic objective grading + subjective assist → teacher HITL approve → marks committed; corrections history + misconception library API
- **AI input hardening** — bounded prompts, injection guards, per-route rate limits, scoped answer-sheet downloads

### Tutor & lesson plans (pre–CurriculumPack)
- **Mistake Recovery Tutor MVP** — recommendations from weak mastery + exam misconceptions; static lesson templates + step player; Azure Neural TTS with Web Speech fallback
- **Lesson plans** — CRUD under Teaching hub; `template-v1` structured output (**not** syllabus-grounded LLM yet)

### Admin web (`apps/admin-web`)
- **Module hubs:** `/dashboard/finance/*`, `/dashboard/students/*`, `/dashboard/teaching/*` with `ModuleHubNav`
- Wired pages: dashboard (+ embedded school analytics), students (+ detail, admissions, guardians), staff, classes, settings, attendance, exams (+ evaluate, corrections, question schema), timetable, finance hub (fees/payroll/expenses), notices, transport, residential, **AI Papers**, **Report Cards**, **Lesson Plans**, **Topic Mastery**, **Mastery Digest**
- Student portal: `/student/tutor`, `/student/mastery` (inside admin-web)
- Auth flow (login, refresh, logout)
- Playwright smoke script: `apps/admin-web/e2e-smoke.cjs`
- Demo readiness script: `apps/api/scripts/smoke_demo_readiness.py`

### Demo data
- Sri Saraswathi High School (SSC) seeded — 288 students, grades 1–10, with attendance + fees

---

## 🟡 Built — Needs Hardening

| Item | Gap |
|------|-----|
| Question paper generator | SSC blueprint approximate — verify against real sample paper; export is HTML print-to-PDF (WeasyPrint not wired) |
| Report cards | LLM remark path proven; needs pilot-school validation on tone/accuracy |
| Answer-sheet evaluation | Vision OCR live; subjective feedback still heuristic — pilot accuracy checklist; async Arq path works but ops tuning needed |
| AI generation | Synchronous on request thread for QP/report — should move heavy jobs to Arq queue for production load |
| Lesson plans | Template-only — **AI-grounded plans blocked on Layer 1 foundation** ([PRODUCT.md §23](./PRODUCT.md#23-ai-intelligent-school-os)) |
| Tutor MVP | Template lessons only — no Concept Cards / Content Review Queue / RAG yet |
| Exams / marks UI | Evaluate + corrections wired; needs pilot validation on real scans |
| Timetable UI | Wired to API; not yet feeding lesson-plan AI context |
| Finance UI | Fees/payroll/expenses under hub; payment UI still missing (API `POST /fees/pay` exists) |
| Notices UI | List works; "New Notice" button not wired to API |
| Mastery module | Built; needs real exam/slip-test data from pilot to prove value |
| IA / UX | Hub consolidation done; visual density pass ongoing — hard refresh after CSS changes |

---

## 🔧 Partial / Stub

| Area | Backend | Frontend | Notes |
|------|---------|----------|-------|
| **Library** | ✅ API | ⬜ static placeholder page | Not in sidebar nav |
| **Events** | ✅ API | ⬜ static placeholder page | Not in sidebar nav |
| **Fee payment UI** | ✅ API | ⬜ missing | Razorpay fields in model; no webhook/order flow |
| **File storage** | local disk only | — | Azure Blob config exists but unimplemented |
| **PDF export** | HTML bytes fallback | print-to-PDF | WeasyPrint not in dependencies |
| **Notifications delivery** | in-app only | — | SMS/email/push handlers are `pass  # TODO` |
| **Outbox worker** | emits events | — | Handlers log only; no real WhatsApp/SMS/email |
| **OTP in production** | dev logs OTP | — | MSG91 / SMS provider not wired |
| **Qdrant / RAG** | docker service + config | — | No application code uses vector store yet |
| **CI/CD** | — | — | No `.github/workflows` found |

---

## ⬜ Not Started (Prioritized)

### Immediate — pilot blockers
1. Close pilot school: written must-have checklist + willingness-to-pay (see [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md))
2. Harden question paper feature; verify SSC blueprint against real sample
3. Finish SMS UIs per pilot checklist (exams/marks, report cards flow, settings, fee payment UI if required)
4. DPDP basics before real student data: consent records, privacy notice, retention policy
5. AI unit-economics benchmark (Gemini vs Claude vs OpenAI on Phase 1 tasks)

### Phase 1.5 — CurriculumPack + exam loop (8-week plan above)
6. **`CurriculumPack` entity stack** — `BookEdition`, `CurriculumPack`, `CurriculumPackVersion`, `Chapter`, `Topic`, `Concept`, `LearningObjective`, `ConceptCard`, `SourceReference`, `ApprovalRecord`
7. **Content strategy** — structured curriculum only; TOC/syllabus ingestion; no full textbook warehouse; temporary uploads deduped + retention-limited
8. **AI-assisted pack onboarding** — white-glove pilot inputs → AI draft → HOD approve
9. **Annual Rollover Wizard** — duplicate → diff → approve (post-pilot)
10. **Wire QP + marking scheme to pack** — replace free-text `topics`; `QuestionItem` + `Rubric` per question
10b. **Question-level intelligence** — split papers → `QuestionBankItem`; bank ingest on approve ✅; generate-from-bank ✅ ([PRODUCT.md](./PRODUCT.md) §7.5)
10c. **Top 5 exam enhancements** — (1) question bank (2) blueprint intelligence (3) eval→question analytics (4) remedial packs (5) inspection/PTA pack ([PRODUCT.md](./PRODUCT.md) §7.6.13)
11. ~~**Answer sheet evaluation v1**~~ — **🟡 MVP shipped** (vision OCR + HITL); tighten against approved-paper-only policy + pack tags in Phase 1.5
12. **Weak-concept extraction** — deepen eval → mastery linkage (partial via misconceptions API)
13. ~~**Mistake Recovery Tutor MVP**~~ — **🟡 template tutor shipped**; upgrade to Concept Cards + `ContentReviewQueue` in Phase 1.5
14. **DPDP purpose tags** — on all student-touching events (`exam_evaluation`, `question_generation`, `ai_tutor`, etc.)
15. RAG embeddings per CurriculumPack (Qdrant)
16. WhatsApp alerts — deferred past 8-week plan unless pilot demands

### AI-Intelligent OS tracks (see [PRODUCT.md §23](./PRODUCT.md#23-ai-intelligent-school-os))

Runs **in parallel** with CurriculumPack — do not skip Layer 1.

| Track | Name | Product phase | Status | Depends on |
|-------|------|---------------|--------|------------|
| **A-OS** | Trust & context | Late Phase 1 → Phase 1.5 | ⬜ | Partial: mastery + eval data exist; **no CurriculumPack / coverage model yet** |
| **B-OS** | Close the loop | Phase 1.5 → 2 | 🟡 partial | QP↔mastery deep links ✅; bulk QP from heatmap, tutor assignments, subjective feedback LLM ⬜ |
| **C-OS** | Intelligent UX | Phase 2 → 3 | ⬜ | Suggestion cards, document inbox (classify + confirm), principal narrative |
| **D-OS** | Workflow orchestration | Phase 3+ | 🔭 | Post-exam loop agent, week-ahead planning agent — **only after A–B used daily** |

**A-OS deliverables (first AI-OS sprint after pilot gate):**
1. Curriculum graph (or interim: syllabus week + topic list per class/subject)
2. Academic calendar + “periods until exam” context
3. Coverage tracking (% taught vs assessed per topic)
4. Unified student/topic state view (mastery + last mistake + tutor usage)
5. **AI lesson plan v1** — structured JSON, 1 credit, HITL, links to QP + mastery flags

**Lesson plan AI minimum spec:** [PRODUCT.md §23.4](./PRODUCT.md#234-lesson-plan-ai--minimum-spec)

### Phase 2+
13. Flutter parent + student apps
14. Text AI tutor (RAG, child-safe, doubt memory)
15. Parent progress feed + online fee payment (Razorpay)
16. Structured teacher–parent chat
17. Principal co-pilot / institutional memory timeline UI

### Finance Command Center (optional paid module)

> **Sticky note:** Finance is a **deal-expander, not the wedge.** Management loves financial visibility — use it to close deals, not to distract engineering from the exam loop. Full spec: [PRODUCT.md](./PRODUCT.md) §14.

| Phase | Scope | Status | When |
|-------|-------|--------|------|
| **FC Phase 1** | Fee due dashboard, overdue list, WhatsApp/SMS reminders, promise-to-pay notes, collection status, class/branch-wise pending | ⬜ | Early — connects to parent comms; **build only if pilot retention needs it in next 8 weeks** |
| **FC Phase 2** | Monthly revenue, manual expenses, salary payable summary, transport expense summary, cashflow view, branch comparison (not accounting) | ⬜ | After Phase 1 proves value |
| **FC Phase 3** | Payroll, vendor payments, approvals, transport route profitability, Tally export, audit reports | 🔭 | Only if schools repeatedly ask |

**Hard boundary — do NOT build (Phases 1–2):** GST engine, tax compliance, bank reconciliation, full double-entry ledger, complete payroll compliance (PF/ESI/TDS). Integrate with Tally/Zoho in Phase 3+ if needed.

**Today:** atomic fee receipts + partial pay API exist; admin finance page is read-only stats/receipts — no reminders, overdue workflow, or management snapshot yet.

### Phase 3–5 & parallel
18. Personalized learning engine, early-warning (gated), voice tutor, gamification
19. Subscription billing, self-serve onboarding, platform-web portal
20. teacher-web, parent-web, student-web, platform-web apps (only admin-web exists today)
21. Azure Blob storage, real PDF pipeline, production SMS/push

---

## 🔭 Exploratory (Do Not Build Until Validated)

- Emotion/engagement recognition from video  
- Autonomous school scheduling / bus optimization  
- Cross-school benchmarking  
- Vertical expansion (hospitals, factories) — same architecture, different GTM  
- Plagiarism / AI-content detection  

---

## Known Issues & Tech Debt

Issues from code reviews (`CODE_REVIEW*.md`, dated ~2026-06-01). Spot-checked against current code — many pass-1 items appear **fixed**; below is what still looks open:

| ID | Issue | Severity |
|----|-------|----------|
| — | Azure Blob storage not implemented (local disk only) | Medium |
| — | PDF generation falls back to HTML (WeasyPrint missing) | Medium |
| — | External notification delivery stubbed (SMS/email/push) | Medium |
| — | AI runs synchronously despite Arq infrastructure | Medium |
| — | Razorpay payment gateway not integrated | Medium (pre-monetisation) |
| — | Qdrant/RAG not wired | Expected (Phase 1.5) |
| — | No frontend unit tests; no CI pipeline | Medium |
| — | Main pytest suite skips Audit/Tenant/Metrics middleware — security tests run separately | Low (by design, but document) |
| — | MSG91 OTP not wired for production | Blocker for prod OTP login |

Rotate any API keys if `.env` was ever copied into Docker layers (historical review finding — `.dockerignore` now exists).

---

## Phase Roadmap (Honest Estimates)

Solo builder, focused effort. **Validate each phase with pilot before starting the next.**

| Phase | Focus | Status | Rough effort |
|-------|-------|--------|--------------|
| **Phase 0** | AI platform foundation | ✅ Done | — |
| **Phase 1** | Pilot-ready SMS + QP + eval + mastery + tutor template + IA hubs | 🟡 In progress | 4–8 weeks |
| **Phase 1.5** | CurriculumPack v1 + exam loop hardening + Concept Cards | ⬜ Next | **8 weeks** (see plan below) |
| **A-OS** | AI-Intelligent OS — trust & context + **AI lesson plan v1** | ⬜ | Overlaps late P1 / P1.5 ([PRODUCT.md §23](./PRODUCT.md#23-ai-intelligent-school-os)) |
| **B-OS** | Close the loop (heatmap QP, tutor assign, eval feedback LLM) | 🟡 partial | P1.5 → P2 |
| **Phase 2** | Mobile apps + tutor RAG + parent feed | ⬜ | 2–3 months |
| **C-OS** | Intelligent UX (suggestions, document inbox, principal narrative) | ⬜ | P2 → P3 |
| **Phase 2b** | **Finance Command Center Phase 1** (optional) | ⬜ | Pilot retention only |
| **Phase 3** | Communication + co-pilot + memory UI | ⬜ | 2–3 months |
| **D-OS** | Workflow orchestration agents | 🔭 | P3+ only if A–B adopted |
| **Phase 4–6** | Learning Companion, Enrichment Studio, voice/vision | 🔭 | [PRODUCT.md §17](./PRODUCT.md#17-phased-vision) |
| **Parallel** | DPDP, billing, onboarding | ⬜ Ongoing | — |

---

## 8-Week Build Plan (Phase 1.5)

Canonical execution plan from product strategy. Full design: [PRODUCT.md](./PRODUCT.md) §4–§8.

| Week | Deliverable |
|------|-------------|
| **1** | `CurriculumPack` data model (`BookEdition`, pack, version, chapter/topic/concept); attach existing QP generation to `curriculum_pack_id` |
| **2** | TOC/syllabus upload + AI extraction into chapter → topic → concept tree |
| **3** | HOD approval flow for curriculum pack (immutable on approve) |
| **4** | Generate QP + marking scheme from approved pack; per-question rubric + concept tags at teacher approval |
| **5** | Answer-sheet evaluator MVP — StudyNexs-generated papers only; snap/upload → AI read → rubric compare | **🟡 Shipped (MVP)** — pack-scoped rubrics in Week 4–5 |
| **6** | Teacher HITL correction screen; **teacher time saved** metric | **🟡 Shipped** — corrections history UI |
| **7** | Weak-concept extraction from approved evaluations → update mastery / concept weakness | 🔧 partial — misconceptions API; full mastery recompute linkage ⬜ |
| **8** | **Mistake Recovery Tutor** MVP — Concept Cards + post-evaluation remediation flow | **🟡 template tutor shipped** — Concept Cards Week 8 |

**Prerequisites before Week 1:** Phase 1 QP hardening complete; pilot school pack inputs collected (book, TOC, syllabus, sample paper).

**Explicitly not in this 8 weeks:** full textbook ingestion, parent app, voice tutor, WhatsApp alerts, master packs at scale (design for Week 8+).

**Finance Command Center:** not in the 8-week plan by default. Build **only** fee reminder + collection visibility (FC Phase 1 subset) if a pilot school needs it for retention — see [PRODUCT.md](./PRODUCT.md) §14.

---

## Open Decisions

| Decision | Status |
|----------|--------|
| Pilot school written checklist | ⏸ Waiting on school |
| Pricing / unit economics | ⬜ Tier structure in [PRICING.md](./PRICING.md); rupee prices not locked |
| SSC blueprint accuracy | ⬜ Need real sample paper |
| Subjective grading in P1 vs P1.5 | Leaning P1.5 with answer sheet eval |
| RAG grounding for QP in P1 vs P1.5 | **Decided:** P1.5 via CurriculumPack (not free-text topics) |
| CurriculumPack as core object | **Decided (2026-06-16):** all QP, grading, mastery, tutor attach to versioned pack |
| No full textbook storage | **Decided (2026-06-17):** structured curriculum + references only; copyright-safe |
| Tutor MVP = Mistake Recovery | **Decided (2026-06-17):** post answer-sheet eval; Concept Cards not per-chat approval |
| 8-week Phase 1.5 plan | **Decided (2026-06-17):** see table above |
| AI-Intelligent OS north star | **Decided (2026-06-15):** context + suggested next action + HITL — [PRODUCT.md §23](./PRODUCT.md#23-ai-intelligent-school-os) |
| Lesson plan AI | **Decided (2026-06-15):** structured LLM v1 in **A-OS** after syllabus/calendar context — not before |
| Document upload router agent | **Decided (2026-06-15):** **C-OS** — classify + user confirm first; no autonomous router in pilot |
| Hybrid rules + ML + LLM | **Decided (2026-06-15):** explicit per feature — see [PRODUCT.md §23.3](./PRODUCT.md#233-hybrid-architecture-rules--ml--llm--workflows) |
| Finance Command Center | **Decided (2026-06-17):** optional paid module; FC Phase 1 only if pilot retention needs it — see [PRODUCT.md](./PRODUCT.md) §14 |
| Second engineer | Consider at Phase 2 |

---

## Immediate Next Steps

**Follow [TRACK_AB_EXECUTION.md](./TRACK_AB_EXECUTION.md)** — Track A (pilot validation) then Track B (hardening).

1. Run pilot discovery meeting (A1) — demo script in [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md)  
2. Collect pack inputs (A2) + verify SSC blueprint (A3)  
3. B3 tests green · B4 cost benchmark · B5 branch hygiene (parallel)  
4. B1 QP harden · B2 UI fixes from forced top-3 only  
5. Gate check → then Phase 1.5 Week 1  

---

## Repository Layout (Actual)

```
apps/
├── api/           ✅ FastAPI — 14 modules mounted
├── admin-web/     ✅ Next.js 16 — only frontend app present
├── teacher-web/   ⬜ not in repo
├── parent-web/    ⬜ not in repo
├── student-web/   ⬜ not in repo
└── platform-web/  ⬜ not in repo
```

**Current branch:** `phase-0-foundation`

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [PRODUCT.md](./PRODUCT.md) | Full product vision and feature catalogue |
| [PRICING.md](./PRICING.md) | Tiers, feature gates, AI credit pools, add-ons |
| [TRACK_AB_EXECUTION.md](./TRACK_AB_EXECUTION.md) | **Start here** — Track A + B checklist |
| [pilot/PILOT_OUTCOME_SHEET.md](./pilot/PILOT_OUTCOME_SHEET.md) | Fill after pilot meeting |
| [DECISION_LOG.md](./DECISION_LOG.md) | Decision history |
| [docs/api/](./api/) | API docs |

### Superseded (do not edit)

These files are replaced by PRODUCT.md + STATUS.md as of 2026-06-15:

- `PRODUCT_PLAN.md`
- `MASTER_PLAN.md`
- `IMPLEMENTATION_PLAN_P0_P1.md`
