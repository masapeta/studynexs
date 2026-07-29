# Assessment Intelligence v1.0 Rubric and Model-Answer Supported Scope Declarations

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Batch C foundation  
> Authorization: ASSESSMENT-V1-BATCH-C-AUTH-001  
> Runtime behavior: Unchanged  
> Scope: Static rubric and model-answer declarations only

---

## 1. Purpose

This document declares the initial Assessment Intelligence v1.0 rubric and
model-answer support posture.

These declarations are static, read-only, and non-runtime. They make expected
answer context explicit without changing answer-sheet evaluation, question-bank
behavior, exam services, AEI, EUI, API contracts, UI behavior, database schema,
feature flags, provider behavior, or LLM prompts.

---

## 2. Declaration rules

StudyNexs may claim rubric/model-answer support only when all of the following
are true:

1. the rubric posture is declared in this document;
2. the declaration mode is `supported`;
3. the question is within the declared board/curriculum/grade/subject/posture;
4. teacher review and approval remain required before authority;
5. academic answer evaluation still flows through AEI;
6. downstream evidence remains teacher-approved.

The product must not claim universal subjective grading.

---

## 3. Declared rubric/model-answer postures

### 3.1 Grade 10 Mathematics MCQ objective key

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://cbse/ncf2023/g10/mathematics/mcq-objective/v1` |
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g10/mathematics/term-exam/v1` |
| Mode | `supported` |
| Rubric posture | `objective_key` |
| Question type | MCQ |
| Marks | 1 |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- answer key must be explicit;
- MCQ options must be explicit where applicable;
- teacher approval remains required;
- no autonomous approval or downstream evidence is implied.

### 3.2 Grade 10 Mathematics numeric answer

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://cbse/ncf2023/g10/mathematics/numeric-answer/v1` |
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g10/mathematics/term-exam/v1` |
| Mode | `supported` |
| Rubric posture | `numeric_answer` |
| Question type | Numeric |
| Marks | 2 |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- answer key must be explicit;
- acceptable answer variants may be explicit;
- tolerance, unit posture, and scientific-notation posture must be explicit
  when claimed;
- uncertain cases remain teacher-review required.

### 3.3 Grade 10 Mathematics acceptable variants

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://cbse/ncf2023/g10/mathematics/acceptable-variants/v1` |
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g10/mathematics/term-exam/v1` |
| Mode | `supported` |
| Rubric posture | `numeric_answer` |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- acceptable answers must be explicit;
- equivalent forms may assist AEI where certified;
- teacher approval remains required before authority.

### 3.4 Grade 10 Mathematics unit, tolerance, and scientific notation

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://cbse/ncf2023/g10/mathematics/unit-tolerance-scientific/v1` |
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g10/mathematics/term-exam/v1` |
| Mode | `supported` |
| Rubric posture | `numeric_answer` |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- numeric tolerance must be explicit;
- unit posture must be explicit;
- scientific-notation posture must be explicit;
- unsupported unit ambiguity routes to teacher review.

### 3.5 Grade 6 Science short-answer model answer

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://cbse/ncf2023/g6/science/short-answer-model/v1` |
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g6/science/unit-test/v1` |
| Mode | `assist` |
| Rubric posture | `model_answer` |
| Question type | Short answer |
| Marks | 2 |
| Product claim allowed | No |

Validation posture:

- model answer must be teacher-visible;
- AEI may assist only where certified;
- confidence/manual-review metadata remains required;
- no autonomous final marks.

### 3.6 Grade 6 Science long-answer criterion rubric

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://cbse/ncf2023/g6/science/long-answer-criterion/v1` |
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g6/science/unit-test/v1` |
| Mode | `manual_review` |
| Rubric posture | `criterion_rubric` |
| Question type | Long answer |
| Marks | 5 |
| Product claim allowed | No |

Validation posture:

- criteria marks must sum to question marks;
- criteria are teacher-reviewable evidence only;
- teacher remains the final authority.

### 3.7 Grade 6 Science biology diagram checklist

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://cbse/ncf2023/g6/science/biology-diagram-checklist/v1` |
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g6/science/unit-test/v1` |
| Mode | `checklist` |
| Rubric posture | `checklist` |
| Question type | Diagram |
| Product claim allowed | No |

Validation posture:

- checklist items must be explicit;
- checklist observations do not automatically award marks;
- teacher confirmation remains required.

### 3.8 Missing answer-key manual review

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://school-custom/missing-answer-key/manual-review/v1` |
| Mode | `manual_review` |
| Rubric posture | `manual_review` |
| Product claim allowed | No |

Validation posture:

- missing or weak answer keys route to teacher-only review;
- no product support claim is made.

### 3.9 Universal subjective-grading claim

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://universal/subjective-autograding/v1` |
| Mode | `unsupported` |
| Rubric posture | `unsupported` |
| Product claim allowed | No |

Validation posture:

- StudyNexs must not claim universal subjective grading;
- unsupported posture routes to teacher review or future certified expansion.

### 3.10 Future advanced visual proof grading

| Field | Value |
|---|---|
| Rubric ID | `assessment-rubric://expansion/advanced-visual-proof-grading/v1` |
| Mode | `expansion` |
| Rubric posture | `unsupported` |
| Product claim allowed | No |

Validation posture:

- future scope only;
- no v1.0 product claim;
- requires separate capability, Golden Harness, teacher proof, and
  certification before support may be claimed.

---

## 4. Product claim posture

Allowed claims:

- declared objective-key posture inside supported scope;
- declared numeric-answer posture inside supported scope;
- explicit acceptable-answer, tolerance, unit, and scientific-notation posture
  where declared;
- teacher-final authority.

Disallowed claims:

- universal subjective grading;
- autonomous answer grading;
- autonomous paper approval;
- autonomous diagram or visual marks;
- direct parent/student evidence before teacher approval;
- direct mastery update from unapproved rubric evidence.

---

## 5. Batch C boundary

These declarations do not replace existing runtime rubric handling.

Runtime answer-sheet evaluation, question-bank runtime behavior, exam services,
AEI, EUI, API contracts, UI behavior, feature flags, provider behavior, LLM
prompts, and database schema remain unchanged.
