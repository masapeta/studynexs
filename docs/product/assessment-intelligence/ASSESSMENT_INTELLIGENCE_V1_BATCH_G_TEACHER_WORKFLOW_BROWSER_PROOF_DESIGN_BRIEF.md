# Assessment Intelligence v1.0 Batch G Teacher Workflow / Browser Proof Design Brief

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Classification: Product implementation design brief
> Program: Assessment Intelligence v1.0
> Batch: G - Teacher Workflow / Browser Proof
> Implementation: Not authorized
> Runtime behavior changes: Not authorized by this document
> Previous baseline: Batch F Bilingual / Multilingual Assessment Readiness
> ARM review: Accepted as the Batch G Teacher Workflow / Browser Proof design baseline

---

## 1. Purpose

Batch G exists to prove that the supported Assessment Intelligence v1.0
teacher-visible workflow works end to end in the browser.

It answers:

> Can a teacher use StudyNexs to create, review, approve, link, evaluate, and
> inspect an assessment workflow without engineering help, while all
> authoritative outcomes remain teacher-approved?

Batch G should be a proof and certification gate, not a new architecture phase.

---

## 2. Why Batch G exists

Batches A-F established the static readiness foundation:

- canonical assessment contract;
- supported-scope capability matrix;
- blueprint readiness;
- rubric/model-answer readiness;
- question-bank/reuse readiness;
- paper-to-evaluation linkage readiness;
- bilingual/multilingual support boundary.

Those foundations are necessary, but a school does not experience declarations
or Golden Harness files. A school experiences the teacher workflow.

Batch G bridges static readiness to product confidence by proving the existing
teacher-facing surfaces operate coherently for the declared supported scope.

---

## 3. Product outcome

The target teacher workflow is:

```text
Teacher / authorized staff
    -> Open AI Papers
    -> Create or use an existing supported-scope draft paper
    -> Review questions, answer context, blueprint posture, and language posture
    -> Submit / approve according to existing role flow
    -> Download or inspect approved paper artifacts where available
    -> Link approved paper to an exam question schema
    -> Open evaluation workflow
    -> Confirm AEI remains the evaluation path
    -> Confirm teacher approval remains final authority
```

The goal is not to make every possible assessment scenario browser-proof. The
goal is to prove one or more declared supported scenarios deeply enough that
Assessment Intelligence v1.0 can be certified honestly.

---

## 4. Current repository surfaces to reuse

Batch G should reuse existing product surfaces.

### 4.1 Frontend surfaces

- `apps/admin-web/src/app/dashboard/teaching/ai-papers/page.tsx`
- `apps/admin-web/src/app/dashboard/teaching/exams/page.tsx`
- `apps/admin-web/src/app/dashboard/teaching/exams/QuestionSchemaEditor.tsx`
- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`
- `apps/admin-web/e2e-smoke.cjs`
- `apps/admin-web/e2e-harness-utils.cjs`

### 4.2 Backend surfaces

- `apps/api/app/modules/ai/services/question_paper_service.py`
- `apps/api/app/modules/ai/services/question_bank_service.py`
- `apps/api/app/modules/ai/endpoints/ai.py`
- `apps/api/app/modules/examinations/services/exam_service.py`
- `apps/api/app/modules/examinations/endpoints/exam.py`
- `apps/api/app/modules/examinations/endpoints/evaluation.py`

### 4.3 Certification foundations

- Assessment Intelligence v1.0 Batch A-F artifacts;
- AEI v1.0 certification artifacts;
- Teacher Evaluation UX-A through UX-E certifications;
- Topic-ID / Mastery Spine passive resolution evidence;
- Operational Proof baseline.

Batch G should extend these surfaces only if later authorized by an
implementation contract.

---

## 5. Batch G design scope

Batch G should define and later certify the browser proof for the supported
teacher assessment workflow.

In scope for a future implementation contract:

1. browser proof scenario definition;
2. deterministic test data or fixture strategy;
3. teacher workflow evidence capture;
4. screenshots or trace artifacts where practical;
5. API failure and console-error guardrails;
6. tenant-boundary evidence;
7. supported-scope assertion checks;
8. question-paper readiness visibility checks;
9. paper-to-exam linkage checks;
10. evaluation-entry checks;
11. certification report.

Batch G may include small browser-harness additions only if the future
implementation contract explicitly authorizes them.

---

## 6. Explicit non-goals

Batch G is not attempting to:

- redesign the teacher UI;
- create a new assessment workflow;
- implement new question-paper generation behavior;
- implement new blueprint logic;
- implement translation or multilingual rendering;
- implement new OCR;
- implement new AEI evaluation logic;
- switch EUI to source of truth;
- expand public product claims;
- migrate parent/student/principal consumers;
- add new database schema;
- add new public APIs;
- enable autonomous marks;
- bypass teacher authority.

This is a proof gate, not a feature-expansion gate.

---

## 7. Proof philosophy

Browser proof should be deterministic, repeatable, and honest.

The preferred posture is:

```text
Existing runtime behavior
    -> deterministic reference data
    -> browser walkthrough
    -> screenshots / trace evidence
    -> no console/API/tenant errors
    -> certification report
```

Browser proof should not depend on live LLM generation unless explicitly
authorized and isolated. If generated content is required for the scenario, the
future implementation contract should prefer one of:

- existing approved fixture paper;
- deterministic seeded paper;
- existing school-private approved paper;
- mocked/stubbed generation only in test harness, not production code.

Live AI may be used only when the implementation contract explicitly permits it
and the result is still teacher-reviewed and non-authoritative until approval.

---

## 8. Supported browser proof scenarios

The future Batch G implementation should define at least one primary supported
scenario and may define secondary smoke scenarios.

### 8.1 Primary supported scenario

Recommended primary proof:

```text
SSC / Telangana reference material / Grade 6 / Science / Unit Test / English
```

Why:

- it is already represented in Assessment Intelligence v1.0 supported scope;
- it aligns with grounded paper posture;
- it exercises paper creation/readiness and evaluation linkage;
- it avoids overclaiming advanced blueprint, multilingual, or visual behavior.

### 8.2 Secondary supported scenario

Recommended secondary proof:

```text
SSC / Reference curriculum / Grade 10 / Mathematics / Unit Test or Term-style paper / English
```

Why:

- it validates Mathematics supported scope;
- it aligns with AEI Maths normalization certification;
- it gives product evidence for a high-value teacher workflow.

Secondary proof may be deferred if the implementation contract needs to stay
very narrow.

---

## 9. Minimum browser proof assertions

Batch G proof should verify:

- authenticated teacher/staff route access works;
- tenant context is preserved;
- AI Papers page renders without console/API failures;
- supported-scope paper details are visible;
- draft/non-authoritative posture is visible before approval;
- teacher approval posture is visible;
- approved paper can be selected or linked for exam schema use;
- exam question schema preserves question numbers and marks;
- evaluation page opens for the linked exam;
- AEI remains the evaluation path;
- teacher remains final authority;
- unsupported bilingual/multilingual claims are not presented as production
  support;
- no parent/student evidence is exposed before teacher-approved outcomes.

The proof should fail loudly if the browser flow redirects to login, loses
tenant context, emits unauthorized API failures, or silently bypasses teacher
authority.

---

## 10. Evidence capture

Batch G certification should capture enough evidence for an independent review.

Recommended evidence:

- command used;
- environment assumptions;
- seeded fixture or reference dataset;
- browser screenshots;
- Playwright trace or equivalent if available;
- console/API failure summary;
- tenant boundary summary;
- route list exercised;
- product-claim assertions;
- final certification decision.

Screenshots should be treated as certification evidence, not product assets.

---

## 11. Runtime constraints

Batch G should not change product behavior unless a later implementation
contract explicitly authorizes a small, necessary fix.

Default constraints:

- no schema changes;
- no public API contract changes;
- no new production feature flags;
- no AI provider changes;
- no LLM prompt changes;
- no OCR changes;
- no marks changes;
- no teacher review routing changes;
- no evidence-ledger behavior changes;
- no parent/student/principal visibility changes;
- no EUI source-of-truth switch;
- no public product claim expansion.

If browser proof exposes a defect, the defect should be handled through a
separate implementation authorization or a clearly scoped bugfix decision.

---

## 12. Validation strategy

A future implementation contract should require:

### 12.1 Frontend validation

- admin-web build;
- focused lint for touched browser proof files;
- browser proof command;
- screenshot/trace artifact check;
- console/API guard check;
- tenant guard check.

### 12.2 Backend validation

- API import;
- focused assessment regression tests;
- focused AEI regression tests where evaluation path is opened;
- `git diff --check`.

### 12.3 Certification validation

- Batch G Certification Report;
- proof evidence inventory;
- explicit unsupported-claim check;
- rollback statement.

---

## 13. Failure handling

Batch G should distinguish between:

| Failure type | Handling |
|---|---|
| Test environment unavailable | Record as blocked; do not claim browser proof. |
| Missing reference data | Add or document deterministic test data only if authorized. |
| Existing UI defect | Record defect; fix only under explicit scope. |
| Runtime product bug | Stop for ARM decision if behavior-impacting. |
| Console/API/tenant failure | Certification fails until resolved or explicitly waived. |
| Live AI unavailable | Use deterministic fixture path unless live AI is explicitly required. |

No certification should claim browser proof if the browser was not actually
exercised.

---

## 14. Certification criteria

Batch G may be accepted only when it can truthfully state:

- browser proof executed against the supported teacher assessment flow;
- teacher workflow renders without blocking errors;
- tenant context is preserved;
- assessment readiness posture is visible or verifiable;
- paper-to-exam linkage is visible or verifiable;
- evaluation path opens without bypassing AEI;
- teacher authority remains intact;
- unsupported bilingual/multilingual claims are not shown as supported;
- no unauthorized schema/API/UI/runtime/marks/evidence behavior changed;
- screenshots/trace/evidence are available for review;
- certification report is complete.

---

## 15. Explicit exclusions

This design brief does not authorize:

- runtime implementation;
- browser harness changes;
- UI changes;
- API changes;
- database changes;
- seed data changes;
- feature flags;
- AI provider changes;
- LLM inference changes;
- question generation changes;
- exam service behavior changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger changes;
- parent/student/principal consumer changes;
- public product claim expansion.

---

## 16. Recommended implementation authorization shape

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/assessment-intelligence/
ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended scope:

- define the exact browser proof scenario;
- authorize any required test harness additions;
- authorize deterministic fixture/reference data only if needed;
- require screenshots/trace evidence;
- require frontend build and browser validation;
- require focused Assessment/AEI regression tests;
- prohibit product behavior changes unless explicitly listed.

---

## 17. ARM gate

Current status:

```text
Design brief: Accepted
Implementation: Not authorized
```

ARM may:

1. accept this design brief and request the Batch G implementation
   authorization contract;
2. request revisions;
3. defer Batch G and move to another product-completion area.
