# Assessment Intelligence v1.0 Implementation Design Brief

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Accepted  
> Classification: Product implementation design  
> Implementation: Not authorized  
> Runtime behavior changes: Not authorized by this document  
> Readiness baseline: [`ASSESSMENT_INTELLIGENCE_V1_PRODUCTION_READINESS_REVIEW.md`](./ASSESSMENT_INTELLIGENCE_V1_PRODUCTION_READINESS_REVIEW.md)
> ARM review: Accepted as the Assessment Intelligence v1.0 implementation design baseline

---

## 1. Purpose

This design brief converts the accepted Assessment Intelligence v1.0 Production
Readiness Review into an implementation design.

It answers:

> How should StudyNexs complete Assessment Intelligence v1.0 without reopening
> AEI/EUI architecture or introducing parallel evaluation logic?

This document does not authorize implementation. It defines the design baseline
that a later implementation authorization contract can reference.

---

## 2. Product outcome

Assessment Intelligence v1.0 should let a school run the assessment loop inside
StudyNexs:

```text
Approved Curriculum
    -> Blueprint-aware Question Paper
    -> Teacher Review and Approval
    -> Question Bank and Reuse
    -> Exam Question Schema
    -> Evaluation / Marks
    -> Approved Evidence
    -> Learning and Mastery Intelligence
```

The teacher should experience this as one coherent workflow, not as separate
tools stitched together by engineering.

---

## 3. Core principle

Assessment Intelligence owns assessment creation, readiness, reuse, and linkage.

It does not own answer evaluation authority.

```text
Assessment Intelligence
    owns: question papers, blueprints, rubrics, reuse, exam linkage

AEI
    owns: answer understanding, reasoning, policy, teacher review, evidence

Teacher
    owns: final academic authority
```

No Assessment Intelligence implementation may bypass AEI for answer evaluation.

---

## 4. Existing foundations to reuse

### 4.1 Question paper foundation

Reuse the existing question paper implementation:

- `apps/api/app/modules/ai/services/question_paper_service.py`
- `apps/api/app/modules/ai/schemas/question_paper.py`
- `apps/api/app/modules/ai/endpoints/ai.py`
- teacher AI papers UI under `apps/admin-web/src/app/dashboard/teaching/ai-papers/`

Current reusable behavior:

- draft generation;
- grounded generation from approved CurriculumPack;
- teacher edit;
- submit;
- approve;
- reject;
- duplicate;
- download;
- AI usage and credit tracking.

### 4.2 Question bank foundation

Reuse:

- `apps/api/app/modules/ai/services/question_bank_service.py`;
- approved-paper ingestion;
- bank compose;
- bank gap-fill;
- rubric bank items;
- concept links.

Question bank work should improve governance and readiness, not create a second
bank.

### 4.3 Exam and evaluation linkage

Reuse:

- `apps/api/app/modules/examinations/services/exam_service.py`;
- approved-paper question schema import;
- per-question marks;
- AEI evaluation endpoints;
- approved-evidence metadata;
- topic/mastery spine foundations.

### 4.4 Platform foundations

Reuse the existing accepted platform layers:

- EUI Educational Identity;
- Educational Context;
- Platform Capability Registry;
- Knowledge Acquisition candidate foundation;
- Educational Knowledge Graph proposal foundation;
- Trust Report foundation;
- AEI rich evidence binding and readiness evidence.

Do not reopen EUI architecture or EUI source adoption under this program.

---

## 5. v1.0 supported-scope policy

Assessment Intelligence v1.0 must be production-complete inside a declared
supported scope.

Supported means:

- board/grade/subject/paper type is declared;
- blueprint posture is known;
- curriculum grounding requirement is explicit;
- teacher approval workflow is available;
- rubric/model-answer posture is known;
- evaluation linkage posture is known;
- Golden Harness coverage exists;
- browser proof exists for the supported teacher flow;
- product claims match certified capability.

StudyNexs must not claim universal assessment support.

---

## 6. Canonical assessment contract

v1.0 should converge existing fields into one canonical assessment contract used
by question papers, exams, AEI, and mastery.

The contract should cover:

| Field group | Purpose |
|---|---|
| Identity | paper ID, exam ID, question ID/number, tenant, class, subject. |
| Curriculum | curriculum pack, educational identity, chapter/topic/concept, learning objective. |
| Blueprint | section, question type, marks, internal-choice posture, required/optional count. |
| Question | question text, options, language, bilingual posture, diagram/visual posture. |
| Answer key | objective key, model answer, acceptable answers, tolerance/unit posture. |
| Rubric | criteria, marks allocation, manual-review notes, unsupported conditions. |
| Provenance | generated/composed/teacher-authored source, grounding sources, version evidence. |
| Evaluation linkage | AEI capability mode, expected answer type, review requirements. |

The design goal is not to force a large schema rewrite first. The design goal is
to stop new assessment code from inventing parallel dictionaries and field names.

---

## 7. Blueprint design posture

Blueprint behavior should become explicit and reviewable.

v1.0 should support:

- board/grade/subject/paper-type matching;
- sections;
- marks per question;
- number of questions;
- answer-any/internal choice posture;
- objective/subjective/question-type posture;
- total-mark validation;
- duration metadata;
- language/bilingual posture where supported.

The current service-level SSC helper is a useful fallback foundation, but v1.0
should not treat it as a universal blueprint.

Implementation should prefer the smallest safe step:

1. define the blueprint contract;
2. certify the existing supported blueprint behavior;
3. move toward data/config-backed blueprint declarations where needed;
4. defer broad board expansion until supported packs exist.

---

## 8. Rubric and model-answer design posture

Assessment Intelligence should standardize the input contract that AEI consumes
for evaluation.

Supported rubric postures:

| Posture | Meaning |
|---|---|
| Objective key | Deterministic exact/key-style evaluation is possible. |
| Numeric answer | AEI Maths normalization/tolerance/unit support may apply. |
| Model answer | Teacher-visible expected answer exists; AEI may assist. |
| Criterion rubric | Marks are distributed across teacher-reviewable criteria. |
| Checklist | Diagram/visual/science checklist assist only. |
| Manual review | No autonomous decision should be inferred. |
| Unsupported | Product must not claim automated assessment support. |

Rubric metadata should strengthen AEI; it must not create a parallel evaluator.

---

## 9. Question bank and reuse design posture

The question bank should be treated as a school-private approved asset store.

v1.0 should make reuse transparent:

- where the question came from;
- whether it was AI-generated, teacher-authored, or composed;
- which approved paper first introduced it;
- how often it was reused;
- whether the answer key/rubric exists;
- what concept/topic it maps to;
- whether it is safe for the current blueprint slot.

Paper duplication and bank compose should always produce a draft requiring
review. Reuse must not silently inherit authority from another context.

---

## 10. Paper-to-evaluation linkage design

v1.0 must certify the link between assessment creation and evaluation.

Target flow:

```text
Approved Question Paper
    -> Exam Question Schema
    -> Answer Collection / OCR / Manual Entry
    -> AEI Evaluation Assist
    -> Teacher Review and Approval
    -> Approved Evidence
    -> Mastery / Student / Parent / Principal Consumers
```

Rules:

- only approved papers should feed authoritative exam schemas;
- question schemas must preserve max marks and topic/concept posture;
- AEI receives rubric/model-answer context through the approved path;
- uncertain cases remain teacher-review only;
- downstream consumers receive approved evidence only.

---

## 11. Multilingual and bilingual design posture

Assessment Intelligence v1.0 should be honest about language support.

The design should distinguish:

- question paper language;
- answer key/model-answer language;
- student answer language;
- OCR/transcription language;
- teacher-facing explanation language.

v1.0 should declare supported language modes before enabling product claims.

Potential supported modes:

- English-only paper;
- supported Indian-language paper;
- bilingual paper;
- teacher-entered bilingual answer key;
- OCR-assisted student answer evaluation where AEI has certified support.

Unsupported language combinations should fail safely or route to manual review.

---

## 12. Teacher workflow design posture

The school-visible v1.0 workflow should be boringly reliable:

1. Select class, subject, and approved curriculum pack.
2. Select blueprint / paper type.
3. Generate or compose a draft paper.
4. Review questions, answer keys, metadata, and grounding.
5. Edit before approval.
6. Submit for approval where role workflow requires it.
7. Approve or reject.
8. Download paper and answer key.
9. Create or link an exam from the approved paper.
10. Enter marks or run AEI-assisted evaluation.
11. Teacher approves final outcomes.
12. Approved evidence flows to learning intelligence.

Browser proof is required before v1.0 certification.

---

## 13. Recommended implementation batches

Implementation should proceed batch-by-batch. No batch is authorized by this
design brief.

| Batch | Name | Objective |
|---|---|---|
| A | Contract and capability matrix | Freeze the canonical assessment contract and supported-scope matrix. |
| B | Blueprint readiness | Make supported blueprint behavior explicit, validated, and non-universal. |
| C | Rubric/model-answer readiness | Standardize objective, model-answer, rubric, acceptable-answer, and review posture. |
| D | Question bank and reuse readiness | Certify question bank governance, reuse provenance, and compose behavior. |
| E | Paper-to-evaluation linkage | Certify approved paper -> exam schema -> AEI/evaluation -> evidence flow. |
| F | Multilingual/bilingual boundary | Declare and enforce supported language modes and fallback behavior. |
| G | Teacher workflow/browser proof | Prove the complete teacher-visible assessment loop in browser. |
| H | v1.0 certification | Final Assessment Intelligence v1.0 certification and product-claim boundary. |

The next implementation authorization, if this design is accepted, should cover
Batch A only.

---

## 14. Validation strategy

Each implementation batch should include:

- focused unit tests;
- API regression tests;
- tenant/RBAC coverage where applicable;
- Golden Harness cases;
- AEI regression where evaluation context is touched;
- EUI regression where educational identity/context/capability is touched;
- browser proof for UI-facing batches;
- rollback/compatibility evidence;
- certification report.

For any user-visible batch, browser proof should be treated as mandatory.

---

## 15. Golden Harness expansion

The Assessment Intelligence Golden Harness should eventually cover:

- grounded generation from approved curriculum;
- unapproved/empty/wrong-subject curriculum refusal;
- supported blueprint validation;
- internal-choice blueprint behavior;
- objective answer key;
- model-answer rubric;
- criterion rubric;
- numeric answer with AEI support;
- acceptable-answer variants;
- question bank ingestion;
- bank compose without LLM when fully covered;
- bank gap-fill with explicit AI provenance;
- paper duplication to draft;
- approved paper -> exam schema import;
- multilingual/bilingual supported and unsupported modes;
- downstream approved-evidence posture.

---

## 16. Certification posture

Assessment Intelligence v1.0 certification should prove:

- supported scope is declared;
- unsupported scope is not overclaimed;
- teachers retain final authority;
- generated papers remain draft until approved;
- approved papers can feed exams;
- AEI remains the only answer-evaluation pipeline;
- approved evidence remains the only downstream source;
- browser proof covers teacher workflow;
- rollback and failure modes are documented;
- product claims match runtime evidence.

---

## 17. Explicit non-goals

This program does not authorize:

- new AEI architecture;
- new EUI architecture;
- autonomous grading;
- autonomous paper approval;
- bypassing the AI gateway;
- provider-specific direct SDK calls;
- universal board support;
- universal handwriting/OCR support;
- broad schema rewrites without separate authorization;
- public product claims before certification;
- parent/student visibility of unapproved evidence;
- EUI source-of-truth switching;
- OCR Phase 3 decisions.

---

## 18. Open decisions for implementation authorization

Before Batch A implementation, ARM should approve:

1. the exact Batch A repository boundary;
2. whether Batch A is docs/contracts-only or includes small runtime constants;
3. the initial supported-scope matrix format;
4. the location of the Assessment Intelligence Golden Harness cases;
5. whether any feature flag is needed for Batch A;
6. required focused tests and regression suites;
7. certification report name and required evidence.

---

## 19. Recommended next step

If ARM accepts this design brief, the next artifact should be:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_A_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`

Scope should remain narrow:

- canonical assessment contract;
- supported-scope/capability matrix;
- Golden Harness starter cases;
- certification report;
- no schema/API/UI/runtime behavior changes unless explicitly included.

This preserves the rhythm:

```text
Readiness Review
    -> Design Brief
    -> Batch A Authorization Contract
    -> Batch A Implementation
    -> Validation
    -> Certification
```
