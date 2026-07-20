# Demo v1 — Customer Review

**Reviewer perspective:** Principal, ARM International School (SSC), seeing StudyNexs for the first time  
**Walkthrough date:** 2026-07-20  
**Method:** Full demo script (`DEMO_V1_SCRIPT.md`), live Reference School tenant (`reference`), API + UI code review, smoke validation (32/32 green)

This is not an engineering assessment. It is what a principal would think and feel during a 45–60 minute demonstration.

---

## The one-question verdict

**If I were a principal seeing StudyNexs for the first time, would I immediately understand why this product is worth piloting?**

**Not yet.**

I would leave impressed by *pieces* — a living school, curriculum structure, AI-assisted marking with teacher control, a parent portal — but I would not yet feel the single thread that answers: *"This saves my school real time, on our syllabus, with trust."* Too much still reads like a capable platform demo, not a finished story told to me.

---

## How I experienced the demo (as the principal)

### Opening — login and dashboard

I log in as `principal`. The dashboard greets me by name. **288 students**, **89.6% present today**, fees collected, admissions in pipeline — this immediately feels like a real school, not a empty SaaS trial. That is a strong first impression.

The **priority queue** surfaces attendance below target, outstanding fees, and admissions — things I actually worry about. I understand why I should care.

What I do **not** see: anything about the demo's academic story. There is no signal that a maths teacher generated an AI paper waiting for approval, or that Class 10 has a unit test with AI-suggested marks ready for review. The engineering report promised that on the principal dashboard; it is not there. The academic AI differentiation — the reason StudyNexs is not "just another ERP" — is invisible from my home screen.

The **quick links** (Curriculum, AI papers, Exam review, Mastery) help, but only if the presenter clicks them. On my own I would not know "Exam review" means answer-sheet marking. I would guess exams or gradebook.

The **latest notice** showing class work on Quadratic Equations is good — it connects classroom to home — but it sits beside older notices (Sports Day, PTM) without highlighting that this is today's teaching loop.

**Class performance** widgets show Class 9-A and Class 5-A on top, not Class 10 Maths where the demo story lives. I would not connect dashboard analytics to the assessment narrative.

### Journey 0 — Curriculum (the "why we're different" moment)

I follow Teaching → Curriculum. The page opens on **Class 1**, not Class 10. I must hunt for the right class and subject before I see the approved Maths pack. In a live demo that is 30–60 seconds of friction and looks like the product does not know my school.

When I reach **Class 10 · Mathematics · Approved**, the depth is real: chapters, topics, learning outcomes, audit trail, grounding preview. I believe the school has a structured academic model — not a folder of PDFs.

But the language is wrong for me:

- "Knowledge spine", "Grounding preview", "RAG indexed", "kg_spine_succeeded" — this is engineer vocabulary.
- I want: *"Your approved syllabus — every AI paper and tutor lesson uses this."*
- The audit trail is reassuring for trust, yet I cannot explain to my HOD what "17 vectors indexed" means without the presenter translating.

**Wow moment (partial):** Seeing 14 SSC chapters with topics and outcomes feels like serious academic infrastructure.  
**Weakened by:** Jargon, default wrong class, no plain-English headline tying curriculum to AI papers and tutor.

### Journey 1 — Teacher planning

Switching to `teacher6`, the teaching hub has **nine tabs**. As a principal watching a teacher demo I am fine; as a teacher I would wonder where to start. Lesson plans show Quadratic Equations linked to Class 10 Maths — credible and grounded.

This act supports the story but is not the headline. Fine for a supporting scene.

### Journey 2 — Assessment and AI evaluation

**AI papers:** Two papers visible — one approved (Quadratic Equations), one pending approval (Progressions). The approved paper shows grounded content. This is a **clear wow**: questions tied to our syllabus, not random ChatGPT output.

**Human-in-the-loop:** The pending paper is the right trust signal — but on the **principal** dashboard I never saw "1 paper awaiting approval." When I switch to `teacher1` (class incharge), the dashboard shows a **teacher command center**, not an approval queue. I would have to navigate to AI papers myself. The demo script says incharge approves; the product does not meet me there.

**Exam evaluation:** Opening Unit Test — Quadratic Equations → Evaluate, the banner *"AI has suggested marks waiting for your review"* is excellent. I see suggested marks, can adjust, approve. **This is the strongest trust moment in the demo** — AI assists, teacher decides.

**Weakened by:** Subtitle "Vision OCR + async grading" — teacher jargon. Upload form still visible even when review is ready — slightly confusing. Finding the right exam requires presenter navigation (Teaching → Exams → Class 10-A → specific unit test).

### Journey 3 — Classroom day

Attendance for Class 10-A has history. Notices include class work. Student portal (`student_demo`) is clean; **AI Tutor — start here** is clear. Tutor recommendations (fractions remediation) connect to learning gaps.

This act works. It feels like one school, multiple roles.

### Journey 4 — Parent and family

Parent login (`parent_demo`) shows **Sai Rao**, Class 10-A, attendance, fees, weak topics — professional and calm.

I tap **Parent Copilot — weekly summary**. It **fails**. Red error: copilot returned an empty briefing. I try asking *"Summarise my child's week in Maths"* — **also fails**.

As a parent I would close the app frustrated. As a principal I would lose confidence immediately: *"If the AI parent feature breaks in the demo, what happens on Monday?"*

This is the **single biggest failure** in the customer walkthrough. Journey 4 is supposed to close the loop; it breaks the story.

### Journey 5 — Back to principal intelligence

Returning to my dashboard, I still have operations KPIs but no unified academic intelligence narrative: curriculum health, pending AI approvals, Class 10 Maths performance, students flagged for tutoring.

The product has the data (smoke tests prove it). The **principal pane of glass** does not yet tell the academic story without a skilled presenter narrating over the UI.

---

## What impressed me

1. **The school feels alive** — 288 students, attendance, fees, notices, admissions. I believe ARM International is a real institution.
2. **Approved curriculum pack** — structured Class 10 SSC Maths with chapters, topics, outcomes. This is the moat, and it is visible (once I find Class 10).
3. **Grounded AI question paper** — Quadratic Equations paper clearly tied to curriculum; not generic AI slop.
4. **AI evaluation with teacher review** — suggested marks, rubric-style review, approve to publish. Trust done right.
5. **Student tutor** — personalised weak-topic remediation; connects assessment → learning.
6. **Unified portals** — admin, teacher, parent, student feel like one product family.
7. **Human-in-the-loop is demonstrable** in evaluation even without live OCR — seeded suggested eval is the right demo choice.

---

## What confused me

1. **Principal dashboard omits the academic story** — no pending paper approval, no Class 10 signal, no "3 students need tutoring" action.
2. **Curriculum opens on Class 1** — wrong default for a Class 10–centric demo.
3. **"Exam review" vs "Review" vs "Exams"** — three labels, unclear which is AI marking.
4. **Curriculum screen language** — spine, grounding, RAG, audit event codes — not principal language.
5. **teacher1 sees teacher home, not approval queue** — incharge approval narrative fights the UI.
6. **Parent Copilot errors** — looks broken, not "AI optional."
7. **Presenter-dependent path** — without the script I would not discover Unit Test → Evaluate or the pending Progressions paper.
8. **Localhost only** — I cannot explore after the meeting; undermines pilot urgency.

---

## What felt unnecessary

1. **Nine teaching hub tabs** in one row for a demo focused on one class story — cognitive load without guidance.
2. **Generic dashboard todos** ("Review pending tuition payments", "Reply to parent messages") — obviously placeholder; erodes polish.
3. **Grounding preview raw text block** on curriculum — useful for engineers, not for me in a first meeting.
4. **Internal staff notices** mixed with parent-facing class work on principal dashboard without filtering.
5. **Optional upload/manual answer grid** on evaluate page when a review is already waiting — noise during the wow moment.

---

## What felt missing

1. **One-sentence product promise on first screen** — e.g. *"Your syllabus powers every AI paper, mark, and tutor lesson."*
2. **Principal-visible pending AI approvals** — school-wide count with one click to review.
3. **Working parent AI summary** without API keys — demo must not depend on Gemini being configured.
4. **Class 10 Maths in performance widgets** — align analytics with the story being told.
5. **Guided demo path in UI** — even a "Today's highlights" strip on the dashboard for Reference School.
6. **Shareable URL** — cannot pilot what I cannot revisit.
7. **Plain-language curriculum headline** — what it is and why it matters before technical panels.

---

## Moments that created confidence

| Moment | Why |
|--------|-----|
| Dashboard KPIs (students, attendance, fees) | Real school operations |
| Approved curriculum pack with chapters/topics | Serious academic foundation |
| Approved AI paper with syllabus grounding | AI is not generic |
| Eval review banner + approve flow | Teacher stays in control |
| Student tutor weak-topic recommendation | Assessment feeds learning |
| Class work notice on parent/student path | Same school day across roles |

---

## Moments that weakened the story

| Moment | Why |
|--------|-----|
| Parent Copilot 400 error | AI promise breaks in front of me |
| No pending QP on principal dashboard | HITL story invisible to decision-maker |
| Curriculum defaults to Class 1 | Product feels unconfigured |
| Engineer jargon on curriculum | I am sold trust, shown infrastructure |
| teacher1 dashboard not approval-focused | Role story does not match script |
| Class performance ignores Class 10 | Analytics disconnected from demo |
| localhost-only | No urgency to start pilot |

---

## Would I start a pilot?

**Not on this demo alone — not yet.**

**What would make me say yes:**

- Parent Copilot works reliably (or gracefully shows a useful non-AI summary).
- Principal dashboard surfaces the academic AI story without narration.
- I can follow the Class 10 journey myself in under 15 minutes after one guided walkthrough.
- A stable URL I can share with my HOD and one parent rep.

**What already pushes me toward yes:**

- The evaluation workflow (AI suggests, teacher approves) matches how I want AI in my school.
- Curriculum-grounded papers are differentiated from every LMS/ERP pitch I have seen.
- Operations depth (fees, attendance, admissions) suggests this could replace fragmented tools.

**Why I would hesitate:**

- Parent-facing AI failed in the demo — highest visibility, highest trust risk.
- I still need a presenter to connect the dots — product does not yet tell the story alone.
- No production URL — pilot feels "later", not "next week".

---

## Priority fixes (customer experience only)

These are the smallest changes that would move the verdict toward **Yes**:

| Priority | Issue | Customer impact |
|----------|-------|-----------------|
| P0 | Parent Copilot fails without LLM key | Journey 4 breaks; trust collapses |
| P0 | Principal does not see pending AI paper approvals | Decision-maker misses HITL story |
| P1 | Curriculum page opens Class 1, not demo class | Journey 0 friction and confusion |
| P1 | Class incharge dashboard prioritises teacher home over approvals | Journey 2 approval scene fights UI |
| P2 | Engineer jargon on curriculum (presenter must translate) | Weakens "wow" into "technical" |
| P2 | Generic placeholder todos on dashboard | Feels unfinished |
| P2 | "Exam review" labelling | Navigation confusion |

No new modules. No architecture redesign. Fix the story breaks above.

---

## Re-test criteria (customer, not engineering)

Demo v1 earns my approval when, **without presenter narration**, I can:

1. Log in as principal and see **at least one academic AI action** waiting (paper approval or eval review).
2. Open curriculum and **immediately see Class 10 Maths approved** (or land there from dashboard).
3. Log in as parent and get a **useful weekly summary** — AI or deterministic — with no error screen.
4. Articulate in one sentence: *"StudyNexs learns our syllabus first, then helps teachers assess and parents stay informed — with teachers always in control."*

When those four are true, the answer to the pilot question becomes **Yes**.

---

## Post-review fixes applied (same session)

The following customer-experience fixes were implemented immediately after this review (no new modules):

| Fix | Addresses |
|-----|-----------|
| Parent Copilot deterministic fallback when LLM empty/unavailable | P0 Journey 4 failure |
| Principal dashboard `pending_qp_approvals` in priority queue | P0 HITL invisible to principal |
| Class incharge dashboard prioritised over teacher home | P1 teacher1 approval scene |
| Curriculum page defaults to Class 10 when present | P1 Journey 0 friction |
| Quick link renamed "AI marking"; evaluate subtitle softened | P2 navigation/jargon |
| Removed generic placeholder dashboard todos | P2 polish |

Re-verified: Parent briefing HTTP 200, principal sees 1 pending QP, teacher1 incharge persona with approval count.

---

*Review completed before further Demo v1 implementation. Engineering baseline: Demo v1 batch (commit `2a9248f`).*
