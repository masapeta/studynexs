# Assessment Intelligence v1.0 Batch B Blueprint Declaration Contract

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Batch B foundation  
> Authorization: ASSESSMENT-V1-BATCH-B-AUTH-001  
> Runtime behavior: Unchanged  
> Scope: Blueprint declaration contract only

---

## 1. Purpose

This document defines the static blueprint declaration contract for Assessment
Intelligence v1.0.

Blueprint declarations describe paper structure for a declared educational
scope. They do not generate questions, assign marks, evaluate answers, approve
papers, or change runtime behavior.

---

## 2. Contract principle

Blueprints are educational data, not hidden generation logic.

```text
Board / Curriculum / Grade / Subject / Paper Type
        |
        v
Blueprint Declaration
        |
        v
Question Paper Draft
        |
        v
Teacher Review and Approval
```

Support for a blueprint means the structure is explicit and validated for the
declared scope. It does not mean generated content is authoritative.

---

## 3. Declaration identity

Each declaration must have a stable `blueprint_id`.

Recommended ID shape:

```text
assessment-blueprint://<board>/<curriculum>/<grade>/<subject>/<paper-type>/<version>
```

Examples:

```text
assessment-blueprint://cbse/ncf2023/g6/science/unit-test/v1
assessment-blueprint://cbse/ncf2023/g10/mathematics/term-exam/v1
```

Names may change over time. Stable IDs should not change for the same declared
scope and structure.

---

## 4. Declaration fields

| Field | Required | Purpose |
|---|---:|---|
| `blueprint_id` | Yes | Stable declaration identifier. |
| `board` | Yes | Board scope, such as `CBSE`. |
| `curriculum` | Yes | Curriculum family, such as `NCF2023`. |
| `grade` | Yes | Grade or class scope. |
| `subject` | Yes | Subject scope. |
| `paper_type` | Yes | Unit test, slip test, term exam, practice, or equivalent. |
| `version` | Yes | Declaration version. |
| `support_mode` | Yes | Supported posture for the declaration. |
| `total_marks` | Yes | Answer-required marks total. |
| `printed_marks_total` | Yes | Marks printed when internal choice increases printed marks. |
| `duration_minutes` | Yes | Expected paper duration. |
| `sections` | Yes | Ordered section declarations. |
| `validation_rules` | Yes | Deterministic structure checks. |
| `product_claim_allowed` | Yes | Whether StudyNexs may claim support for this blueprint. |
| `teacher_authority_required` | Yes | Must be `true` for consequential assessment outcomes. |
| `runtime_behavior_change` | Yes | Must be `false` for Batch B. |

---

## 5. Section fields

| Field | Required | Purpose |
|---|---:|---|
| `section_id` | Yes | Stable section identifier inside the blueprint. |
| `title` | Yes | Teacher-visible section title. |
| `instructions` | Yes | Teacher/student instruction text. |
| `question_type` | Yes | MCQ, short, long, diagram, map, or equivalent. |
| `marks_per_question` | Yes | Marks per printed question. |
| `question_count` | Yes | Number of printed questions. |
| `answer_any_count` | Yes | Number required to answer. Equal to `question_count` when no internal choice applies. |
| `required` | Yes | Whether the section is mandatory. |
| `options_required` | Conditional | Required for MCQ sections. |

---

## 6. Support modes

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared scope. |
| `assist` | System may help, but teacher must verify structure. |
| `manual_review` | Teacher must define or approve structure; no product support claim. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future scope only. |

Batch B declarations may not imply autonomous paper approval, autonomous answer
grading, or bypass of AEI for academic evaluation.

---

## 7. Deterministic calculation rules

Blueprint validation must distinguish printed marks from answer-required marks.

For each section:

```text
printed_section_marks = marks_per_question * question_count
effective_section_marks = marks_per_question * answer_any_count
```

For the blueprint:

```text
printed_marks_total = sum(printed_section_marks)
total_marks = sum(effective_section_marks)
```

Internal choice is present when any section has:

```text
answer_any_count < question_count
```

This allows structures such as "answer any 4 of 6" without treating the printed
paper as malformed.

---

## 8. Batch B invariants

1. Blueprint declarations are read-only artifacts.
2. Blueprint declarations do not change runtime question-paper generation.
3. Product claims are allowed only for `supported` declarations.
4. `assist`, `manual_review`, `unsupported`, and `expansion` declarations do
   not permit production support claims.
5. Teachers remain the final authority for assessment approval.
6. AEI remains the only academic answer-evaluation pipeline.
7. Parent/student/principal consumers receive only approved evidence.
8. Batch B introduces no schema, API, UI, feature flag, or runtime behavior
   change.

---

## 9. Minimal declaration example

```json
{
  "blueprint_id": "assessment-blueprint://cbse/ncf2023/g6/science/unit-test/v1",
  "board": "CBSE",
  "curriculum": "NCF2023",
  "grade": "6",
  "subject": "Science",
  "paper_type": "unit_test",
  "version": "v1",
  "support_mode": "supported",
  "total_marks": 20,
  "printed_marks_total": 20,
  "duration_minutes": 60,
  "sections": [
    {
      "section_id": "section-a",
      "title": "Section A",
      "instructions": "Answer all questions.",
      "question_type": "mcq",
      "marks_per_question": 1,
      "question_count": 5,
      "answer_any_count": 5,
      "required": true,
      "options_required": 4
    }
  ],
  "validation_rules": {
    "requires_teacher_approval": true,
    "allows_internal_choice": false
  },
  "product_claim_allowed": true,
  "teacher_authority_required": true,
  "runtime_behavior_change": false
}
```

---

## 10. Batch B boundary

This contract defines blueprint declarations only.

It does not authorize runtime source switching, question generation changes,
schema changes, API changes, UI changes, feature flags, or product claim
expansion.
