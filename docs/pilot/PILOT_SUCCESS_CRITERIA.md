# StudyNexs Pilot Success Criteria — Release 0.3

> Objective customer-centered criteria for deciding whether the Principal + Teacher pilot is successful.

**Release baseline:** `v0.3.0`
**Pilot scope:** Principal + Teacher workflows
**Deferred:** Student and Parent journeys

---

## 1. Success definition

A Release 0.3 pilot is successful if the school concludes:

> “StudyNexs is worth piloting with real teachers because it can learn our curriculum and help teachers prepare grounded academic work with human control.”

Success is not defined by the number of screens shown. It is defined by principal confidence and teacher willingness to use the workflow.

---

## 2. Required customer outcomes

| Outcome | Success threshold |
|---|---|
| Principal understands the value | Principal can explain StudyNexs in their own words as curriculum-grounded teacher support |
| Teacher sees usefulness | At least one teacher says they would use the lesson-plan or question-paper workflow in real preparation |
| Trust is maintained | Principal and teachers understand that AI outputs are grounded and human-reviewed |
| Pilot scope is accepted | School agrees to start with Principal + Teacher workflow before Student/Parent expansion |
| First pilot wedge identified | School names one class, one subject, and one or two teachers for the first week |

---

## 3. Objective acceptance criteria

### Principal criteria

| Criterion | Pass condition |
|---|---|
| Value clarity | Principal understands “curriculum first, AI second” |
| Trust | Principal is comfortable that teacher review remains required |
| Pilot fit | Principal can identify where StudyNexs fits in current academic operations |
| Decision readiness | Principal is willing to schedule or approve a small teacher pilot |

### Teacher criteria

| Criterion | Pass condition |
|---|---|
| Workflow clarity | Teacher can identify where to start |
| Output usefulness | Teacher rates lesson plan or question paper as useful enough to edit |
| Trust | Teacher understands the output comes from approved curriculum |
| Control | Teacher feels they remain responsible for review and final use |
| Adoption | Teacher is willing to try the workflow with one real class/subject |

### Operator criteria

| Criterion | Pass condition |
|---|---|
| Runtime readiness | Runtime proof passes before pilot |
| Browser readiness | Browser walkthrough passes before pilot |
| Tenant isolation | Correct tenant observed in validation |
| AI readiness | AI credits or override available |
| No live engineering | Demo completes without terminal/API intervention during the school conversation |

---

## 4. Pilot scorecard

Score each item from 1 to 5.

| Area | Score | Notes |
|---|---:|---|
| Principal understood value | | |
| Principal trusted the workflow | | |
| Principal willing to pilot | | |
| Teacher 1 found lesson plan useful | | |
| Teacher 1 found question paper useful | | |
| Teacher 2 understood governance | | |
| Workflow felt clear | | |
| AI felt trustworthy | | |
| Demo required no engineering intervention | | |
| School identified first class/subject | | |

Interpretation:

| Total | Meaning |
|---:|---|
| 40–50 | Strong pilot fit |
| 30–39 | Pilot fit with conditions |
| 20–29 | Needs remediation before pilot |
| <20 | Do not proceed |

---

## 5. Go / no-go decision

### Go

Proceed to pilot if:

- runtime proof passed;
- browser walkthrough passed;
- principal is willing to pilot;
- at least one teacher is willing to use the workflow;
- first class/subject is identified;
- no critical trust objections remain.

### Go with conditions

Proceed only after conditions are addressed if:

- principal is interested but wants one concern clarified;
- teacher output is useful but setup needs tightening;
- AI credits/setup need operator preflight;
- school wants a narrower one-week trial.

### No-go

Do not proceed if:

- principal does not understand the value;
- teachers do not see preparation value;
- school expects Student/Parent workflows in the first pilot;
- school wants fully automated AI without human review;
- pilot requires capabilities outside Release 0.3;
- demo needed live engineering rescue.

---

## 6. Required post-pilot notes

Capture:

- principal quote;
- Teacher 1 quote;
- Teacher 2 quote;
- top three objections;
- top three moments of interest;
- confusing workflow points;
- requested first class/subject;
- desired pilot start date;
- decision: go / conditional / no-go.

---

## 7. What counts as failure

The pilot should be considered unsuccessful if any of these occur:

- the school leaves thinking StudyNexs is just a chatbot;
- teacher cannot see how to use the workflow;
- principal does not trust AI-generated academic material;
- product requires engineering intervention during the customer session;
- tenant/data isolation is questioned;
- the school’s desired pilot depends on deferred Student/Parent scope.

---

## 8. What counts as strong success

Strong success looks like:

- principal asks to try it with a real class;
- teachers ask whether they can upload their own syllabus or generate for tomorrow’s class;
- academic lead asks about approval workflow;
- school accepts a narrow first-week pilot;
- school understands Student/Parent workflows are next-phase, not missing from this pilot.
