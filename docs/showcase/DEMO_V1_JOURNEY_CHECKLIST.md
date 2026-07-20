# Demo v1 Journey Checklist

**Reference School:** ARM International School · tenant `reference`  
**Use before every demo.** Every box must pass without ad-hoc DB fixes or improvisation.

---

## Pre-flight (operator)

| # | Check | Pass | Notes |
|---|-------|------|-------|
| P1 | Docker stack up (`postgres`, `redis`, `qdrant`, `api`) | ☐ | |
| P2 | `GET http://localhost:8000/health` → 200 | ☐ | Use `localhost`, not `127.0.0.1` if port conflict |
| P3 | `python scripts/smoke_reference_school.py` → ALL GREEN | ☐ | 32 checks |
| P4 | `python scripts/seed_reference_school.py` completed (idempotent OK) | ☐ | |
| P5 | Admin-web `NEXT_PUBLIC_TENANT_SLUG=reference` | ☐ | |
| P6 | Login card printed / shared | ☐ | [`REFERENCE_SCHOOL_LOGIN_CARD.md`](./REFERENCE_SCHOOL_LOGIN_CARD.md) |

---

## Journey 0 — School Intelligence Setup

**Login:** `principal` · **Duration:** ~20 min

| # | Step | Route / action | Expected | Pass |
|---|------|----------------|----------|------|
| 0.1 | Dashboard shows live school | `/dashboard` | Student count ~288, non-zero attendance/fees | ☐ |
| 0.2 | Settings / academic structure | `/dashboard/settings`, `/dashboard/classes` | Academic year, 12 classes visible | ☐ |
| 0.3 | Open approved curriculum pack | `/dashboard/teaching/curriculum` | Class 10 Maths pack **Approved** | ☐ |
| 0.4 | Chapters visible | curriculum pack detail | ≥14 chapters | ☐ |
| 0.5 | Topics + concepts visible | expand chapters | Topic rows with concepts | ☐ |
| 0.6 | Learning outcomes present | chapter 1+ | ≥1 LO visible | ☐ |
| 0.7 | Knowledge spine stats | pack header / spine panel | concept_count > 0, edge_count > 0 | ☐ |
| 0.8 | Grounding preview works | grounding panel | Grounded / indexed, no error | ☐ |
| 0.9 | Audit trail shows approve | pack audit | `pack_approved`, `kg_spine_succeeded`, `rag_index_succeeded` | ☐ |

**Journey 0 pass:** ☐ (all 0.1–0.9)

**Known gaps (acceptable for Demo v1 if narrated):** no live school-creation UI; no textbook PDF wizard; no graph canvas.

---

## Journey 1 — Teacher Planning

**Login:** `teacher6` · **Duration:** ~8 min

| # | Step | Route / action | Expected | Pass |
|---|------|----------------|----------|------|
| 1.1 | Teaching hub loads | `/dashboard/teaching` | No empty state | ☐ |
| 1.2 | Lesson plan exists | `/dashboard/teaching/lesson-plans` | Quadratic Equations draft visible | ☐ |
| 1.3 | Plan links to curriculum | open plan | Subject/class = Class 10 Maths | ☐ |
| 1.4 | Timetable visible | timetable / teaching hub | teacher6 has Class 10 slots | ☐ |

**Journey 1 pass:** ☐

---

## Journey 2 — Assessment

**Login:** `teacher6`, then `teacher1` for approve · **Duration:** ~15 min

| # | Step | Route / action | Expected | Pass |
|---|------|----------------|----------|------|
| 2.1 | AI papers page loads | `/dashboard/teaching/ai-papers` | List/generate UI works | ☐ |
| 2.2 | Generate or open paper | ai-papers | Paper grounded to Class 10 Maths | ☐ |
| 2.3 | In-charge approval | `teacher1` approve flow | HITL approve succeeds | ☐ |
| 2.4 | Exam list populated | exams / gradebook | Class 10-A Maths exams visible | ☐ |
| 2.5 | Marks populated | exam marks view | Non-empty marks for class | ☐ |
| 2.6 | AI eval pending (optional) | eval review UI | ≥1 pending eval **OR narrate gap** | ☐ |
| 2.7 | Analytics visible | gradebook / dashboard widget | Class performance data | ☐ |

**Journey 2 pass:** ☐ (2.1–2.5 required; 2.6 target for P1 seed)

---

## Journey 3 — Classroom

**Login:** `teacher6`, then `student_demo` · **Duration:** ~10 min

| # | Step | Route / action | Expected | Pass |
|---|------|----------------|----------|------|
| 3.1 | Mark / view attendance | `/dashboard/attendance` | Class 10-A history non-empty | ☐ |
| 3.2 | Notices / class work | notices or dashboard | ≥1 notice for students/parents | ☐ |
| 3.3 | Student portal loads | `/student` as `student_demo` | Dashboard, no error | ☐ |
| 3.4 | Student tutor | `/student/tutor` | ≥1 recommendation (fractions) | ☐ |

**Journey 3 pass:** ☐

---

## Journey 4 — Parent & Student

**Login:** `parent_demo` · **Duration:** ~8 min

| # | Step | Route / action | Expected | Pass |
|---|------|----------------|----------|------|
| 4.1 | Parent home loads | `/parent` | Child Sai Rao linked | ☐ |
| 4.2 | Child attendance | parent child / attendance | Last 7 days data | ☐ |
| 4.3 | Assigned work visible | notices / child view | Notice or class work **OR narrate** | ☐ |
| 4.4 | Parent copilot responds | copilot with child context | Sensible summary (not error) | ☐ |

**Journey 4 pass:** ☐

---

## Journey 5 — Principal Intelligence

**Login:** `principal` · **Duration:** ~10 min

| # | Step | Route / action | Expected | Pass |
|---|------|----------------|----------|------|
| 5.1 | Morning briefing populated | `/dashboard` | Non-zero attendance, fees, headcount | ☐ |
| 5.2 | Curriculum signal | briefing / teaching links | Approved pack or pending approvals visible | ☐ |
| 5.3 | Learning signal | performance widgets | Class/exam summary non-empty | ☐ |
| 5.4 | Teacher signal | pending QP / activity | Actionable item visible | ☐ |
| 5.5 | Can articulate recommended action | verbal | e.g. tutor flag, fee follow-up | ☐ |

**Journey 5 pass:** ☐

---

## Demo v1 definition of done

| Criterion | Pass |
|-----------|------|
| All pre-flight checks (P1–P6) | ☐ |
| Journey 0 pass | ☐ |
| Journey 1 pass | ☐ |
| Journey 2 pass (2.6 optional until seed lands) | ☐ |
| Journey 3 pass | ☐ |
| Journey 4 pass | ☐ |
| Journey 5 pass | ☐ |
| Completed in ≤60 min without ad-hoc setup | ☐ |
| Principal feedback: *"I understand why I should buy"* | ☐ |

---

## P1 engineering queue (close before next external demo)

1. ☑ Seed one AI answer-sheet eval in **pending review** state  
2. ☑ Seed one **approved question paper** on Class 10 Maths  
3. ☑ Seed parent-facing **"Class work" notice** for Journey 3/4  
4. ☑ Extend `smoke_reference_school.py` with curriculum grounding + pack audit checks  

---

*Checklist version: Demo v1 · ARM International School · 2026-07-20*
