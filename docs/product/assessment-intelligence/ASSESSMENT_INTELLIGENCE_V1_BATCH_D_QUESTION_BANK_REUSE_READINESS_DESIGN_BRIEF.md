# Assessment Intelligence v1.0 Batch D Design Brief

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Program: Assessment Intelligence v1.0
> Batch: D - Question Bank and Reuse Readiness
> Status: Accepted
> Classification: Product implementation design
> Implementation: Not authorized
> Runtime behavior changes: Not authorized by this document
> Previous baseline: Batch C - Rubric and Model-Answer Readiness
> ARM review: Accepted as the Batch D Question Bank and Reuse Readiness design baseline

---

## 1. Purpose

Batch D should make question-bank reuse explicit, provenance-backed,
school-private, and non-authoritative until teacher approval.

It answers:

> Which approved questions may be reused, what evidence proves their origin, and
> how do we prevent question-bank convenience from silently becoming academic
> authority?

This document is design-only. It does not authorize implementation.

---

## 2. Why Batch D exists

Assessment Intelligence v1.0 Batch A established the canonical assessment
contract.

Batch B made blueprint behavior explicit and non-universal.

Batch C made answer-key, model-answer, rubric, and manual-review posture
explicit.

Batch D is the next dependency because question reuse sits between assessment
creation and evaluation. Once a teacher can reuse approved questions, StudyNexs
must preserve:

- tenant isolation;
- question provenance;
- approval lineage;
- rubric and answer-key lineage;
- blueprint-slot suitability;
- gap-fill provenance;
- reuse count and audit posture;
- teacher review before the reused question carries authority in a new paper.

Without this layer, question-bank compose can become a hidden shortcut where a
question's previous approval is incorrectly treated as approval for every future
context.

---

## 3. Repository foundations to reuse

Batch D should extend existing question-bank foundations rather than creating a
parallel bank or marketplace.

Relevant backend foundations include:

- `apps/api/app/db/models/question_bank.py`;
- `QuestionBankItem`;
- `RubricBankItem`;
- `BANK_STATUS_APPROVED`;
- `QuestionSource`;
- `apps/api/app/modules/ai/services/question_bank_service.py`;
- `content_fingerprint`;
- `ingest_from_paper`;
- `fetch_rubrics_for_paper`;
- `count_compose_candidates`;
- `fetch_compose_candidates`;
- `compose_sections_from_plan`;
- `merge_gap_fill`;
- `renumber_sections`;
- `note_bank_items_used`;
- question concept linking during bank ingestion.

Relevant current behavior includes:

- approved papers are split into atomic `QuestionBankItem` rows;
- re-approval replaces previous bank rows for the same source paper;
- bank rows are scoped by `school_id`, `class_id`, and `subject_id`;
- approved bank rows can carry answer keys through `RubricBankItem`;
- compose candidates are filtered to approved rows in the same school, class,
  and subject;
- compose selects by marks and question type;
- gap-fill can append generated questions when the bank cannot cover the plan;
- reused bank item usage can be recorded through `usage_count` and
  `used_in_paper_ids`.

Batch D should document and test the contract posture first. Runtime behavior
changes require a later implementation authorization.

---

## 4. Product outcome

After Batch D is eventually implemented and certified, StudyNexs should be able
to say:

> For the declared supported scope, approved school-private questions can be
> reused transparently with provenance, rubric posture, and teacher-review
> boundaries intact.

Teachers should be able to understand where a reused question came from, whether
it has answer context, why it matches a blueprint slot, and whether review is
required before the new paper becomes authoritative.

---

## 5. Design principle

The question bank is an approved asset store. It is not an automatic authority
engine.

```text
Approved Question Paper
        |
        v
School-Private Question Bank
        |
        v
Question Reuse / Compose Candidate
        |
        v
Draft Question Paper
        |
        v
Teacher Review and Approval
```

Previous approval proves a question was accepted in its original paper context.
It does not automatically approve the question for a different assessment,
blueprint slot, academic year, curriculum version, language, or marking posture.

---

## 6. Relationship to earlier Assessment Intelligence batches

Batch D should build on the previous Assessment Intelligence contracts rather
than introducing a new reuse model.

### Batch A fields

Question-bank reuse should preserve or reference:

- `assessment_id`;
- `paper_id`;
- `school_id`;
- `class_id`;
- `subject_id`;
- `board`;
- `grade`;
- `paper_type`;
- `section_id`;
- `section_title`;
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

Reuse should be checked against blueprint posture:

- `blueprint_id`;
- `section_id`;
- `marks_per_question`;
- `question_count`;
- `answer_any_count`;
- `question_type`;
- `validation_rules`;
- `product_claim_allowed`.

### Batch C fields

Reuse should preserve answer-context posture:

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

---

## 7. Question-bank reuse declaration model

A question-bank reuse declaration should describe provenance and suitability
without approving the reused question.

Minimum declaration fields:

| Field | Purpose |
|---|---|
| `bank_item_id` | Stable reusable question identifier. |
| `source_paper_id` | Original approved paper that created the bank item. |
| `source_question_bank_item_id` | Source bank item when the question is reused into a new draft paper. |
| `school_id` | Tenant boundary, derived server-side only. |
| `class_id` | Class scope. |
| `subject_id` | Subject scope. |
| `board` | Board scope. |
| `grade` | Grade/class label. |
| `topics` | Topic tags carried from the approved paper where available. |
| `concepts` | Concept links where available. |
| `educational_identity_id` | Canonical EUI identity where available. |
| `section_title` | Original or target section title. |
| `question_number` | Source or draft question number. |
| `question_text` | Question text. |
| `marks` | Question marks. |
| `question_type` | MCQ, short, long, diagram, etc. |
| `options` | MCQ options where applicable. |
| `source` | AI, teacher, previous paper, or composed. |
| `approval_status` | Current bank approval status. |
| `approved_by` | Teacher/admin who approved the source paper or bank item. |
| `approved_at` | Approval timestamp for the source paper or bank item. |
| `content_fingerprint` | Stable content hash for dedup and audit. |
| `usage_count` | Reuse count for operational transparency. |
| `used_in_paper_ids` | Papers where the item has been used. |
| `rubric_posture` | Batch C answer-context posture. |
| `answer_context_available` | Whether answer key/model/rubric/checklist context exists. |
| `blueprint_slot_id` | Target blueprint slot where available. |
| `marks_match` | Whether item marks match target slot marks. |
| `type_match` | Whether item type matches target slot type. |
| `topic_overlap` | Whether topics/concepts overlap target scope. |
| `gap_fill_provenance` | Whether the question came from bank reuse or gap-fill generation. |
| `reuse_review_required` | Whether teacher review is required before authority. |
| `product_claim_allowed` | Whether this reuse posture may be claimed as supported. |

This declaration should be deterministic and inspectable.

---

## 8. Question-bank reuse support modes

Batch D should use the conservative support vocabulary already used by AEI, EUI,
and Assessment Intelligence.

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared school-private scope. |
| `assist` | System can help find or compose candidates, but teacher review remains required. |
| `manual_review` | Teacher must approve suitability before the question carries authority. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future roadmap candidate, not a v1.0 claim. |

Supported reuse does not mean the reused question is automatically approved in a
new paper. It means the reuse provenance and suitability checks are declared and
validated for the supported scope.

---

## 9. Recommended initial reuse postures

### 9.1 Approved-paper ingestion

Use when an approved question paper is split into atomic bank items.

Design expectations:

- source paper must be approved;
- source paper must belong to the same school;
- blank questions are ignored;
- malformed papers with no valid questions fail clearly;
- each item receives source paper provenance;
- answer keys are carried into rubric bank items where present;
- concept links are retained where available;
- re-approval remains idempotent.

### 9.2 Same-school approved bank reuse

Use when an approved bank item is reused into a draft question paper for the same
school, class, and subject.

Design expectations:

- reuse is school-private;
- only approved bank items are candidates;
- target paper remains draft until teacher approval;
- previous approval is visible but non-authoritative for the new paper;
- source bank item and source paper provenance are retained.

### 9.3 Blueprint-slot compose

Use when the bank can fill a blueprint slot.

Design expectations:

- marks must match the target slot;
- question type must match or be an explicitly accepted equivalent;
- topic/concept overlap should be recorded where available;
- answer-key/rubric availability should be recorded;
- selected bank items should not be reused twice in the same composed paper;
- composed paper remains draft and reviewable.

### 9.4 Gap-fill assist

Use when the bank cannot fill one or more blueprint slots and generation fills
the gap.

Design expectations:

- gap-fill provenance must be explicit;
- generated questions must not be represented as approved bank reuse;
- answer-key/rubric posture must be explicit or manual-review;
- teacher approval remains required.

### 9.5 Changed-context reuse

Use when a previously approved question is reused in a changed academic context,
such as a different chapter, paper type, curriculum version, language, academic
year, or board scope.

Design expectations:

- the reused question must remain draft in the new context;
- review requirement must be explicit;
- the system must not silently transfer product support claims;
- conflicts should be recorded for review.

### 9.6 Unsupported reuse

Use when the requested reuse would violate safety or governance boundaries.

Examples:

- cross-school reuse;
- marketplace/global bank reuse;
- draft or rejected bank item reuse;
- missing tenant scope;
- unknown approval status;
- unsupported board/subject/product scope;
- reuse that bypasses teacher review.

---

## 10. Deterministic validation expectations

Batch D should define deterministic validation for question-bank reuse
declarations.

Validation should cover:

- `school_id` is required and server-derived;
- only approved bank items may be reused in supported posture;
- source paper provenance is present;
- source bank item provenance is present for reused questions;
- `content_fingerprint` is stable for identical content, marks, and type;
- usage metadata is present and bounded to the school context;
- cross-tenant reuse is blocked;
- draft/rejected/unapproved bank items are not supported;
- marks match target blueprint slot where compose claims support;
- question type matches target blueprint slot where compose claims support;
- topic/concept/EUI identity posture is explicit where available;
- answer-key/rubric availability is explicit;
- gap-fill questions are distinguishable from bank-reused questions;
- composed papers remain drafts until teacher approval;
- no direct marks, parent evidence, mastery update, or source-of-truth switch is
  implied by reuse.

---

## 11. AEI and EUI handoff posture

Batch D should strengthen assessment inputs without bypassing AEI or EUI.

Permitted posture:

```text
Question Bank Reuse Declaration
        |
        v
Draft Question Paper
        |
        v
Teacher Review / Approval
        |
        v
AEI Evaluation Context
        |
        v
Teacher-Approved Evidence
```

Forbidden posture:

```text
Question Bank Reuse Declaration
        |
        v
Direct Marks / Direct Parent Evidence / Direct Mastery Update
```

EUI may provide identity, context, capability, KAI, EKG, and trust metadata.
AEI remains the only academic answer-evaluation pipeline.

---

## 12. Current runtime migration posture

The current runtime already has useful question-bank behavior:

- approving papers can ingest bank items;
- re-approval can replace prior bank rows;
- bank compose can select approved items by school, class, subject, marks, and
  type;
- gap-fill can supplement missing bank coverage;
- answer keys can be carried with reused bank items;
- usage can be recorded.

Batch D should not delete or rewrite this behavior abruptly.

Recommended posture:

1. declare the supported question-bank/reuse contract;
2. add deterministic Golden Harness coverage for reuse postures;
3. certify provenance, tenant boundary, compose, and gap-fill posture;
4. keep runtime behavior unchanged unless a later implementation contract
   explicitly authorizes mapping or enforcement changes.

---

## 13. Suggested Batch D implementation scope

The later implementation contract should decide exact files, but the design
recommends a narrow Batch D foundation:

- question-bank/reuse declaration contract document;
- read-only supported-scope reuse declarations;
- Golden Harness question-bank/reuse cases;
- focused static/deterministic tests;
- certification report.

Optional only if authorized:

- small pure helpers that validate reuse declarations without touching
  production request paths;
- tests that inspect existing question-bank behavior without changing it.

---

## 14. Explicit non-goals

Batch D should not implement:

- runtime question-bank behavior changes unless separately authorized;
- autonomous paper approval;
- autonomous question approval;
- schema changes;
- API changes;
- UI changes;
- feature flags;
- public product claim changes;
- new AI provider behavior;
- LLM prompt changes;
- question generation behavior changes;
- answer-sheet evaluation behavior changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger changes;
- parent/student visibility changes;
- mastery updates;
- global question bank;
- cross-school question marketplace;
- paid question marketplace;
- Batch E paper-to-evaluation linkage.

---

## 15. Golden Harness expectations

Batch D Golden Harness should include:

- approved-paper ingestion posture;
- idempotent re-approval posture;
- source paper provenance present;
- source bank item provenance present for reuse;
- stable content fingerprint;
- answer-key/rubric context carried where available;
- compose marks match;
- compose question-type match;
- compose topic/concept overlap posture;
- bank gap-fill assist posture;
- changed-context reuse requires review;
- draft/unapproved bank item unsupported;
- cross-tenant reuse unsupported;
- no autonomous grading, approval, parent evidence, or mastery implied by reuse.

Cases should be deterministic and require no LLM, provider, browser, or network
execution. Database-backed tests may be used only if the implementation contract
explicitly authorizes them.

---

## 16. Certification expectations

Batch D certification should prove:

- question-bank/reuse declaration contract exists;
- supported and unsupported reuse postures are explicit;
- provenance requirements are deterministic;
- tenant boundary expectations are explicit;
- approved-only reuse expectations are explicit;
- compose suitability expectations are deterministic;
- gap-fill provenance is distinguishable from approved bank reuse;
- previous approval does not silently become new paper authority;
- AEI remains the answer-evaluation pipeline;
- no autonomous grading or approval claim is introduced;
- no runtime behavior changed unless separately authorized;
- no schema/API/UI changes occurred;
- adjacent question-bank, question-paper, rubric, and AEI tests still pass;
- Batch A, Batch B, and Batch C contracts remain intact.

---

## 17. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`

Recommended authorization posture:

- authorize static question-bank/reuse readiness foundation only;
- keep runtime question-bank behavior unchanged unless explicitly scoped;
- require Golden Harness and focused tests;
- require certification;
- prohibit Batch E paper-to-evaluation linkage until Batch D is certified and
  published.

---

## 18. ARM gate

ARM may choose one of three decisions:

1. Accept the design brief and request the Batch D implementation authorization
   contract.
2. Accept with clarification requests.
3. Reject and revise the design.

Until ARM explicitly accepts a future implementation authorization contract,
Batch D implementation is not authorized.
