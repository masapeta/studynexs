# Full product plan and greenfield restart guide

This document has **four layers**:

1. **Part 1 — Original product vision (authoritative)** — the full AI-powered School Management & Learning Platform script (student intelligence, hybrid comms, AI tutor, SMS modules, multi-app strategy, RBAC, tech stack, positioning).
2. **Part 1 supplement — Detailed requirements & delivery** — consolidated feature list (triad chat, tutor phases, SMS AI modules), core AI enhancements, risk/alerts, gamification, parent dashboard, **India compliance**, subscription model, **Phase 1–4 roadmap** tuned to a **Python / GenAI–strong** team, and **extra suggested enhancements**.
3. **Part 2 — Multi-tenant SaaS addendum** — control plane (platform operators), B-then-A delivery, PR-style milestones, and the MVP gap table from `Platform_owner.md` (onboarding, billing, audit, tickets, etc.).
4. **Part 3 — Greenfield restart plan** — engineering discipline so a new codebase (or reboot) does not repeat process/architecture mistakes.

---

# Part 1 — Original plan: AI-powered School Management Platform (full script)

## 1. Introduction (vision)

We are building an **AI-powered end-to-end School Management and Learning Platform** that acts as a **central intelligence system** for schools.

Unlike traditional systems that only manage data, this platform:

- Understands students  
- Assists teachers  
- Engages parents  
- Predicts outcomes  

It functions as a **Smart School Operating System** powered by AI.

---

## 2. Student Intelligence AI (core system)

Foundation of the entire platform.

### 2.1 What the AI evaluates — 360° student profile

**Academic performance**

- Subject-wise strengths and weaknesses  
- Concept-level understanding  
- Performance trends over time  

**Cognitive abilities**

- Logical reasoning  
- Problem-solving style  
- Memory vs conceptual learning  
- Learning style: visual, auditory, practical  

**Language and vocabulary**

- Vocabulary growth  
- Sentence construction  
- Reading comprehension  

**Extra-curricular and sports**

- Participation  
- Performance trends  
- Skill development  

**Self-development**

- Consistency  
- Discipline  
- Improvement rate  

### 2.2 AI output (examples)

- “Strong in concepts but weak in application”  
- “Improving vocabulary but lacks sentence clarity”  
- “High logical ability but low consistency”  

This becomes the student’s **AI profile (digital twin)**.

---

## 3. Intelligent communication system (human + AI hybrid)

Core innovation: **structured** communication, not generic group chats.

### 3.1 Structured communication model

Threads are modeled as:

**(Student + Parent + Subject Teacher + AI Assistant)**

Examples:

- Student1 + Parent1 + Math Teacher  
- Student1 + Parent1 + Science Teacher  
- Student2 + Parent2 + English Teacher  

### 3.2 How communication works

**Normal flow**

- Student asks a question  
- Teacher responds  
- AI remains passive  

### 3.3 AI fallback mechanism (key feature)

If the teacher does not respond within a defined time:

**AI decision logic**

1. Classify message: subject doubt, homework, general query, complaint  

**If academic query**

- AI responds with step-by-step explanation  
- Personalized to student level  
- Uses syllabus + past data  

**If non-academic query**

- AI responds: *“I’ll notify your teacher and ensure this is addressed shortly.”*  

### 3.4 Escalation system

If the teacher still does not respond:

1. Reminder to teacher  
2. Escalation to class in-charge  
3. Optional admin alert  

### 3.5 AI modes in chat

- Passive observer  
- Fallback responder  
- Teacher copilot (suggest replies)  
- Escalation manager  

### 3.6 Additional capabilities

- Auto summarize chats  
- Highlight student issues  
- Track teacher response time  

---

## 4. AI tutor (student learning assistant)

24/7 personalized tutor.

**Core features**

- Instant doubt resolution  
- Step-by-step explanations  
- Follow-up questions  
- Personalized teaching style  

**Roadmap**

- Phase 1: Text tutor  
- Phase 2: Voice tutor  
- Phase 3: Image-based tutor  
- Phase 4: Video-based tutor  

**Intelligence**

- RAG (books + syllabus)  
- Tracks student weaknesses  
- Adapts explanation style  

---

## 5. Student digital diary / planner

**Features**

- Homework tracking  
- Exam schedules  
- Task reminders  

**AI enhancements**

- Auto daily study plan  
- Smart prioritization  
- Adaptive scheduling  

---

## 6. School management system (AI-driven)

### 6.a Dashboard

- School-wide analytics  
- AI alerts: performance drops, attendance issues  

### 6.b Student AI management

**i. Subject management**

- Topic-level analysis  
- Weak area detection  

**ii. Attendance management**

- Pattern detection  
- Risk alerts  

**iii. Grade-wise management**

- Student vs class comparison  
- Trend analysis  

**iv. Extra-curricular management**

- Participation tracking  
- Skill evaluation  

**v. Personalized AI learning engine**

- Auto-generated study plans  
- Difficulty adjustment  
- Recommendations: videos, tests, revision schedules  

*Example:* Student weak in Algebra → assign practice + video + revision plan.

### 6.c Teacher AI management

**Teacher evaluation**

- Based on student outcomes, subject performance, engagement  

**Teacher “superpowers”**

- Auto lesson plan  
- Auto PPT generation  
- Auto question paper  
- Auto grading  
- One-click reports  

### 6.d Class AI management

- Class performance trends  
- Difficult topics identification  

### 6.e Class in-charge AI management

- Detect teacher absence  
- Auto assign substitute teacher  

### 6.f Fee AI management

- Predict payment delays  
- Smart reminders  

### 6.g Transport AI management

- Route optimization  
- Delay prediction  

### 6.h Library AI management

- Book recommendations  
- Reading analytics  

### 6.i Event AI management

- Event planning insights  
- Participation tracking  

### 6.j Notice AI management

- Personalized notifications  
- Priority alerts  

---

## 7. AI alert and highlight system

Proactive signals for:

- **Students** — weak areas  
- **Parents** — performance gaps  
- **Teachers** — class-level issues  

---

## 8. Core AI capabilities

- **Predictive analytics** — academic risk, attendance trends  
- **Adaptive learning** — personalized difficulty  
- **Skill gap analysis** — exact weak topics  
- **Automated assessment** — question generation, AI grading, plagiarism detection  
- **Gamification** — rewards, badges, leaderboards  
- **Multi-language** — regional language support  

---

## 9. Technology architecture

| Layer | Choice |
|--------|--------|
| Backend | FastAPI |
| AI | Agentic AI (LangGraph / CrewAI), RAG, LLMs |
| Data | PostgreSQL, MongoDB, Vector DB |
| Frontend | React (web), Flutter (mobile) |
| Infra | AWS + Docker |

*(Implementation may evolve; this section captures the original architecture intent.)*

---

## 10. Final positioning (product)

**Not**

- Just a school ERP  
- Just a learning app  

**It is**

- AI-powered **Student Intelligence System**  
- **Teacher Productivity** platform  
- **Personalized Learning** engine  
- **Hybrid Human + AI Communication** system  
- **Predictive School Operating System**  

---

## 11. Multi-role access (web + mobile)

**Core concept:** dedicated experiences per role — not one generic app. Each user sees a **personalized interface** powered by AI.

**Supported roles**

- Student  
- Parent  
- Teacher  
- Class in-charge  
- School admin / management  
- School operations (transport, library, accounts, etc.)  

### 11.1 Student mobile app

Features: AI tutor, digital diary, homework, performance dashboard, gamification, subject insights.  
AI: daily study plan, weak-area alerts, adaptive path.  
Experience: *“Your personal AI learning companion.”*

### 11.2 Parent mobile app

Features: child dashboard, attendance, fees, teacher communication, notifications.  
AI: struggle/improvement insights, weekly AI reports.  
Experience: *“Real-time visibility into child’s growth.”*

### 11.3 Teacher app (web + mobile)

Features: class dashboard, student insights, assignments, chat (with AI fallback), attendance.  
AI copilot: auto grading, lesson plans, question papers, suggested replies.  
Experience: *“AI-powered teaching assistant.”*

### 11.4 Class in-charge app

Features: class analytics, monitoring, communication oversight, escalations.  
AI: weak students, class-level issues, interventions.  
Experience: *“Class performance controller with AI insights.”*

### 11.5 School admin / management (primarily web)

Features: school-wide analytics, fees, staff, timetable, reports/compliance.  
AI: trends, revenue predictions, operational bottlenecks.  
Experience: *“Command center for entire school.”*

### 11.6 Operations team apps

- **Transport** — routes, student tracking, delay alerts  
- **Library** — issue/return, AI recommendations  
- **Accounts** — fee tracking, payment alerts, defaulter prediction  

---

## 12. Unified experience layer

Multiple apps, **one connected platform**.

**Example flow:** Student asks doubt → teacher notified → parent sees interaction → AI monitors → admin insight if needed → **fully connected ecosystem**.

---

## 13. Role-based access control (RBAC)

Each role has defined permissions, data boundaries, and action controls.

**Examples**

- Student → own data only  
- Parent → their children only  
- Teacher → assigned classes  
- Admin → school-wide access (within policy)  

---

## 14. Device strategy

- **Mobile** — students, parents, teachers  
- **Web** — admin, management, advanced teacher tools  
- **Cross-platform** — real-time sync, notifications across devices  

---

## 15. AI everywhere (cross-app intelligence)

AI is embedded per role: student (learning), teacher (productivity), parent (insights), admin (decisions).

### Refined positioning

- Multi-role **ecosystem**  
- AI at **every layer**  
- Role-specific **web + mobile** apps  

### One-line pitch

> **An AI-powered school ecosystem with dedicated apps for students, parents, teachers, and administrators — ensuring personalized learning, intelligent teaching, and seamless school operations.**

---

## Part 1 supplement — Detailed requirements, tutor roadmap, compliance, phased delivery & tech stack

*This section consolidates an extended product specification: feature checklist, AI enhancements, alerts, gamification, tutor phases (refined), India compliance, subscription intent, a phased build plan aligned to a Python / GenAI–strong team, and suggested additions.*

### S.1 Consolidated feature checklist

1. **360° student assessment (AI)** — Studies, sports, cognitive style (e.g. thinking strategy), vocabulary, self-development, consistency, and trends over time.

2. **Structured academic communication (not WhatsApp-style groups)** — One conversation thread per **(student, parent, subject teacher)** triad (and optional AI participant), e.g.  
   `stud1 + parent1 + math_teacher`, `stud1 + parent1 + science_teacher`, `stud2 + parent2 + math_teacher`, etc. Supports chat and voice; escalation when teacher is slow to respond.

3. **Tutor bot (student mobile)** — Subject doubts via **text** (Phase 1) → **voice** (Phase 2) → **images** (Phase 3) → **video** (Phase 4); RAG over syllabus/books; visual explanations where applicable.

4. **Student digital diary / planner** — Web + mobile; homework, exams, reminders; AI-generated daily plans and prioritization.

5. **School management (web + mobile)**  
   - **a.** Dashboard — school-wide KPIs, AI highlights.  
   - **b.** Student AI management — same dimensions as (1); sub-areas: **i** subject, **ii** attendance, **iii** grade-level / cohort, **iv** extracurricular, **v** personalized learning engine (daily plans, Duolingo-style difficulty, recommendations: videos, practice tests, revision schedules).  
   - **c.** Teacher AI management — performance signals; **superpowers:** auto lesson plan, PPT from syllabus, difficulty-aware question papers, objective + subjective auto-grading, one-click student summaries.  
   - **d.** Class AI management — class trends, weak topics.  
   - **e.** Class in-charge AI — oversight metrics; **auto-assign buffer/substitute teachers** on absence.  
   - **f.** Fee AI — collection patterns, delay risk, reminders.  
   - **g.** Transport AI — routes, delays, utilization.  
   - **h.** Library AI — lending, recommendations, reading analytics.  
   - **i.** Event AI — planning, participation.  
   - **j.** Notice AI — targeting, priority, read receipts + AI summarization for parents.

### S.2 Core AI enhancements (cross-cutting)

| Theme | Examples |
|--------|-----------|
| **Predictive analytics** | Early warning on marks, attendance, behavior |
| **Adaptive learning** | Dynamic difficulty and path (curriculum-aligned) |
| **Emotion / engagement** | Signals from sessions (where ethically & legally allowed); stress/engagement heuristics |
| **Smart scheduling** | Timetables: teachers, rooms, electives, constraints |
| **Assessment** | Plagiarism detection; auto question generation; skill gap analysis; peer / cohort benchmarks (privacy-preserving) |
| **Communication** | Multi-language (India regional); parent–teacher AI-assisted summaries |
| **Engagement** | Gamification; optional social / peer study matching (moderated) |
| **Surfacing gaps** | In-app highlights to student, parent, teacher on subject weaknesses |

### S.3 Real-time risk & alert system

Illustrative alerts:

- “Student likely to underperform in **Math** within **N** days”  
- “Attendance drop pattern detected”  
- “Behavioral / engagement anomaly (policy-defined)”  

**Channels:** parents, teachers, class in-charge, admin — with **severity**, **explainability** (which features triggered), and **recommended next step** (human-in-the-loop).

### S.4 “AI school brain” (admin / operations)

- **Predict:** fee default risk, teacher overload, infra bottlenecks (buses, labs, rooms).  
- **Optimize:** timetable, bus routes, teacher allocation (constraint solver + AI assists).  
- Tie high-impact decisions to **audit logs** and optional **simulation** (“what-if”) before publish.

### S.5 Gamification engine

XP, leaderboards (privacy-aware cohorts), badges, **skill progression trees**, streaks — tuned so competition stays healthy and **opt-in** where needed for younger learners.

### S.6 Parent intelligence dashboard

Examples:

- “Child is **X%** vs class average in **Science**”  
- “Strong in vocabulary, weaker in structured problem-solving”  
- **Weekly AI digest** (auto-generated, editable by school policy)  
- Deep link into **tutor history** and **teacher threads** (with permissions).

### S.7 Tutor bot — refined phased roadmap

| Phase | Mode | Tech emphasis |
|-------|------|----------------|
| **1** | **Text tutor** | RAG (curriculum + books), citations, guardrails, cost/latency controls |
| **2** | **Voice tutor** | STT + TTS + optional translation; low-latency streaming |
| **3** | **Vision tutor** | Image understanding (diagrams, handwritten steps) + translation |
| **4** | **Video tutor** | Multimodal (clip + explanation) + translation |

**Add-ons (high value, team-aligned):**

- **Whiteboard-style** step explanations (generated diagrams / equation chains).  
- **Step-by-step math solver** (symbolic + verbal explanation; board-aligned).  
- **Doubt memory** — per-student misconception graph; spaced repetition for weak concepts.  
- **Chatbot for interactive learning** with **visual representations** (charts, number lines, simple animations) — Phase 1 can start with **SVG / pre-rendered templates** before full generative UI.

### S.8 Compliance & trust (especially India)

| Area | Practices |
|------|-------------|
| **Student data privacy** | Minimize collection; purpose limitation; retention schedules; **child data** heightened care |
| **Parental consent** | Verifiable flows for minors; opt-in for AI tutoring / profiling beyond core schooling |
| **Security** | Encryption in transit (TLS) and at rest; secrets vault; key rotation |
| **Audit** | Append-only audit for admin/AI actions; export for inspections |
| **Regulatory** | Map to **DPDP Act** obligations; appoint responsibilities; DPIA for high-risk processing |
| **AI transparency** | When AI vs human replied in threads; model/version logging for disputes |
| **Data residency** | Offer **India region** hosting (e.g. Azure/AWS India) for sensitive workloads |

### S.9 Subscription product model (schools + parents)

**Packaging ideas**

- **Per school / per active student** (tiered by modules: core SIS, AI tutor seats, transport, etc.).  
- **Parent add-on** — premium tutor minutes, advanced analytics digest (still school-governed).  
- **Pilot → paid** with clear module flags and usage caps to control LLM cost.

**Tech enablers for SaaS**

- Multi-tenant DB (tenant id on rows or schema-per-tenant for large deals).  
- **Platform operator** console (onboarding, billing, support) — see Part 2.  
- Metering: API calls, tutor tokens, storage — for invoices and fair-use policies.

### S.10 Phased delivery & tech stack (aligned to Python / GenAI strength)

Below is a **practical** phased plan; timelines are indicative — adjust to team size.

#### Phase 1 — Foundation & MVP (≈ 4–6 months)

**Infra & core**

- **Backend:** FastAPI, PostgreSQL, Redis (cache + queues).  
- **Auth:** JWT + roles (student / teacher / parent / admin / operations / class in-charge).  
- **Cloud:** AWS or Azure, containers (Docker → ECS/AKS/App Service), basic autoscaling.  
- **Frontend:** React admin dashboard; **Flutter** student/parent MVP.  

**MVP features**

- User management + **school onboarding** (single-tenant solid before multi-tenant explosion).  
- SIS-lite: student profile, grades, attendance.  
- **Text tutor** (OpenAI / Azure OpenAI / open weights) with **strict RAG** + citation.  
- **Structured triad chat** (one thread per student–parent–subject teacher) + basic escalation timer.  
- Simple reporting dashboard.

**AI (MVP)**

- NLP for routing queries (academic vs non-academic).  
- Light sentiment on free-text feedback (opt-in).  
- Objective auto-scoring where answer key exists.

**Stack summary:** Python (FastAPI), Celery workers, React (MUI/Chakra), Flutter (GetX or Riverpod), PostgreSQL, Redis, Docker on AWS/Azure.

#### Phase 2 — Core SMS + AI enhancement (≈ 6–8 months)

- Full timetable, library, fees + payment gateway, richer analytics.  
- **Multi-school tenancy** on API + DB patterns.  
- Tutor: better context, personalization, **early** risk scores.  
- Essay / subjective assist (human-in-the-loop approval for grades).  
- Flutter: offline-friendly **read** caches, push notifications.  

**Tech adds:** vector DB (**pgvector** in Postgres, or Qdrant/Milvus/Chroma), WebRTC for voice/office hours, CI/CD, integration tests.  
*Architecture choice:* stay **modular monolith** until load forces extract (your team ships faster).

#### Phase 3 — Advanced AI & analytics (≈ 8–12 months)

- Vision tutor (diagrams, worksheet photos); stronger **predictive** models (tabular + LLM features).  
- Adaptive paths (bandit / rules + LLM explanations).  
- Question bank generation + **plagiarism** pipeline.  
- Smart scheduling / route optimization (OR-Tools + heuristics + AI assist).  
- **Audit & compliance** module maturity; DPIA artifacts.  

**Tech adds:** event bus (**Kafka** or **NATS** or Postgres outbox first — simpler), Prometheus/Grafana, optional Elasticsearch/OpenSearch for full-text.  
**Security:** OAuth2/OIDC for SSO with schools, rate limits, WAF, field-level encryption for sensitive PII where needed.

#### Phase 4 — Enterprise & agentic AI (≈ 12–18 months)

- **Agentic** tutors (LangGraph / CrewAI-style): multi-step plans, tool use (calculator, syllabus lookup, parent-safe language).  
- Deeper multimodal (handwriting, proctored assessment patterns where policy allows).  
- NLG for personalized reports; richer **what-if** admin simulations.  
- White-label, board-specific content packs, MDM hooks for school devices.  
- DR, multi-region, advanced BI.

**Team leverage:** Python + GenAI + agents = **core differentiator**; use **managed LLM** APIs first, fine-tune / small models only where ROI is clear.

### S.11 Suggested improvements & enhancements (beyond current list)

1. **Offline-first read** for diary and notices in Flutter; queue writes.  
2. **Content safety** — classifiers + blocklists for student chat and tutor; teacher override.  
3. **Cost governance** — per-school LLM budgets, model routing (small model for triage, large for hard doubts).  
4. **Evaluation harness** — golden datasets for tutor quality and regression after prompt/model changes.  
5. **SIS / LMS integrations** — CSV/Google Classroom-style import/export early; API later.  
6. **Accessibility** — WCAG 2.1 for web; large text / TTS for low-literacy households.  
7. **Cohort privacy** — suppress peer benchmarks for tiny classes; differential privacy if publishing aggregates.  
8. **Teacher workload** — caps on notifications; batch grading UX; AI suggests *prioritized* replies.  
9. **Incident response** — runbook for data breach and model misuse; school-visible status page.  
10. **Board / curriculum packs** — CBSE/ICSE/state variants as versioned RAG corpora.  
11. **Scientific honesty** — avoid over-claiming “emotion detection”; label uncertainty and confidence.  
12. **Equity** — low-bandwidth mode (text-first, compressed images); SMS fallback for critical alerts.  
13. **Governance** — school-level policy: which AI features are on, age gates, data retention.  
14. **Synthetic monitoring** — nightly scripted flows on production to catch API/auth regressions.  
15. **Parent languages** — not just UI strings: tutor explanations in home language where model supports.

---

# Part 2 — Multi-tenant SaaS addendum (control plane + delivery)

*This section is the **engineering / SaaS operator** layer on top of Part 1. It does not replace the product vision; it describes how **you** (the product company) operate many schools safely.*

## 2.1 Strategy: B first, then A (not “B forever”)

| Phase | Name | Goal |
|-------|------|------|
| **B** | Same backend, real control plane | Platform identity, auth, guards, audit, failed-actions store, recovery APIs — on **one** API service. |
| **A** | Split operator UI | Dedicated `apps/platform-web` (or `web-platform`) once the spine is real. |

**Hard gates**

- No impersonation / act-on-behalf until **audit + failed-actions** are trustworthy.  
- No long-term reliance on school `super_admin` alone for **platform** APIs; use **`PlatformUser`** (or equivalent) + explicit permissions.  
- **Separate** cookie/token namespaces for school vs platform auth when both exist.  
- **Module flags** enforced in API dependencies, not UI-only.  

## 2.2 Identity model (SaaS)

| Actor | Meaning | Scope |
|-------|---------|--------|
| **School user** (`User`, `school_id`) | Admin, teacher, student, parent, … | One tenant |
| **`super_admin` (school role)** | Highest privilege **inside that school** | School data plane |
| **Platform operator** (`PlatformUser`) | Onboarding, subscriptions, cross-tenant support, audit | Control plane |

**Naming**

- **School portal** — one school’s operations.  
- **Platform console** — operator / company-wide.  

## 2.3 Technical milestones (PR-style)

| Milestone | Content |
|-----------|---------|
| **PR1** | `platform_users`, roles, migration, bootstrap, tests. |
| **PR2** | `/platform-auth` login/refresh/logout; `principal_type=platform`; separate refresh cookie; reject wrong JWT on wrong routes. |
| **PR3** | `get_current_platform_user`, `require_platform_permission`; `/platform/*` off school-only checks; audit/tickets carry platform actor where needed. |
| **Later** | Failed-action store, permission inspector API, tickets/helpdesk depth, elevation + impersonation, module matrix, billing, `platform-web`. |

## 2.4 MVP themes — gap table (`Platform_owner.md`)

| MVP theme | What exists today | What you still need |
|-----------|-------------------|---------------------|
| **School onboarding** | Static checklist page | APIs + UI: create school, lifecycle (draft → active), slug, seed admin, optional CSV, checklist in DB |
| **School/tenant management** | Single-school GET/PUT `/schools/me` | List/search, suspend/archive, limits, subscriptions, activity — tables + endpoints |
| **School admin recovery** | Nothing systematic | Privileged reset/unlock/revoke, ticket + audit |
| **User management across schools** | Per-school APIs | Cross-school search, moves, duplicates — platform queries |
| **Permission inspector** | Implicit 403 | Evaluator API: allow/deny + reason codes |
| **Failed action logs** | App logs only | Structured store + platform list/filter API |
| **Helpdesk tickets** | Minimal / none | Tickets, SLA, assignments, links |
| **Act-on-behalf + audit** | No safe wrapper | Elevation + ticket + audited execution |
| **Impersonation + audit** | None | Short-lived tokens, UI banner, scoped claims, audit stream |
| **Module/feature control** | Partial settings JSON | Per-school module flags + enforcement in dependencies |

## 2.5 Web split (end state)

- **`staff-web` / `web-school`** — school JWT, tenant, school roles.  
- **`platform-web`** — platform JWT only; avoid permanent dual-login in one app.  

---

# Part 3 — Greenfield restart plan (avoid previous issues)

Use when starting a **new repo** or a **disciplined v2** to avoid: no git, Alembic from repo root, broken `down_revision`, ambiguous “super admin,” half-finished modules with dead imports.

## 3.1 What “from scratch” means

| Option | Best when |
|--------|------------|
| **A. Greenfield repo** | Discard old tree; want clean history. |
| **B. New repo + selective copy** | Keep tests/domain logic from old repo. |
| **C. Same repo, v2 folder** | Rare; prefer A or B. |

**Non-negotiable:** `git init` day one, remote, small commits, **tags** at milestones.

## 3.2 Repository layout

```text
school-platform/
  README.md              # Bold: DB/migrations from apps/api only
  .gitignore
  .env.example
  docker-compose.yml
  apps/
    api/
      alembic.ini        # ONLY HERE for API Postgres
      alembic/
      app/
      tests/
    web-school/
    web-platform/        # later
  docs/
    ADR/
    RUNBOOK.md
```

```bash
cd apps/api && alembic upgrade head
```

## 3.3 Identity and auth (day one)

- **ADR #1:** school JWT vs platform JWT; cookies; route matrix.  
- Add **platform auth** when the **first** cross-tenant API ships.  

## 3.4 Database and Alembic

1. Linear `down_revision` chain — every parent file **exists**.  
2. After each migration: `alembic upgrade head` locally.  
3. CI: ephemeral Postgres + `upgrade head` (and downgrade when safe).  

## 3.5 API boundaries

- `/api/v1/...`  
- `school_*` vs `platform_*` modules  
- Dependencies: school user + tenant vs platform user + permissions  

## 3.6 Testing minimum

- Smoke: import app, `/health`  
- Auth: login → me → 401 without token  
- RBAC: one allow + one deny per sensitive surface  
- CI migration smoke on empty DB  

## 3.7 Delivery phases (suggested order)

1. Repo + Postgres/Redis + Alembic + health + **git** + **CI**.  
2. School + `User` + school JWT + tenant resolution.  
3. One **vertical slice** end-to-end (e.g. admin users list).  
4. `platform_users` + platform JWT + first `/platform` API.  
5. **`web-platform`**.  
6. Billing / subscriptions (platform-scoped).  
7. School modules in slices + module flags + API enforcement.  

Each phase: **tag**, migrations green, tests green, README updated.

## 3.8 Operations

- Backups before prod migrations.  
- RUNBOOK: upgrade, `downgrade -1`, when `alembic stamp` is allowed (rare).  

## 3.9 Anti-regression checklist

| Issue | Prevention |
|-------|------------|
| No `alembic.ini` from root | Document `cd apps/api` or `alembic -c apps/api/alembic.ini` |
| Broken migration parent | CI + review `down_revision` |
| Cannot revert | Git + tags |
| Platform vs school confusion | ADR + naming + separate apps |
| Dead imports | CI test/import gate |
| Dual-login UX | Separate `web-platform` when operators are first-class |

## 3.10 Salvaging an old repo (option B)

**Copy:** tests, stable domain logic, production-verified modules.  
**Do not copy:** broken Alembic links, undocumented `super_admin`-as-platform shortcuts.

---

# Part 4 — How this doc relates to other files

| File | Role |
|------|------|
| **`Platform_owner.md`** (repo root) | Short **MVP gap table** for SaaS/control plane — can stay or link here. |
| **`docs/FULL_PRODUCT_PLAN_AND_GREENFIELD_RESTART.md`** (this file) | **Part 1** = vision script; **Part 1 supplement** = detailed checklist, tutor phases, compliance, phased tech roadmap, subscription notes, extra suggestions; **Part 2** = SaaS addendum; **Part 3** = greenfield discipline. |

---

*Academix / school-management-system — update as the product and architecture evolve.*
