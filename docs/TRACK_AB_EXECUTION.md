# Track A → B Execution Plan

> Owner: Avinash Reddy Masapeta (ARM) · **Start here after PRODUCT.md is done.**  
> Goal: validate demand with one pilot school, then ship a demo they can actually use next term.  
> Status doc: [STATUS.md](./STATUS.md) · Pilot script: [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md)

---

## Overview

| Track | Goal | Duration |
|-------|------|----------|
| **A** | Turn interest into a **buy-list** (top-3 + price + contacts + pack inputs) | 1–2 weeks |
| **B** | **Pilot-ready product** scoped to that buy-list only | 2–4 weeks after A |

**Rule:** Track B item **B2** (UI fixes) waits on **A1** forced top-3. Everything else in B can start in parallel with A.

---

## Track A — Business validation

### A1 — Pilot discovery meeting (do this first)

**Before the meeting**

- [ ] API + admin-web running locally (or deployed demo URL)
- [ ] Demo login works (seed school: Sri Saraswathi / your pilot school user)
- [ ] Generate **live** Class 10 Maths paper on screen (~20 sec)
- [ ] Show approve → export/print flow
- [ ] Optional: report card draft if time allows
- [ ] Print [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md) or have questions on phone
- [ ] Blank **[Pilot Outcome Sheet](./pilot/PILOT_OUTCOME_SHEET.md)** ready to fill during/after call (save copy under `docs/pilot/<school-slug>/`)

**Meeting flow (45–60 min)**

1. **5 min** — context: "I'm building tools that save teachers time in exam season, grounded in your syllabus."
2. **10 min** — **DEMO FIRST** (QP generation live). No slides. No feature list.
3. **25 min** — discovery questions (see PILOT_DISCOVERY.md). **Do not lead** on grading until Q2 is answered naturally.
4. **10 min** — forced top-3, price question, names for exam in-charge + 1 teacher
5. **5 min** — ask for pack inputs (A2 checklist) if interest is real

**Fill the outcome sheet:** [docs/pilot/PILOT_OUTCOME_SHEET.md](./pilot/PILOT_OUTCOME_SHEET.md)  
Save a copy as `docs/pilot/<school-slug>/outcome-YYYY-MM-DD.md` (e.g. `docs/pilot/sri-saraswathi/outcome-2026-06-20.md`).

**Done when:** Verdict is REAL INTEREST **or** you have a clear POLITE NO (stop treating as maybe).

---

### A2 — Collect CurriculumPack inputs (one subject)

Ask the pilot school for **one** class × subject you'll demo end-to-end (default: **SSC Class 10 Maths**).

| # | Input | Format | Received |
|---|-------|--------|----------|
| 1 | Board | SSC / CBSE / State | ☐ |
| 2 | Class & subject | e.g. Class 10 Maths | ☐ |
| 3 | Textbook name + publisher + edition/year | Photo of cover or typed | ☐ |
| 4 | Term-wise syllabus (which chapters this term) | PDF or photo | ☐ |
| 5 | Table of contents / index | Photo or PDF | ☐ |
| 6 | Exam blueprint (if they use one) | PDF or describe sections | ☐ |
| 7 | One previous question paper (same class/subject) | PDF or clear photo | ☐ |
| 8 | Sample model answers / marking notes (if any) | Optional | ☐ |
| 9 | HOD / exam in-charge contact for approval | Name + phone | ☐ |

Store in: `docs/pilot/<school-slug>/` (create folder; no copyrighted full books in git — use Drive/links in a `SOURCES.md`).

**Done when:** Items 1–7 checked for at least one subject.

---

### A3 — Verify SSC blueprint against real paper

**Done when:** You have item 7 from A2 (real sample paper).

| Check | Pass? |
|-------|-------|
| Section count and names match (I, II, III, Part-B) | ☐ |
| Marks per section match (60 + 20 = 80 or school's total) | ☐ |
| Internal choice rules match ("answer any 4 of 6") | ☐ |
| Question types match (VSA / SA / LA / MCQ) | ☐ |
| Generate paper with StudyNexs → compare side-by-side | ☐ |
| Note gaps in `docs/pilot/<school>/blueprint-gap-notes.md` | ☐ |

If gaps exist: fix `_ssc_blueprint()` in `question_paper_service.py` **before** promising the school.

---

## Track B — Phase 1 hardening (pilot-ready)

### What runs in parallel with Track A

| ID | Task | Owner | Done when |
|----|------|-------|-----------|
| **B3** | Tests green | Dev | `pytest tests/` passes; note count |
| **B5** | Branch hygiene | Dev | Demo code committed; branch pushed or merged plan clear |
| **B4** | AI cost benchmark | Dev | Table of ₹/paper per provider (see below) |

### What waits on A1 (forced top-3)

| ID | Task | Done when |
|----|------|-----------|
| **B2** | Pilot-blocker UIs only | Each item in school's top-3 has working UI |

### Default B2 scope (if top-3 matches exam wedge)

Use this **only until** the real checklist arrives:

| Priority | Item | Likely needed if… |
|----------|------|-------------------|
| P0 | AI Papers — harden approve/export | Always (wedge) |
| P0 | Exams + marks entry UI polish | They need marks in system |
| P0 | Report cards flow end-to-end | They mention report cards |
| P1 | Settings (school profile, academic year) | They need term rollover |
| P1 | Notices — wire "New Notice" | They mention communication |
| P1 | Finance — fee payment UI | They mention fees |
| P2 | Timetable polish | Only if in top-3 |
| Skip | Library, events placeholders | Not in sidebar; ignore unless asked |

---

### B1 — Question paper hardening

- [ ] A3 blueprint verification complete
- [ ] Export works for demo (HTML print-to-PDF acceptable for pilot; document limitation)
- [ ] Error messages user-friendly on AI failure
- [ ] Rate limit / cap behaviour tested (won't blow budget in demo)
- [ ] Teacher can edit all sections before approve
- [ ] Approved paper persists and re-opens correctly

---

### B3 — Tests green

```powershell
cd apps\api
pip install -e ".[dev]"
pytest tests/ -q
pytest tests_security/ -q   # optional separate run
```

Admin smoke (API on :8000, Next on :3000):

```powershell
cd apps\admin-web
node e2e-smoke.cjs
```

- [ ] Backend tests pass
- [ ] Record count in STATUS.md when updating
- [ ] e2e-smoke passes or document blockers

---

### B4 — AI cost benchmark

Run representative tasks on **2–3 providers** (e.g. gpt-4o-mini, gemini-1.5-flash, claude-haiku):

| Task | Tokens in/out | Cost INR | Notes |
|------|---------------|----------|-------|
| 1× QP generate (Class 10 Maths) | | | |
| 1× report card remark | | | |
| 1× (planned) grading assist stub | | | defer if no API yet |

Use gateway + `ai_usage` table or script. **Output:** pick default provider for pilot + rough ₹/student/month at expected usage.

---

### B5 — Branch & demo stability

- [ ] All Track B work on `phase-0-foundation` or new `pilot-ready` branch
- [ ] No secrets in git; `.env` local only
- [ ] `scripts/smoke_demo_readiness.py` passes against local API
- [ ] Tag or note commit hash in Pilot Outcome Sheet as "demo version"
- [ ] Update [STATUS.md](./STATUS.md) snapshot when B complete

---

## Suggested calendar (solo builder)

| Week | Track A | Track B (parallel) |
|------|---------|-------------------|
| **1** | Schedule + run A1 pilot meeting | B3 tests · B5 branch · start B4 |
| **1–2** | A2 pack inputs · A3 blueprint verify | B1 QP harden |
| **2** | Follow-up with exam in-charge if needed | B2 from forced top-3 only |
| **3–4** | Design-partner agreement / informal yes | Finish B2 · pilot dry-run at school or remote |
| **5+** | — | Start Phase 1.5 Week 1 (CurriculumPack) — only if A1 = REAL INTEREST + A2 underway |

---

## Gate before Phase 1.5 (8-week plan)

All must be true:

- [ ] A1 verdict: **REAL INTEREST** (top-3 + price + contact)
- [ ] A2: pack inputs 1–7 collected for one subject
- [ ] A3: blueprint verified or gaps documented + fixed
- [ ] B1: QP demo-ready for that subject
- [ ] B2: top-3 features work in UI
- [ ] B3: tests green
- [ ] B4: default provider + rough unit economics
- [ ] C1 minimal (if real student data): consent note — see STATUS.md

If any gate fails → **do not start CurriculumPack migration.**

---

## After Track A + B

1. Update [STATUS.md](./STATUS.md) — snapshot, check off completed items  
2. Log decisions in [DECISION_LOG.md](./DECISION_LOG.md) (pilot school name, top-3, pricing)  
3. Begin [8-week Phase 1.5 plan](./STATUS.md#8-week-build-plan-phase-15) Week 1  

---

## Related

- [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md) — questions + demo tips  
- [PRODUCT.md](./PRODUCT.md) — full vision (don't rebuild; reference only)  
- [STATUS.md](./STATUS.md) — what's in the repo today
