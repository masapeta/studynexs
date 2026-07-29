# Assessment Intelligence v1.0 Paper-to-Evaluation Linkage Supported Scope Declarations

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Batch E foundation
> Authorization: ASSESSMENT-V1-BATCH-E-AUTH-001
> Runtime behavior: Unchanged
> Scope: Static paper-to-evaluation linkage declarations only

---

## 1. Purpose

This document declares the initial Assessment Intelligence v1.0
paper-to-evaluation linkage support posture.

These declarations are static, read-only, and non-runtime. They make approved
paper, exam schema, rubric context, answer input, AEI assist, teacher approval,
evidence, marks, and mastery boundaries explicit without changing exam services,
answer-sheet evaluation services, teacher review, AEI, EUI, API contracts, UI
behavior, database schema, feature flags, provider behavior, or LLM prompts.

---

## 2. Declaration rules

StudyNexs may claim paper-to-evaluation linkage support only when all of the
following are true:

1. the linkage posture is declared in this document;
2. the declaration mode is `supported`;
3. the source paper belongs to the same school-private scope;
4. the source paper is approved;
5. the exam has a question schema derived from or linked to the approved paper;
6. answer-key, model-answer, rubric, or checklist context is retrieved through
   the linked source paper where available;
7. OCR and manual answer input are treated as input capture only;
8. AEI suggestions remain non-authoritative;
9. teacher review and approval remain required before marks/evidence authority;
10. downstream consumers receive only approved evidence.

The product must not claim autonomous grading, autonomous marks, direct parent
evidence, direct mastery updates, or universal paper-to-evaluation support.

---

## 3. Declared paper-to-evaluation linkage postures

### 3.1 Approved paper to exam schema

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://same-tenant/approved-paper-schema/v1` |
| Mode | `supported` |
| Linkage posture | `approved_paper_schema` |
| Source scope | Same-school approved question paper |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- source paper must be approved;
- source paper must belong to the same school context as the exam;
- usable paper questions may define exam question numbers and max marks;
- blank or zero-mark questions are not evaluation-ready;
- question schema remains the exam-level structure for marks and evaluation;
- teacher authority remains required for marks and evidence.

### 3.2 Source paper plus schema evaluation readiness

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://same-tenant/source-paper-schema-evaluation-ready/v1` |
| Mode | `supported` |
| Linkage posture | `source_paper_schema_evaluation_ready` |
| Source scope | Exam has `source_paper_id` and `question_schema` |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- evaluation readiness requires both source paper and question schema;
- question numbers must be unique;
- per-question max marks must be positive;
- internal-choice schemas may exceed exam total marks;
- schemas below exam total marks indicate missing questions;
- AEI assist remains non-authoritative.

### 3.3 Linked rubric/model-answer context

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://same-tenant/linked-rubric-context/v1` |
| Mode | `supported` |
| Linkage posture | `linked_rubric_context` |
| Source scope | Rubric context fetched through linked source paper |
| Product claim allowed | Yes, where Batch C context exists |

Validation posture:

- answer key, acceptable answers, model answer, rubric criteria, checklist
  items, and evaluation config must come from the linked paper path where
  available;
- missing context should not become an unsupported autonomous grading claim;
- manual review remains required when the rubric/model-answer posture is weak or
  unavailable.

### 3.4 OCR answer input assist

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://assist/ocr-answer-input/v1` |
| Mode | `assist` |
| Linkage posture | `ocr_input_assist` |
| Source scope | OCR output used as student-answer input only |
| Product claim allowed | No |

Validation posture:

- OCR reads answer text; it never marks;
- OCR output is input capture only;
- low-confidence or ambiguous OCR must remain reviewable;
- AEI and teacher review determine evaluation posture separately;
- raw OCR text must not be published as approved evidence before teacher
  approval.

### 3.5 Manual answer input assist

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://assist/manual-answer-input/v1` |
| Mode | `assist` |
| Linkage posture | `manual_input_assist` |
| Source scope | Teacher-entered or transcribed answers |
| Product claim allowed | No |

Validation posture:

- manual input is answer capture only;
- manual input does not bypass rubric context, AEI assist, teacher approval, or
  approved evidence requirements;
- teacher final authority remains unchanged.

### 3.6 Manual schema without approved source paper

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://manual-review/manual-schema-without-source-paper/v1` |
| Mode | `manual_review` |
| Linkage posture | `manual_schema_review` |
| Source scope | Exam has manual question schema but no approved source paper |
| Product claim allowed | No |

Validation posture:

- manual schemas may support total/per-question marks entry;
- manual schema alone is not an AEI paper-grounded evaluation support claim;
- linked rubric/model-answer context is absent unless separately provided and
  approved;
- teacher review remains required.

### 3.7 Draft or unapproved source paper

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://unsupported/draft-or-unapproved-source-paper/v1` |
| Mode | `unsupported` |
| Linkage posture | `unsupported_linkage` |
| Source scope | Draft, edited, pending, rejected, unknown, or unapproved source paper |
| Product claim allowed | No |

Validation posture:

- unsupported for v1.0 evaluation readiness;
- source must not be used as an authoritative schema source;
- teacher approval workflow must complete first.

### 3.8 Cross-tenant source paper

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://unsupported/cross-tenant-source-paper/v1` |
| Mode | `unsupported` |
| Linkage posture | `unsupported_linkage` |
| Source scope | Different school or tenant |
| Product claim allowed | No |

Validation posture:

- cross-tenant paper linkage is unsupported;
- tenant isolation is mandatory;
- no shared source-paper evaluation path is implied.

### 3.9 Missing question schema

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://unsupported/missing-question-schema/v1` |
| Mode | `unsupported` |
| Linkage posture | `unsupported_linkage` |
| Source scope | Exam missing question schema |
| Product claim allowed | No |

Validation posture:

- a source paper without exam question schema is not evaluation-ready;
- `can_evaluate_sheets` must remain false without schema;
- schema generation or import requires separate existing workflow.

### 3.10 Autonomous marks or pre-approval downstream evidence

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://unsupported/autonomous-marks-or-preapproval-evidence/v1` |
| Mode | `unsupported` |
| Linkage posture | `unsupported_linkage` |
| Source scope | Any path that treats AEI/OCR/input as final authority |
| Product claim allowed | No |

Validation posture:

- AEI suggestions cannot become final marks without teacher approval;
- evidence cannot be exposed downstream before approval;
- mastery cannot update from unapproved evidence;
- parent/student/principal consumers receive only approved evidence.

### 3.11 Broader source adoption

| Field | Value |
|---|---|
| Linkage Declaration ID | `assessment-linkage://expansion/source-of-truth-adoption/v1` |
| Mode | `expansion` |
| Linkage posture | `future_expansion` |
| Source scope | Future source-of-truth or broader paper/evaluation adoption |
| Product claim allowed | No |

Validation posture:

- future scope only;
- requires separate architecture, implementation authorization, Golden Harness,
  certification, and rollback proof before support may be claimed.

---

## 4. Product claim posture

Allowed claims:

- approved same-school paper can define an evaluation-ready exam question
  schema;
- exam with linked source paper and schema can be prepared for evaluation
  assist;
- linked rubric/model-answer context can ground AEI suggestions where available;
- teacher-final authority.

Disallowed claims:

- evaluation readiness from draft/unapproved papers;
- cross-tenant source-paper linkage;
- evaluation readiness without question schema;
- OCR as marking authority;
- manual transcription as marking authority;
- autonomous marks from AEI suggestions;
- direct parent/student evidence before teacher approval;
- direct mastery update from unapproved evaluation evidence;
- EUI source-of-truth adoption;
- universal paper-to-evaluation support.

---

## 5. Batch E boundary

These declarations do not replace existing runtime examination or answer-sheet
evaluation handling.

Exam services, answer-sheet evaluation services, teacher approval, evidence
ledger, mastery, AEI, EUI, API contracts, UI behavior, feature flags, provider
behavior, LLM prompts, and database schema remain unchanged.
