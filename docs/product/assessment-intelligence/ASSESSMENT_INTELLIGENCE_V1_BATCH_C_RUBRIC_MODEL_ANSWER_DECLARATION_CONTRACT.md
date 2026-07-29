# Assessment Intelligence v1.0 Batch C Rubric and Model-Answer Declaration Contract

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Batch C foundation  
> Authorization: ASSESSMENT-V1-BATCH-C-AUTH-001  
> Runtime behavior: Unchanged  
> Scope: Rubric and model-answer declaration contract only

---

## 1. Purpose

This document defines the static rubric and model-answer declaration contract
for Assessment Intelligence v1.0.

Rubric declarations describe expected answer context. They do not grade
student answers, approve marks, publish evidence, or change runtime behavior.

---

## 2. Contract principle

Rubric context informs evaluation. It does not replace teacher authority.

```text
Approved Question Paper
        |
        v
Question + Blueprint Slot
        |
        v
Rubric / Model-Answer Declaration
        |
        v
AEI Evaluation Context
        |
        v
Teacher Review and Approval
```

Assessment Intelligence owns the assessment-side declaration of expected answer
context. AEI owns academic answer evaluation. Teachers remain final authority.

---

## 3. Declaration identity

Each declaration must have a stable `rubric_id`.

Recommended ID shape:

```text
assessment-rubric://<board>/<curriculum>/<grade>/<subject>/<posture>/<version>
```

Examples:

```text
assessment-rubric://cbse/ncf2023/g10/mathematics/mcq-objective/v1
assessment-rubric://cbse/ncf2023/g6/science/short-answer-model/v1
```

Names may change over time. Stable IDs should not change for the same declared
scope and posture.

---

## 4. Declaration fields

| Field | Required | Purpose |
|---|---:|---|
| `rubric_id` | Yes | Stable declaration identifier. |
| `blueprint_id` | Where available | Related blueprint declaration. |
| `board` | Yes | Board scope, such as `CBSE`. |
| `curriculum` | Yes | Curriculum family, such as `NCF2023`. |
| `grade` | Yes | Grade or class scope. |
| `subject` | Yes | Subject scope. |
| `question_type` | Yes | MCQ, numeric, short, long, diagram, map, science, etc. |
| `marks` | Yes | Maximum marks for the question or slot. |
| `rubric_posture` | Yes | Objective, numeric, model answer, criterion, checklist, manual review, or unsupported. |
| `support_mode` | Yes | Supported posture for the declaration. |
| `answer_key` | Conditional | Required for objective and numeric postures. |
| `model_answer` | Conditional | Required for model-answer posture. |
| `acceptable_answers` | Optional | Explicit equivalent answer variants. |
| `numeric_tolerance` | Conditional | Required when tolerance is claimed. |
| `unit_posture` | Conditional | Required when unit handling is claimed. |
| `scientific_notation_posture` | Conditional | Required when scientific-notation handling is claimed. |
| `criteria` | Conditional | Required for criterion-rubric posture. |
| `checklist_items` | Conditional | Required for checklist posture. |
| `manual_review_reason` | Conditional | Required for manual-review posture. |
| `unsupported_reason` | Conditional | Required for unsupported posture. |
| `teacher_review_required` | Yes | Must be `true` before authority. |
| `evaluation_pipeline` | Yes | Must be `AEI` for answer evaluation. |
| `approved_evidence_required` | Yes | Must be `true` before downstream consumption. |
| `product_claim_allowed` | Yes | Whether StudyNexs may claim support for this posture. |
| `runtime_behavior_change` | Yes | Must be `false` for Batch C. |

---

## 5. Rubric postures

| Posture | Meaning |
|---|---|
| `objective_key` | Concise deterministic key, such as MCQ or true/false. |
| `numeric_answer` | Numeric answer context that AEI Maths support may consume. |
| `model_answer` | Teacher-visible model answer for subjective assist. |
| `criterion_rubric` | Teacher-reviewable criteria with marks allocation. |
| `checklist` | Visual/science checklist evidence only; no autonomous marks. |
| `manual_review` | Teacher-only marking or answer-context review. |
| `unsupported` | Product must not claim automated or assist support. |

---

## 6. Support modes

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared scope. |
| `assist` | System may assist, but teacher review remains required. |
| `checklist` | System may provide checklist evidence only; no autonomous marks. |
| `manual_review` | Teacher must mark or approve the answer context. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future scope only. |

Supported rubric posture does not mean autonomous grading. It means the
answer-context contract is declared and validated for that scope.

---

## 7. Deterministic validation rules

Rubric validation must be deterministic and non-runtime in Batch C.

Required checks:

1. `rubric_id` is stable and unique.
2. `rubric_posture` is known.
3. `support_mode` is known.
4. `answer_key` exists for `objective_key` and `numeric_answer`.
5. MCQ objective declarations define option posture.
6. `model_answer` exists for `model_answer`.
7. `criteria` exists for `criterion_rubric`.
8. Criterion marks sum to the question `marks`.
9. `checklist_items` exists for `checklist`.
10. `manual_review_reason` exists for `manual_review`.
11. `unsupported_reason` exists for `unsupported`.
12. Non-supported modes block product claims.
13. `teacher_review_required` remains true.
14. `evaluation_pipeline` remains `AEI`.
15. `approved_evidence_required` remains true.

---

## 8. Batch C invariants

1. Rubric declarations are read-only artifacts.
2. Rubric declarations do not change runtime answer-sheet evaluation.
3. Product claims are allowed only for declared `supported` postures.
4. `assist`, `checklist`, `manual_review`, `unsupported`, and `expansion`
   declarations do not permit autonomous grading claims.
5. Teachers remain the final authority for assessment outcomes.
6. AEI remains the only academic answer-evaluation pipeline.
7. Parent/student/principal consumers receive only approved evidence.
8. Batch C introduces no schema, API, UI, feature flag, or runtime behavior
   change.

---

## 9. Minimal declaration example

```json
{
  "rubric_id": "assessment-rubric://cbse/ncf2023/g10/mathematics/numeric-answer/v1",
  "blueprint_id": "assessment-blueprint://cbse/ncf2023/g10/mathematics/term-exam/v1",
  "board": "CBSE",
  "curriculum": "NCF2023",
  "grade": "10",
  "subject": "Mathematics",
  "question_type": "numeric",
  "marks": 2,
  "rubric_posture": "numeric_answer",
  "support_mode": "supported",
  "answer_key": "0.5",
  "acceptable_answers": ["1/2", "50%", "½"],
  "numeric_tolerance": "0",
  "unit_posture": "not_required",
  "scientific_notation_posture": "accepted_when_equivalent",
  "teacher_review_required": true,
  "evaluation_pipeline": "AEI",
  "approved_evidence_required": true,
  "product_claim_allowed": true,
  "runtime_behavior_change": false
}
```

---

## 10. Batch C boundary

This contract defines rubric/model-answer declarations only.

It does not authorize runtime source switching, answer-sheet evaluation changes,
schema changes, API changes, UI changes, feature flags, rubric generation,
autonomous grading, or product claim expansion.
