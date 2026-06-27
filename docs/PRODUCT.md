# StudyNexs — Product Bible

> Owner: Avinash Reddy Masapeta (ARM) · Last updated: 2026-06-15  
> **Complete product definition** — vision, features, value to schools, operations impact, memory layer, compliance.  
> For build status see [STATUS.md](./STATUS.md).

### Contents

1. [What StudyNexs Is](#1-what-studynexs-is)  
2. [Who It Is For](#2-who-it-is-for)  
3. [Core Problem](#3-core-problem)  
4. [What Schools Get — Outcomes & Value](#4-what-schools-get--outcomes--value)  
5. [How School Operations Speed Up](#5-how-school-operations-speed-up)  
6. [CurriculumPack — The Source of Truth](#6-curriculumpack--the-source-of-truth)  
7. [Hero Workflow — The Exam Loop](#7-hero-workflow--the-exam-loop)  
   - [7.1 Question Paper Generation](#71-question-paper-generation)  
   - [7.2 Answer-Sheet Evaluation](#72-answer-sheet-evaluation)  
   - [7.3 AI Tutor — Mistake Recovery](#73-ai-tutor--mistake-recovery-mvp)  
   - [7.4 School Question Bank](#74-school-question-bank-not-cache)  
   - [7.5 Question-Level Intelligence](#75-question-level-intelligence)  
   - [7.6 Exam Intelligence Enhancements](#76-exam-intelligence-enhancements)  
8. [StudyNexs Learning Companion — Smart Workbooks](#8-studynexs-learning-companion--smart-workbooks)  
9. [Institutional Memory Layer](#9-institutional-memory-layer)  
10. [Guiding Principles](#10-guiding-principles)  
11. [Approval Model](#11-approval-model)  
12. [Suggested Data Models](#12-suggested-data-models)  
13. [Feature Catalogue (Detailed)](#13-feature-catalogue-detailed)  
14. [Finance Command Center (Optional Module)](#14-finance-command-center-optional-module)  
15. [Architecture](#15-architecture-high-level)  
16. [Moat & Differentiation](#16-moat--differentiation)  
17. [Phased Vision](#17-phased-vision)  
18. [Go-to-Market](#18-go-to-market)  
19. [Compliance & Trust](#19-compliance--trust)  
20. [Demo & Wow Moments](#20-demo--wow-moments-by-persona)  
21. [Pricing & Plans](#21-pricing--plans)  
22. [Related Documents](#24-related-documents)  
23. [AI-Intelligent School OS](#23-ai-intelligent-school-os)

---

## 1. What StudyNexs Is

**StudyNexs** is an AI-native school operating system for the Indian K-12 market (SSC, CBSE, and state boards). It combines day-to-day school operations with an AI layer that **assesses, automates, and explains** — always with a human in the loop for anything that affects a child.

Schools today run on WhatsApp, Excel, paper, and fragmented apps. Existing ERPs optimize data entry; they do not reduce **coordination chaos** between teachers, parents, admins, and students. StudyNexs is built to fix that: less admin overhead, clearer communication, and intelligence that compounds term over term.

**Positioning:** Not "another ERP with AI bolted on." Not a ChatGPT wrapper. Not a textbook warehouse.

> *StudyNexs learns each school's actual syllabus, creates teacher-approved curriculum intelligence, and uses it to generate papers, evaluate answer sheets, and tutor students safely.*

The textbook is only the input. The moat is the school's approved CurriculumPack, question bank, rubrics, evaluation history, and weak-concept memory.

**StudyNexs does not copy textbooks.** It turns teaching ideas — including globally inspired ones — into school-approved, locally aligned learning material.

---

## 2. Who It Is For

| Persona | Portal (planned) | Primary value |
|---------|------------------|---------------|
| **School admin / principal** | admin-web | Operations dashboard, fees, compliance, school-wide intelligence |
| **Teacher** | admin-web today → teacher-web | Attendance, exams, AI papers, grading assist, class insights |
| **Parent** | parent-web (Flutter, Phase 2+) | Child progress feed, fees, notices, AI summaries |
| **Student** | student-web + mobile (Phase 2+) | Timetable, marks, AI tutor, digital diary |
| **Platform operator** | platform-web | School onboarding, subscriptions, audit |

**Market:** India first — multilingual, board-aligned (NEP 2020), low-bandwidth tolerant, DPDP-compliant handling of minors' data.

**Who pays:** Schools (per-school or per-student tiers) and parents (per-child tiers). Pricing is segment-dependent and set from pilot validation, not upfront spreadsheets.

### 2.1 Portals

| Portal | Status | Roles | Key screens |
|--------|--------|-------|-------------|
| **admin-web** | Built | admin, super_admin, teacher (today) | Dashboard, students, staff, classes, attendance, fees, exams, timetable, AI papers, report cards, mastery, settings, transport, residential |
| **teacher-web** | Planned | teacher, class_incharge | Attendance, marks, AI tools, class mastery, timetable — mobile-friendly |
| **parent-web** | Planned (Flutter) | parent | Child feed, fees, notices, chat, AI reports |
| **student-web** | Planned (Flutter) | student | Timetable, marks, Mistake Recovery Tutor, diary |
| **platform-web** | Planned | platform_operator | School onboarding, subscriptions, usage, audit |

Each portal sees only what the role requires. Parents never see other children's data.

---

## 3. Core Problem

Schools are **coordination systems**, not software markets. Critical context is lost constantly:

- Why a student was warned or supported  
- Parent concerns and escalation history  
- Teacher observations and intervention outcomes  
- Performance transitions across terms  
- Decisions made in meetings, calls, and WhatsApp  

Every academic year, institutional memory resets. StudyNexs aims to become **persistent educational intelligence** — searchable, purpose-bound, and trust-preserving — not surveillance.

---

## 4. What Schools Get — Outcomes & Value

StudyNexs is not sold as "AI software." Schools buy **measurable outcomes**:

### 4.1 For school management & principals

| Outcome | What changes |
|---------|--------------|
| **Faster exam cycles** | Papers set in minutes, not hours; grading assisted, not all manual |
| **Inspection readiness** | Records, marks, attendance, compliance packs assembled on demand |
| **Data-driven decisions** | "Which class is slipping?" answered from live mastery data, not guesswork |
| **Parent trust** | Transparent progress updates, professional communication — not WhatsApp chaos |
| **Teacher retention** | Less burnout from repetitive grading and paperwork |
| **Admissions advantage** | "We use intelligent assessment and personalized learning" as a differentiator |
| **Year-over-year continuity** | Curriculum changes tracked; historical performance not lost when books change |

### 4.2 For teachers

| Outcome | What changes |
|---------|--------------|
| **Time back** | Evenings and weekends during exam season reclaimed |
| **Board-accurate papers** | No more formatting anxiety — papers match school's book and blueprint |
| **Grading assist** | AI reads answer sheets, suggests marks + corrections; teacher approves |
| **Class insight** | See which concepts the whole class missed — re-teach with evidence |
| **Less duplicate work** | Reuse last year's approved rubrics, questions, Concept Cards |
| **Safe AI** | Nothing reaches students or parents until teacher clicks approve |

### 4.3 For parents

| Outcome | What changes |
|---------|--------------|
| **Clarity** | See child's progress as a story — not a once-a-term report card surprise |
| **Timely alerts** | Fee dues, absences, results — on phone, in their language |
| **Trust** | Know the school uses structured, privacy-safe systems for their child's data |
| **Actionable insight** | "Weak in fractions — here's what school is doing" not just "failed maths" |

### 4.4 For students

| Outcome | What changes |
|---------|--------------|
| **Targeted help** | Tutor focuses on *their* mistakes from *their* exams — not generic videos |
| **Faster feedback loop** | Understand what went wrong soon after evaluation |
| **Curriculum-aligned** | Help matches the exact book and syllabus the school teaches |

### 4.5 What StudyNexs is NOT

| Not this | Why |
|----------|-----|
| Generic ChatGPT for schools | No syllabus grounding, no HITL, no workflow integration |
| Full ERP replacement on day one | Sits alongside or gradually replaces — starts with highest-pain workflows |
| Textbook piracy platform | Structured curriculum maps + references — not full book storage |
| Surveillance system | Structured events + purpose tags — not WhatsApp/call scraping |
| Auto-grader without teacher | AI suggests; teacher always approves consequential outputs |
| One-size-fits-all content | Every school has its own CurriculumPack |

### 4.6 The one-line pitch to a principal

> *"Your teachers go home earlier during exam week, your parents see real progress, and your school remembers what worked — year after year, even when the textbook changes."*

---

## 5. How School Operations Speed Up

StudyNexs reduces **operational entropy** — the hidden cost of coordination, repetition, and lost context.

### 5.1 Before vs after (exam season — highest impact)

| Task | Today (typical school) | With StudyNexs | Time saved |
|------|------------------------|----------------|------------|
| Set unit test paper | 2–4 hours per subject teacher | ~2 minutes generate + 15 min review/approve | **~3 hours/paper** |
| Create marking scheme | 30–60 min manual | Auto-generated with paper; teacher edits | **~45 min** |
| Grade 40 answer sheets | 4–6 hours subjective marking | 45–90 min review AI suggestions | **~4 hours/class** |
| Enter marks in register/ERP | 1–2 hours | Auto from approved evaluation | **~1.5 hours** |
| Write report card remarks | 3–5 min × 40 students | 1-click AI draft + bulk approve | **~2 hours/class** |
| Identify weak topics | Gut feel after results | Instant heatmap from question-level marks | **Days → minutes** |
| Parent "why did my child fail?" | Teacher reconstructs from memory | Timeline: every assessment + concept weakness | **15 min → 2 min** |

**Conservative estimate per exam cycle per class:** 8–12 teacher-hours saved.  
**School with 30 teachers, 3 exam cycles/year:** 700+ teacher-hours recoverable.

### 5.2 Daily operations acceleration

| Area | Speed-up | How |
|------|----------|-----|
| **Attendance** | Bulk mark entire class in one screen; auto-summaries | Admin-web + API (built) |
| **Fee collection** | Atomic receipts, partial pay, instant PDF | No duplicate receipt numbers, no manual ledgers |
| **Notices** | AI drafts circular → admin approves → distribute | Phase 3; replaces handwritten notices |
| **Timetable** | Central slot management | Changes propagate; no Excel version wars |
| **Student lookup** | One profile: marks, attendance, fees, parents, transport | Single pane — no hunting across files |
| **Inspection prep** | Auto-assemble compliance pack | Phase 2+; replaces frantic folder collection |

### 5.3 Academic year operations acceleration

| Annual task | Today | With StudyNexs |
|-------------|-------|----------------|
| New textbook / syllabus | Teachers re-map mentally; start from zero | **Rollover Wizard** — approve diff only |
| Question bank for new year | Rebuild or photocopy old papers | Prior approved papers tagged + reusable |
| HOD syllabus briefing | Manual comparison of old vs new book | **Curriculum Change Tracker** report |
| Concept weakness carry-forward | Lost when book changes | **Cross-year concept mapping** |
| Teacher handover (Class 5A → new teacher) | Oral briefing | Mastery history + intervention log |

### 5.4 Communication speed-up

| Channel | Today | With StudyNexs |
|---------|-------|----------------|
| Fee reminders | Admin calls or manual WhatsApp | Automated WhatsApp/SMS with ledger link |
| Results published | Paper report cards, slow distribution | Digital feed + optional print |
| Parent queries | "Ask teacher on WhatsApp" | Structured threads + AI parent chatbot for FAQs |
| PTA summary | Someone writes minutes hours later | AI digest from notes → admin approves |

### 5.5 Where StudyNexs does NOT speed things up (honest)

- Physical exam conduct (students still write on paper)  
- First-year CurriculumPack setup (white-glove — one-time per subject)  
- Management committee budget approval (human process)  
- Building parent trust in AI (requires HITL demo and time)  

Speed comes from **eliminating repetitive cognitive work**, not magic.

---

## 6. CurriculumPack — The Source of Truth

Books change. Chapter names change. Topics move. Schools use different publishers. But the underlying academic structure is stable:

```
Class → Subject → Board/School → Academic Year → Book Edition → Chapter → Topic → Concept → Learning Objective
```

**StudyNexs learns your school's actual syllabus — not a generic NCERT/CBSE memory.** That is the difference between a toy AI question-paper generator and a serious school exam intelligence system.

### 6.1 What a CurriculumPack Is

Every school gets its own versioned **School Curriculum Pack** per class × subject × academic year.

**Example:**

| Field | Value |
|-------|-------|
| School | VidyaNova AI School |
| Academic Year | 2026–27 |
| Class | 7 |
| Subject | Science |
| Board | State / CBSE / Custom |
| Book | Publisher ABC, Edition 2026 |
| Pack ID | `sci-7-2026-school123` |

The pack is the **approved source of truth** for that school's teaching and assessment context. Question paper generation, answer-sheet evaluation, mastery tracking, tutoring, and remediation all run **against a specific pack** — never against a generic "Class 7 Science" prompt.

### 6.2 Pack Structure

Each pack contains a hierarchical map (teacher/HOD-approved):

- **Chapters** — e.g. Chapter 3: Heat  
- **Topics** — Temperature, Measurement of heat, Conduction, Convection, Radiation  
- **Concepts** — heat transfer, conductors and insulators, real-life applications  
- **Learning objectives** — board-aligned outcomes where available  
- **Exam blueprint** — section weights, mark distribution, question-type mix (if school provides one)  
- **Term-wise syllabus scope** — which chapters belong to which term/unit test  

### 6.3 Onboarding — Minimal Input, AI-Assisted Draft

At onboarding, do **not** ask the school to configure 200 fields. Ask for:

- Board  
- Class / subject  
- Textbook name and edition  
- Term-wise syllabus  
- Exam blueprint (if they have one)  
- Chapter list, book PDF, or table of contents  
- Sample previous paper (if available)  

AI drafts the chapter → topic → concept map. Teacher or HOD **reviews once and approves**. That approved pack becomes immutable source of truth for the year.

### 6.4 Versioning — Never Overwrite

**Design rule:** never overwrite curriculum. When books or syllabus change, create a new pack version:

- `Science Class 7 — 2025–26`  
- `Science Class 7 — 2026–27`  

StudyNexs diffs versions and surfaces a **Curriculum Change Tracker**:

- Added: Radiation applications  
- Removed: Clinical thermometer  
- Moved: Convection from Chapter 3 → Chapter 4  
- Renamed: Heat Transfer → Transfer of Heat  

Schools struggle every year when publishers shift content. This feature alone has standalone value for academic heads and HODs.

### 6.5 What Attaches to a CurriculumPack

Everything academic intelligence touches should reference a pack:

| Artifact | Why it links to the pack |
|----------|--------------------------|
| Question papers | Generated from this school's chapters, topics, and blueprint |
| Answer keys & rubrics | Per-question tags to chapter/topic/concept |
| Answer-sheet evaluations | Evaluated against approved paper + key + rubric — not generic LLM memory |
| Question bank | School-private, compounding per pack |
| Exam marks & `question_schema` | Per-question topic/concept attribution |
| Concept mastery | Weakness tracked at concept level within a pack |
| Student summaries & remediation | Targeted to gaps in *this* syllabus |
| Tutor RAG namespace | Retrieval scoped to pack content |

### 6.6 Cross-Year Concept Mapping

When a new pack version is created, map old concepts to new concepts. The school does not lose history. Full detail in [§9 Institutional Memory](#9-institutional-memory-layer).

- Last year's "Conduction" weakness data links forward to the 2026–27 equivalent  
- Longitudinal mastery survives book changes  
- This is where the **institutional memory layer** begins  

### 6.7 Product Line

> *"StudyNexs learns your school's actual syllabus, not some generic syllabus."*

QP generation says: *"Generate paper from this school's 2026–27 Class 7 Science curriculum pack."*  
Answer-sheet evaluation uses: exact question paper + marking scheme + model answer + concept tags — **not full textbook content**.

StudyNexs is **not built around textbooks**. It is built around the stable academic hierarchy above. The textbook is an **input**; the moat is the school's approved pack, question bank, rubrics, evaluation history, and weak-concept memory.

### 6.8 What We Store (and What We Don't)

**Do not store full textbooks as the main content layer.** Textbooks are copyrighted, heavy, and operationally painful. Under Indian copyright law, reproduction includes storage in computer memory; copying entire private textbooks into a SaaS product is risky without permission or licensing.

**Store instead:**

- Textbook metadata (name, publisher, edition, year)  
- Chapter list, topics, concepts, learning objectives  
- Teacher/HOD-approved explanations and **Concept Cards**  
- Rubrics, practice questions, model answers  
- Source references and page references (pointers, not full text)  

This gives academic intelligence without becoming a textbook warehouse. The real cost is not storage — it is **copyright risk + yearly curriculum operations**. Design to minimize both.

### 6.9 Content Sources

Four sources feed each CurriculumPack:

| Source | What comes in |
|--------|----------------|
| **1. School inputs** | Book name, edition/year, index/TOC photos, term syllabus, exam blueprint, previous papers, teacher model answers |
| **2. Official/open references** | NCERT / ePathshala for curriculum alignment — always verify reuse rights before copying content into the product |
| **3. AI-generated original content** | AI drafts explanations, examples, hints, quizzes, and rubrics from the curriculum map |
| **4. Teacher/HOD approval** | Once approved, content becomes reusable StudyNexs learning material |

### 6.10 Who Adds Content Each Year?

**Year 1 / Pilot — white-glove setup**

StudyNexs asks the school for: book names, edition/year, TOC/index images, syllabus PDF, 2 previous papers, exam blueprint, sample model answers. AI creates the first pack. HOD approves.

**Year 2+ — Annual Rollover Wizard**

```
Duplicate last year's pack
  → upload new TOC/syllabus
  → AI compares old vs new
  → shows added / removed / moved / renamed
  → HOD approves diff
  → new pack version is active
```

The teacher is not "adding the whole book." The teacher is **approving a diff**.

**Long term — Master packs**

Platform-maintained packs schools can clone and customize:

- `CBSE Class 7 Science NCERT 2026`  
- `Telangana Class 8 Maths State Board 2026`  
- `Publisher XYZ Class 6 English 2026`  

If 20 schools use the same book, the mapping work is done once.

### 6.11 Storage Strategy

**Hot storage (structured curriculum):** chapters, topics, concepts, learning objectives, rubrics, concept cards, question banks, evaluations.

**Raw textbook uploads (optional, temporary):** ingestion only; deduplicated by file hash; school/license scoped; archived or deleted per retention policy. Not the primary content layer.

---

## 7. Hero Workflow — The Exam Loop

The flagship end-to-end workflow ties teacher AI to real school operations:

```
Select school's CurriculumPack (class × subject × year)
        ↓
Generate question paper from pack (chapters, topics, blueprint)
        ↓
Teacher reviews & approves paper + answer key + rubrics (HITL)
        ↓
Print & conduct exam
        ↓
Teacher snaps answer sheet photos
        ↓
AI evaluates against approved paper, key, rubric, and pack tags
        ↓
Teacher reviews, adjusts & approves marks (HITL)
        ↓
Marks + concept tags flow into mastery, report cards & parent updates
```

This closed loop — **pack → generate → assess → approve → report** — is the product wedge and the foundation for concept-level mastery and institutional memory.

### 7.1 Question Paper Generation

```
CurriculumPack → Exam Blueprint → Question Paper → Marking Scheme → Teacher Approval → School Question Bank
```

| Bad | Good |
|-----|------|
| "Generate Class 7 Science paper." | "Generate Class 7 Science paper from this school's 2026–27 **approved curriculum pack**." |

Every generated paper, answer key, and rubric is tagged to chapter/topic/concept within the pack. **Approved** papers become trusted bank assets; **rejected** papers become audit history assets that can still be **manually reused** later (edit, clone, resubmit). Nothing is discarded. See [§7.4](#74-school-question-bank-not-cache).

### 7.2 Answer-Sheet Evaluation

Does **not** depend on full textbook content. Uses:

- Exact approved question paper  
- Teacher-approved marking scheme  
- Model answer per question  
- Concept tags from the pack  
- Student answer sheet image  
- Teacher HITL approval  

```
Answer sheet uploaded
  → AI reads student answer
  → compares against rubric + model answer
  → suggests marks per question
  → generates correction summary
  → teacher approves / edits
  → final marks saved
  → weak concepts updated
```

**Scope for MVP:** StudyNexs-generated papers only (known layout, QR-linked exam + student). Strongest wedge after QP generation.

### 7.3 AI Tutor — Mistake Recovery (MVP)

The tutor does **not** answer from random textbook dumps. It answers from:

**Approved Concept Cards + CurriculumPack + Student Mistake Context**

```
Student asks doubt (or triggered post-evaluation)
  → detect class / subject / concept
  → retrieve approved Concept Card
  → generate explanation
  → log doubt pattern
  → flag low-confidence or missing content for teacher review
```

**Approval model for tutor:** HOD/teacher approves **Concept Cards** upfront. AI answers instantly from approved cards. Exceptions go to a **Content Review Queue** — AI drafts once, teacher approves once, all future students get the approved answer.

**Mistake Recovery Tutor (best MVP):** After answer-sheet evaluation, if a student lost marks on fractions / photosynthesis / grammar:

1. What went wrong  
2. Simple explanation (from Concept Card)  
3. Worked example  
4. 2–3 practice questions  
5. Retry check  

### 7.4 School Question Bank (Not Cache)

> **Sticky rule:** Generated papers cost credits. **Both approved and rejected papers become assets.** Approved → trusted question bank (auto-compose reuse). Rejected → audit history **plus** manual reuse path — edit, clone, or resubmit; re-approval promotes items into the bank.

Do **not** treat generated QPs as throwaway LLM cache. Every outcome compounds school value.

#### Two kinds of reuse

| Kind | Who | Approved papers | Rejected papers |
|------|-----|-----------------|-----------------|
| **Auto-compose reuse** | AI `qp_from_bank` mode pulls structured items | **Yes** — trusted bank items | **No** — not auto-indexed until re-approved |
| **Manual reuse** | Teacher / HOD | Clone, edit, export | **Yes** — edit, **clone (0 credits)**, fix & **resubmit**; on re-approval → enters bank |

Rejected does **not** mean dead. It means *not yet trusted for automatic generation*. A teacher can salvage good questions, incharge can approve the fixed version later, and those items then become bank assets — without paying for a fresh full generate.

| Asset type | Source | Stored | Auto bank? | Manual reuse? |
|------------|--------|--------|------------|---------------|
| **Trusted bank asset** | Approved paper | `QuestionBankItem` rows | Yes | Yes |
| **Audit + salvage asset** | Rejected paper | Full paper + reason + actor/time | No (until re-approved) | **Yes** — edit / clone / resubmit |

| Layer | What it is | When to use |
|-------|------------|-------------|
| **LLM response cache** | Exact same request → same draft (deduped hash) | Prevent accidental double-billing on identical retries |
| **School question bank** | Approved questions/rubrics as structured reusable items | Future papers for **that school** only |
| **Master question bank** | Platform-reviewed generic items (not private school papers) | Optional seed content; never mix with school-private without explicit policy |

The **school question bank** is the valuable layer. Approved questions become building blocks; the second paper in a topic should reuse ~40% from bank + generate only gaps.

#### Lifecycle policy

| State | Stored? | Credits | Asset outcome | Auto bank? | Manual reuse? |
|-------|---------|---------|---------------|------------|---------------|
| **Generated draft** | Yes | Charged at generation | Pending | No | Edit, submit |
| **Approved paper** | Yes | Already charged | Trusted bank asset | **Yes** | Clone, edit, export |
| **Rejected paper** | Yes | Already charged | Audit + salvage asset | No (until re-approved) | **Edit, clone, resubmit** |

Rejected papers keep the full audit trail (*who, why, credits spent*). They also stay in the school's paper library for future salvage — a common path: reject → teacher fixes difficulty → resubmit → approve → bank.

#### Structured `QuestionBankItem` (not whole papers in prompts)

**Architecture shift:** do not only save whole papers — **split every paper into reusable question items**. Each question is an asset with memory. Full metadata: [§7.5.1](#751-question-bank-metadata).

**Do not** send entire old papers to the LLM every time — that increases tokens. Store and retrieve **structured items** (summary fields; see §7.5 for intelligence layers):

| Field | Purpose |
|-------|---------|
| `question_text`, `answer_key`, `rubric` | Core content |
| `marks`, `difficulty`, `question_type`, `board_pattern` | Blueprint fit |
| `curriculum_pack_id`, `chapter_id`, `topic_id`, `concept_id`, `learning_objective_id` | Pack-scoped tags |
| `approval_status`, `source` (AI / teacher / previous paper) | Trust + provenance |
| `used_in_papers`, `usage_count` | Reuse tracking |
| `teacher_rating`, `student_average_score` | Calibration (post-eval) |

**Token-saving generation example:**

```
Generate Class 7 Science paper
  → retrieve approved items from same curriculum_pack (vector + filters)
  → reuse ~40% (compose sections from bank)
  → LLM generates only missing/new questions to fill blueprint
  → quality check final paper
```

#### Generation modes

| Mode | AI usage | Credits (example) |
|------|----------|-------------------|
| **Fresh paper** | Full LLM | 5 |
| **Balanced from question bank** | Bank compose + small LLM fill | 2 |
| **Previous paper variant** | Clone + teacher edit | 0 |
| **Chapter test** | Bank-filtered by chapter + fill | 2 |
| **Weak concept remedial test** | Bank + mastery weak concepts | 2 |
| **Board pattern mock test** | Blueprint-strict compose | 2–5 |
| **Regenerate section** | One section | 2 |
| **Regenerate one question** | One item | 1 |
| **Paper quality check** | Cheap checker pass | 1 |
| **Export / edit** | No LLM | 0 |

See [§7.5](#75-question-level-intelligence) for similarity checking, quality checker, and difficulty calibration.

UI must label the mode before generation so teachers see cost vs reuse tradeoff.

#### Security / retrieval scope

Exam papers are sensitive. Bank retrieval **must** filter by:

- `school_id` (tenant isolation — non-negotiable)
- `academic_year` / `curriculum_pack_id`
- `class_id`, `subject_id`
- `teacher_role` (who may pull from bank)
- `approval_status = approved`

**Never** let one school's private items leak into another school's generation unless the item is in the **master question bank** (platform-reviewed, generic, explicitly shared).

#### Link to approval workflow

On `POST …/approve`: extract questions + rubrics → upsert `QuestionBankItem` (trusted auto-compose asset). Works for first-time approve **or re-approve after rejection**.

On `POST …/reject`: persist full paper + `rejection_reason` + actor/timestamp → audit record; **do not** add to auto-compose bank yet. Paper remains editable/clonable for manual reuse.

**Today in repo:** `question_papers` stores full papers; approve/reject workflow live; on approve → `QuestionBankItem` + `RubricBankItem` ingest (`question_bank_service`). `qp_from_bank` generation, quality checker, similarity — **not implemented**. Build order: [§7.5.10](#7510-recommended-build-order) · [STATUS.md](./STATUS.md).

### 7.5 Question-Level Intelligence

> **Big idea:** Every exam should make the next exam smarter. That is the whole company hiding inside the QP wedge.

Papers are containers. **Questions are the unit of memory.** Break every generated paper into `QuestionBankItem` + `RubricBankItem` rows; compound intelligence with each approval, rejection, and answer-sheet evaluation.

#### 7.5.1 Question bank metadata

Every generated question stores (minimum):

| Field | Purpose |
|-------|---------|
| `school_id`, `class_id`, `subject_id` | Scope |
| `curriculum_pack_id` | Pack anchor |
| `chapter`, `topic`, `concept`, `learning_objective` | Curriculum tags |
| `question_text`, `answer_key`, `marks` | Content |
| `difficulty`, `question_type`, `board_pattern` | Blueprint |
| `source` | `ai` / `teacher` / `previous_paper` |
| `approval_status` | draft / approved / rejected |
| `used_in_papers` | Paper IDs where item appeared |
| `teacher_rating` | Optional HOD/teacher score |
| `student_average_score` | From eval history (calibrated) |

This structured bank is the **real academic moat** — not the PDF of a paper.

#### 7.5.2 Duplicate / similarity checker

Before generating or adding a question, warn:

> *This question is 82% similar to one used in Unit Test 1.*

**Why:** avoid repeats, reduce paper leakage risk, keep exams fresh, skip unnecessary LLM calls when bank item suffices.

Implementation: embedding similarity + pack-scoped search; threshold configurable per school.

#### 7.5.3 Paper quality checker

After generation (cheap step — 1 credit), run deterministic + light AI checks:

| Check | Example output |
|-------|----------------|
| Blueprint match | 92% |
| Marks total | 80/80 |
| Difficulty balance | OK |
| Chapter coverage | Missing Chapter 4 |
| Repeated concepts | Too many from Heat Transfer |
| Language level | Suitable for Class 7 |

Strong **trust** feature before incharge approval. Teacher sees fixes before submit.

#### 7.5.4 Difficulty calibration (eval → bank)

After answer-sheet evaluation, update each `QuestionBankItem`:

| Signal | Example |
|--------|---------|
| Expected difficulty | Medium |
| Actual performance | Hard |
| Average marks | 1.2 / 3 |
| Common mistake | Confused convection and radiation |

Future papers become smarter. **Bridge to institutional memory** — link eval results back to question IDs.

#### 7.5.5 Reuse modes (teacher-facing)

Product should feel powerful without burning credits every time:

- Fresh paper  
- Balanced from question bank  
- Previous paper variant  
- Chapter test  
- Weak concept remedial test  
- Board pattern mock test  

Each mode maps to credit tier ([§7.4](#74-school-question-bank-not-cache), [PRICING.md](./PRICING.md)).

#### 7.5.6 Approval memory

On HOD reject (paper or question), capture **structured reason** — not only free text:

| Reason code | Use |
|-------------|-----|
| Too difficult | Tune difficulty mix next time |
| Out of syllabus | Pack boundary guard |
| Poor language | Prompt / level adjustment |
| Wrong answer key | Rubric QA |
| Repeated question | Similarity checker feedback |
| Not board pattern | Blueprint enforcement |

Rejected items stay **out of auto-compose bank** until re-approved; **rejection reasons feed future generation** (approval memory). Manual salvage still allowed ([§7.4](#74-school-question-bank-not-cache)).

#### 7.5.7 Exam security layer

Schools care about leakage. Add over time:

- Paper access logs  
- Download watermark  
- Version history  
- Lock paper after approval  
- Only exam in-charge can publish  
- Teacher drafts only assigned subject  
- No public sharing links for final papers  

#### 7.5.8 Rubric bank

Do not save questions alone. Save **rubrics** as first-class `RubricBankItem`:

- Question link  
- Expected answer  
- Step-wise marking  
- Common acceptable answers  
- Common wrong answers  
- Teacher correction note  

Directly improves answer-sheet evaluator accuracy.

#### 7.5.9 Cost controls (admin view)

Credits already tiered by mode ([§11.1](#111-ai-credits-vs-approval-status)). Monthly principal view should show:

- Credits used  
- Papers generated  
- Rejected vs approved drafts  
- Estimated teacher hours saved  
- **Cost per approved paper** (credits ÷ approved count)

#### 7.5.10 Recommended build order

| Step | What | Status |
|------|------|--------|
| 1 | Save generated papers | ✅ `question_papers` |
| 2 | Split paper → individual question items | ✅ ingest on approve |
| 3 | Approval / rejection + structured reason | 🟡 reject reason free-text; codes ⬜ |
| 4 | School-private question bank ingest on approve | ✅ |
| 5 | Generate-from-bank mode | ✅ `POST …/generate-from-bank` |
| 6 | Paper quality checker | ⬜ |
| 7 | Link answer-sheet eval results → each question | ⬜ |
| 8 | Similarity checker | ⬜ |
| 9 | Rubric bank + eval accuracy | ⬜ |
| 10 | Exam security / leakage prevention | ⬜ |

**Top 5 product enhancements** (if picking only five): see [§7.6.13](#7613-top-5-next-enhancements).

### 7.6 Exam Intelligence Enhancements

Extensions to question-level intelligence ([§7.5](#75-question-level-intelligence)). Together they compound into one story:

> **Generate better papers → correct faster → understand weakness → create remediation → prove improvement.**

#### 7.6.1 Blueprint intelligence

Let schools store **exam patterns** as data — not free text:

```
Class 10 Maths · Pre-final
Section A: 10 × 1 mark
Section B: 6 × 2 marks
Section C: 8 × 4 marks
Competency questions: 20%
Application questions: 30%
```

AI generates **inside** the blueprint. Post-gen, the system can advise:

- *Your paper has too many memory-based questions.*
- *Board pattern expects more application questions.*

Links to `ExamBlueprint` on `CurriculumPack` + [§7.5.3](#753-paper-quality-checker) quality checker. Very high value for HOD trust.

#### 7.6.2 Paper versioning

Schools need multiple sets from one blueprint:

| Variant | Use |
|---------|-----|
| Set A / Set B | Parallel papers |
| Re-test | Second chance |
| Absentees paper | Late sitters |
| Practice paper | Class drill |
| Remedial paper | Weak groups |

**Generate equivalent variant** — same blueprint, same difficulty distribution, **different questions** (bank compose + minimal LLM). Lower credits than fresh full generate.

#### 7.6.3 Teacher style memory

Per-teacher preferences learned from approvals and edits (scoped to **that teacher + school only**):

- Prefers direct questions  
- Uses case-study questions  
- Avoids very long answers  
- Likes diagram-based questions  

Stored as `TeacherStyleProfile` — influences prompts, never leaks across schools.

#### 7.6.4 HOD quality workflow

Professional multi-layer review (extends current submit/approve):

```
Teacher draft
  → HOD review (comments)
  → Exam in-charge lock
  → Principal final approval (optional)
```

Comment examples: *Change Q5 difficulty · Add one HOTS question · Remove out-of-syllabus topic.*

Maps to `PaperStatus` progression + threaded review comments — not a single approve button only.

#### 7.6.5 Leakage prevention (premium trust)

Exam papers are sensitive. Expand [§7.5.7](#757-exam-security-layer):

| Control | What |
|---------|------|
| Watermark on PDF | School + user + timestamp |
| Unique teacher copy watermark | Per-download traceability |
| Download / view logs | Who opened what, when |
| Role-based access | Draft vs locked vs published |
| Paper lock | No edits after exam-incharge lock |
| View-only mode | Preview without export |
| Regenerate after suspected leak | New variant from blueprint, invalidate old set |

Premium / Pro+ trust feature — schools will pay for this.

#### 7.6.6 Answer-key confidence

For every generated marking scheme, surface trust signals:

| Signal | Example |
|--------|---------|
| AI confidence | 87% overall |
| Needs teacher review | Q8, Q12 |
| Possible alternate answer | Yes — Q4 |

Helps teachers approve faster without blind trust. Feeds [§7.5.8](#758-rubric-bank).

#### 7.6.7 Misconception library

From answer-sheet evaluation, extract reusable entries:

```
Common mistake: Students confuse mass and weight.
Suggested remedial activity: Use spring balance example.
```

`MisconceptionEntry` — concept-tagged, school-private. Product becomes more than correction — becomes **teaching memory**.

#### 7.6.8 Auto remedial packs

After exam, generate (low/medium credits):

- Remedial worksheet for students weak in fractions  
- Revision plan for Class 8B  
- Parent summary for low performers  

**QP → evaluation → tutor** connection. See also [§7.3](#73-ai-tutor--mistake-recovery-mvp) Mistake Recovery Tutor.

#### 7.6.9 School benchmarking (later)

**Do not build early.** With consent + anonymized aggregates only:

- *Class 7A performed 18% below school average in Algebra.*
- *This chapter has been hard for 3 years.*
- Later: *Compared to similar schools, your Class 8 Science application questions are weaker.*

Powerful at scale; privacy-sensitive.

#### 7.6.10 Curriculum drift alerts

When syllabus/book changes ([CurriculumPack rollover](./PRODUCT.md#6-curriculumpack--the-source-of-truth)):

- *Chapter removed from 2026 syllabus but still appears in your paper.*
- *New topic added but not covered in lesson plan.*

Directly solves textbook-change chaos.

#### 7.6.11 Inspection pack

Sleeper feature schools may pay for. One-click assemble:

- Lesson plan records  
- Exam blueprint  
- Question paper approval logs  
- Marks analysis  
- Remedial action report  
- Teacher workload report  

Extends existing inspection-pack vision in [§13.1](#131-school-management-core).

#### 7.6.12 Parent meeting pack (PTA)

Before PTA, per student or class:

- Strengths · weak concepts · attendance impact  
- Recent improvements · teacher notes  
- Suggested home practice  

Creates **parent-visible value** without extra teacher writing.

#### 7.6.13 Top 5 next enhancements

If picking only five to build next:

| # | Enhancement | Why |
|---|-------------|-----|
| 1 | **School-private question bank** | Moat + token savings ([§7.5](#75-question-level-intelligence)) |
| 2 | **Blueprint intelligence** | Board-accurate generation + quality feedback |
| 3 | **Answer-sheet eval → question analytics** | Difficulty calibration + misconception library |
| 4 | **Remedial worksheet generation** | Closes exam loop to learning |
| 5 | **Inspection / PTA pack** | Management buy-in + willingness to pay |

Everything else in §7.6 layers on after these prove value in pilot schools.

---

## 8. StudyNexs Learning Companion — Smart Workbooks

**Product name (working):** StudyNexs Learning Companion · *School-Customized Smart Book*

The first version **does not replace** NCERT or private textbooks. It **sits beside them** — a school-owned, teacher-approved companion built from the school's CurriculumPack and compounding exam data.

> *"Your school's book gets smarter every exam."*

That line is stronger than "AI textbook generator."

### 8.1 What it is — and what it is not

| Wrong (do not build) | Right (build this) |
|----------------------|-------------------|
| Upload NCERT/private book → AI rewrites full textbook | CurriculumPack → approved concept map → **original** school content |
| Replace publisher textbooks | Companion workbooks beside existing books |
| Copy or lightly paraphrase copyrighted expression | Curriculum-**aligned**, teacher-approved, **originally written** material |
| "AI textbook generator" | Living workbook that improves from exam data |

**Copyright:** Indian copyright protects expression (reproduction, adaptation, translation). Storing a work in computer memory can count as reproduction. StudyNexs stores **ideas-aligned structure** (chapters, topics, concepts) and **original approved content** — not publisher prose. NCERT/ePathshala are useful for **alignment and reference**; verify reuse rights before any content enters a commercial product.

### 8.2 What the school gets

From an approved CurriculumPack, generate **school-customized learning materials**:

- Teacher-approved concept map  
- School examples and local-language explanations  
- Practice questions and exam-style items  
- Weak-concept remediation sheets  
- Chapter summaries  
- **Printable workbook / smart book** (PDF or print-ready)  

**Example product title:**

> *Class 7 Science — Sri Chaitanya 2027 Edition*  
> Aligned to: State Board / NCERT / Publisher ABC  
> Customized with: school's syllabus order, teacher explanations, Telugu+English notes, practice sets, last year's common mistakes, exam-style questions, remedial worksheets  

### 8.3 Entry formats (sell these first — not full textbooks)

Schools may hesitate to replace textbooks. They will say yes to:

| Format | Example ask |
|--------|-------------|
| **Chapter Companion Notes** | Per-chapter summary + key points beside the physical book |
| **Revision Booklets** | Term-1 revision for Class 8 Maths from *our* syllabus |
| **Practice Workbooks** | 50 questions on fractions — calibrated to *our* class level |
| **Mistake Recovery Sheets** | From last exam: what 43% got wrong + extra practice |
| **Exam Prep Packs** | Pre-final bundle from question bank + weak concepts |

**Clear yes line:**

> *"Generate Class 8 Maths Term-1 revision workbook from our syllabus and last year's mistakes."*

### 8.4 Where content comes from

All originally generated or teacher-approved — never copied textbook blocks:

| Source | Use |
|--------|-----|
| CurriculumPack | Structure, scope, chapter order |
| Concept Cards | Approved explanations and examples |
| Past question papers | School question bank |
| Answer-sheet evaluation | Common mistakes, weak concepts |
| School examples | Local context, bilingual notes |
| Official curriculum references | Alignment only — with reuse-rights check |
| Licensed/open materials | Where explicitly allowed — see [§8.8](#88-global-enrichment-studio--global-learning-inspiration-layer) risk levels |
| **Global Enrichment Studio** | International pedagogy inspiration → original local content (Green/Yellow/Red source checks) |

### 8.5 Institutional memory becomes visible

After one exam cycle, the companion can include data no static book has:

> *Last year, 43% of students struggled with convection vs radiation. This year: extra explanation + 5 targeted practice questions.*

The workbook **updates** as the school teaches and examines — a **living book**, not a frozen PDF.

### 8.6 Build sequence (Layer 4 — not Phase 1)

| Order | Capability |
|-------|------------|
| 1 | QP generation |
| 2 | Answer-sheet evaluation |
| 3 | Weak-concept memory |
| 4 | Mistake Recovery Tutor |
| 5 | **School-customized smart workbooks** ← Learning Companion |
| 6 | **Global Enrichment Studio** ← Global Learning Inspiration Layer (Year 2 premium) |
| 7 | Full living textbook (1–2 year horizon) |

Do not start with full textbooks. Start with **revision booklets and mistake recovery sheets** — easiest to approve, easiest to sell.

### 8.7 Approval

Same HITL model: HOD approves CurriculumPack and Concept Cards; teacher approves generated workbook sections before print/distribution to students.

### 8.8 Global Enrichment Studio — Global Learning Inspiration Layer

**Architecture name:** Global Learning Inspiration Layer  
**Product feature name:** **Global Enrichment Studio** (alt: Curriculum Enrichment Layer)

Schools can point StudyNexs at an international **method, worksheet style, activity, assessment pattern, or teaching approach** — and the platform converts the **pedagogical idea** into **original, locally aligned** content for their CurriculumPack.

> **Sticky rule:** *StudyNexs does not copy textbooks. It helps schools turn the world's best teaching ideas into their own approved learning material.*

> **International content can inspire. It must not be copied.**

**Copyright (India):** There is **no copyright in an idea**. Copyright protects **expression** — reproduction, adaptation, translation. Storing a work in computer memory can count as reproduction. The product must **extract the teaching pattern**, then generate **original** StudyNexs content — never copy text, images, or worksheets.

**Global movement:** UNESCO's OER recommendation supports reusing, repurposing, adapting, and redistributing **open** educational resources for local, culturally relevant materials — when **licensing is respected**.

#### What schools say

> *"We liked this international activity. Make an Indian syllabus-aligned version for our Class 6 Science chapter."*

**Wow line:**

> *"Our school can learn from the best education systems in the world — but stay aligned to our board, our students, our language, and our exam pattern."*

#### Bad flow vs good flow

**Example:** School sees a Singapore-style maths worksheet.

| Bad | Good |
|-----|------|
| Upload worksheet → AI rewrites it → school uses it | School adds source/link or describes method |
| Copy protected expression | AI identifies **method**: bar model for word problems |
| Foreign syllabus | Maps to **Class 5 Indian curriculum** (CurriculumPack) |
| | Generates **original** examples — local names, currency, context |
| | HOD approves |
| | Added to Smart Book / Tutor / Practice Pack |

#### Platform workflow

```
School submits source (link, description, or licensed upload)
        ↓
Platform checks license / source risk level
        ↓
Extracts teaching idea only (not prose/images to copy)
        ↓
Maps to target CurriculumPack (class, subject, concept)
        ↓
Generates original local content:
  explanations · examples · worksheets · activities
  board-aligned assessments · local-language versions
        ↓
Adds attribution / source note if required
        ↓
Teacher / HOD approves
        ↓
Content becomes reusable (Concept Cards, Learning Companion, tutor)
```

#### What the platform generates (always original)

- Original explanations  
- Original examples (local context)  
- Original worksheets and activities  
- Indian-board-aligned assessments  
- Local-language versions (e.g. Telugu + English)  

Never: copied paragraphs, traced images, or paraphrased textbook blocks.

#### Source risk levels

| Level | Sources | Platform behaviour |
|-------|---------|------------------|
| **Green** | Open educational resources, public domain, CC BY, CC BY-SA | Allow ingestion for **pattern extraction**; attribution stored; generate original output |
| **Yellow** | CC-NC, government/open with unclear commercial terms, school's own internal material | Flag for review; may block commercial SaaS use of source text; description-only mode preferred |
| **Red** | Paid worksheets, private textbook pages, competitor content, CC-ND, copyrighted images | **Block copy/reproduce**; teacher may describe method in free text only; no upload of protected work |

**Creative Commons (commercial SaaS):**

| License | Commercial adaptation? | Notes for StudyNexs |
|---------|------------------------|---------------------|
| **CC BY** | Yes, with attribution | Preferred OER; attribute inspiration source |
| **CC BY-SA** | Yes, with attribution + ShareAlike | Generated outputs may need compatible licensing policy — legal review |
| **CC-NC** | **No** (noncommercial only) | StudyNexs is commercial → do not adapt NC-licensed **expression**; idea-only mode |
| **CC-ND** | **No adaptations** | No derivative works → description-only; never upload and adapt |

#### When to build

**Not now. Year 2 premium moat** — after:

1. QP generation  
2. Answer-sheet evaluation  
3. Concept weakness memory  
4. AI tutor (Mistake Recovery)  
5. Smart workbooks (Learning Companion)  
6. **Global Enrichment Studio**  
7. Living school-customized textbook  

Requires mature CurriculumPack, Concept Cards, approval flows, and license-check plumbing.

---

## 9. Institutional Memory Layer

> *"StudyNexs remembers your syllabus, your exams, your students' learning patterns, and your decisions — year after year, even when the textbook changes."*

Institutional memory is **not** "record everything." It is **structured, purpose-bound continuity** — the wow factor schools feel when context doesn't reset every June.

### 9.1 Design philosophy

| Principle | Meaning |
|-----------|---------|
| **Continuity, not surveillance** | Structured events + approved artifacts — not WhatsApp/call scraping |
| **Purpose-bound** | Exam data ≠ tutor profiling unless consent allows |
| **Role-gated** | Teachers see pedagogy; admins see ops; parents see own child only |
| **Never overwrite curriculum** | New academic year = new pack version; history maps forward |
| **Compounding value** | More usage → smarter question bank, rubrics, weakness detection |

### 9.2 Memory layers — what is included

#### Layer 1: Curriculum memory (school-wide)

| Memory | Stores | School wow moment |
|--------|--------|-------------------|
| Pack version history | 2025–26 vs 2026–27 Science Class 7 | *"Show what changed in the new book."* |
| Concept lineage map | Old "Conduction" → new "Heat transfer — conduction" | *"Last year's data still applies."* |
| Blueprint evolution | Exam pattern/weightage changes year over year | *"Why did Unit Test 2 feel harder?"* |
| Approved content lineage | Which Concept Cards/rubrics came from which pack | *"Reuse last year's rubric for the renamed topic."* |

#### Layer 2: Academic performance memory (per student)

| Memory | Stores | School wow moment |
|--------|--------|-------------------|
| Concept weakness timeline | Marks lost on "fractions" across UT1, UT2, half-yearly — mapped across pack versions | *"When did this weakness start?"* |
| Intervention → outcome | Remediation given → did marks improve? | *"Did the extra worksheet work?"* |
| Exam attempt history | Per question: marks, AI correction, teacher override reason | *"Every time she lost marks on word problems."* |
| Mastery trajectory | Concept strength over terms | *"Weak on photosynthesis for 3 terms — here's the trend."* |
| Slip-test patterns | Micro-assessments tagged to concepts | *"Class 8B always trips on balancing equations."* |

#### Layer 3: Question & assessment memory (school-private asset)

| Memory | Stores | School wow moment |
|--------|--------|-------------------|
| School question bank | Approved questions tagged concept + difficulty + outcome stats | *"Questions that worked for our kids."* |
| Difficulty calibration | % full/partial/zero marks per question over time | *"This question is too hard for Section A."* |
| Rubric & marking history | Teacher partial-credit patterns vs AI suggestion | *"Our teachers consistently award +1 for show-your-work."* |
| Class mistake patterns | Same wrong approach across students (from answer-sheet eval) | *"40% drew the ray diagram the same wrong way."* |

#### Layer 4: Teacher & HOD decision memory (institutional, role-gated)

| Memory | Stores | School wow moment |
|--------|--------|-------------------|
| Approval audit trail | Who approved pack, paper, marks, Concept Card — when | *"Who signed off this marking scheme?"* |
| Teacher observation notes | Structured, purpose-tagged student notes | *"What did maths teacher note before the parent meet?"* |
| Intervention log | Counselling, extra class, parent call — linked to student + concept | *"What did we already try for this child?"* |
| HOD curriculum decisions | Why topic deprioritized, chapter skipped, blueprint changed | *"Why aren't we testing Chapter 5 this term?"* |

#### Layer 5: Parent & communication memory

| Memory | Stores | School wow moment |
|--------|--------|-------------------|
| Parent interaction timeline | Fee follow-ups, absence calls, meeting notes | *"Escalation history before PT meet."* |
| Concern → resolution | Parent worry → school action → outcome | *"We addressed this last term — here's what happened."* |
| Notice & alert history | What was sent, when, to whom | *"Did they receive the fee reminder?"* |
| PTA / circular archive | Searchable — not lost in WhatsApp scroll | *"What did we tell parents about the picnic?"* |

#### Layer 6: Tutor & remediation memory (consent-gated)

| Memory | Stores | School wow moment |
|--------|--------|-------------------|
| Doubt pattern log | What student asked, which Concept Card used | *"Asked about LCM 4 times — flag teacher."* |
| Mistake Recovery history | Post-exam remediation + retry scores | *"Tutor helped after UT2 — improved in UT3?"* |
| Content gap queue | Concepts missing approved cards | *"System learns what our students struggle with."* |

#### Layer 7: Class & cohort memory (aggregate)

| Memory | Stores | School wow moment |
|--------|--------|-------------------|
| Class weakness heatmap over time | Concepts dragging class down across terms | *"Section A has algebra gaps for 2 years."* |
| Teacher workload memory | Papers set, sheets evaluated, hours saved | *"Saved 120 teacher-hours this exam season."* |
| Cohort comparison (within school) | 7A vs 7B on same pack | *"Same syllabus — why is B behind on grammar?"* |
| At-risk trajectory | Attendance + marks + concept weakness composite | *"These 12 students match last year's dropout pattern."* |

### 9.3 Cross-year mapping example

When `Science Class 7 — 2026–27` replaces `2025–26`:

```
Old concept: "Conduction" (Ch 3, 2025–26)
    ↓ mapped to
New concept: "Transfer of heat — conduction" (Ch 4, 2026–27)
    ↓ carries forward
├── 23 students had weakness flags
├── 4 approved rubrics linked
├── 67 question-bank items tagged
├── Class heatmap: 62% avg mastery
└── 2 intervention outcomes logged
```

**HOD wow line:** *"Last year's weakness data didn't disappear. It moved with the syllabus."*

### 9.4 What memory deliberately excludes

| Exclude | Why |
|---------|-----|
| Raw WhatsApp scraping | Creepy, messy, consent issues |
| Call recordings | High consent burden |
| Emotion/video inference on students | Privacy-sensitive; future only |
| Cross-school student data | Tenant isolation — never |
| Undisclosed disciplinary labels to parents | Liability |
| Cross-purpose profiling without consent | DPDP violation |

### 9.5 Memory rollout by phase

| Phase | Memory that ships |
|-------|-------------------|
| **1.5** | Pack versions, concept map, question bank, eval history, weak concepts |
| **2** | Parent timeline, mastery trajectory, Mistake Recovery log |
| **3** | Intervention log, principal queries, curriculum change tracker UI |
| **4+** | Cohort risk patterns, cross-year principal co-pilot |

---

## 10. Guiding Principles

1. **Evolve, don't restart** — Build on the proven multi-tenant FastAPI core; add AI as additive layers.
2. **Provider-agnostic AI** — All LLM access through one internal gateway; no vendor lock-in.
3. **Human-in-the-loop (HITL)** — AI grades, flags, and reports are *suggestions* until a teacher or admin approves. Trust is the product.
4. **CurriculumPack as source of truth** — Board, book, chapter, topic, and concept hierarchy lives in versioned, school-specific packs. Never overwrite; diff across years. All AI runs against an approved pack, not generic syllabus memory.
5. **Purpose-bound memory (DPDP-aligned)** — Data used only for the purpose consented to; collect the minimum needed; consent specific and revocable.
6. **Cost-aware by design** — Model routing, semantic caching, per-tenant token budgets; AI cost is subscription margin.
7. **Validate before building** — A real school's forced top-3 beats a 100-feature roadmap.
8. **Integrate, don't silo** — Features must reduce teacher work, not add parallel tools.
9. **Structured curriculum, not textbook warehousing** — Metadata, maps, approved content, and references — never full copyrighted books as the primary layer.
10. **Inspire, don't copy** — Global teaching ideas welcome; protected expression never. See [Global Enrichment Studio](#88-global-enrichment-studio--global-learning-inspiration-layer).

---

## 11. Approval Model

Three layers of human approval for consequential outputs:

| Layer | Who approves | What |
|-------|--------------|------|
| **Curriculum** | HOD | CurriculumPack (chapter → topic → concept map); annual rollover diff |
| **Assessment** | Teacher | Question paper, marking scheme, model answers; final answer-sheet marks |
| **Tutor content** | HOD / teacher | Concept Cards (reusable); review-queue drafts for missing concepts |

Tutor chat responses are **not** approved one-by-one. They are served from pre-approved Concept Cards. Unmapped doubts enter the review queue.

### 11.1 AI credits vs approval status

**Credits are charged at generation time** — when the LLM runs — not when a teacher or HOD approves the output. Rejected or abandoned drafts still consume credits; provider cost is already incurred.

| Concept | What it tracks |
|---------|----------------|
| **AI usage / credits** | Every generation attempt (full paper, regen, marking scheme, quality check) |
| **Approval status** | Human review outcome on the artifact — independent of billing |

**Question paper status flow:**

```
Draft Generated → Edited → Submitted for Approval → Approved / Rejected → Published / Archived
```

**Credit rules (school-facing):**

| Action | Credits |
|--------|---------|
| Fresh full QP generation | 5 |
| Generate from question bank | 2 |
| Clone & modify previous paper | 0 |
| Regenerate full paper | 4 |
| Regenerate section | 2 |
| Regenerate one question | 1 |
| Marking scheme generation | 2 (or bundled with paper) |
| Quality check | 1 |
| Export approved paper | 0 |

See [§7.4](#74-school-question-bank-not-cache) for why bank-based generation costs less.

**UI / accountability:** Before generation, show *"This will use N AI credits. Generated drafts consume credits even if not approved."* Principals get a usage log: who generated, class, subject, credits used, approval status, rejection reason.

---

## 12. Suggested Data Models

Core entities to implement (curriculum module):

| Model | Role |
|-------|------|
| `BookEdition` | Publisher, title, edition, year metadata |
| `CurriculumPack` | School × class × subject × academic year × book edition |
| `CurriculumPackVersion` | Immutable approved snapshot; never overwrite |
| `Chapter` | Ordered chapter within a pack version |
| `Topic` | Topic within a chapter |
| `Concept` | Teachable/testable unit; links to mastery |
| `LearningObjective` | Board-aligned outcome where available |
| `ConceptCard` | Teacher-approved explanation, examples, hints (tutor retrieval unit) |
| `SourceReference` | Page/chapter pointer to external book — not full text |
| `ApprovalRecord` | Who approved what, when, which version |
| `QuestionPaper` | Links to `curriculum_pack_id`; draft → approved → bank ingest |
| `QuestionBankItem` | **Atomic reusable question** — full metadata per §7.5.1; memory compounds via eval |
| `RubricBankItem` | Step-wise marking, acceptable/wrong answers, correction notes — eval accuracy |
| `ExamBlueprint` | Stored exam pattern — sections, marks, competency/application %; AI generates inside it |
| `PaperVersion` | Set A/B, re-test, absentees, practice, remedial — same blueprint, different items |
| `TeacherStyleProfile` | Per-teacher generation preferences (school-scoped) |
| `PaperReviewComment` | HOD / exam-incharge threaded review on draft papers |
| `MisconceptionEntry` | Common mistake + remedial activity from eval |
| `RemedialPack` | Post-exam worksheet, class revision plan, parent summary |
| `CurriculumDriftAlert` | Syllabus vs paper/lesson-plan mismatch |
| `InspectionPackSnapshot` | Assembled compliance bundle for board visits |
| `ParentMeetingPack` | PTA-ready student summary |
| `QuestionSimilarityIndex` | Pack-scoped embeddings for duplicate / leakage warnings |
| `PaperQualityReport` | Post-gen checker output (blueprint, marks, coverage, difficulty) |
| `QuestionPerformanceStats` | Expected vs actual difficulty, avg marks, common mistakes (from eval) |
| `ApprovalMemoryEvent` | Structured rejection/approval reasons → improve future generation |
| `QuestionPaperAuditRecord` | Rejected-paper audit trail; salvage via edit/clone/resubmit |
| `MasterQuestionBankItem` | Platform-reviewed generic item; never auto-mixed with school-private |
| `LLMGenerationCache` | Hash of request → cached draft (dedup retries only; not a substitute for bank) |
| `QuestionItem` | Per-question on a paper (transitional; migrates to `QuestionBankItem` on approve) |
| `Rubric` | Marking scheme per question or question type |
| `AnswerSheetEvaluation` | Image, AI suggestion, teacher override, approval status |
| `TutorInteraction` | Doubt log, concept detected, card used, confidence |
| `ContentReviewQueue` | AI-drafted content awaiting teacher approval |
| `InstitutionalMemoryEvent` | Purpose-tagged event for memory timeline (audit + retrieval) |
| `ConceptLineageMap` | Old concept → new concept across pack versions |
| `InterventionRecord` | Structured teacher/admin intervention linked to student + concept |
| `LearningCompanion` | Generated workbook/revision pack linked to CurriculumPack |
| `WorkbookSection` | Chapter companion, revision booklet, mistake sheet, exam prep pack |
| `EnrichmentRequest` | School source submission + risk level + inspiration metadata |
| `SourceAttribution` | License, link, attribution text for approved enriched content |
| `ParentInteractionRecord` | Fee follow-up, meeting, concern — structured communication memory |

Existing models (`Exam`, `ExamMark`, `QuestionPaper`, `StudentTopicMastery`) gain `curriculum_pack_id` and concept-level foreign keys over time.

---

## 13. Feature Catalogue (Detailed)

Features below describe the **full product vision**. Implementation status lives only in [STATUS.md](./STATUS.md).  
Each feature includes: **what it does · who uses it · what it brings to the school**.

### 13.1 School Management Core

Multi-tenant school operations: each school isolated at database level (`school_id` on every row). Subdomain per school (e.g. `sia.studynexs.com`).

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Identity & access** | Password + OTP login, JWT sessions, RBAC | All | Secure, role-appropriate access |
| **Academic structure** | Years, classes, sections, subjects, staff mappings | Admin, HOD | One source of truth for school structure |
| **Students & parents** | Enrollment, linking, profiles, admission records | Admin | No duplicate registers; parent accounts ready |
| **Attendance** | Bulk mark, class view, daily/monthly summaries | Teacher, admin | Fast marking; instant absence visibility |
| **Fees** | Structures, partial payments, atomic receipts, PDF | Admin, parent | No receipt clashes; clean audit trail |
| **Exams & marks** | Exam CRUD, per-question schema, mark entry, performance | Teacher, admin | Question-level insight — not just total marks |
| **Timetable** | Class and teacher slot management | Admin | Central schedule; fewer clashes |
| **Notices** | School-wide and targeted announcements | Admin | Replace notice boards + scattered WhatsApp |
| **Library** | Books, issue/return tracking | Librarian | Basic ops without separate software |
| **Transport** | Routes, stops, student assignments, driver/vehicle | Admin | Parent knows pickup point; ops visibility |
| **Residential** | Hostel blocks, room allocation, warden contact | Warden, admin | Boarding school ops in same system |
| **Events** | School event calendar and records | Admin | Coordination + future parent feed content |
| **Settings** | School profile, logo, academic year switch | Admin | Self-service configuration |
| **Report cards** | Consolidated marks + attendance + AI remark (approved) | Teacher, admin | Hours saved on remark writing |
| **Inspection packs** | Auto-assemble board inspection documents | Admin, principal | Inspection week panic eliminated |

### 13.2 Curriculum & Content

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **CurriculumPack** | Versioned syllabus map per class × subject × year | HOD, teacher | AI runs on *your* book — not generic |
| **AI syllabus mapping** | TOC upload → draft chapter/topic/concept tree | HOD | Setup in hours, not weeks |
| **Annual Rollover Wizard** | Diff old vs new year; approve changes only | HOD | June syllabus shift handled systematically |
| **Master packs** | Clone platform packs (CBSE/SSC/publisher) | HOD | 20 schools same book → work once |
| **Curriculum Change Tracker** | Added/removed/moved/renamed report | HOD, principal | Teachers briefed accurately on new book |
| **Concept Cards** | Approved explanations for tutor retrieval | Teacher, HOD | Reusable teaching content; safe AI answers |
| **Content Review Queue** | AI drafts → teacher approves once → reusable | Teacher | Gap-filling without answering same doubt 100× |
| **Exam blueprint** | Section weights, question types per pack | HOD | Papers match school's actual exam pattern |

### 13.3 Teacher AI

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Question paper generation** | Board-style paper from CurriculumPack in ~20 sec | Teacher | 3+ hours saved per paper |
| **Marking scheme generation** | Auto rubric + model answers with paper | Teacher | Consistent, fair marking criteria |
| **Answer sheet evaluation** | Snap photo → AI marks + correction summary → approve | Teacher | 4+ hours saved per class per exam |
| **Objective auto-grade** | Deterministic MCQ/fill scoring | Teacher | Instant for objective sections |
| **Subjective grading assist** | Suggested marks + written feedback | Teacher | Starting point for essays/show-work |
| **Student summary** | One-click narrative from marks + attendance | Teacher | Parent meetings prep in seconds |
| **Lesson plans / worksheets** | Generated from pack concepts + mastery gaps | Teacher | Daily prep time reduced — **today: template v1 only; AI v1 in A-OS** ([§23](#23-ai-intelligent-school-os)) |
| **Time-saved dashboard** | Cumulative hours saved per teacher/school | Principal | ROI proof for management/trust |

### 13.4 Topic Mastery & Learning Intelligence

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Student mastery profile** | Per-concept strength/weakness over time | Teacher, HOD | Know *what* student doesn't know — not just marks |
| **Class heatmap** | Color map of weak concepts across class | Teacher, HOD | Target re-teaching precisely |
| **Mastery flags** | AI alert on sustained weakness (teacher-reviewed) | Teacher | Early intervention before final exams |
| **Mastery digest** | Periodic class/school academic summary | HOD, principal | Management reporting without manual compile |
| **Personalized remediation** | Worksheets from weakness gaps | Teacher, student | Targeted homework — not generic |
| **Adaptive difficulty** | Question difficulty from school's own results | Teacher | Papers calibrated to class level |

### 13.5 Student AI & Tutor

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Mistake Recovery Tutor** | Post-exam: what went wrong → explain → practice → retry | Student | Closes loop same day as results |
| **Concept Card tutor** | Answers from approved school content only | Student | Safe, syllabus-aligned — not random ChatGPT |
| **Doubt pattern log** | Tracks repeated struggles → flags teacher | Teacher | System surfaces students needing help |
| **Voice tutor** | STT/TTS in Indian languages | Student | Tier 2/3 accessibility |
| **Digital diary** | Assignments and revision planner | Student | Organization without separate app |

### 13.6 Parent Experience

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Child progress feed** | Visual timeline: results, streaks, achievements | Parent | Daily engagement; word-of-mouth referrals |
| **Moments feed** | Event photos, participation highlights | Parent | Emotional connection to school |
| **Fee payment** | Status, reminders, Razorpay pay, receipts | Parent | Faster collection; less admin chasing |
| **Weekly AI report** | Auto progress summary push notification | Parent | Proactive communication — fewer "what's happening?" calls |
| **Structured teacher chat** | 1:1 per subject — not group WhatsApp chaos | Parent, teacher | Professional, auditable communication |
| **WhatsApp alerts** | Results, fees, absence notifications | Parent | Meets parents where they are |
| **Multi-child** | One parent account, multiple children | Parent | Family-friendly |
| **Telugu/English** | Regional language support | Parent | SSC/state board parent accessibility |

### 13.7 Communication Hub

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **AI circular generation** | Draft notice from bullet points → approve → send | Admin | 30 min notice → 2 min |
| **Voice announcements** | Multilingual TTS broadcasts | Admin | Reach illiterate/low-literacy parents |
| **PTA summaries** | AI digest of meeting → action items | Admin | Accountability without hours of writing |
| **Parent chatbot** | FAQ from school knowledge base | Parent | Routine queries off admin desk |

### 13.8 Admin Intelligence — "AI School Brain"

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Principal co-pilot** | Natural language over school data | Principal | "Which Class 9 students are at risk?" — instant |
| **Early-warning** | Fail/attendance/behavior risk (human-reviewed) | Principal, teacher | Prevent dropouts before they happen |
| **Fee-default prediction** | Families at risk before dropout | Admin | Proactive fee follow-up |
| **Teacher workload** | Overload detection across subjects | Principal | Fair distribution; retention |
| **Memory timeline** | Searchable institutional history | Principal, HOD | Decisions and context never lost |
| **Smart scheduling** | Timetable/transport optimization | Admin | Long-term ops efficiency |

### 13.10 StudyNexs Learning Companion

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Chapter Companion Notes** | Per-chapter summary beside physical textbook | Teacher, student | Study aid without replacing NCERT |
| **Revision booklets** | Term/chapter revision from school's pack | Teacher | Exam prep aligned to *their* syllabus |
| **Practice workbooks** | Question sets from pack + difficulty calibration | Teacher | Homework that matches class level |
| **Mistake Recovery Sheets** | Extra practice from last exam's common errors | Teacher, student | Targets what class actually got wrong |
| **Exam prep packs** | Pre-board bundle from question bank + weak concepts | Teacher, HOD | One-click exam season readiness |
| **Living workbook** | Auto-updates with % struggled, extra explanations | HOD, teacher | *"Book gets smarter every exam"* |
| **Printable smart book** | PDF/print-ready school-branded companion | Admin, teacher | Physical distribution where needed |

### 13.11 Global Enrichment Studio

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Inspiration submission** | Link/describe international method, activity, or assessment style | HOD, teacher | Capture "we liked this" without copying |
| **License & risk check** | Green / Yellow / Red source classification | Platform | Commercial SaaS stays legally safe |
| **Pattern extraction** | Identifies pedagogy (e.g. bar model, inquiry lab) — not prose | Platform | Ideas in, original content out |
| **Local alignment** | Maps to CurriculumPack; local examples + board exam format | Platform | Singapore method, SSC exam style |
| **Attribution** | Source note where license requires | Platform, HOD | Transparent provenance |
| **Approval & reuse** | HOD/teacher approve → Concept Card / workbook / tutor | HOD, teacher | One approval, whole school benefits |

*Phase: Year 2 premium — after Learning Companion. See [§8.8](#88-global-enrichment-studio--global-learning-inspiration-layer).*

### 13.12 Platform & Business

| Feature | What it does | Who | School benefit |
|---------|--------------|-----|----------------|
| **Multi-tenant SaaS** | Isolated school environments | Platform | Secure, scalable |
| **LLM gateway** | Multi-provider AI with failover | Internal | No vendor lock-in; cost control |
| **Usage metering** | Per-feature token/cost tracking | Platform, school | Transparent AI economics |
| **RAG per pack** | Embeddings scoped to school's curriculum | Internal | Accurate retrieval |
| **Billing** | Razorpay subscriptions schools + parents | Platform | Monetization |
| **Onboarding console** | Platform operator provisions schools | Platform | Scale beyond white-glove |
| **DPDP compliance** | Consent, purpose tags, retention | All | Legal trust for minors' data |

---

## 14. Finance Command Center (Optional Module)

**Product name:** StudyNexs Finance Command Center  
**Positioning:** Optional paid module — **fee tracking, reminders, follow-up memory, salary/expense overview, management dashboard.**

> **Sticky note:** Finance is a **deal-expander, not the wedge.**  
> Teachers love QP/evaluation. Principals love academic reports. Parents love communication. **Management loves financial visibility.** Finance helps close deals — but it must not become the first technical mountain.

### 14.1 Strategic fit

| Stakeholder | What they love | Finance adds |
|-------------|----------------|--------------|
| Teachers | QP, grading, daily workflow | — |
| Principals | Academic reports, inspection readiness | Collection visibility |
| Parents | Communication, child progress | Fee reminders, clear dues |
| **Management / trust** | ROI, control | **Revenue snapshot, branch comparison, cashflow view** |

Build finance **close enough to help sales, far enough to not distract engineering** from the exam loop and CurriculumPack moat.

### 14.2 Phase 1 — Fee Visibility + Reminders (early)

**When:** Can ship early — connects naturally to parent communication and pilot retention.  
**For the next 8 weeks:** Build **only** fee reminder + collection visibility if a pilot school needs it for retention. Nothing heavier.

| Capability | What it does | Who |
|------------|--------------|-----|
| **Fee due dashboard** | At-a-glance: total due, collected, outstanding | Admin, accounts |
| **Overdue list** | Students/families past due, sortable, actionable | Admin, accounts |
| **WhatsApp / SMS reminders** | Automated fee due / overdue nudges with ledger link | Admin → parent |
| **Promise-to-pay notes** | Record parent commitment ("will pay by 15th") + follow-up date | Admin |
| **Collection status** | Paid / partial / overdue / promised per student | Admin |
| **Class-wise / branch-wise pending** | Drill-down for multi-branch schools | Management, admin |

**Why Phase 1 first:** Useful, sellable, not too complex. Reuses notices/outbox patterns and parent comms — no accounting engine required.

### 14.3 Phase 2 — Management Finance Snapshot (later)

**When:** After Phase 1 proves value and schools ask for management reporting.  
**Still not accounting** — manual entry + summaries, not a general ledger.

| Capability | What it does |
|------------|--------------|
| Monthly revenue | Fee collection rollup by month |
| Expenses (manual entry) | Simple expense log — categories, amounts, dates |
| Salary payable summary | Outstanding salary obligations (entered, not computed payroll) |
| Transport expense summary | Route/vehicle cost rollup |
| Cashflow view | Money in (fees) vs money out (expenses + salaries) — directional |
| Branch comparison | Side-by-side pending + collected across branches |

### 14.4 Phase 3 — Deeper Finance Ops (only if schools repeatedly ask)

Build **only** when multiple schools explicitly request and will pay:

- Payroll processing  
- Vendor payments  
- Approval workflows (expense/payment sign-off)  
- Transport route profitability  
- Tally export  
- Audit reports  

### 14.5 Hard boundary — do NOT build (early)

These will eat the company alive too early. **Explicitly out of scope** for StudyNexs Finance Command Center in Phases 1–2:

| Do not build | Why |
|--------------|-----|
| GST engine | Tax compliance is a product company |
| Tax compliance / filing | Same |
| Bank reconciliation | Requires banking integrations + ledger truth |
| Full double-entry ledger | You become an accounting ERP |
| Complete payroll compliance (PF, ESI, TDS) | Regulatory depth ≠ school ops wedge |

If a school needs full accounting, **integrate with Tally / Zoho Books** in Phase 3+ — do not rebuild them.

### 14.6 Relationship to existing fees module

Today the platform has **atomic fee receipts, partial pay, and PDF receipts** (built). Finance Command Center **extends** that with visibility, reminders, and management reporting — it does not replace the core fee collection API.

---

## 15. Architecture (High Level)

```
Clients:   Next.js admin-web (today)  →  teacher / parent / student portals (Phase 2+)
                    │  HTTPS (Azure Front Door + WAF → Nginx)
API:       FastAPI modular monolith — Auth · Tenant · RBAC · SMS modules · curriculum/ · ai/ · mastery/
                    │
         ┌──────────┼──────────┬──────────────┐
    LLM Gateway   Job Queue   RAG (Qdrant)   Object Storage
    (multi-provider) (Arq)   per CurriculumPack  (Azure Blob)
         │
Cross-cutting:  usage metering · audit log · event/outbox · per-tenant isolation
```

**Stack:** FastAPI (Python 3.11+), PostgreSQL 16 + JSONB, Redis 7, Qdrant, Arq, Next.js 16, Flutter (mobile, Phase 2+), Azure (Container Apps, Postgres Flex, Blob, Key Vault), India region.

**Design pattern:** Event stream + purpose-tagged memory + agents. School actions (attendance marked, paper approved, mark entered, notice sent) become structured events that power intelligence over time — not raw surveillance of WhatsApp or calls.

---

## 16. Moat & Differentiation

1. **School-specific CurriculumPacks** — Not generic board memory. Each school's book, edition, chapter order, and topic map — versioned and diffable year over year.
2. **Curriculum Change Tracker** — Standalone value: schools see exactly what shifted when publishers update books.
3. **Closed exam loop** — Pack → generate paper → approve key/rubric → snap sheets → evaluate against approved source → approve marks.
4. **Cross-year concept continuity** — Mastery and weakness history survives book changes via concept mapping between pack versions.
5. **Human-in-the-loop trust** — AI assists; teachers and HODs approve packs, papers, and marks. Required for Indian schools and DPDP.
6. **Compounding school data** — Private question bank, rubrics, difficulty calibration, concept-level performance — all scoped to packs.
7. **Learning Companion** — School-customized workbooks beside textbooks; gets smarter every exam.
8. **Global Enrichment Studio** — World's best teaching *ideas*, locally aligned — premium Year 2 moat.
9. **Purpose-bound institutional memory** — Longitudinal intelligence with parent consent and role-gated access, not surveillance.

Schools buy **time saved, better academics, parent trust, and inspection readiness** — not "AI."

---

## 17. Phased Vision

High-level sequencing intent (effort and scope in [STATUS.md](./STATUS.md)):

| Phase | Focus |
|-------|-------|
| **Phase 0** | AI platform foundation — gateway, job queue, metering, core fixes |
| **Phase 1** | Pilot-ready SMS + teacher AI (QP, report cards, eval MVP, mastery, tutor templates) + admin IA hubs |
| **Phase 1.5** | CurriculumPack v1 + exam loop hardening + Concept Cards + pack-grounded QP/eval |
| **A-OS** | **AI-Intelligent OS — Layer 1 foundation + AI lesson plan v1 + weekly teacher brief** ([§23](#23-ai-intelligent-school-os)) |
| **B-OS** | Close the loop — heatmap QP, tutor assignments, subjective eval feedback LLM |
| **Phase 2** | Flutter parent/student apps, tutor RAG, fee payment, progress feed |
| **C-OS** | Intelligent UX — dashboard suggestions, document inbox (classify + confirm), principal narrative |
| **Phase 2b** | **Finance Command Center Phase 1** (optional) |
| **Phase 3** | Communication hub, principal co-pilot, institutional memory UI |
| **D-OS** | Named workflow orchestration (post-exam loop, week-ahead planning) — only if A–B adopted |
| **Phase 4** | **Learning Companion** — revision booklets, practice workbooks, mistake sheets |
| **Phase 5** | **Global Enrichment Studio** + voice, vernacular UI |
| **Phase 6** | Full living textbook; vision/video tutor |
| **Finance Phase 2–3** | Management snapshot → deeper ops — on demand |
| **Parallel** | DPDP compliance, billing, onboarding console, multi-board expansion |

---

## 18. Go-to-Market

- **Pilot-first, design-partner model** — One school, discounted or free, in exchange for co-defined scope and a reference case.
- **Wedge:** AI question papers + answer sheet grading assist — measurable teacher time saved during exam weeks.
- **Sales motion:** Relationship-led; principal identifies need, management/trust approves budget. Demo with outcomes, never lead with "AI."
- **Land and expand:** Nail one board (SSC Telangana) deeply, then add boards as config + content packs.
- **Optional module upsell:** StudyNexs Finance Command Center — sell to management/trust after academic wedge lands; Phase 1 (reminders + visibility) only until pilot retention needs it.
- **Pricing tiers:** Free creates interest · Pro closes small schools · **Pro+ is the main growth plan** · Enterprise protects chains. Full gates and credit pools: [PRICING.md](./PRICING.md). First 3–5 schools: sell **Paid Pilot = Pro+ for one class + one subject**, not four equal choices.
- **Validation discipline:** Forced top-3 from pilot school, willingness-to-pay early, written checklist before building. See [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md).

---

## 19. Compliance & Trust

### DPDP & children's data

Under India's DPDP Act, a child is under 18; parents/guardians are the Data Principal for children. Consent must be specific, informed, purpose-bound, limited to necessary data, and withdrawable.

**Every data event should carry:**

| Field | Purpose |
|-------|---------|
| `school_id` | Tenant isolation |
| `student_id` | Subject of data (where applicable) |
| `purpose_tag` | Why this data is processed |
| `source` | Which feature created the event |
| `data_fields_used` | Minimization audit trail |
| `retention_policy` | When data expires |
| `created_by` | Actor |
| `approval_status` | HITL state where applicable |

**Purpose tags (do not mix casually):**

| Tag | Used for |
|-----|----------|
| `curriculum_mapping` | Pack creation, TOC extraction, rollover diff |
| `question_generation` | QP and marking scheme generation |
| `exam_evaluation` | Answer-sheet images, AI mark suggestions |
| `ai_tutor` | Tutor interactions, doubt logs |
| `student_summary` | Progress reports and narratives |
| `parent_alert` | WhatsApp/push notifications to parents |

Answer-sheet data collected for `exam_evaluation` must not silently become `ai_tutor` profiling unless consent and school policy allow cross-purpose use.

### Security baseline

- **Data residency in India** — Encryption at rest and in transit; field-level encryption for sensitive PII  
- **AI transparency** — Disclose AI involvement; marks show approving teacher name  
- **Child safety** — Content moderation, age-appropriate filters, no PII in LLM prompts where avoidable  
- **Multi-tenant AI isolation** — Per-pack / per-tenant RAG namespaces; never mix schools  

---

## 20. Demo & Wow Moments by Persona

Use these lines in pilot demos, sales conversations, and product videos. Lead with **outcomes**, never "AI."

| Persona | Demo moment | Script |
|---------|-------------|--------|
| **HOD** | Curriculum Change Tracker | *"Here's exactly what changed in the new Science book — and which old topics map where."* |
| **HOD** | Global Enrichment Studio | *"We liked Singapore bar models — make an SSC-aligned version for our Class 6 fractions chapter."* |
| **HOD** | Learning Companion | *"Generate Term-1 revision workbook from our syllabus — with extra practice on what 43% got wrong last year."* |
| **Teacher** | QP generation | *"Class 10 Maths paper — 100 marks, board format — in 20 seconds. You edit, approve, print."* |
| **Teacher** | Answer-sheet eval | *"Snap 40 sheets. AI suggests marks and corrections. You review in under an hour, not six."* |
| **Teacher** | Student weakness | *"This student lost marks on fractions in 4 tests — here's the pattern and what we tried."* |
| **Principal** | Time saved | *"Your school saved 340 teacher-hours this exam season. Here's the breakdown."* |
| **Principal** | Early warning | *"These 12 Class 9 students show the same pattern as last year's failures — act now."* |
| **Parent** | Progress feed | *"Your child's photosynthesis score improved after remedial — here's before and after."* |
| **Management** | ROI | *"Teachers go home earlier. Parents stop calling. Inspection records are one click away."* |
| **Management** | Fee visibility | *"₹4.2L outstanding — 23 families overdue. Reminders sent. 8 promised to pay by Friday."* |

### 18.1 Day-in-the-life (exam week — teacher)

1. Morning: bulk attendance marked in 2 minutes  
2. Period 3: generate Unit Test paper from approved CurriculumPack → edit 2 questions → approve  
3. Print papers; conduct exam  
4. Evening: snap answer sheets on phone → review AI mark suggestions over chai → approve  
5. System updates mastery, flags 3 students for Mistake Recovery Tutor  
6. Next day: parent app shows results (after teacher publish gate)  

### 18.2 Day-in-the-life (June — HOD)

1. New textbooks arrive  
2. Upload TOC to Annual Rollover Wizard  
3. Review diff: 4 topics added, 2 removed, 1 renamed  
4. Approve → new pack active  
5. Last year's weakness data maps forward automatically  

---

## 21. Pricing & Plans

Commercial packaging lives in **[PRICING.md](./PRICING.md)** — the canonical doc for tiers, feature gates, AI credit pools, add-ons, and pilot sales guidance.

| Plan | Strategic role |
|------|----------------|
| **Free** | Controlled demo — QP quality sample, not production |
| **Pro** | Exam starter for small schools / first paid conversion |
| **Pro+** | **Main growth plan** — QP + answer evaluation + progress intelligence |
| **Enterprise** | Multi-branch, custom controls, Finance Command Center, negotiated credits |

**Rules:** No unlimited AI in any tier. Credits charge at generation, not approval ([§11.1](#111-ai-credits-vs-approval-status)). Finance Command Center is an Enterprise upsell / Pro+ basics ([§14](#14-finance-command-center-optional-module)).

**First sales motion:** Publicly show all four tiers; in conversation pitch *"Pro+ Exam Intelligence for one class and one subject"* as the paid pilot.

Rupee prices are **not locked** — validate in pilot meetings before publishing.

---

## 23. AI-Intelligent School OS

> **Build status:** [STATUS.md](./STATUS.md) — snapshot, A–D-OS tracks, lesson-plan gate.  
> **Decided 2026-06-15:** This is the product north star for AI beyond individual sparkle features.

### 23.1 What it means (and what it does not)

**Not:** every screen has a sparkle button or a chat box.

**Yes:** the system **knows context** (class, subject, week, syllabus, exam results, mastery gaps) and **proposes the next right action** — with a teacher or admin **always approving** before anything reaches parents or published exams.

**North star (Monday morning test):**

> *"Monday morning, the OS tells each teacher what to teach, what to reteach, what to assess, and what to communicate — grounded in their school's data."*

**Today (partial):** mastery → QP deep links, exam eval loop, template tutor, report/mastery LLM narratives, dashboard analytics. **Gap:** planning (syllabus week, lesson plans, timetable context) and **proactive suggestions** (not just tools).

### 23.2 Layer model — map to product phases

| Layer | Capability | Why | Product phase | Status |
|-------|------------|-----|---------------|--------|
| **L1 Foundation** | Curriculum graph, academic calendar, coverage tracking, unified student/topic state, audit + HITL | Without L1, AI lesson plans are generic ChatGPT | **A-OS** (late P1 / P1.5) | ⬜ — free-text topics today |
| **L2 Lesson plans** | Structured LLM plans grounded in L1 + timetable | Daily teacher utility | **A-OS** | 🟡 template only |
| **L3 Extensions** | Heatmap QP, bank intelligence, eval feedback LLM, tutor assign, report v2, ops briefs | Close exam → teach → communicate loop | **B-OS** (P1.5 → P2) | 🟡 partial |
| **L4 Intelligent UX** | Persona command centers, suggestion cards, document inbox, explainability | Feels like an OS, not a module list | **C-OS** (P2 → P3) | ⬜ |
| **L5 Workflows** | Post-exam loop, week-ahead planning, parent-concern flow | Multi-step orchestration | **D-OS** (P3+) | 🔭 |

**Prerequisite rule:** Do not ship L4–L5 autonomous routing before L1 + at least one L2 feature is trusted in pilot.

### 23.3 Hybrid architecture (rules + ML + LLM + workflows)

Use the **cheapest correct engine** per step — not "agents everywhere."

| Step type | Engine | Examples in StudyNexs |
|-----------|--------|------------------------|
| Policy, eligibility, flags | **Rules** | Mastery compute, flag rules, RBAC, credit caps |
| Classification, similarity, anomalies | **ML / heuristics** | Objective grading, duplicate-Q warning (planned), upload classify (C-OS) |
| Language generation | **LLM** | QP, report remarks, mastery narratives, vision OCR, lesson plan prose (A-OS) |
| Multi-step jobs with tools | **Workflow** (not open-ended agent) | Async eval job, post-exam loop (D-OS) |

**Document upload router (user idea):** classify upload → **user confirms** → specialist pipeline. Phase **C-OS**, not pilot. Misrouting answer sheets into mastery is unacceptable.

### 23.4 Lesson plan AI — minimum spec

First new AI surface after L1 foundation (or interim syllabus-week model):

1. Teacher picks class + subject + **week** (or accepts system suggestion).
2. UI shows: topics planned, mastery gaps, upcoming exam.
3. **Generate plan** → structured JSON (objectives, period breakdown, differentiation, homework) — **1 credit**, saved as draft.
4. Actions: **Generate slip test** (→ QP), **Add to timetable notes**, **Copy homework to notices**.
5. Class incharge can **approve as school template** for reuse.

**Inputs (rules + DB):** period length from timetable, topics from syllabus plan or mastery lag, prior week summary, exam countdown, school board/language prefs.

**Outputs (structured, not essay):** objectives, hook/explain/practice/exit per period, support + extension, homework link.

**Avoid:** long prose, plans disconnected from exams/mastery, auto-publish to parents.

**Today:** `lesson_plan_service` uses `ai_model="template-v1"` — placeholder until A-OS.

### 23.5 Layer 3 enhancement backlog (prioritized for Indian pilot)

**A. Teaching & assessment** — QP from heatmap (bulk), question-bank auto-tag, subjective **feedback** LLM only (marks stay heuristic), misconception → tutor assign, report remark v2.

**B. Planning & operations** — AI lesson plan (above), weekly class-incharge brief, substitute pack PDF, notice drafts from bullets.

**C. People** — admission doc triage, guardian comms drafts (HITL).

**D. Student** — adaptive tutor paths (rules), practice QP after tutor, "study tonight" from mastery + tomorrow timetable.

**E. Principal** — school health narrative (extends dashboard analytics), AI credit forecast, anomaly alerts.

### 23.6 Layer 4 — Intelligent UX

- **Command center per persona** — admin: ops + AI usage; teacher: periods + plans + pending approvals; student: tutor + homework.
- **Suggestions, not modules** — e.g. *"Period 4 tomorrow has no plan — generate from week 12?"*
- **Document inbox** — upload → classify → confirm → pipeline.
- **Explainability** — every AI output: data used, model, credits, edit-before-use.

### 23.7 Layer 5 — Named workflows (agents only here)

| Workflow | Steps |
|----------|--------|
| **Post-exam loop** | Marks in → mastery recompute → flags → suggest QP → queue tutor lessons |
| **Week-ahead planning** | Syllabus week + gaps → draft lesson plans → link slip tests |
| **Parent concern** | Teacher note → draft parent message → incharge approve → notify |

Each step is an existing **service**; orchestration adds retries, notifications, and audit — not a single mega-agent.

### 23.8 Sequencing vs CurriculumPack

| Track | Relationship |
|-------|----------------|
| **Phase 1.5 CurriculumPack** | Moat — pack-grounded QP, eval, mastery, tutor RAG |
| **A-OS** | Runs **in parallel** once pilot gate passes — can start with interim "syllabus week" before full pack |
| **B-OS** | Accelerates after pack tags exist; some items work today (QP deep links) |
| **C-OS / D-OS** | After daily use of A–B |

**Do not delay pilot** for full OS vision. **Do not build D-OS** before teachers use lesson plans and post-exam suggestions weekly.

---

## 24. Related Documents

| Document | Purpose |
|----------|---------|
| [STATUS.md](./STATUS.md) | What's built vs planned **as of today** — includes **A–D-OS** track status |
| [PRICING.md](./PRICING.md) | **Tiers, feature gates, AI pools, add-ons, pilot packaging** |
| [TRACK_AB_EXECUTION.md](./TRACK_AB_EXECUTION.md) | **Start here** — Track A + B execution |
| [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md) | Pilot meeting questions + demo script |
| [DECISION_LOG.md](./DECISION_LOG.md) | Architectural and product decisions (append-only) |
| [docs/api/](./api/) | API integration docs for developers |
| [docs/runbooks/](./runbooks/) | Operational runbooks |
