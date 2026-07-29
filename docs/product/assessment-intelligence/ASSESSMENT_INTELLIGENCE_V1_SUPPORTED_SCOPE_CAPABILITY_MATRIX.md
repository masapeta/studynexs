# Assessment Intelligence v1.0 Supported Scope Capability Matrix

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Batch A foundation  
> Authorization: ASSESSMENT-V1-BATCH-A-AUTH-001  
> Runtime behavior: Unchanged  
> Scope: Supported-scope declaration only

---

## 1. Purpose

This matrix declares what Assessment Intelligence v1.0 may claim for the
initial supported scope.

It is intentionally conservative. Supported means production-quality for the
declared scenario, not universal capability.

---

## 2. Capability modes

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared scope. |
| `assist` | AI may assist, but teacher review remains required and product claims must be cautious. |
| `checklist` | System may provide checklist evidence only; no autonomous marks. |
| `manual_review` | Teacher-only authority; system records need for review. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future roadmap candidate, not v1.0 claim. |

---

## 3. Initial v1.0 supported scope

The initial supported scope is intentionally framed around current foundations:

| Dimension | v1.0 posture |
|---|---|
| Boards | CBSE / NCF2023 as primary supported matrix declaration; legacy SSC-style generation remains existing behavior but not a new universal claim. |
| Grades | Grade 6 and Grade 10 starter coverage for contract validation. |
| Subjects | Science and Mathematics starter coverage for assessment contract validation. |
| Paper types | Unit test, slip test, term exam, practice where declared by blueprint posture. |
| Languages | English supported for paper contract; bilingual and Indian-language generation require explicit later certification. |
| Evaluation | AEI remains the only answer-evaluation pipeline. |
| Authority | Teacher final authority for all consequential outcomes. |

---

## 4. Capability declarations

| Capability ID | Domain | Scope | Mode | Product claim posture |
|---|---|---|---|---|
| `assessment://generation/grounded-question-paper/cbse/ncf2023/g6/science/unit-test/v1` | Question paper generation | CBSE NCF2023 Grade 6 Science unit-test draft from approved CurriculumPack | `supported` | May claim grounded draft generation with teacher approval. |
| `assessment://generation/grounded-question-paper/cbse/ncf2023/g10/mathematics/unit-test/v1` | Question paper generation | CBSE NCF2023 Grade 10 Mathematics unit-test draft from approved CurriculumPack | `supported` | May claim grounded draft generation with teacher approval. |
| `assessment://blueprint/internal-choice/cbse/ncf2023/g10/mathematics/term-exam/v1` | Blueprint | Internal-choice posture for Grade 10 Mathematics term-style paper | `supported` | May claim internal-choice validation when blueprint is declared. |
| `assessment://rubric/objective-key/cbse/ncf2023/g10/mathematics/mcq/v1` | Rubric/model answer | Objective answer key for Mathematics MCQ | `supported` | May claim objective-key readiness; AEI/evaluation still teacher-approved. |
| `assessment://rubric/model-answer/cbse/ncf2023/g6/science/short-answer/v1` | Rubric/model answer | Grade 6 Science short-answer model answer | `assist` | May claim teacher-visible model-answer assist, not autonomous marking. |
| `assessment://rubric/criterion-review/cbse/ncf2023/g6/science/long-answer/v1` | Rubric/model answer | Criterion rubric posture for long-answer Science | `manual_review` | Teacher review required; no autonomous grading claim. |
| `assessment://question-bank/reuse/approved-school-private/v1` | Question bank | Approved school-private question bank reuse | `supported` | May claim approved-question reuse into draft papers. |
| `assessment://linkage/paper-to-evaluation/approved-paper-aei/v1` | Evaluation linkage | Approved paper -> exam schema -> AEI evaluation context | `supported` | May claim linkage only when paper is approved and AEI remains evaluator. |
| `assessment://language/bilingual-paper-generation/cbse/ncf2023/general/v1` | Language | Bilingual paper generation | `manual_review` | Do not claim production bilingual generation until later certification. |
| `assessment://language/universal-multilingual-assessment/v1` | Language | Universal multilingual generation/evaluation | `unsupported` | No universal multilingual assessment claim. |
| `assessment://visual/autonomous-diagram-grading/v1` | Visual/science | Autonomous diagram marks | `unsupported` | Checklist/assist only through AEI where certified. |
| `assessment://future/broad-board-expansion/v1` | Expansion | Additional boards/grades/subjects beyond certified scope | `expansion` | Future capability; no v1.0 claim. |

---

## 5. Product claim rules

Assessment Intelligence v1.0 may claim only:

- grounded draft paper generation for declared supported scopes;
- teacher review and approval workflow;
- approved school-private question-bank reuse into drafts;
- explicit blueprint validation where declared;
- paper-to-evaluation linkage through approved papers and AEI;
- teacher-final authority.

Assessment Intelligence v1.0 must not claim:

- universal board support;
- universal blueprint support;
- universal bilingual or multilingual generation;
- autonomous paper approval;
- autonomous answer grading;
- autonomous diagram grading;
- downstream visibility before teacher approval.

---

## 6. Batch A boundary

This matrix is a declaration foundation. It does not enable, disable, or modify
runtime behavior.

Later batches may map runtime behavior to these declarations only after separate
ARM authorization.
