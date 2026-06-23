# StudyNexs — Complete Product Plan & Roadmap

> **⚠️ SUPERSEDED (2026-06-15)** — Do not edit for ongoing updates. Use [PRODUCT.md](./PRODUCT.md) + [STATUS.md](./STATUS.md) instead.

### Finance Command Center (added 2026-06-17)

Canonical spec lives in **[PRODUCT.md §14](./PRODUCT.md#14-finance-command-center-optional-module)** and build status in **[STATUS.md](./STATUS.md)** (Finance Command Center section).

**Pricing tiers:** [PRICING.md](./PRICING.md) — Free / Pro / Pro+ / Enterprise, feature gates, AI credit pools.

**StudyNexs Finance Command Center** — optional paid module: fee tracking, reminders, follow-up memory, salary/expense overview, management dashboard.

| Phase | What |
|-------|------|
| **Phase 1** (early) | Fee due dashboard, overdue list, WhatsApp/SMS reminders, promise-to-pay notes, collection status, class/branch-wise pending |
| **Phase 2** (later) | Monthly revenue, manual expenses, salary payable summary, transport expense summary, cashflow view, branch comparison — still not accounting |
| **Phase 3** (on demand) | Payroll, vendor payments, approvals, transport route profitability, Tally export, audit reports |

**Do not build:** GST engine, tax compliance, bank reconciliation, full double-entry ledger, complete payroll compliance.

**Strategy:** Finance is a deal-expander, not the wedge. For the next 8 weeks, build only fee reminder + collection visibility if needed for pilot retention.

---

> Owner: Avinash Reddy Masapeta (ARM) · Status: **Living document v1.0** · Last updated: 2026-06-01
> The single source of truth for what StudyNexs is, what's built, what's next, and why.
> Companion docs: [MASTER_PLAN.md](./MASTER_PLAN.md) (architecture) · [IMPLEMENTATION_PLAN_P0_P1.md](./IMPLEMENTATION_PLAN_P0_P1.md) (build detail).

---

## 1. Executive Summary

**StudyNexs** is an AI-native School Management System (SMS) for the Indian K-12 market (SSC + CBSE first), sold on subscription to schools and parents. It pairs a complete, working school-operations platform with an AI layer that *saves teachers hours, gives parents real insight, and helps students learn* — with a human always in the loop.

- **Wedge (live today):** an AI question-paper generator for teachers — draft a board-style paper from the syllabus in ~20 seconds, edit, approve, print.
- **Moat (being built):** AI grounded in each school's own board syllabus, blueprint, and question bank — something free ChatGPT cannot do — plus deep integration into the school's daily operations.
- **Status today:** the SMS core works; the AI platform (provider-agnostic gateway, job queue, metering) is built; the Teacher-AI question-paper feature is **built and proven end-to-end**; one real school is interested, pending a complete working product.
- **The binding constraint:** this is currently a solo build. Scope discipline and validation-before-building are survival skills, not preferences.

---

## 2. Vision & Business Model

- **What it is:** every school-operations module (students, attendance, fees, exams, timetable, communication…) paired with an AI capability that assesses, predicts, automates, or tutors.
- **Who pays:** schools (per-student or per-school tiers) and parents (per-child tiers). Pricing is deliberately **deferred and segment-dependent** (local vs. premium vs. multi-branch) — to be set from real school conversations, not a spreadsheet.
- **Market:** India K-12. Start: SSC (Telangana State) + CBSE, Hyderabad/Telangana–AP region. Expand board-by-board and region-by-region.
- **Positioning:** not "another ERP with AI bolted on," and not "a ChatGPT wrapper" — a board-grounded, workflow-integrated assistant that schools trust because a human approves everything consequential.

---

## 3. Current Status — What's Built (honest inventory)

### ✅ SMS core (pre-existing, verified working — 29/29 tests pass)
Multi-tenant isolation, JWT/refresh auth with rotation + reuse detection, OTP, RBAC, 3-layer rate limiting; modules with working backends: **users, students/academic, attendance, fees (atomic receipts), notices, school-ops**. Admin web portal (Next.js) with wired pages: dashboard, students, staff, classes, attendance, finance, notices.

### ✅ Phase 0 — Foundation & AI platform (built this cycle, on branch `phase-0-foundation`)
- Fixed the **audit-logging bug** (was silently writing nothing in production) + regression test.
- Fixed **money handling** to stay `Decimal` end-to-end.
- **Async job queue** (Arq + `jobs` table) for background AI work.
- **Provider-agnostic LLM gateway** — Gemini / Claude / OpenAI adapters behind one interface, with **usage metering** (`ai_usage`) and **feedback capture** (`ai_feedback`). OpenAI path verified live.
- `ai` module scaffold + `/api/v1/ai/health`.

### 🟡 Phase 1 (hero) — Teacher AI: Question Paper Generator (built + proven E2E, not yet productionised)
- Generates a board-style paper (SSC Class 10 Maths verified: 100 marks, 4 sections, 33 Qs, **~₹0.13/paper**), with a teacher answer-key version.
- Teacher reviews/edits → **approves** (human-in-the-loop gate) → prints/exports.
- Full stack proven live: login → generate → export → approve, all 200.
- Demo school seeded: **Sri Saraswathi High School (SSC), 288 students, grades 1–10**, with attendance + fees.
- Admin-web "AI Papers" page built; nav curated (stub pages hidden).

### ⬜ Everything else below is planned/aspirational and **not built yet.**

> **Caveat to keep visible:** demand is not yet validated by a signed deal; pricing/unit-economics are not modelled; the SSC paper blueprint is approximate (needs a real sample to verify); export is HTML print-to-PDF (real PDF optional).

---

## 4. Guiding Principles

1. **Evolve, don't rebuild** — build on the proven core.
2. **Provider-agnostic AI** — no vendor lock-in; pick models on cost/quality after benchmarking.
3. **Human-in-the-loop** for anything consequential (grades, risk flags, reports). Trust is the product.
4. **Content as data** — board/grade/subject/syllabus/blueprint are versioned data, never hardcoded. Adding a board = config + content, not new code.
5. **Integrate, don't silo** — schools already run ERPs; plug in, never add teacher work.
6. **Cost-aware** — model routing, semantic caching, per-tenant budgets; AI cost is the margin.
7. **Validate before building** — a real school's words beat our guesses.
8. **Compliance-first** — children's data, India DPDP, from the start.

---

## 5. Target Architecture (summary)

```
Clients:  Next.js web (admin/teacher)      Flutter app (students/parents, Phase 2+)
              |  HTTPS (Azure Front Door + WAF -> Nginx)
API (FastAPI):  Auth · Tenant · RBAC · SMS modules · ai/ module
              |            |                |               |
       LLM Gateway   Async Job Queue   RAG / Vector     Realtime (chat, P3+)
       (Gemini/      (Arq + jobs)      (Qdrant, per-    Object storage (media, P2+)
        Claude/                         tenant ns)
        OpenAI)
Cross-cutting:  usage metering · eval/feedback · audit · per-tenant content packs
```
**Stack:** FastAPI (Python 3.13), PostgreSQL 16 + JSONB, Redis, Qdrant, Arq, Next.js 16, Flutter (mobile), Azure (Container Apps, Postgres Flex, Blob, Key Vault), India region.

---

## 6. Full Feature Catalogue (with status)

Legend: ✅ Done · 🟡 Built (demo, needs hardening) · ⬜ Planned · 🔭 Future/exploratory

### 6.1 School Management core
| Feature | Status |
|---|---|
| Multi-tenant, multi-school isolation | ✅ |
| Auth (password + OTP), RBAC, sessions | ✅ |
| Students, parents, classes, subjects, staff | ✅ (backend) / 🟡 (some UI) |
| Attendance (mark, summary) | ✅ |
| Fees (structures, payments, atomic receipts, PDF) | ✅ |
| Notices / communication board | ✅ |
| Exams & marks entry (UI) | ⬜ (backend exists, UI is a stub) |
| Timetable management (UI) | ⬜ (backend exists, UI is a stub) |
| Report cards | ⬜ |
| Library, transport, events | ⬜ (backend exists, UI stubs) |
| Settings (school profile, academic year) | ⬜ |
| Inspection/compliance document pack | 🔭 (see §7) |

### 6.2 Teacher AI
| Feature | Status |
|---|---|
| **AI question-paper generation (difficulty-based, board-grounded)** | 🟡 **built + proven** |
| Teacher edit + approve (human-in-the-loop) + print/PDF | 🟡 built |
| Auto-grading — objective (deterministic key-match) | ⬜ |
| AI-assisted grading — subjective (suggested marks + feedback, teacher-approved) | ⬜ |
| 1-click student summary report | ⬜ |
| Auto lesson-plan generation | ⬜ |
| Auto PPT / teaching material from syllabus | ⬜ |
| Teacher performance insights | 🔭 |
| "Teacher time saved" ROI dashboard | ⬜ (suggested, §7) |

### 6.3 Student AI & Tutor Bot (phased)
| Feature | Status |
|---|---|
| Text tutor (RAG, curriculum-grounded, child-safe) | ⬜ Phase 2 |
| Voice tutor (STT/TTS/translate, Indian languages) | ⬜ Phase 4 |
| Image/visual tutor | 🔭 Phase 5 |
| Video tutor (multimodal) | 🔭 Phase 5 |
| Whiteboard explanation + step-by-step solver | ⬜ Phase 2/4 |
| Doubt memory (remembers each student's weak spots) | ⬜ Phase 2/3 |
| Personalised learning engine (daily plans, adaptive difficulty, recommendations) | ⬜ Phase 3 |
| Skill-gap analysis + remediation | ⬜ Phase 3 |
| Digital diary / planner | ⬜ Phase 2 |

### 6.4 Parent mobile app & intelligence (Flutter)
A **consumer-grade parent experience — an Instagram-style feed of their child's school life**, not a dry data dump. Parents are a paying segment, and this surface drives daily engagement, word-of-mouth, and retention.
| Feature | Status |
|---|---|
| **Child "progress feed"** — visual timeline: results as published, attendance streaks, teacher remarks, achievements/badges, AI insight cards | ⬜ Phase 2/3 |
| **Moments feed** — school event photos, the child's participation, parent-targeted notices (shareable) | ⬜ Phase 2 |
| Fee status, due reminders, **online fee payment** (Razorpay), receipts/history | ⬜ Phase 2 |
| **1:1 chat** with each subject/class teacher (the structured threads, §6.5) | ⬜ Phase 3 |
| Weekly auto **AI progress report** + push notifications (results out, fee due, absence) | ⬜ Phase 2/3 |
| "Your child is X% behind in Science / strong in vocabulary" insight cards | ⬜ Phase 3 |
| Multi-child support; **Telugu/English** | ⬜ Phase 2/4 |

*Design ethos: engaging, visual, daily-open-worthy. The feed must **auto-populate from existing data** (marks, attendance, achievements, fees, notices) so it adds **zero teacher work**; manual posts (event photos) optional. **Privacy-first:** a parent sees only their own child's data — heightened DPDP consent + access control for a minor's data on a parent-facing feed.*

### 6.5 Communication
| Feature | Status |
|---|---|
| **Structured 1:1 threads per (student × parent × subject-teacher)** — NOT group chat | ⬜ Phase 3 |
| Realtime chat + voice | ⬜ Phase 3 |
| WhatsApp-first parent comms (reports, fee/attendance alerts) | ⬜ (suggested, §7) |
| Multi-language / vernacular UI | ⬜ Phase 4 |

### 6.6 Admin "AI School Brain"
| Feature | Status |
|---|---|
| Real-time risk & early-warning (fail/attendance/behavior) — human-reviewed | ⬜ Phase 3 |
| Predict fee-default risk, teacher overload | 🔭 Phase 5 |
| Optimise timetable, bus routes, teacher allocation; buffer-teacher auto-assign | 🔭 Phase 5 |
| Natural-language "ask your school data" co-pilot | ⬜ (suggested, §7) |

### 6.7 Engagement & advanced
| Feature | Status |
|---|---|
| Gamification (XP, leaderboards, badges, skill tree) | 🔭 Phase 4 |
| Peer comparison / benchmarking | 🔭 Phase 5 |
| Plagiarism / AI-content detection (advisory signal only) | 🔭 Phase 5 |
| Emotion/engagement recognition | 🔭 Phase 5+ (privacy-sensitive) |

### 6.8 Platform & business
| Feature | Status |
|---|---|
| Provider-agnostic LLM gateway + metering | ✅ |
| Async job queue | ✅ |
| RAG content pipeline (per-board/year packs, Qdrant) | ⬜ Phase 1.5/2 |
| Subscription billing (Razorpay) | ⬜ Parallel (buy, not build) |
| Self-serve school onboarding + platform-operator console | ⬜ Parallel |
| Offline / low-bandwidth mobile mode | ⬜ Phase 2+ |

### 6.9 Finance Command Center (optional paid module)

> Superseded detail: [PRODUCT.md §14](./PRODUCT.md#14-finance-command-center-optional-module). **Finance is a deal-expander, not the wedge.**

| Feature | Status |
|---|---|
| Fee due dashboard, overdue list, collection status | ⬜ FC Phase 1 |
| WhatsApp/SMS fee reminders, promise-to-pay notes | ⬜ FC Phase 1 |
| Class-wise / branch-wise pending fees | ⬜ FC Phase 1 |
| Monthly revenue, manual expenses, cashflow view, branch comparison | ⬜ FC Phase 2 |
| Payroll, vendor payments, Tally export, audit reports | 🔭 FC Phase 3 (on demand) |
| GST engine, tax compliance, bank reconciliation, full ledger | ❌ Hard boundary — do not build |

---

## 7. Key Differentiators (and enhancements I'd add)

**The moat we're already building toward:**
1. **Board-grounded AI.** Generation/tutoring grounded in the school's exact board syllabus, blueprint, and marking scheme — free ChatGPT can't match CBSE/SSC format or stay in-syllabus. This is the single most important defensibility.
2. **Human-in-the-loop trust.** AI assists; a teacher approves. This is what makes a risk-averse Indian school adopt AI at all.
3. **Workflow integration.** One system: generate → grade → report → notify, on the school's real data — not a disconnected tool.

**Enhancements I recommend adding to sharpen the differentiation (new suggestions):**
4. **Compounding school question-bank.** Every approved paper/question feeds a school-private bank; the product gets better and stickier the more it's used → data moat + switching cost.
5. **Difficulty calibration from the school's own results.** Use existing exam-mark history to tune question difficulty per class — closes the loop with data the school already has.
6. **WhatsApp-first parent communication.** Indian parents live on WhatsApp. Deliver report cards, fee reminders, attendance/risk alerts via WhatsApp Business API. Huge for Tier 2/3 adoption and retention.
7. **Vernacular + bilingual (Telugu/English) from early.** SSC schools teach in regional medium; AI4Bharat/Bhashini for regional voice & translation. A real India edge most competitors skip.
8. **Inspection/compliance pack generator.** Schools dread board inspections — auto-assemble inspection-ready records and reports. A sleeper feature schools will pay for.
9. **Principal co-pilot.** Natural-language questions over school data ("students at risk in Class 9", "this month's fee collection"). A lightweight "AI School Brain" that demos extremely well.
10. **"Teacher time saved" dashboard.** Quantify hours saved per teacher/week — the ROI metric that justifies the subscription to management and drives renewals.
11. **Explainable, gated risk alerts.** "Likely to fail" predictions are teacher-reviewed and never shown raw to students — turn a scary black box into a trusted early-warning system.
12. **A delightful, Instagram-style parent app.** Most Indian school parent apps are clunky data-dumps. A visual feed of the child's school life — results, attendance streaks, achievements, event photos, AI insight cards — drives daily engagement, parent word-of-mouth, and retention. Parents are a paying segment, and the feed auto-populates from existing data, so it adds no teacher work.

> Honest note: "AI" itself is **not** a differentiator — schools buy time saved, better academics, easier inspections, happier parents. Lead with outcomes, never with "AI."

---

## 8. Phased Roadmap & Timelines

> Timelines are **honest estimates assuming focused effort**. Solo, they stretch; with a small team they compress. **Validate each phase with the pilot school before building the next.** Don't treat these as promises to anyone until scoped against a written requirement.

| Phase | Focus | Key deliverables | Rough effort* |
|---|---|---|---|
| **Phase 0** | Foundation + AI platform | Gateway, job queue, metering, fixes | ✅ **Done** |
| **Phase 1** | Teacher AI + pilot-ready core | Question-paper gen (done) → **harden**; finish the SMS modules on the school's checklist (exams/marks UI, report cards, timetable, settings); seed; close pilot | **4–8 weeks** |
| **Phase 1.5** | Grounding + grading | RAG content packs (SSC/CBSE), objective auto-grade, subjective AI-assist (teacher-approved), 1-click student summary, WhatsApp alerts | **4–6 weeks** |
| **Phase 2** | Student tutor + parents + mobile | Flutter app shell, **text tutor (RAG, child-safe, doubt-memory)**, **parent app — Instagram-style child-progress feed** + weekly AI report + online fee pay, digital diary | **2–3 months** |
| **Phase 2b** | Finance Command Center Phase 1 | Fee visibility, overdue list, reminders, promise-to-pay (optional module; pilot retention only in near term) | **After pilot need** |
| **Phase 3** | Communication + intelligence | Structured 1:1 chat (realtime), risk/early-warning (gated), personalised learning engine, skill-gap analysis, principal co-pilot | **2–3 months** |
| **Phase 4** | Voice + engagement + scale | Voice tutor (Indian languages), gamification, multi-language UI, offline mode | **~3 months** |
| **Phase 5** | Vision/video + AI School Brain | Image/video tutor, predictive admin (fee/teacher/infra), smart scheduling, benchmarking | **3–6 months** |
| **Parallel** | Monetise + comply + expand | Subscription billing (Razorpay), DPDP compliance, onboarding console, more boards/regions | **Ongoing** |
| **Finance Phase 2** | Management finance snapshot | Revenue, expenses, salary/transport summaries, cashflow, branch compare (not accounting) | **After FC Phase 1** |
| **Finance Phase 3** | Deeper finance ops | Payroll, vendors, approvals, Tally export — only if schools repeatedly ask | **🔭 On demand** |

\* *Solo, full-time. A second engineer roughly halves Phase 2+ calendar time.*

---

## 9. Completed vs. To-Be-Completed (at a glance)

**Completed ✅**
- SMS core (auth, tenancy, students/academic, attendance, fees, notices) — verified.
- Phase 0 platform: LLM gateway (3 providers), job queue, metering, feedback, key bug fixes.
- Teacher-AI question-paper generator — built and proven end-to-end (₹0.13/paper).
- Demo SSC school seeded (288 students); admin-web AI page + curated nav.

**In progress / immediate 🟡**
- Hardening the question-paper feature; verifying SSC blueprint authenticity.
- Awaiting the pilot school's written "must-have modules" checklist to scope Phase 1.

**To be completed ⬜ (everything else)**
- Finish core SMS UIs (exams/marks, report cards, timetable, settings) per checklist.
- RAG grounding, grading, student summaries (Phase 1.5).
- Tutor bot, parent portal, mobile app (Phase 2).
- Chat, risk, personalised learning (Phase 3).
- Voice, gamification, multi-language (Phase 4).
- Vision/video tutor, AI School Brain (Phase 5).
- Billing, DPDP compliance, multi-board/region (parallel).

---

## 10. AI Cost & Unit Economics

- **Proven:** one question paper ≈ ₹0.13 on OpenAI gpt-4o-mini. Cheap at demo scale.
- **At scale, AI cost scales with usage** (per paper, per tutor message), unlike normal SaaS — so margin discipline matters: model routing (cheap model first), **semantic caching** (Qdrant), per-tenant token budgets.
- **Owed deliverable:** a per-student/per-school unit-economics model benchmarking Gemini vs. Claude vs. OpenAI on the real Phase-1 tasks, to set pricing and margins. **Do this before pricing is locked.**
- **Provider stance:** gateway is provider-agnostic; OpenAI for the demo; final choice after the benchmark.

---

## 11. Compliance, Security & Non-Functionals

- **India DPDP Act 2023:** verifiable parental/guardian consent for minors, consent records, data-subject rights, breach notification.
- **Data residency in India**; encryption at rest + in transit; field-level encryption for sensitive PII; key management (Azure Key Vault).
- **Audit logging** (now fixed) and tamper-evidence.
- **Child safety** on the tutor: content moderation, age-appropriate filters, no PII leakage, refusal behaviour.
- **AI transparency:** disclose AI involvement in grades/reports; human approval gate.
- **Multi-tenant AI isolation:** per-tenant RAG namespaces; never mix one school's data into another's context.
- **Scale/ops:** async jobs, metering, soak-tested infra, Azure Container Apps autoscaling.

---

## 12. Go-to-Market

- **Pilot-first, design-partner model:** one school, discounted/free, in exchange for co-defining scope and being the reference. (One school is already interested.)
- **Sales motion:** relationship + on-ground; principal identifies, management/trust approves budget. Long, committee-driven cycles — plan for it.
- **Validation discipline:** get the must-have-modules checklist in writing; ask willingness-to-pay early; lead demos with outcomes ("teachers home 2 hours earlier in exam week"), never with "AI."
- **Land-and-expand:** nail one board (SSC) deeply, then add boards as config + content.

---

## 13. Risks & Open Decisions

| Risk / decision | Status / mitigation |
|---|---|
| Demand not validated by a signed deal | One school interested; get written checklist + close pilot |
| Pricing/unit-economics unmodelled | Owed cost analysis before locking price |
| Scope vs. solo capacity (biggest risk) | Ruthless phase discipline; validate before building; consider a second engineer at Phase 2 |
| SSC blueprint accuracy | Verify generated papers vs. a real SSC sample before showing schools |
| Content sourcing/onboarding | Hybrid: ingest standard board content centrally; white-glove school-specific uploads for pilots |
| "Full product" = moving target | Pin to a finite written checklist with the school |
| DPDP/children's data | Address before going live with real student data |
| Competition (Teachmint, LEAD, Classplus, Entab) | Differentiate on board-grounding, integration, trust — not "AI" |

---

## 14. Immediate Next Steps

1. Get the pilot school's **written must-have-modules checklist** + timeline.
2. Commit the current build (Phase 0 + Teacher-AI demo) to version control.
3. Verify the **SSC paper blueprint** against a real sample (or obtain one).
4. Scope **Phase 1 productionisation** from the checklist; finish the required SMS UIs.
5. Produce the **AI unit-economics / provider benchmark**.
6. Keep validating with real schools at every step.
