# Reference School Capability Audit

**Repository:** `studynexs-dev` (canonical)  
**Audit date:** 2026-07-20 (validated against running software)  
**Reference School:** **ARM International School** · tenant slug `reference`  
**Method:** Codebase routes/API modules + `seed_reference_school.py` + `smoke_reference_school.py` (25 HTTP checks) — **not** backlog or governance docs.

**Legend:** **Exists** = implemented in code · **Demo Ready** = works on ARM International School today after seed · **Missing** = blocks the buy moment

Status: ✅ Yes · ⚠️ Partial · ❌ No

---

## Executive summary

StudyNexs has **substantially more built than the sales story currently tells**. The Reference School tenant is seeded, curriculum is approved, and API smoke is **25/25 green**. The gap is not “build the product” — it is **wire four journeys into one convincing 45-minute walkthrough**.

| Your instinct | Verdict |
|---------------|---------|
| “Framework around the product, not the product” | **Correct** — governance and module breadth ran ahead of the end-to-end demo |
| “We're not far off” | **Correct** — portals, ops data, curriculum, exams all exist on `reference` |
| “Schools buy outcomes, not AI features” | **Correct** — Demo v1 is four journeys; Batch 2 / Assessment Intelligence **after** the story sells |

**North star:** Reference School Demo v1 → *A principal says “I understand why I should buy this.”*

---

## Capability snapshot (your format)

| Capability | Exists | Demo Ready | Missing |
|------------|--------|------------|---------|
| Login (staff / student / parent) | ✅ | ✅ | — |
| Principal Dashboard | ✅ | ⚠️ | Populated (288 students, fees, attendance); **learning-insight widgets thin** |
| Curriculum Packs | ✅ | ✅ | Approved Class 10 Maths pack on `reference` |
| Lesson Plans | ✅ | ⚠️ | Draft exists (Quadratic Equations); needs **visible polish in walkthrough** |
| Question Papers | ✅ | ⚠️ | HITL workflow built; **no pre-seeded approved paper in demo path** |
| Answer Evaluation (OCR + AI) | ✅ | ❌ | **Built in code**; no seeded submission → eval → review loop on Reference School |
| Teacher Dashboard | ✅ | ⚠️ | Teaching hub + Command Center; no standalone `/teacher` portal |
| Parent App (web) | ✅ | ⚠️ | `parent_demo` works; attendance + fees; **no homework module** |
| Student App (web) | ✅ | ⚠️ | `student_demo` + tutor recs (3); exams/attendance linked |
| Homework module | ❌ | ❌ | Not built — use notice or lesson plan for Demo v1 |
| School / Learning Analytics | ❌ | ⚠️ | No analytics product module; Morning Briefing widgets only |
| Reference School seed | ✅ | ✅ | `python scripts/seed_reference_school.py` |
| Reference School smoke | ✅ | ✅ | `python scripts/smoke_reference_school.py` → **25/25** (API on `localhost:8000`) |

---

## What was validated (running software)

| Check | Result |
|-------|--------|
| Tenant | `reference` — ARM International School |
| Students / classes | 288 students · 12 classes (Grades 1–10) |
| Attendance / fees | Seeded · smoke hits `/attendance/school-summary`, `/fees/stats` ✅ |
| Exams / marks | 144 exams · 3,456 mark rows · smoke hits `/exams/{id}/marks` ✅ |
| Timetable | Seeded · smoke hits `/timetable/class/{id}` ✅ |
| Curriculum pack | Approved v1 · KG spine + RAG indexed |
| Lesson plan | Draft in teacher dashboard seed |
| Portal logins | `principal`, `teacher6`, `parent_demo`, `student_demo` · `Demo@1234` |
| Parent → child | Sai Rao, Class 10-A roll 1 |
| Student tutor | 3 recommendations on smoke |

**Smoke does not yet validate:** four human Demo v1 journeys end-to-end in the browser.

---

## Detailed capability audit

### Authentication & portals

| Capability | Exists | Demo Ready | Missing |
|------------|--------|------------|---------|
| Password login | ✅ | ✅ | — |
| OTP login | ✅ | ⚠️ | Not on demo login card |
| Principal / admin (`/dashboard`) | ✅ | ⚠️ | Live data; insight story needs scripting |
| Teacher hub (`/dashboard/teaching/*`) | ✅ | ⚠️ | `teacher6` for Class 10 Maths |
| Student portal (`/student/*`) | ✅ | ⚠️ | Tutor, context API green |
| Parent portal (`/parent/*`) | ✅ | ⚠️ | Child overview; no homework |

### School operations (Reference School seed)

| Capability | Exists | Demo Ready | Missing |
|------------|--------|------------|---------|
| Roster Grades 1–10 | ✅ | ✅ | — |
| Attendance history | ✅ | ✅ | — |
| Fees (offline) | ✅ | ✅ | No Razorpay |
| Timetable | ✅ | ✅ | — |
| Notices | ✅ | ⚠️ | Seeded; use for parent “assigned work” substitute |
| Admissions / library / transport | ✅ | ❌ | Out of Demo v1 scope |

### Curriculum & teaching

| Capability | Exists | Demo Ready | Missing |
|------------|--------|------------|---------|
| Pack import → approve → ground | ✅ | ✅ | On `reference` |
| Lesson plan generate | ✅ | ⚠️ | One visible artifact in demo script |
| AI question papers + incharge approve | ✅ | ⚠️ | Live workflow; seed one approved paper |
| Knowledge graph / RAG | ✅ | ❌ | Backend; not principal-facing in Demo v1 |

### Assessment

| Capability | Exists | Demo Ready | Missing |
|------------|--------|------------|---------|
| Exam + gradebook | ✅ | ✅ | 144 exams seeded |
| Answer sheet eval (OCR + async AI) | ✅ | ❌ | **Not wired in Reference School demo path** |
| Report cards | ✅ | ❌ | Not in Demo v1 walkthrough |

### AI

| Capability | Exists | Demo Ready | Missing |
|------------|--------|------------|---------|
| Teacher copilot | ✅ | ⚠️ | Needs scripted prompt |
| Parent copilot | ✅ | ⚠️ | Works with child context |
| Student tutor | ✅ | ⚠️ | Fractions misconception seeded |
| Principal learning / teacher insights | ⚠️ | ⚠️ | Widgets only — no intelligence product layer |

---

## Reference School Demo v1

### Milestone

> **A principal says: “I understand why I should buy this.”**

Not “Curriculum Intelligence complete.” Not “Batch 2 shipped.” Not 100 features.

**Done when:** 4 journeys · one tenant · ≤45 min · self-login · zero “imagine this existed.”

### Journey map vs today

| Journey | Steps | Demo Ready? | Gap |
|---------|-------|-------------|-----|
| **1 — School comes alive** | Principal → living school → teacher timetable → curriculum → lesson plan | ⚠️ **~80%** | Polish lesson plan visibility; demo script |
| **2 — Assessment loop** | Teacher → exam → submissions → review → analytics | ⚠️ **~60%** | Marks exist; **no AI eval loop seeded**; no analytics story |
| **3 — Parent informed** | Parent → attendance → homework → AI summary | ⚠️ **~70%** | **No homework** — use notice; script copilot prompt |
| **4 — Principal health** | Dashboard → school health → learning → teacher signals | ⚠️ **~75%** | Data populated; **insights are widgets not a product story** |

### Journey scripts (target)

**Journey 1**
```
Principal logs in
    → Headcount, attendance %, fees snapshot (live)
    → teacher6 opens teaching hub → timetable
    → Curriculum pack approved (Class 10 Maths)
    → Lesson plan visible (Quadratic Equations)
```

**Journey 2**
```
teacher6 opens exam (Mid-Term / Final seeded)
    → Marks visible in gradebook
    → [GAP] AI answer-sheet eval pending review
    → Class outcome on gradebook or briefing widget
```

**Journey 3**
```
parent_demo logs in
    → Child attendance (Sai Rao, Class 10-A)
    → [GAP] Homework → substitute: notice or lesson plan link
    → Parent copilot summary (scripted prompt)
```

**Journey 4**
```
principal dashboard
    → School health (attendance, fees, 288 students)
    → Class performance / exam summary widget
    → Pending QP approvals / teacher activity signal
```

### Explicitly after Demo v1

- Batch 2 Assessment Intelligence expansion  
- New School Intelligence module  
- Homework as first-class module  
- Online fees · native mobile apps · transport/library demos  

---

## Gap list — prioritized (what engineering should do next)

**Stop:** Sprint/Batch/intelligence-layer framing. **Start:** journey pass/fail on ARM International School.

| P | Gap | Status | Unblocks |
|---|-----|--------|----------|
| ~~P0~~ | Canonical tenant `reference` / ARM International School | ✅ Done | — |
| ~~P0~~ | `seed_reference_school.py` | ✅ Done | — |
| ~~P0~~ | `smoke_reference_school.py` (25 API checks) | ✅ Done | — |
| ~~P0~~ | Curriculum pack approved on Reference School | ✅ Done | Journey 1 |
| **P1** | **Seed exam → AI eval pending review** (even 1 sheet) | ❌ Open | Journey 2 |
| **P1** | **Pre-seed one approved question paper** in demo path | ❌ Open | Journey 1–2 |
| **P1** | **Demo v1 script** — 45 min, four journeys, login card | ❌ Open | Sales |
| **P1** | **Journey checklist** — human pass/fail, not feature checklist | ❌ Open | Definition of done |
| **P2** | Parent homework substitute (notice titled “Class work”) | ❌ Open | Journey 3 |
| **P2** | Principal dashboard widget audit — no empty charts in walkthrough | ❌ Open | Journey 4 |
| **P2** | Playwright: four Demo v1 journeys in browser | ❌ Open | Regression |
| **Defer** | Analytics module, homework module, Batch 2 OCR expansion | — | After Demo v1 |

---

## Operator quick reference

```powershell
cd D:\Projects\studynexs-platform\studynexs-dev\apps\api
python scripts/seed_reference_school.py
python scripts/smoke_reference_school.py   # API on http://localhost:8000
```

**Admin-web:** `NEXT_PUBLIC_TENANT_SLUG=reference` · `NEXT_PUBLIC_API_URL=http://localhost:8000`

| Role | Username | Password |
|------|----------|----------|
| Principal | `principal` | `Demo@1234` |
| Maths teacher | `teacher6` | `Demo@1234` |
| Parent | `parent_demo` | `Demo@1234` |
| Student | `student_demo` | `Demo@1234` |

Login card: [`REFERENCE_SCHOOL_LOGIN_CARD.md`](./REFERENCE_SCHOOL_LOGIN_CARD.md)

---

## Customer lifecycle (context only)

```
Prospect → ARM International School (reference) → signs → new tenant → import data → pilot
```

Reference School is a **product asset**, never a customer's production tenant.

---

## Engineering directive

1. **Measure progress** by four journeys on one tenant — not by documents or batch completion.  
2. **Close P1 gaps** (eval loop, QP seed, demo script, journey checklist) before any new standalone AI feature.  
3. **Then** Assessment Intelligence / Batch 2 — because OCR impresses most when it sits inside a story that already sells.

---

*This is the capability audit. Update when Demo v1 journeys pass human validation — not when individual features merge.*
