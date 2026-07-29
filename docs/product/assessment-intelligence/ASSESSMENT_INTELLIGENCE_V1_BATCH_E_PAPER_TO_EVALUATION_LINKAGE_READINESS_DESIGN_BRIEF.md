# Assessment Intelligence v1.0 Batch E Design Brief

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Program: Assessment Intelligence v1.0
> Batch: E - Paper-to-Evaluation Linkage Readiness
> Status: Accepted
> Classification: Product implementation design
> Implementation: Not authorized
> Runtime behavior changes: Not authorized by this document
> Previous baseline: Batch D - Question Bank and Reuse Readiness
> ARM review: Accepted as the Batch E Paper-to-Evaluation Linkage Readiness design baseline

---

## 1. Purpose

Batch E should make the path from approved question paper to evaluation explicit,
auditable, and teacher-governed.

It answers:

> How does an approved paper become evaluation-ready without allowing OCR, AEI,
> question schemas, or reused assessment assets to bypass teacher authority?

This document is design-only. It does not authorize implementation.

---

## 2. Why Batch E exists

Assessment Intelligence v1.0 Batch A established the canonical assessment
contract.

Batch B made blueprint readiness explicit.

Batch C made rubric and model-answer readiness explicit.

Batch D made question-bank reuse explicit and provenance-backed.

Batch E is the next dependency because assessment creation only becomes useful
when it safely connects to evaluation.

The product loop now needs a certified linkage posture:

```text
Approved Question Paper
        |
        v
Exam Question Schema
        |
        v
Student Answer Input
        |
        v
AEI Evaluation Assist
        |
        v
Teacher Review and Approval
        |
        v
Approved Evidence / Marks / Mastery
```

Without this layer, a paper may be approved, a schema may exist, and AEI may
produce suggestions, but the system would not have a clearly documented contract
for which source is authoritative at each step.

Batch E should close that gap before broader teacher-facing assessment flows
depend on the linkage.

---

## 3. Repository foundations to reuse

Batch E should extend the existing examination, evaluation, and question-paper
linkage foundations rather than introducing a parallel evaluation path.

Relevant backend foundations include:

- `apps/api/app/db/models/examination.py`;
- `Exam.source_paper_id`;
- `Exam.question_schema`;
- `ExamMark.question_marks`;
- `apps/api/app/modules/examinations/schemas/exam.py`;
- `QuestionSchemaSet`;
- `ExamOut.can_evaluate_sheets`;
- `apps/api/app/modules/examinations/services/exam_service.py`;
- `ExamService.set_question_schema`;
- `ExamService._questions_from_paper`;
- `ExamService.enter_marks`;
- `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py`;
- `AnswerSheetEvalService.create_and_evaluate`;
- `AnswerSheetEvalService._resolve_student_answers`;
- `AnswerSheetEvalService._grade_exam`;
- `AnswerSheetEvalService._grade_subjective_items`;
- `AnswerSheetEvalService.approve`;
- `fetch_rubrics_for_paper`;
- `EvaluationOut`;
- `CorrectionHistoryItem`.

Relevant current behavior includes:

- an exam can reference an approved source question paper through
  `source_paper_id`;
- an exam can carry a per-question `question_schema`;
- paper import derives question numbers, max marks, and topic posture;
- evaluation is only available when an exam has both a source paper and a
  question schema;
- answer-sheet evaluation uses the linked source paper to fetch rubric and
  answer context;
- teacher approval remains the point where marks become authoritative;
- correction history already exposes paper and curriculum grounding fields.

Batch E should document and test this posture first. Runtime behavior changes
require a later implementation authorization.

---

## 4. Product outcome

After Batch E is eventually implemented and certified, StudyNexs should be able
to say:

> For the declared supported scope, an approved question paper can be linked to
> an exam, used to create an evaluation-ready question schema, provide AEI with
> rubric/model-answer context, and produce teacher-approved evidence without
> changing the rule that teachers remain the final authority.

Teachers should be able to trust that evaluation suggestions are grounded in the
approved paper and its approved answer context, not in a detached OCR result,
ad hoc prompt, or unreviewed question structure.

---

## 5. Design principle

Paper-to-evaluation linkage creates readiness, not authority.

```text
Approved Paper
     |
     v
Linked Exam Schema
     |
     v
AEI Suggestion
     |
     v
Teacher Approval
     |
     v
Authoritative Marks and Evidence
```

The linked paper and schema tell the platform what can be evaluated and which
context should be used. They do not approve marks, override teacher review, or
make downstream learning evidence authoritative by themselves.

---

## 6. Relationship to earlier Assessment Intelligence batches

Batch E should consume the previous Assessment Intelligence contracts rather
than redefining them.

### Batch A fields

Paper-to-evaluation linkage should preserve or reference:

- `assessment_id`;
- `paper_id`;
- `school_id`;
- `class_id`;
- `subject_id`;
- `board`;
- `grade`;
- `paper_type`;
- `section_id`;
- `question_number`;
- `question_type`;
- `marks`;
- `topics`;
- `educational_identity_id` where available;
- `source`;
- `approval_status`;
- `teacher_review_required`;
- `approved_evidence_required`.

### Batch B fields

Evaluation readiness should preserve blueprint posture where available:

- `blueprint_id`;
- `section_id`;
- `marks_per_question`;
- `question_count`;
- `answer_any_count`;
- `validation_rules`;
- `product_claim_allowed`.

### Batch C fields

AEI and evaluation assist should receive answer-context posture from the linked
paper:

- `answer_key`;
- `model_answer`;
- `acceptable_answers`;
- `rubric_id`;
- `rubric_posture`;
- `criteria`;
- `checklist_items`;
- `manual_review_reason`;
- `unsupported_reason`;
- `aei_capability_mode`;
- `teacher_review_required`.

### Batch D fields

If the approved paper was composed partly from the question bank, linkage should
preserve reuse provenance:

- `bank_item_id`;
- `source_paper_id`;
- `source_question_bank_item_id`;
- `content_fingerprint`;
- `reuse_posture`;
- `gap_fill_posture`;
- `reuse_requires_teacher_review`.

---

## 7. Paper-to-evaluation linkage declaration model

A paper-to-evaluation linkage declaration should describe whether an exam is
ready for evaluation assist. It should not approve marks or evidence.

Minimum declaration fields:

| Field | Purpose |
|---|---|
| `linkage_id` | Stable declaration identifier for review and certification. |
| `school_id` | Tenant boundary, derived server-side only. |
| `exam_id` | Exam that receives the schema and evaluation linkage. |
| `source_paper_id` | Approved paper used as the source of evaluation context. |
| `source_paper_status` | Approval status of the source paper. |
| `question_schema_source` | `approved_paper`, `manual`, `unsupported`, or `unknown`. |
| `question_schema` | Canonical per-question structure used for marks and evaluation. |
| `question_numbers` | Question numbers expected in the evaluation input. |
| `max_marks` | Per-question max marks used to validate teacher-approved marks. |
| `topic_posture` | Topic/concept linkage posture. |
| `educational_identity_posture` | Whether canonical Educational Identity is attached, absent, or deferred. |
| `rubric_source` | Source of answer key, model answer, rubric, or checklist context. |
| `rubric_available` | Whether linked rubric/model-answer context exists. |
| `ocr_input_allowed` | Whether OCR may be used as an answer-input assist. |
| `manual_input_allowed` | Whether manual answer input is accepted. |
| `can_evaluate_sheets` | Whether the exam is ready for evaluation assist. |
| `aei_assist_allowed` | Whether AEI may produce non-authoritative suggestions. |
| `teacher_review_required` | Whether teacher approval is required before authority. |
| `approved_evidence_required` | Whether downstream evidence must wait for teacher approval. |
| `marks_source` | Expected authority source for marks. |
| `mastery_source` | Expected authority source for mastery events. |
| `product_claim_allowed` | Whether the supported product claim may be made for this linkage. |

---

## 8. Linkage support modes

Batch E should use explicit support modes instead of implying universal
coverage.

| Mode | Meaning |
|---|---|
| `supported` | Linkage is within declared scope and may proceed under teacher authority. |
| `assist` | Linkage can provide non-authoritative assistance but requires review. |
| `manual_review` | Human review is required before any downstream authority. |
| `unsupported` | Linkage must not be treated as evaluation-ready. |
| `expansion` | Future scope; no product claim should be made. |

---

## 9. Initial supported posture

Batch E should begin with conservative declarations.

| Scenario | Posture |
|---|---|
| Approved paper imports into exam question schema in same tenant | `supported` |
| Draft or unapproved paper used as schema source | `unsupported` |
| Cross-tenant source paper reference | `unsupported` |
| Approved paper has no usable questions | `unsupported` |
| Exam has source paper and question schema | `supported` for evaluation readiness |
| Exam has manual schema but no source paper | `manual_review` / not AEI-supported |
| Exam has source paper but missing schema | `unsupported` |
| Schema replacement would orphan existing marks | `unsupported` / protected |
| OCR answer input for linked exam | `assist` only |
| Manual answer input for linked exam | `assist` only |
| Rubric fetch by linked source paper | `supported` where Batch C context exists |
| AEI-generated marks before teacher approval | `unsupported` |
| Teacher-approved marks and evidence | `supported` |
| Parent/student/principal evidence before approval | `unsupported` |

---

## 10. Deterministic validation expectations

Batch E should define deterministic validation rules for linkage readiness.

At minimum:

- the source paper must belong to the same school as the exam;
- the source paper must be approved before it can be used as an authoritative
  schema source;
- question numbers must be unique in the exam question schema;
- per-question max marks must be positive and bounded;
- the question schema must be compatible with the exam total-marks posture;
- `can_evaluate_sheets` must require both `source_paper_id` and
  `question_schema`;
- rubric/model-answer context must be fetched through the linked source paper;
- OCR and manual input must be treated as answer-input mechanisms only;
- AEI output must remain non-authoritative until teacher approval;
- marks must become authoritative only through teacher approval;
- evidence and mastery outputs must be based on approved marks/evidence only.

---

## 11. Current runtime migration posture

The existing runtime already contains several linkage seams:

- `source_paper_id` links an exam to a question paper;
- `question_schema` links marks to question numbers;
- `can_evaluate_sheets` exposes evaluation readiness;
- answer-sheet evaluation requires linked source paper and schema;
- rubric fetch is scoped to `school_id` and `source_paper_id`;
- teacher approval writes final marks;
- correction history exposes paper/curriculum grounding.

Batch E should not assume these seams are complete product readiness. It should
turn them into a declared, testable linkage foundation and identify any gaps
before consumer-facing expansion depends on them.

---

## 12. Recommended future implementation scope

The future Batch E implementation authorization should remain narrow.

Recommended authorized scope:

- paper-to-evaluation linkage declaration contract;
- supported-scope declarations for approved-paper linkage;
- deterministic linkage readiness helper or service where needed;
- Golden Harness cases for linkage readiness;
- focused tests for existing paper/schema/evaluation boundary behavior;
- certification report.

The implementation should remain compatibility-first. If it touches runtime
code, it should only clarify or verify existing behavior unless the
authorization contract explicitly permits a behavior change.

---

## 13. Explicit exclusions

Batch E design does not authorize:

- runtime behavior changes;
- database schema changes;
- API changes;
- UI changes;
- new OCR engine behavior;
- AEI grading changes;
- autonomous marks;
- teacher-review routing changes;
- evidence-ledger behavior changes;
- mastery-source changes;
- parent/student/principal visibility changes;
- EUI source-of-truth switch;
- new LLM calls;
- question-bank marketplace behavior;
- blueprint generation changes;
- Assessment Intelligence Batch F behavior.

---

## 14. Golden Harness expectations

Batch E Golden Harness cases should validate the linkage contract.

Minimum scenarios:

- approved source paper imports into an exam schema;
- draft source paper is rejected as authoritative schema source;
- cross-tenant source paper is rejected;
- paper with no usable questions is unsupported;
- duplicate question numbers are invalid;
- max marks are preserved from source paper to schema;
- `can_evaluate_sheets` is true only when `source_paper_id` and schema exist;
- evaluation is unavailable without linked paper and schema;
- rubric/model-answer context resolves through the linked source paper;
- OCR/manual input remains input-only and non-authoritative;
- AEI suggestions require teacher review before authority;
- marks become authoritative only after approval;
- downstream evidence and mastery require approved marks/evidence.

---

## 15. Observability expectations

If Batch E later introduces runtime helpers, operational observability should
measure linkage health rather than educational outcomes.

Useful future metrics include:

- `assessment_linkage.invoked`;
- `assessment_linkage.completed`;
- `assessment_linkage.failed`;
- `assessment_linkage.unsupported`;
- `assessment_linkage.manual_review`;
- `assessment_linkage.duration`.

Logs should avoid student PII and must not include answer content.

---

## 16. Certification criteria

Batch E should not be accepted until it can demonstrate:

- approved-paper linkage declarations exist;
- linkage support modes are explicit;
- Golden Harness cases validate declared supported and unsupported scenarios;
- same-tenant approved-paper import behavior is protected;
- unapproved and cross-tenant paper linkage is rejected;
- `can_evaluate_sheets` posture is verified;
- AEI receives context only through the linked approved path;
- teacher approval remains the point of authority;
- no schema, API, UI, AEI behavior, or evidence-ledger behavior changes were
  introduced unless separately authorized;
- existing Assessment Intelligence Batch A-D tests continue to pass;
- existing AEI evaluation regression slice continues to pass;
- certification report is completed.

---

## 17. ARM gate

This design brief may be accepted as the Batch E Paper-to-Evaluation Linkage
Readiness design baseline.

Acceptance of this brief does not authorize implementation.

The next artifact should be:

```text
docs/product/assessment-intelligence/
ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

That contract should define the exact repository boundary, permitted runtime
touchpoints, validation commands, Golden Harness additions, rollback posture,
and certification evidence before any Batch E implementation begins.
