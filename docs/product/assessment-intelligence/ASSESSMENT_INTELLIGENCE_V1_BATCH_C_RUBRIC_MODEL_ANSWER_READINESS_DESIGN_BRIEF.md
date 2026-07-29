# Assessment Intelligence v1.0 Batch C Design Brief

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Program: Assessment Intelligence v1.0  
> Batch: C - Rubric and Model-Answer Readiness  
> Status: Accepted  
> Classification: Product implementation design  
> Implementation: Not authorized  
> Runtime behavior changes: Not authorized by this document  
> Previous baseline: Batch B - Blueprint Readiness
> ARM review: Accepted as the Batch C Rubric and Model-Answer Readiness design baseline

---

## 1. Purpose

Batch C should make answer keys, model answers, acceptable answers, and rubric
posture explicit, reviewable, and non-authoritative until teacher approval.

It answers:

> For each supported assessment question, what evaluation context exists, what
> may AEI safely consume, and when must the teacher remain the only evaluator?

This document is design-only. It does not authorize implementation.

---

## 2. Why Batch C exists

Assessment Intelligence v1.0 Batch A established the canonical assessment
contract.

Batch B made blueprint behavior explicit and non-universal.

Batch C is the next dependency because a question paper is not evaluation-ready
merely because its structure is valid. Every evaluable question also needs a
clear posture for:

- objective answer keys;
- numeric answer keys;
- acceptable answer variants;
- model answers;
- criterion rubrics;
- visual/science checklists;
- manual-review conditions;
- unsupported evaluation conditions.

Without this layer, downstream evaluation can silently infer too much from raw
answer-key text or legacy rubric dictionaries.

---

## 3. Repository foundations to reuse

Batch C should extend existing foundations rather than creating a parallel
rubric engine.

Relevant existing backend foundations include:

- `apps/api/app/db/models/question_bank.py`;
- `QuestionBankItem`;
- `RubricBankItem`;
- `apps/api/app/modules/ai/services/question_bank_service.py`;
- `fetch_rubrics_for_paper`;
- `answer_key`;
- `acceptable_answers`;
- `common_wrong_answers`;
- `teacher_correction_note`;
- `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py`;
- objective answer-key evaluation;
- model-answer / subjective evaluation fallback;
- AEI v1 Maths normalization metadata;
- AEI v1 visual/science checklist metadata.

Relevant UI foundations include:

- teacher answer-key display in the question-paper workflow;
- rubric and evidence display in the teacher evaluation page;
- teacher override reason workflow;
- approved evidence posture.

Batch C should document and test the contract posture first. Runtime behavior
changes require a later implementation authorization.

---

## 4. Product outcome

After Batch C is eventually implemented and certified, StudyNexs should be able
to say:

> For the declared supported scope, every evaluation-ready question has an
> explicit answer-key, model-answer, rubric, checklist, manual-review, or
> unsupported posture before it reaches AEI or teacher review.

Teachers should be able to inspect what the system believes is the expected
answer context. The system should never treat missing or weak rubric context as
permission to guess.

---

## 5. Design principle

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

Assessment Intelligence owns the assessment-side declaration of expected
answer context.

AEI owns academic answer understanding, reasoning, policy, teacher review, and
approved evidence.

Teachers remain final authority.

---

## 6. Relationship to Batch A contract

Batch C should build directly on Batch A answer-key and rubric fields:

- `answer_key`;
- `model_answer`;
- `acceptable_answers`;
- `numeric_tolerance`;
- `unit_posture`;
- `scientific_notation_posture`;
- `rubric_id`;
- `rubric_posture`;
- `criteria`;
- `checklist_items`;
- `manual_review_reason`;
- `unsupported_reason`;
- `aei_capability_mode`;
- `expected_answer_type`;
- `teacher_review_required`;
- `evaluation_pipeline`;
- `approved_evidence_required`.

Batch C should not invent a second rubric contract.

---

## 7. Rubric declaration model

A rubric declaration should describe evaluation context without performing
evaluation.

Minimum declaration fields:

| Field | Purpose |
|---|---|
| `rubric_id` | Stable rubric or answer-context identifier. |
| `blueprint_id` | Blueprint declaration associated with the question where available. |
| `question_number` | Human-visible question number or slot reference. |
| `question_type` | MCQ, numeric, short, long, diagram, map, science, etc. |
| `marks` | Maximum marks for the question. |
| `rubric_posture` | Objective, numeric, model answer, criterion, checklist, manual review, or unsupported. |
| `answer_key` | Objective or concise expected answer where applicable. |
| `model_answer` | Teacher-visible model answer for subjective questions. |
| `acceptable_answers` | Explicit equivalent answer variants. |
| `numeric_tolerance` | Numeric tolerance where deterministic evaluation is allowed. |
| `unit_posture` | Whether units are required, accepted, converted, or manual review. |
| `scientific_notation_posture` | Whether scientific notation equivalents are accepted. |
| `criteria` | Teacher-reviewable criterion allocation where applicable. |
| `checklist_items` | Checklist items for diagram/visual/science assist. |
| `manual_review_reason` | Why teacher review is required. |
| `unsupported_reason` | Why the posture is unsupported. |
| `teacher_review_required` | Whether human review is required before authority. |
| `product_claim_allowed` | Whether StudyNexs may claim this posture as supported. |

---

## 8. Rubric support modes

Batch C should use the same conservative support posture as Batch A and Batch B.

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared scope. |
| `assist` | System can assist, but teacher review remains required. |
| `checklist` | System may produce checklist evidence only; no autonomous marks. |
| `manual_review` | Teacher marks or approves the answer context manually. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future roadmap candidate, not a v1.0 claim. |

Supported rubric posture does not mean autonomous grading. It means the
answer-context contract is declared and validated for that scope.

---

## 9. Recommended initial rubric postures

### 9.1 Objective key

Use when the answer has a concise objective key.

Examples:

- MCQ option key;
- true/false;
- fill-in-the-blank with a short exact key.

Design expectations:

- answer key must be explicit;
- options should be present for MCQ when applicable;
- teacher approval remains required for consequential outcomes;
- no parent/student evidence before approval.

### 9.2 Numeric answer

Use when AEI deterministic Maths support can consume numeric context.

Examples:

- fractions;
- decimals;
- percentages;
- units;
- tolerance;
- scientific notation.

Design expectations:

- answer key must be explicit;
- acceptable answers may be explicit;
- tolerance and unit posture must be explicit when used;
- uncertain or unsupported cases route to manual review.

### 9.3 Model answer

Use when the expected answer is explanatory or subjective.

Examples:

- Grade 6 Science short answer;
- explanation-based language or social-science answer;
- teacher-visible model answer.

Design expectations:

- model answer is teacher-visible;
- AEI may assist only where certified;
- confidence and manual-review metadata must remain visible;
- no autonomous final marks.

### 9.4 Criterion rubric

Use when marks are distributed across explicit criteria.

Examples:

- long-answer science explanation;
- multi-step proof;
- extended answer with allocation.

Design expectations:

- criteria must sum to the question max marks;
- each criterion must have a teacher-reviewable description;
- criteria evidence can support teacher review;
- teacher remains the final authority.

### 9.5 Checklist

Use when visual/science evidence is checklist-only.

Examples:

- biology diagram labels;
- map elements;
- graph axes and labels.

Design expectations:

- checklist items must be explicit;
- checklist evidence must not automatically award marks;
- missing/uncertain elements route to teacher review.

### 9.6 Manual review

Use when no safe automated or assist posture exists.

Examples:

- missing answer key;
- unclear model answer;
- ambiguous question;
- unsupported language/visual/science posture.

Design expectations:

- manual-review reason must be explicit;
- product support claim is not allowed;
- teacher-only marking remains authoritative.

### 9.7 Unsupported / expansion

Use when the system must not claim support or when support belongs to a future
certification.

Examples:

- universal subjective grading claim;
- unsupported board/language/rubric style;
- advanced visual proof grading not yet certified.

---

## 10. Deterministic validation expectations

Batch C should define deterministic validation for rubric declarations.

Validation should cover:

- stable `rubric_id`;
- known `rubric_posture`;
- known support mode;
- answer key required for objective/numeric posture;
- options required for MCQ posture;
- model answer required for model-answer posture;
- criteria marks sum to question marks for criterion rubric;
- checklist items required for checklist posture;
- manual-review reason required for manual-review posture;
- unsupported reason required for unsupported posture;
- product claim blocked for non-supported modes;
- teacher authority required for all consequential outcomes;
- AEI evaluation pipeline required for answer evaluation;
- approved evidence required before downstream consumption.

---

## 11. AEI handoff posture

Batch C should strengthen AEI inputs, not bypass AEI.

Permitted design:

```text
Assessment Rubric Declaration
        |
        v
AEI Evaluation Context
        |
        v
AEI Understanding / Reasoning / Policy
        |
        v
Teacher Review
```

Forbidden design:

```text
Assessment Rubric Declaration
        |
        v
Direct Marks / Direct Parent Evidence / Direct Mastery Update
```

AEI remains the only academic answer-evaluation pipeline.

---

## 12. Current runtime migration posture

The current runtime already has useful rubric-related behavior:

- approved papers can create question-bank items;
- rubrics can be stored as `RubricBankItem`;
- answer keys can be fetched for approved papers;
- AEI evaluation can consume rubric dictionaries;
- Maths normalization can use answer keys, acceptable answers, tolerance, and
  unit posture;
- visual/science assist can use checklist metadata where present.

Batch C should not delete or rewrite this behavior abruptly.

Recommended posture:

1. declare the supported rubric/model-answer contract;
2. add static Golden Harness coverage for supported and unsupported postures;
3. certify deterministic validation;
4. keep runtime evaluation behavior unchanged until a later implementation
   contract explicitly authorizes mapping or source changes.

---

## 13. Suggested Batch C implementation scope

The later implementation contract should decide exact files, but the design
recommends a narrow Batch C foundation:

- rubric/model-answer declaration contract document;
- read-only supported-scope rubric declarations;
- Golden Harness rubric/model-answer readiness cases;
- focused static/deterministic tests;
- certification report.

Optional only if authorized:

- a small pure helper that validates rubric declarations without touching
  production request paths.

---

## 14. Explicit non-goals

Batch C should not implement:

- runtime answer-sheet evaluation behavior changes;
- autonomous grading;
- autonomous paper approval;
- schema changes;
- API changes;
- UI changes;
- feature flags;
- public product claim changes;
- new AI provider behavior;
- LLM prompt changes;
- rubric generation;
- question-paper generation behavior changes;
- question-bank runtime behavior changes;
- exam service runtime changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger changes;
- parent/student visibility changes;
- browser workflow changes;
- Batch D question-bank/reuse readiness.

---

## 15. Golden Harness expectations

Batch C Golden Harness should include:

- objective-key supported posture;
- numeric-answer supported posture with tolerance;
- acceptable-answer variants;
- unit posture;
- scientific notation posture;
- model-answer assist posture;
- criterion-rubric manual-review posture;
- checklist-only visual/science posture;
- missing answer key manual-review posture;
- unsupported universal subjective-grading posture;
- no autonomous grading or approval implied by any rubric posture.

Cases should be deterministic and require no database, LLM, provider, browser,
or network execution.

---

## 16. Certification expectations

Batch C certification should prove:

- rubric/model-answer declaration contract exists;
- every declaration has stable IDs and versioning;
- support modes are explicit;
- answer-key/model-answer/criteria/checklist requirements are deterministic;
- unsupported/expansion scopes do not become product claims;
- AEI remains the answer-evaluation pipeline;
- no autonomous grading claim is introduced;
- no runtime behavior changed unless separately authorized;
- no schema/API/UI changes occurred;
- adjacent answer-sheet, question-bank, and AEI tests still pass;
- Batch A and Batch B contracts remain intact.

---

## 17. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`

Recommended authorization posture:

- authorize static rubric/model-answer readiness foundation only;
- keep runtime evaluation behavior unchanged;
- require Golden Harness and focused tests;
- require certification;
- prohibit Batch D question-bank/reuse readiness until Batch C is certified and
  published.

---

## 18. ARM gate

ARM may choose one of three decisions:

1. Accept the design brief and request the Batch C implementation authorization
   contract.
2. Accept with clarification requests.
3. Reject and revise the design.

Until ARM explicitly accepts a future implementation authorization contract,
Batch C implementation is not authorized.
