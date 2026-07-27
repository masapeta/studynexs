# AEI v1.0 Teacher Evaluation Experience Design Brief

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Classification:** Product-facing design brief
- **Status:** Accepted
- **Implementation:** Not authorized by this document
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Architecture baseline:** [`../../architecture/AEI.md`](../../architecture/AEI.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

AEI v1.0 is certified for the declared supported scope. That certification proves
the foundations exist, the Golden Harness passes, and the behavior-changing
capabilities are safely guarded.

The next product problem is different:

> Make the certified AEI v1.0 capability visible, understandable, and useful to
> teachers in the real evaluation workflow without breaking trust.

This design brief defines the school-facing teacher evaluation experience that
should be implemented after AEI v1.0 certification.

It does not authorize code, schema, API, UI, configuration, or rollout changes.
Implementation must still proceed through separate ARM implementation
authorization contracts.

---

## 2. Product outcome

The teacher evaluation workflow should feel production-ready inside the declared
AEI v1.0 supported scope.

A teacher should be able to:

1. choose a student and upload an answer sheet or enter answers manually;
2. run evaluation against an approved question paper;
3. see AI-suggested marks clearly labeled as suggestions;
4. understand why a suggestion was made;
5. see confidence, manual-review, and capability-boundary signals;
6. inspect deterministic Maths normalization where available;
7. inspect language/OCR assist posture where available;
8. inspect visual/science checklist posture where available;
9. adjust marks and record meaningful override reasons;
10. approve final marks;
11. trust that only teacher-approved evidence flows downstream.

The teacher remains the final authority.

---

## 3. Core principle

This workstream must turn internal AEI trust evidence into teacher confidence.

It must not turn AI suggestions into autonomous grading.

```text
Answer Sheet / Manual Answers
        |
        v
Existing Evaluation Service
        |
        v
AEI v1.0 supported-scope metadata
        |
        v
Teacher Review UI
        |
        v
Teacher Approval / Override
        |
        v
Approved Evidence Only
```

The product should communicate:

```text
AI recommends. Teacher decides. Evidence explains.
```

---

## 4. Existing surfaces to reuse

### 4.1 Backend surfaces

Reuse and extend only through authorized implementation contracts:

- `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py`
- `apps/api/app/modules/examinations/endpoints/evaluation.py`
- `apps/api/app/modules/examinations/schemas/evaluation.py`
- `apps/api/app/modules/examinations/services/aei_v1_math_normalization.py`
- `apps/api/app/modules/examinations/services/aei_v1_review_policy.py`
- `apps/api/app/modules/examinations/services/aei_v1_evidence_ledger.py`
- `apps/api/app/modules/examinations/services/aei_v1_language_ocr_assist.py`
- `apps/api/app/modules/examinations/services/aei_v1_visual_science_assist.py`
- `apps/api/app/modules/examinations/data/subject_capability_registry.v1.json`

### 4.2 Frontend surfaces

Reuse the existing evaluation page rather than creating a parallel experience:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`
- `apps/admin-web/src/app/dashboard/exams/[examId]/evaluate/page.tsx`

The existing teaching route is the canonical teacher evaluation surface. The
legacy dashboard route already redirects to it.

### 4.3 Existing product primitives

Reuse:

- existing upload/manual-answer flow;
- existing async evaluation polling;
- existing suggestions table;
- existing final-marks input;
- existing approval endpoint;
- existing evidence-chain strip;
- existing `EvaluationOut.ai_suggestions` and `EvaluationOut.evidence_ledger`
  additive JSON shapes;
- existing teacher override payload;
- existing Mastery / misconceptions propagation after approval.

Do not create a second evaluation page or parallel evaluation API.

---

## 5. Experience design

### 5.1 Entry state

The page should make the supported input modes clear:

- answer sheet image upload;
- manual answer entry;
- mixed flow where manual answers fill OCR gaps.

The copy should avoid overclaiming OCR.

Preferred posture:

```text
Upload an answer sheet photo or enter answers manually. Low-confidence or
unsupported cases remain teacher-reviewed.
```

Avoid:

```text
AI automatically corrects all answer sheets.
```

### 5.2 Evaluation running state

While evaluation is processing, teachers should see calm, operationally honest
status:

- evaluation queued;
- OCR/extraction may be in progress;
- AI suggestions are draft only;
- teacher review is required before marks are published.

### 5.3 Suggested-review state

The review table should show more than marks.

Each question should communicate:

- suggested marks;
- final teacher marks;
- confidence;
- method or capability mode;
- manual review requirement;
- reason for manual review;
- normalization/equivalence evidence where present;
- language/OCR assist evidence where present;
- visual/science checklist evidence where present;
- feedback/rubric breakdown;
- missing concepts, if available.

### 5.4 Trust summary

The page should include a compact trust summary above the table:

- how many questions are high-confidence supported;
- how many require teacher review;
- how many are assist/checklist/manual-review only;
- whether evidence is grounded to a question paper/curriculum pack;
- whether approved evidence will be produced only after teacher approval.

This summary should be teacher-facing, not executive analytics.

### 5.5 Manual review indicators

Manual review should be visually obvious but not alarming.

Examples:

- "Teacher review required"
- "Low confidence"
- "Assist only"
- "Checklist only"
- "Unsupported for automatic marks"
- "OCR needs confirmation"

The UI should never hide uncertain output behind a normal-looking mark.

### 5.6 Teacher override experience

If the teacher changes marks, the UI should require or strongly guide an
override reason.

The reason should be:

- per-question;
- short;
- auditable;
- visible before approval;
- stored through the existing override contract where authorized.

Defaulting every override to `"Teacher adjustment"` should be replaced in a
future implementation batch with an explicit teacher-entered reason or a
teacher-selected reason.

### 5.7 Approval state

After approval, the page should clearly distinguish:

- original AI suggestion;
- final teacher decision;
- override reason where applicable;
- approval timestamp;
- approved evidence chain.

The product should communicate that marks are now teacher-approved and eligible
for downstream learning intelligence.

---

## 6. Supported-scope display policy

Teacher-facing labels must align with the supported scope matrix.

| Capability posture | Teacher-facing wording | Product behavior |
|---|---|---|
| `supported` | Supported deterministic check | May show match/equivalence evidence |
| `assist` | Assist only - teacher confirmation required | Do not imply automatic correctness |
| `checklist` | Checklist only - teacher confirmation required | Show observations, not final marks authority |
| `manual_review` | Teacher review required | Do not present as certified AI evaluation |
| `unsupported` | Not supported for automatic evaluation | Preserve teacher authority |

No UI, tooltip, support copy, or marketing copy should claim more than the
supported scope matrix certifies.

---

## 7. Data/API posture

Preferred posture:

- use existing additive JSON payloads where already available;
- avoid schema migrations unless a later implementation contract proves
  necessity;
- avoid public API contract breaking changes;
- expose only teacher-safe metadata in the teacher evaluation UI;
- keep student/parent-facing consumers on teacher-approved evidence only.

If a future batch requires explicit response fields, they must be additive to
`/api/v1` and separately authorized.

---

## 8. Feature-flag and rollout posture

All AEI v1.0 behavior flags remain default-off in source:

- `AEI_V1_MATH_NORMALIZATION_ENABLED=false`
- `AEI_V1_REVIEW_POLICY_ENABLED=false`
- `AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false`
- `AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false`
- `AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false`

Product-facing enablement should use controlled configuration and certification.

Recommended rollout posture:

1. implement UI display with safe fallback when metadata is absent;
2. prove existing behavior with all flags off;
3. enable one capability family at a time in controlled environments;
4. run browser proof on the teacher evaluation page;
5. certify teacher-facing claims against the supported scope matrix.

A later implementation contract may introduce a dedicated UI display flag if
needed, but this design does not require one yet.

---

## 9. Proposed implementation batches

Implementation should be incremental, school-visible, and reviewable.

### Batch UX-A - Review-table trust metadata display

Goal:

Show AEI suggestion metadata that already exists in `ai_suggestions`.

Candidate scope:

- confidence badge;
- method/capability badge;
- manual-review badge;
- manual-review reason;
- normalized/matched answer evidence for Maths;
- safe fallback when metadata is absent.

Expected surfaces:

- teacher evaluation page;
- frontend types/helpers;
- focused UI tests where available;
- browser proof.

Explicit exclusions:

- no marks logic changes;
- no approval logic changes;
- no API/schema changes unless separately authorized;
- no source switch;
- no public product claim changes.

### Batch UX-B - Override reason workflow

Goal:

Replace generic override reasons with teacher-visible, auditable override
reason capture.

Candidate scope:

- per-question override reason input when marks change;
- validation before approval;
- preserve existing approval endpoint shape if possible;
- display approved override reasons after approval.

Explicit exclusions:

- no new review-state machine;
- no notification workflows;
- no parent/student visibility changes.

### Batch UX-C - Evidence and approved-decision panel

Goal:

Make the evidence chain and approved-evidence posture understandable.

Candidate scope:

- improve existing evidence strip;
- show original suggestion versus final teacher decision;
- show approved evidence status after approval;
- make grounded/citation status clearer.

Explicit exclusions:

- no new evidence ledger schema;
- no downstream consumer migration;
- no EUI source adoption.

### Batch UX-D - Supported-scope assist panels

Goal:

Expose language/OCR and visual/science assist/checklist metadata honestly.

Candidate scope:

- OCR/source confidence messages;
- language/script/code-mixed metadata;
- visual/science checklist observations;
- clear "teacher confirmation required" posture.

Explicit exclusions:

- no new OCR engine;
- no LLM vision expansion;
- no autonomous visual/science marks;
- no universal handwriting claim.

### Batch UX-E - Teacher evaluation experience certification

Goal:

Certify the product-facing teacher evaluation experience.

Candidate scope:

- browser proof;
- API regression;
- frontend build/lint where practical;
- supported-scope copy review;
- feature-flag matrix;
- rollback proof;
- teacher-trust acceptance checklist.

---

## 10. Non-goals

This workstream is not:

- a new AEI architecture;
- a new EUI source-adoption wave;
- a new evaluation engine;
- a new OCR engine;
- a new visual grading engine;
- autonomous grading;
- report-card automation;
- parent/student result publication;
- principal analytics expansion;
- broad school-operations work;
- marketing-site claim expansion.

---

## 11. Explicit exclusions

Until a batch-specific implementation authorization contract states otherwise,
this workstream does not authorize:

- database schema changes;
- database migrations;
- breaking API changes;
- new public endpoints;
- source-of-truth switching to EUI;
- Phase 7F source adoption;
- marks calculation changes;
- teacher-review routing changes outside existing approval flow;
- evidence-ledger persistence changes;
- parent/student UI visibility of uncertified AI suggestions;
- public capability claim changes;
- enabling AEI v1.0 flags in production;
- enabling unsupported capabilities;
- LLM provider changes;
- payment/billing changes.

---

## 12. Testing and certification strategy

Each implementation batch should include evidence appropriate to its blast
radius.

Minimum expected validation:

- focused API/backend tests for any touched backend surface;
- focused frontend build/type/lint validation for touched UI surfaces;
- browser proof for the teacher evaluation page when UI changes;
- Golden Harness additions if metadata interpretation changes;
- regression for flag-off behavior;
- regression for approval/marks persistence when approval flow is touched;
- `python -c "import app.main"` when backend is touched;
- `git diff --check`.

Batch certification should explicitly state:

- what changed;
- what did not change;
- feature flags and defaults;
- user-visible behavior;
- supported-scope claim alignment;
- rollback path;
- tests and browser proof.

---

## 13. Acceptance criteria for the full workstream

The teacher evaluation experience is complete when:

- teachers can see why AI suggested each mark;
- confidence and manual-review cases are obvious;
- supported Maths equivalence metadata is visible where present;
- assist/checklist-only cases are clearly labeled as teacher-reviewed;
- override reasons are captured instead of hidden behind generic text;
- approved evidence is visibly distinct from unapproved AI suggestions;
- parent/student downstream posture remains approved-evidence only;
- no unsupported capability is claimed;
- browser proof passes for the teacher evaluation workflow;
- rollback is straightforward through configuration and code revert;
- AEI/EUI architecture remains unchanged.

---

## 14. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended first implementation batch:

```text
Batch UX-A - Review-table trust metadata display
```

Reason:

It delivers visible teacher trust value by displaying existing certified AEI
metadata, while minimizing risk by avoiding marks logic, approval logic, schema
changes, source switching, and downstream consumer changes.

---

## 15. ARM review decision

**Design brief status:** Accepted

ARM decision:

```text
Accept the design brief.
Next artifact: Batch UX-A Implementation Authorization Contract.
Implementation remains unauthorized until the contract is accepted.
```
