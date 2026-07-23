# StudyNexs Pilot Demo Script — Release 0.3

> 20–30 minute walkthrough for a principal and two teachers.

**Release baseline:** `v0.3.0`
**Scope:** Principal + Teacher pilot experience
**Deferred:** Student and Parent journeys remain Release 0.4.

---

## Demo goal

By the end of the session, the principal and teachers should understand:

1. StudyNexs learns the school’s curriculum first.
2. Teachers stay in control.
3. Lesson plans and question papers are grounded in the approved curriculum.
4. The school can pilot the Principal + Teacher workflow without engineering assistance.

---

## Participants

| Participant | Role in demo |
|---|---|
| Principal | Decision-maker; evaluates pilot value |
| Teacher 1 | Subject teacher; runs teaching workflow |
| Teacher 2 | Academic lead/class incharge; evaluates governance and adoption |
| Operator | Runs the scripted walkthrough |

---

## Timing overview

| Segment | Time |
|---|---:|
| Opening and scope | 3 min |
| Principal journey | 6 min |
| Teacher 1 journey | 10–12 min |
| Teacher 2 discussion | 4 min |
| Pilot success criteria and next steps | 5 min |
| Buffer | 3–5 min |

Total: 20–30 minutes.

---

## 0. Pre-demo setup

Before joining the call:

1. Complete [`PILOT_PREFLIGHT_CHECKLIST.md`](./PILOT_PREFLIGHT_CHECKLIST.md).
2. Keep one browser ready for principal.
3. Keep one browser ready for Teacher 1.
4. Keep Teacher 2 credentials ready only if preflight verified.
5. Record canonical pack, lesson plan, and question paper IDs.
6. Confirm AI credits or principal override.

Do not begin the live demo if runtime proof or browser walkthrough failed.

---

## 1. Opening — 3 minutes

Say:

> “Today we are not showing a generic school ERP or a chatbot. We are showing the first pilot slice of StudyNexs: the school teaches StudyNexs its curriculum, and teachers use that approved curriculum to generate grounded lesson plans and question papers. Humans remain in control.”

Clarify scope:

> “This Release 0.3 pilot is focused on principal and teacher workflows. Student and parent experiences are intentionally planned for the next release phase after we validate teacher adoption.”

Do not overpromise:

> “The goal today is not to show every future module. The goal is to see whether this core academic workflow is valuable enough for a pilot.”

---

## 2. Principal journey — 6 minutes

### Step 2.1 — Login

Open:

```text
/login
```

Login as principal.

Reference account:

```text
principal / Demo@1234
```

Say:

> “We start as the principal because the pilot must make sense at the school-leadership level.”

### Step 2.2 — Dashboard

Open:

```text
/dashboard
```

Show:

- school overview;
- students/classes;
- attendance or operational indicators.

Say:

> “This gives the principal the operating view, but the pilot value is in the academic intelligence layer.”

### Step 2.3 — Curriculum / Academic Intelligence

Open:

```text
/dashboard/teaching/curriculum
```

Show:

- approved curriculum pack;
- Academic Intelligence Ready;
- KG/RAG readiness if visible.

Say:

> “This is the key moment: StudyNexs is not generating generic content. It is using an approved school curriculum as the source of academic memory.”

### Step 2.4 — Teacher output evidence

Open:

```text
/dashboard/teaching/lesson-plans
/dashboard/teaching/ai-papers
```

Say:

> “The principal does not need to inspect every question. What matters is that teacher-facing outputs are connected to the same approved curriculum.”

Do not dive into every field. Keep the principal story short and confidence-focused.

---

## 3. Teacher 1 journey — 10–12 minutes

Teacher 1 is the subject teacher who demonstrates daily value.

Reference account:

```text
teacher6 / Demo@1234
```

### Step 3.1 — Login

Open teacher session:

```text
/login?portal=teacher
```

Say:

> “Now we switch to the teacher view. This is where the product has to save real time.”

### Step 3.2 — Teaching hub

Open:

```text
/teacher
```

or:

```text
/dashboard/teaching
```

Show:

- teacher workspace;
- assigned class/subject context;
- teaching tools.

Say:

> “The teacher should not have to think about the full school system. They need their class, their subject, and useful academic output.”

### Step 3.3 — Lesson plan

Open:

```text
/dashboard/teaching/lesson-plans
```

Use the prevalidated class/subject and approved pack.

If live generation is safe, generate a grounded lesson plan.

If live AI is slow or risky, open the prevalidated generated lesson plan.

Say:

> “This lesson plan is not a blank AI response. It is grounded in the approved curriculum pack.”

Point out:

- class;
- subject;
- topic;
- grounding/curriculum connection.

Do not discuss embeddings, RAG internals, tokens, or model details unless asked.

### Step 3.4 — Question paper

Open:

```text
/dashboard/teaching/ai-papers
```

Use the same class/subject/curriculum context.

Generate or open the prevalidated question paper.

Say:

> “The same curriculum memory can support assessment creation. This is where StudyNexs becomes more than a lesson-plan tool.”

Point out:

- teacher remains in control;
- output is reviewable;
- citations/grounding are available where visible;
- generated drafts consume AI credits, so schools retain budget control.

### Step 3.5 — Teacher reaction

Ask Teacher 1:

- “Would this save preparation time?”
- “Is the output close enough to review/edit rather than start from scratch?”
- “Would you trust this if your academic lead approved the curriculum first?”

Record exact objections.

---

## 4. Teacher 2 / academic lead discussion — 4 minutes

Teacher 2 should evaluate governance and adoption, not introduce a new workflow.

Reference option:

```text
teacher1 / Demo@1234
```

Use only if preflight verified.

Say:

> “In a real school, one teacher may create or use content, while an academic lead or class incharge cares about consistency, approval, and quality.”

Discuss:

- curriculum approval;
- teacher ownership;
- human-in-the-loop review;
- class/subject boundaries;
- how the school would introduce this to teachers.

Ask Teacher 2:

- “Would your teachers understand where to start?”
- “Who should approve curriculum packs in your school?”
- “What would you need before using this in one class for one week?”

Do not open Student or Parent portals.

---

## 5. Success criteria and next steps — 5 minutes

Use [`PILOT_SUCCESS_CRITERIA.md`](./PILOT_SUCCESS_CRITERIA.md).

Ask the principal:

1. “Is the academic workflow clear?”
2. “Would you allow two teachers to try this for one week?”
3. “What would block you from piloting this?”
4. “Which class and subject should be first?”

Ask the teachers:

1. “Would you use this to prepare a class?”
2. “Would you edit the output instead of starting manually?”
3. “Where did the workflow feel confusing?”

Close with:

> “If you choose to pilot, we recommend one class, one subject, two teachers, and a tightly measured first week. We will judge success by teacher time saved, output trust, and principal confidence — not by the number of modules shown.”

---

## 6. What not to say

Avoid:

- “The system is fully pilot-ready for every persona.”
- “Students and parents are included in this release.”
- “AI automatically replaces teacher review.”
- “It can ingest any textbook perfectly.”
- “The AI is always correct.”

Use instead:

- “Release 0.3 validates principal and teacher workflows.”
- “Humans approve consequential academic outputs.”
- “The system uses approved curriculum memory.”
- “Student and parent journeys are next-phase pilot scope.”

---

## 7. If something goes wrong

### AI generation is slow

Say:

> “AI generation can take a little time because it is grounding against the approved curriculum. I’ll open the prevalidated output so we can keep the discussion focused.”

### AI credit warning appears

Say:

> “This tenant is credit-metered. For the pilot we configure the school budget ahead of time. I’ll use the prevalidated output for now.”

Do not debug credits live.

### Browser route fails

Say:

> “This looks like an environment refresh issue, not the academic workflow. I’ll switch to the validated backup session.”

Do not show terminal logs unless the school is technical and asks.

---

## 8. Post-demo notes

Immediately after the call, record:

- principal confidence level;
- Teacher 1 usefulness rating;
- Teacher 2 governance concerns;
- confusing screens;
- missing guidance;
- pilot blockers;
- requested first class/subject;
- decision: proceed / wait / reject.
