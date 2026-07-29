# Assessment Intelligence v1.0 Blueprint Supported Scope Declarations

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Batch B foundation  
> Authorization: ASSESSMENT-V1-BATCH-B-AUTH-001  
> Runtime behavior: Unchanged  
> Scope: Static blueprint declarations only

---

## 1. Purpose

This document declares the initial Assessment Intelligence v1.0 blueprint
support posture.

These declarations are static, read-only, and non-runtime. They make supported
paper structures explicit without changing question-paper generation,
question-bank behavior, exam services, AEI, EUI, API contracts, UI behavior, or
database schema.

---

## 2. Declaration rules

StudyNexs may claim blueprint support only when all of the following are true:

1. the blueprint is declared in this document;
2. the declaration mode is `supported`;
3. the paper is within the declared board/curriculum/grade/subject/paper type;
4. teacher review and approval remain required before authority;
5. academic answer evaluation still flows through AEI.

The product must not claim universal blueprint support.

---

## 3. Declared blueprints

### 3.1 Grade 6 Science unit-test blueprint

| Field | Value |
|---|---|
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g6/science/unit-test/v1` |
| Mode | `supported` |
| Board | CBSE |
| Curriculum | NCF2023 |
| Grade | 6 |
| Subject | Science |
| Paper type | Unit test |
| Duration | 60 minutes |
| Printed marks total | 20 |
| Answer-required total | 20 |
| Product claim allowed | Yes, inside this declared scope only |

Sections:

| Section | Question type | Printed count | Answer count | Marks each | Options |
|---|---|---:|---:|---:|---:|
| Section A | MCQ | 5 | 5 | 1 | 4 |
| Section B | Short answer | 5 | 5 | 2 | - |
| Section C | Long answer | 1 | 1 | 5 | - |

Validation posture:

- no internal choice;
- total marks are deterministic;
- teacher approval remains required;
- no autonomous grading or approval is implied.

### 3.2 Grade 10 Mathematics term-exam blueprint

| Field | Value |
|---|---|
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g10/mathematics/term-exam/v1` |
| Mode | `supported` |
| Board | CBSE |
| Curriculum | NCF2023 |
| Grade | 10 |
| Subject | Mathematics |
| Paper type | Term exam |
| Duration | 180 minutes |
| Printed marks total | 92 |
| Answer-required total | 80 |
| Product claim allowed | Yes, inside this declared scope only |

Sections:

| Section | Question type | Printed count | Answer count | Marks each | Options |
|---|---|---:|---:|---:|---:|
| Section I | Very short | 6 | 6 | 2 | - |
| Section II | Short answer | 6 | 6 | 4 | - |
| Section III | Long answer | 6 | 4 | 6 | - |
| Part B | MCQ | 20 | 20 | 1 | 4 |

Validation posture:

- internal choice is present in Section III;
- printed marks are intentionally higher than answer-required marks;
- teacher approval remains required;
- no autonomous grading or approval is implied.

### 3.3 Grade 10 Mathematics practice-MCQ blueprint

| Field | Value |
|---|---|
| Blueprint ID | `assessment-blueprint://cbse/ncf2023/g10/mathematics/practice-mcq/v1` |
| Mode | `assist` |
| Board | CBSE |
| Curriculum | NCF2023 |
| Grade | 10 |
| Subject | Mathematics |
| Paper type | Practice |
| Duration | 30 minutes |
| Printed marks total | 20 |
| Answer-required total | 20 |
| Product claim allowed | No |

Sections:

| Section | Question type | Printed count | Answer count | Marks each | Options |
|---|---|---:|---:|---:|---:|
| Practice A | MCQ | 20 | 20 | 1 | 4 |

Validation posture:

- MCQ option count must be explicit;
- teacher verification remains required before classroom use;
- no production support claim is made in Batch B.

### 3.4 School-custom manual-review blueprint

| Field | Value |
|---|---|
| Blueprint ID | `assessment-blueprint://school-custom/manual-review/v1` |
| Mode | `manual_review` |
| Board | School custom |
| Curriculum | School defined |
| Grade | Any |
| Subject | Any |
| Paper type | Custom |
| Product claim allowed | No |

Validation posture:

- teacher or academic coordinator must define and approve the structure;
- StudyNexs may record that manual review is required;
- no universal school-custom support claim is made in Batch B.

### 3.5 Universal blueprint claim

| Field | Value |
|---|---|
| Blueprint ID | `assessment-blueprint://universal/any-board/any-grade/any-subject/v1` |
| Mode | `unsupported` |
| Product claim allowed | No |

Validation posture:

- StudyNexs must not claim universal blueprint support;
- unsupported scope routes to manual teacher definition or later expansion.

### 3.6 Future Telugu-medium state-board expansion

| Field | Value |
|---|---|
| Blueprint ID | `assessment-blueprint://expansion/state-board/telugu-medium/v1` |
| Mode | `expansion` |
| Product claim allowed | No |

Validation posture:

- future scope only;
- no v1.0 product claim;
- requires separate curriculum pack, blueprint declaration, Golden Harness, and
  certification before support may be claimed.

---

## 4. Product claim posture

Allowed claims:

- declared Grade 6 Science unit-test structure;
- declared Grade 10 Mathematics term-exam internal-choice structure;
- support only inside the declared scope;
- teacher-final authority.

Disallowed claims:

- universal board support;
- universal blueprint support;
- universal bilingual or multilingual assessment support;
- autonomous paper approval;
- autonomous answer grading;
- autonomous teacher-review bypass;
- parent/student visibility before approval.

---

## 5. Batch B boundary

These declarations do not replace existing runtime helpers.

Runtime question-paper generation, question-bank compose, exam schema behavior,
AEI, EUI, API contracts, UI behavior, and database schema remain unchanged.
