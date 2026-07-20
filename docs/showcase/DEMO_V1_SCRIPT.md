# Reference School Demo v1 — Day in the Life

**School:** ARM International School · tenant `reference`  
**Duration:** 45–60 minutes  
**Audience:** Principal (+ optional teacher / parent personas)  
**Goal:** *"I understand why I should buy StudyNexs."*

**Prep (5 min):**

```powershell
cd D:\Projects\studynexs-platform\studynexs-dev\apps\api
python scripts/seed_reference_school.py
python scripts/smoke_reference_school.py   # expect ALL GREEN — API on http://localhost:8000
```

**Admin-web:** `NEXT_PUBLIC_TENANT_SLUG=reference` · `NEXT_PUBLIC_API_URL=http://localhost:8000`

| Role | Username | Password |
|------|----------|----------|
| Principal | `principal` | `Demo@1234` |
| Class 10 incharge (curriculum approve) | `teacher1` | `Demo@1234` |
| Maths teacher | `teacher6` | `Demo@1234` |
| Parent | `parent_demo` | `Demo@1234` |
| Student | `student_demo` | `Demo@1234` |

---

## How to present it

**Do not** walk feature-by-feature. Present **one school day** — five roles, one story.

Every AI moment must trace back to the curriculum foundation:

```
Textbooks & syllabus inputs
        ↓
Curriculum Intelligence  ← Journey 0
        ↓
Assessment Intelligence  ← Journey 2
        ↓
Learning Intelligence    ← Journey 2 analytics + Journey 4
        ↓
Teacher Intelligence     ← Journey 1 + 3
        ↓
School Intelligence      ← Journey 5
```

**Say once, early:** *"StudyNexs doesn't bolt AI onto a spreadsheet. It learns your school's academic model first — then every paper, lesson, and insight is grounded to what you approved."*

---

## The day (role-based timeline)

| Time | Role | Journey | What happens |
|------|------|---------|--------------|
| 08:00 | Principal | **0** | School intelligence is live — curriculum knowledge constructed |
| 08:30 | Teacher | **1** | Lesson prepared from approved curriculum |
| 10:00 | Teacher + Student | **3** | Class runs — attendance, lesson, activity |
| 13:00 | Teacher | **2** | Assessment — paper, marks, analytics |
| 15:00 | Teacher | **2** | AI assists evaluation and review |
| 17:00 | Principal | **5** | School health and insights |
| 18:00 | Parent + Student | **4** | Progress and AI summary |

---

## Journey 0 — School Intelligence Setup (08:00 · Principal)

**Story:** *How StudyNexs learned ARM International School's academic model.*

> **Demo note:** ARM International School is **pre-seeded** so you don't spend 30 minutes creating a school live. Frame it as: *"Your school is already onboarded — let me show you what StudyNexs constructed from your syllabus, and how you'd extend it."*

### 0.1 — School context (3 min)

- Login: `principal` → `/dashboard`
- **Show:** 288 students, attendance %, fees — a living school (not an empty tenant)
- `/dashboard/settings` — profile, academic year, enabled modules
- `/dashboard/classes` — Grades 1–10, sections

**Say:** *"When a real school signs, they get their own tenant. This Reference School shows the fully populated outcome."*

### 0.2 — Curriculum pack — structured knowledge (12 min)

- Navigate: **Teaching → Curriculum** (`/dashboard/teaching/curriculum`)
- Open **Class 10 · Mathematics** approved pack

**Show explicitly (this is the Journey 0 payoff):**

| Layer | What to point at |
|-------|------------------|
| Chapters | 14 SSC chapters (Real Numbers → Statistics) |
| Topics | Per-chapter topic rows |
| Learning outcomes | LO on chapter 1; concepts on all chapters |
| Blueprint | 80-mark SSC structure (Sections I–III + Part-B) — *seed/API today; UI editor coming* |
| Knowledge spine | Chapter → topic → concept hierarchy + concept/edge counts |
| Grounding preview | Pack grounding panel — RAG indexed, approved version |
| Audit trail | Approve events — KG spine + RAG index succeeded |

**Say:** *"This isn't a folder of PDFs. StudyNexs built a queryable curriculum graph. Every AI feature downstream reads from here."*

### 0.3 — Optional live extension (5 min, if time)

- **Create a draft pack** for another subject OR add one chapter to a draft
- **Document ingest** (`/dashboard/teaching/document-ingest`) — upload a worksheet/notes PDF → show ingest pipeline
- **Content review queue** — if items exist, show human-in-the-loop extraction review

**Honest limits today (don't oversell):**

- No dedicated "upload textbook PDF → auto syllabus" wizard
- No interactive knowledge-graph canvas (hierarchical spine list, not node graph)
- Blueprint is seeded for demo; not editable in UI yet

---

## Journey 1 — Teacher Planning (08:30 · teacher6)

**Story:** *From approved curriculum to today's lesson.*

1. Login: `teacher6` → `/dashboard/teaching`
2. **Lesson plans** (`/dashboard/teaching/lesson-plans`)
   - Open draft: *Class 10 A — Mathematics: Quadratic Equations*
   - Show generate / review / publish flow
3. **Curriculum tab** — trace lesson topic back to approved pack chapter

**Say:** *"The teacher didn't start from a blank page. The lesson is grounded to your approved Class 10 Maths map."*

---

## Journey 3 — Classroom (10:00 · teacher6 + student_demo)

**Story:** *A normal teaching day.*

1. **Attendance** — `/dashboard/attendance` — Class 10-A, today + recent history
2. **Timetable** — teaching hub or timetable view — teacher6's Maths slots
3. **Lesson** — link to lesson plan from Journey 1
4. **Activity substitute for homework** — `/dashboard` notices or a notice visible to students/parents (*homework module not built — use notice titled "Class work"*)
5. **Student** — login `student_demo` → `/student` — attendance, tutor (`/student/tutor`) — fractions remedial from exam misconception

**Say:** *"Teacher, student, and parent all see the same school day — not three disconnected apps."*

---

## Journey 2 — Assessment (13:00 + 15:00 · teacher6 + teacher1)

**Story:** *Grounded assessment, not random AI questions.*

### 13:00 — Paper and exam

1. **AI Papers** (`/dashboard/teaching/ai-papers`)
   - Show generate flow grounded to approved pack
   - **In-charge approves:** logout → `teacher1` → approve paper (HITL)
2. **Exams** (`/dashboard/teaching/exams` or exams module)
   - Open Mid-Term / Final for Class 10-A Maths — **144 exams seeded**
   - Gradebook / marks visible

**Say:** *"Questions come from your approved curriculum — incharge approves before students see them."*

### 15:00 — AI evaluation (show if seeded; otherwise narrate)

- Answer sheet evaluation workflow (OCR + async AI + teacher review)
- **Today:** marks and gradebook are demo-ready; **full eval loop needs seed completion (P1)**
- Class outcome → gradebook or briefing performance widget

**Say if eval not seeded:** *"The evaluation pipeline is built — for today's demo you see marks and analytics; live OCR eval is the next seed step."*

---

## Journey 5 — Principal Intelligence (17:00 · principal)

**Story:** *One pane of glass for the whole school.*

1. Login: `principal` → `/dashboard` (Morning Briefing)
2. **School health:** attendance %, fee collection, headcount (288 students)
3. **Curriculum progress:** link to approved packs count / pending QP approvals
4. **Learning signal:** class performance widgets, exam summaries
5. **Teacher signal:** pending approvals, teaching activity
6. **Recommended actions** (verbal): *"3 students below threshold in Class 10 Maths — tutor already flagged for student_demo"*

**Say:** *"This isn't 20 dashboards. It's one school story — health, curriculum, learning, teachers — connected."*

---

## Journey 4 — Parent & Student (18:00 · parent_demo + student_demo)

**Story:** *Families stay informed without calling the office.*

1. **Parent** — `parent_demo` → `/parent`
   - Child: **Sai Rao**, Class 10-A roll 1
   - Attendance last 7 days
   - Fees snapshot (read-only)
   - Notice / class work (Journey 3 substitute)
2. **Parent copilot** — scripted prompt: *"Summarise my child's week in Maths"*
3. **Student** — `student_demo` → `/student/tutor` — personalised fractions lesson

**Say:** *"Parent and student experiences are grounded to the same curriculum and assessment data the school approved."*

---

## Close (2 min)

> *"What you saw is one tenant — ARM International School. When you sign, we create **your** school, import **your** data, and your staff get the same journeys. StudyNexs learned your curriculum first; everything else followed."*

**Next step:** discovery → signing → tenant provisioning → data import → pilot on **their** tenant (never Reference School).

---

## Engineering gaps to close (for seamless demo)

| Gap | Affects | Priority |
|-----|---------|----------|
| Seed AI eval pending review (1 sheet) | Journey 2 @ 15:00 | P1 |
| Pre-seed one approved question paper | Journey 2 @ 13:00 | P1 |
| Parent "class work" notice seeded | Journey 3 / 4 | P1 |
| Journey 0 live draft pack optional path | Journey 0 extension | P2 |
| Blueprint editor in UI | Journey 0 | P2 |
| KG graph visualization | Journey 0 wow moment | P3 |

Use [`DEMO_V1_JOURNEY_CHECKLIST.md`](./DEMO_V1_JOURNEY_CHECKLIST.md) before every demo.
