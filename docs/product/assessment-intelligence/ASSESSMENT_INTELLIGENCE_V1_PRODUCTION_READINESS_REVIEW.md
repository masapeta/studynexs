# Assessment Intelligence v1.0 Production Readiness Review

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Accepted  
> Classification: Product-facing readiness review  
> Implementation: Not authorized  
> Runtime behavior changes: Not authorized
> ARM review: Accepted as the Assessment Intelligence v1.0 readiness baseline

---

## 1. Purpose

This review answers one question:

> What must be completed for Assessment Intelligence v1.0 to feel production-ready to a school?

This is not an implementation contract. It does not authorize code, schema, API,
UI, feature-flag, or behavior changes. It is the bridge from the existing
assessment foundation to a school-visible, trusted assessment workflow.

---

## 2. Product framing

Assessment Intelligence is the product loop that turns approved curriculum into
approved assessments, and then links those assessments into evaluation and
learning intelligence.

```text
Curriculum
    -> Question Paper
    -> Assessment
    -> Evaluation
    -> Teacher Review
    -> Approved Evidence
    -> Learning Gaps
    -> Student / Parent / Principal Intelligence
```

The product goal is not simply "generate a paper." The product goal is:

> A teacher can create, approve, conduct, evaluate, and analyze an assessment
> without engineering help, while every authoritative outcome remains
> teacher-approved.

---

## 3. Relationship to AEI and EUI

Assessment Intelligence must consume the existing platform foundation rather
than reimplementing it.

| Layer | Role in Assessment Intelligence |
|---|---|
| Curriculum Intelligence | Source of approved curriculum content and learning objectives. |
| EUI | Shared educational identity, context, capability, knowledge, and trust foundation. |
| AEI | Evaluation intelligence for student answers after an assessment is conducted. |
| Teacher authority | Final approval for generated papers, evaluation outcomes, and evidence. |

Assessment Intelligence must not introduce parallel evaluation logic. Any answer
evaluation continues to flow through AEI.

---

## 4. Repository discovery summary

The repository already contains meaningful Assessment Intelligence foundations.
This review is grounded in the following surfaces.

### Backend implementation surfaces

| Surface | Evidence |
|---|---|
| Question paper generation | `apps/api/app/modules/ai/services/question_paper_service.py` |
| Question paper API and approval lifecycle | `apps/api/app/modules/ai/endpoints/ai.py` |
| Question paper schemas | `apps/api/app/modules/ai/schemas/question_paper.py` |
| Question bank ingestion and compose | `apps/api/app/modules/ai/services/question_bank_service.py` |
| Curriculum grounding | `apps/api/app/modules/ai/services/assessment_grounding.py` |
| Exam creation and question schema import | `apps/api/app/modules/examinations/services/exam_service.py` |
| Exam routes | `apps/api/app/modules/examinations/endpoints/exam.py` |
| AEI evaluation routes | `apps/api/app/modules/examinations/endpoints/evaluation.py` |
| Concept links for question bank items | `apps/api/app/modules/knowledge_graph/services/question_concept_link_service.py` |

### Frontend implementation surfaces

| Surface | Evidence |
|---|---|
| Teacher AI papers page | `apps/admin-web/src/app/dashboard/teaching/ai-papers/page.tsx` |
| Legacy AI papers redirect | `apps/admin-web/src/app/dashboard/ai-papers/page.tsx` |
| Exam question schema editor | `apps/admin-web/src/app/dashboard/teaching/exams/QuestionSchemaEditor.tsx` |
| Teacher exam pages | `apps/admin-web/src/app/dashboard/teaching/exams/` |
| Teacher evaluation page | `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx` |

### Test surfaces

| Surface | Evidence |
|---|---|
| Grounded assessment generation | `apps/api/tests/test_assessment_grounding.py` |
| Question paper generation / duplication / credits | `apps/api/tests/test_question_paper.py` |
| Question bank ingestion | `apps/api/tests/test_question_bank.py` |
| Question bank compose | `apps/api/tests/test_question_bank_compose.py` |
| Exam question schemas and marks | `apps/api/tests/test_exam_questions.py` |
| Question concept links | `apps/api/tests/test_question_concept_links.py` |

---

## 5. Current implemented strengths

### 5.1 Grounded question paper generation exists

The backend can generate draft question papers and, when a `pack_id` is
provided, ground those papers in an approved `CurriculumPack`. Grounded papers
carry pack provenance, grounding sources, citations, Bloom metadata,
difficulty, learning outcome, and concepts.

Important current behavior:

- papers are generated as drafts;
- AI does not publish papers;
- teacher / incharge approval is required before use;
- generation refuses unsafe grounded mode when the pack is empty, unapproved, or
  mismatched to class/subject;
- all LLM calls go through the shared AI gateway.

### 5.2 Question bank foundation exists

Approved papers can be ingested into a school-private question bank.

Existing capabilities include:

- splitting approved papers into reusable question bank items;
- storing answer keys as rubric bank items;
- stable content fingerprints for dedup/similarity foundations;
- idempotent re-approval behavior;
- compose-from-bank generation;
- LLM gap fill only when bank coverage is insufficient;
- no LLM call when the bank fully covers the plan.

### 5.3 Human approval lifecycle exists

The paper lifecycle includes draft/edit/submit/approve/reject style behavior.
Approved papers enter the question bank. Rejected papers retain rejection
reason and can be edited or reused.

### 5.4 Paper-to-exam linkage exists

The exam service can import question structure from an approved question paper.
This establishes an important bridge:

```text
Approved Question Paper -> Exam Question Schema -> Per-question Marks -> Mastery / AEI
```

Existing validation prevents obvious corruption:

- duplicate question numbers are rejected;
- question max marks below exam total are rejected;
- internal-choice totals above exam total are permitted;
- schemas cannot be replaced if doing so would orphan existing marks.

### 5.5 Teacher-facing surfaces exist

The teacher portal has surfaces for:

- AI paper generation;
- grounding pack selection;
- question bank status;
- recent papers;
- paper edit/save;
- paper approval/download flow;
- exam question schema import from approved AI papers.

This means v1.0 work can be product-completion work, not greenfield build.

---

## 6. v1.0 production scope

Assessment Intelligence v1.0 should be complete inside a declared supported
scope, not universal.

### Must include

| Capability | v1.0 expectation |
|---|---|
| Question paper generation | Grounded generation from approved curriculum packs for supported boards/grades/subjects. |
| Blueprint support | Board/grade/subject paper structure must be explicit, reviewable, and not hardcoded as universal. |
| Question bank | Approved questions become reusable assets; reuse is visible and auditable. |
| Rubric/model answer handling | Every evaluable question has a teacher-visible answer key/model answer/rubric posture. |
| Paper approval workflow | Generated or composed papers remain non-authoritative until approved. |
| Paper reuse | Teachers can duplicate/reuse safely without silently bypassing review. |
| Paper-to-evaluation linkage | Approved papers can create/import exam question schema and feed AEI/evaluation. |
| Bilingual/multilingual support boundary | Supported language posture is explicit; unsupported cases are not overclaimed. |
| Analysis readiness | Assessment outputs can feed mastery/topic evidence after teacher-approved marks/evaluation. |
| Certification | Golden Harness + focused API/UI/browser proof for the full assessment loop. |

---

## 7. Readiness assessment

| Area | Current state | Readiness |
|---|---|---|
| Grounded generation | Implemented and tested at service level. | Partial - needs v1.0 workflow certification and supported-scope declaration. |
| Blueprint support | Default SSC-style blueprint exists in service code. | Needs work - board/grade/subject blueprint contract should become data/config, not implicit service logic. |
| Question bank | Implemented with approval ingestion and compose. | Partial - needs UX/readiness proof, governance, and reuse/citation clarity. |
| Rubric/model answers | Answer keys and rubric bank items exist. | Partial - needs standardized rubric/model-answer contract for AEI and teacher review. |
| Human approval | Implemented. | Partial - needs end-to-end browser proof and role/RBAC acceptance evidence. |
| Paper reuse | Duplicate-to-draft exists. | Partial - needs product UX proof and clear reuse provenance. |
| Paper-to-exam linkage | Approved paper schema import exists. | Partial - needs complete paper -> exam -> evaluation -> evidence proof. |
| Bilingual/multilingual | Some language/OCR support exists in AEI; assessment generation scope not yet declared. | Needs design and supported-scope boundary. |
| Analysis readiness | Per-question marks and topic fields exist; topic/mastery spine work exists separately. | Partial - needs canonical topic-ID/mastery linkage in assessment path. |
| Certification | Unit/service tests exist. | Needs v1.0 certification pack and browser proof. |

---

## 8. Main production gaps

### Gap 1 - Blueprint governance

The current generation path contains an SSC-style blueprint helper. That is a
useful foundation but not a v1.0 production posture for multiple boards/grades.

Production readiness requires:

- a clear blueprint source of truth;
- board/grade/subject applicability;
- support for school-provided blueprint variants;
- internal choice semantics;
- marks distribution validation;
- no hidden universal assumptions.

### Gap 2 - Assessment contract unification

Question paper, exam schema, AEI evaluation, approved evidence, and mastery
should share a consistent contract for:

- question number;
- max marks;
- question type;
- topic/concept identity;
- learning objective;
- answer key;
- rubric/model answer;
- acceptable answers;
- evidence linkage.

Current components have pieces of this contract, but v1.0 needs a formal
Assessment Intelligence contract so future consumers do not invent field names.

### Gap 3 - Rubric and model-answer readiness

Answer keys exist, and rubric bank items exist, but v1.0 needs a teacher-trust
rubric posture:

- objective key;
- model answer;
- criterion-based rubric;
- acceptable variants;
- manual-review notes;
- unsupported/assist-only cases.

This should align with AEI v1.0 and must not create parallel grading logic.

### Gap 4 - Paper-to-evaluation proof

The linkage exists technically, but v1.0 requires certified proof that the
entire teacher-visible loop works:

```text
Approved CurriculumPack
    -> Grounded Question Paper
    -> Teacher Approval
    -> Question Bank
    -> Exam Question Schema
    -> Answer Collection / Evaluation
    -> Teacher Review
    -> Approved Evidence
    -> Learning/Mastery Evidence
```

### Gap 5 - Multilingual and bilingual support boundary

Assessment generation and paper rendering must not imply universal language
support. v1.0 needs explicit supported-scope posture:

- supported languages;
- whether question papers can be bilingual;
- whether answer keys/rubrics can be bilingual;
- how unsupported language requests fail or route to review;
- relationship to OCR/language assist in AEI.

### Gap 6 - Product/browser proof

The backend has strong tests, but school readiness needs browser-level evidence
for teacher workflows:

- create grounded paper;
- review and edit;
- submit;
- approve/reject;
- download;
- duplicate/reuse;
- create exam from approved paper;
- evaluate or enter marks;
- see downstream evidence.

---

## 9. v1.0 implementation sequence recommendation

No implementation is authorized by this review. If ARM accepts this readiness
review, the next artifact should be:

`docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_IMPLEMENTATION_DESIGN_BRIEF.md`

Recommended implementation batches after design and authorization:

| Batch | Theme | Purpose |
|---|---|---|
| Batch A | Assessment contract and capability matrix | Freeze the canonical assessment contract and supported-scope matrix. |
| Batch B | Blueprint readiness | Make blueprint behavior explicit, data-driven where possible, and validated. |
| Batch C | Rubric/model-answer readiness | Standardize objective, model-answer, rubric, acceptable-answer, and review posture. |
| Batch D | Question bank and reuse readiness | Improve reuse provenance, bank governance, compose clarity, and certification. |
| Batch E | Paper-to-evaluation linkage | Certify approved paper -> exam schema -> AEI/evaluation -> evidence loop. |
| Batch F | Multilingual/bilingual support boundary | Declare and enforce supported language/posture boundaries. |
| Batch G | Teacher workflow/browser proof | Browser-proof create/edit/submit/approve/download/reuse/evaluate flow. |
| Batch H | Assessment Intelligence v1.0 certification | Final supported-scope certification, rollback posture, and product claims. |

---

## 10. Explicit non-goals for this review

This review does not authorize:

- implementation;
- schema changes;
- API contract changes;
- UI changes;
- feature-flag changes;
- new AI providers;
- autonomous paper approval;
- autonomous grading changes;
- AEI contract changes;
- EUI contract changes;
- parent/student visibility changes;
- public product claims;
- OCR Phase 3 decisions;
- source-of-truth switching.

---

## 11. Acceptance criteria for the future v1.0 program

Assessment Intelligence v1.0 should be declared complete only when all of the
following are true:

- supported boards, grades, subjects, languages, and paper types are declared;
- question paper generation is grounded in approved curriculum for supported
  scope;
- unsupported or weakly-supported cases fail safely or remain teacher-review
  only;
- blueprint behavior is explicit and test-covered;
- rubrics/model answers/acceptable answers are available for evaluation-ready
  questions;
- generated and reused papers remain teacher-approved before authority;
- approved papers can feed exam question schemas without manual engineering;
- paper-to-evaluation-to-evidence flow is certified;
- no answer evaluation bypasses AEI;
- parent/student downstream views consume only teacher-approved evidence;
- Golden Harness covers generation, blueprint, rubric, bank, linkage, and
  supported-scope boundaries;
- teacher browser proof demonstrates the full v1.0 assessment loop.

---

## 12. ARM recommendation

Recommendation:

> Accept this readiness review as the starting point for Assessment Intelligence
> v1.0 product completion, then draft the v1.0 implementation design brief.

The implementation posture should remain disciplined:

```text
Readiness Review
    -> Design Brief
    -> ARM Implementation Authorization Contract
    -> Batch-by-batch implementation
    -> Certification
    -> Publication
```

Assessment Intelligence should now move from "existing foundational capability"
to "school-visible, production-complete workflow" without reopening AEI/EUI
architecture or creating parallel evaluation logic.
