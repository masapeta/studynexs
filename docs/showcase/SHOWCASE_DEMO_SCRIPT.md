# Gate 2 Demo Script — Reference School Showcase Workflows

> **Baseline:** `v0.1.0-batch1` · Showcase tenant (slug `naagarjuna` until Phase B → `showcase`)  
> **Formal name:** StudyNexs Reference School    
> **Duration:** ~90 minutes total (45 min HOD + 45 min Teacher) or combined 60 min compressed  
> **Environment:** http://localhost:3003/login · API http://localhost:8000  
> **Automated reference:** [BATCH_1_UI_WORKFLOW_DEMO.md](../../product/BATCH_1_UI_WORKFLOW_DEMO.md) (11/11 validated)

---

## Before you begin

1. Run smoke: `python scripts/smoke_pilot_readiness.py` (from `apps/api`)
2. Confirm `NEXT_PUBLIC_TENANT_SLUG=naagarjuna`
3. Have school's chapter list or placeholder seed visible
4. Set expectations slide / verbal: **AI suggests → human approves**

**Accounts**

| Role | Username | Password |
|------|----------|----------|
| HOD / Principal | `principal` | `Demo@1234` |
| Maths teacher | `maths_teacher` | `Demo@1234` |
| Exam in-charge | `incharge` | `Demo@1234` |

---

## Part A — HOD / Principal workflow (~45 min)

**Narrative:** *"We map your syllabus once. After you approve the pack, every AI paper and lesson plan is grounded to **your** approved content — not the open internet."*

### A0 — Opener (3 min)

> *"This is your school's workspace — tenant `naagarjuna`. Only your staff see your data. Today we walk through how you own the curriculum map and approve what teachers use."*

Log in as **`principal`**.

---

### A1 — Dashboard orientation (5 min)

1. Land on dashboard / morning briefing
2. Point out: attendance, fees, school day — **visibility**, not today's wedge
3. Navigate to **Curriculum** (or Teaching → Curriculum)

**Say:** *"Our pilot focus is Class 10 Maths. The dashboard shows you can grow into full school ops later."*

---

### A2 — Review existing or seed pack (5 min)

**If seed already loaded:**

1. Open Class 10 Maths pack (draft or approved)
2. Show chapter → topic → learning outcome hierarchy

**If starting fresh:**

1. **Create pack** — name: `Class 10 Mathematics — Telangana SSC` (or school board)
2. Select class: Class 10 · Subject: Mathematics

**Say:** *"We enter structured syllabus maps — not full textbook PDFs. Your HOD team validates chapter names and outcomes once."*

---

### A3 — Add chapter (5 min)

1. Add chapter (e.g. *Real Numbers* or from school list)
2. Save draft

**Say:** *"Chapters match your textbook order. Teachers won't need to re-type this."*

---

### A4 — Add topic + learning outcome (8 min)

1. Expand chapter → **Add topic** (e.g. *Euclid's division lemma*)
2. **Add learning outcome** — e.g. *"Apply Euclid's algorithm to find HCF of two numbers"*
3. Save draft

**Say:** *"Learning outcomes are what we index for AI grounding. Precise outcomes = better papers."*

---

### A5 — Edit draft inline (3 min)

1. Edit a topic title or LO text inline
2. Save draft

**Say:** *"Drafts are editable until you approve. After approval, changes need a new version — audit trail stays clean."*

---

### A6 — Approve pack (5 min) ⚠️ critical

1. Click **Approve pack**
2. Wait for success (RAG index runs — may take 10–30 s)
3. Confirm status shows **Approved**

**If error (500 / qdrant):** Stop. Check [GATE2_ENVIRONMENT_VALIDATION.md](./GATE2_ENVIRONMENT_VALIDATION.md) § Qdrant. Do not continue demo without approved pack.

**Say:** *"This moment locks the syllabus for AI. Question papers and lesson plans will cite this pack."*

---

### A7 — Audit trail (5 min)

1. Open **Audit trail** / pack history panel
2. Show: created → edited → approved events with actor + timestamp

**Say:** *"For compliance: who approved what, when. Curriculum audit is separate from generic admin logs by design."*

---

### A8 — HOD close (3 min)

**Ask:**

- Does this chapter structure match your syllabus?
- Who will own pack updates when syllabus changes?
- Any missing chapters before teachers generate papers?

**Logout** or hand laptop to teacher.

---

## Part B — Teacher workflow (~45 min)

**Narrative:** *"You select the approved pack, generate a paper, edit it like a Word doc, and **you** approve before it goes to print or exam."*

Log in as **`maths_teacher`**.

---

### B1 — Grounded lesson plan (10 min)

1. Navigate **Teaching → Lesson Plans** (or equivalent)
2. **Create lesson plan**
3. Select **Class 10 · Mathematics**
4. Select **approved curriculum pack**
5. Select chapter/topic
6. Generate

**Wait:** ~12 s (validated harness timing)

7. Show **provenance badge** — pack name, topic, LO references
8. Walk through plan segments (template structure)

**Say:** *"Structure is syllabus-aligned with provenance. You edit segments for your classroom — we're not replacing your teaching voice yet."*

**Do not say:** *"AI wrote your full lesson"* — say *"syllabus-aligned skeleton with citations."*

---

### B2 — Grounded question paper (15 min) ⚠️ longest step

1. Navigate **Teaching → AI Papers**
2. **New question paper**
3. Select class, subject, **approved pack**
4. Configure: marks, duration, section mix (match school blueprint if available)
5. **Generate**

**Wait:** up to ~90 s — narrate: *"Model is reading your approved outcomes, not random web content."*

6. Review generated paper in editor
7. Edit 1–2 questions (wording, marks)
8. Save draft

**Say:** *"Treat this as first draft — you are the examiner of record."*

---

### B3 — Approve question paper (5 min)

**Option A — teacher approves:** Continue as `maths_teacher` if RBAC allows  
**Option B — in-charge approves:** Switch to **`incharge`**

1. Open paper → **Approve**
2. Confirm approved state

**Say:** *"Nothing goes to students or print without this step. Always."*

---

### B4 — Exam + eval (10 min) — with limits

1. Navigate **Exams** / evaluation entry
2. Upload or snap **sample answer sheet** (use redacted pilot sheet if available)
3. Show AI-suggested marks per question
4. **Override** one subjective question
5. **Approve** marks

**Say (required):** *"AI suggests from your approved paper and rubric. Messy handwriting, diagrams, and long proofs stay teacher-led. See our eval limits one-pager."*

Reference: [CLASS_10_MATHS_EXAM_LOOP.md](../CLASS_10_MATHS_EXAM_LOOP.md)

---

### B5 — Weak topics + tutor (5 min)

1. **Topic Mastery** / weak topics view — show heatmap or list
2. Optional: log in **`student_demo`** → **AI Tutor** for one flagged topic

**Say:** *"Weak topics drive revision. Tutor demo is opt-in for students — not pack-grounded yet in Batch 1."*

---

### B6 — Teacher close (5 min)

**Ask:**

1. Would you trust this paper after your edits?
2. Did eval save time on objective questions?
3. What's missing before a real class test?

Hand out [GATE2_FEEDBACK_COLLECTION_TEMPLATE.md](./GATE2_FEEDBACK_COLLECTION_TEMPLATE.md) (teacher section).

---

## Compressed 60-minute agenda

| Min | Segment | Account |
|-----|---------|---------|
| 0–5 | Opener + login | principal |
| 5–25 | Pack create → approve → audit | principal |
| 25–35 | Lesson plan + provenance | maths_teacher |
| 35–50 | QP generate → edit → approve | maths_teacher / incharge |
| 50–58 | Eval sample + weak topics | maths_teacher |
| 58–60 | Q&A + feedback form | all |

---

## Troubleshooting during live demo

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Login 500 | Wrong API host (`127.0.0.1:8000` ghost) | Use `localhost:8000`; restart admin-web |
| Pack approve 500 | Missing `qdrant_client` | Docker `[rag]` install; restart API |
| QP timeout | LLM slow / no credits | Use pre-approved backup QP ([BACKLOG DEMO-03](../../BACKLOG.md)) |
| No pack in dropdown | Pack not approved | Complete A6 first |
| CORS error | Wrong admin port | Use port 3003 |

---

## Post-demo checklist

- [ ] Feedback forms collected
- [ ] Issues logged in [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md)
- [ ] Daily log updated ([template](./GATE2_DAILY_PILOT_LOG_TEMPLATE.md))
- [ ] Screenshots captured if school allows
