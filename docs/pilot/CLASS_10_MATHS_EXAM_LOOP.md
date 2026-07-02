# Class 10 Maths — Exam Loop Pilot Meeting Pack

> **Use for:** one-school design-partner meeting (Gate 1 demo → Gate 2 pilot scope).  
> **Wedge:** Question paper → exam → correction → weak topics → AI tutor — **not** full ERP.  
> **Reference school pattern:** [krishnaveni-talent-school/outcome-2026-06-15.md](./krishnaveni-talent-school/outcome-2026-06-15.md)

---

## 30-second opener

> *"Today is **demo data only** — our sample school Sri Saraswathi. If we pilot together, we start with **Class 10 Maths only**: your syllabus, your paper pattern, ten answer sheets, and a weak-topic report teachers can trust. Everything AI-generated is **approved by your teacher** before parents or students see it."*

---

## What we will show (45 min hands-on)

| # | Who logs in | Show | Pilot tie-in |
|---|-------------|------|----------------|
| 1 | `teacher6` | **AI Papers** — generate SSC-style Maths paper → edit → **Approve** | Their blueprint + chapter weightage |
| 2 | `teacher6` | **Exams** — marks / evaluation entry | Real scans in pilot |
| 3 | `teacher6` | **Report Cards** — remark draft → edit → approve | Tone check with Class teacher |
| 4 | `teacher6` | **Topic Mastery** — weak topics heatmap | Drives revision plan |
| 5 | `student_demo` | **AI Tutor** — fractions lesson, **Neerja voice**, pause/replay | Mistake Recovery from exam errors |
| 6 | `parent_demo` | Child progress + fees (read-only) | Opt-in parents only in pilot |
| 7 | `principal` | Dashboard snapshot | Management visibility, not wedge |

**Hands-on script:** [HANDS_ON_RUNBOOK.md](./HANDS_ON_RUNBOOK.md)  
**One-command demo seed:** `python scripts/seed_demo_e2e_journey.py` (from `apps/api`)

---

## Pilot scope to propose (write on whiteboard)

| In scope (8 weeks) | Out of scope (say no) |
|--------------------|------------------------|
| Class **10** · Subject **Mathematics** | Full-school ERP go-live |
| Curriculum pack inputs (syllabus + 1 sample paper) | Online fee payment (Razorpay) |
| AI question paper + teacher HITL approve | WhatsApp blast to all parents |
| ~10 answer sheets → vision eval + teacher approve | Flutter native apps |
| Weak-topic + misconception report | Library / transport / payroll modules |
| AI tutor for flagged mistakes (opt-in students) | Autonomous scheduling / bus routes |

---

## Pricing anchor (adjust per school)

| Offer | Amount | Notes |
|-------|--------|-------|
| Per student / month | ₹100 + GST | Full platform list; exam wedge only in pilot |
| Pilot bundle (one class) | ~₹94,500 + GST / month | Limited exam intelligence; verify accuracy first |
| Easy no | > ₹250 + GST / student | Unless correction + analysis + parent reports included |

**Budget owner:** Principal + management/trust (typical).

---

## Discovery questions (last 10 min)

1. What triggered you to look at software **now**?
2. What do you use today for papers, marks, parent comms? What's broken?
3. Without us leading: are **exams / grading** in your top-2 pains?
4. **Force top-3** features in their words (not yours).
5. Who approves budget? What price is an easy **no**?
6. **Next step they commit to** (date + deliverable).

Fill **[PILOT_OUTCOME_SHEET.md](./PILOT_OUTCOME_SHEET.md)** before you leave.

---

## Pack inputs checklist (if REAL INTEREST)

Collect within 1 week:

- [ ] Class 10 Maths **syllabus** / chapter list (current year)
- [ ] One **previous board-style paper** + marking scheme
- [ ] Blueprint or weightage table (chapters → marks)
- [ ] Exam in-charge **name + phone**
- [ ] Class 10 Maths teacher **name + phone**
- [ ] 10 sample **answer sheets** (redacted) for eval accuracy test
- [ ] Consent approach for parent/student accounts (verbal OK for now)

---

## Verdict rubric

| Verdict | Criteria |
|---------|----------|
| **REAL INTEREST** | Top-3 + price discussed + named contact + dated next step |
| **POLITE NO** | Praise but no number, no name, no date → stop chasing |
| **MAYBE** | One follow-up only; set date or downgrade to no |

---

## After the meeting

1. Save `docs/pilot/<school-slug>/outcome-YYYY-MM-DD.md`
2. Update [BACKLOG.md](../BACKLOG.md) Gate 2 items if they commit
3. **Do not build** tutor LLM or QP hardening until pilot sheet says which hurts most
4. Run smoke before next demo: `smoke_demo_readiness.py` + `npm run e2e-smoke`

---

## Demo logins (print this)

```
URL: http://127.0.0.1:3000  (or your HTTPS demo URL)
API: http://127.0.0.1:8000  (use 127.0.0.1 on Windows — not localhost)

principal    / Demo@1234  → Admin
teacher6     / Demo@1234  → Class 10 Maths teacher
parent_demo  / Demo@1234  → Parent
student_demo / Demo@1234  → Student + AI Tutor
```
