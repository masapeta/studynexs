# Assessment Intelligence v1.0 Canonical Contract

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Batch A foundation  
> Authorization: ASSESSMENT-V1-BATCH-A-AUTH-001  
> Runtime behavior: Unchanged  
> Scope: Contract definition only

---

## 1. Purpose

This document defines the canonical Assessment Intelligence v1.0 contract.

It is the shared vocabulary for:

- question papers;
- question bank items;
- exam question schemas;
- AEI evaluation inputs;
- teacher review;
- approved evidence;
- topic/mastery linkage.

The contract prevents each layer from inventing its own field names for the same
academic object.

This document does not introduce database fields, API fields, UI behavior, or
runtime behavior. Later batches may map existing runtime fields into this
contract incrementally.

---

## 2. Contract principle

Assessment Intelligence owns the assessment object.

AEI owns answer evaluation.

Teachers own authority.

```text
Assessment Contract
    -> Question Paper
    -> Exam Question Schema
    -> AEI Evaluation Context
    -> Teacher Review
    -> Approved Evidence
    -> Learning/Mastery Consumers
```

No consumer should reinterpret an assessment artifact from raw labels when a
contract field is available.

---

## 3. Canonical field groups

### 3.1 Identity fields

| Field | Meaning |
|---|---|
| `tenant_id` | Tenant/school boundary. Never client-trusted. |
| `assessment_id` | Canonical assessment/paper/exam reference when available. |
| `question_id` | Stable question reference when available. |
| `question_number` | Human-visible question number such as `1`, `2(a)`, or `Part B - 5`. |
| `source_artifact_id` | Source paper, bank item, worksheet, or imported artifact reference. |
| `source_artifact_type` | `question_paper`, `question_bank_item`, `exam_schema`, `worksheet`, or equivalent. |

### 3.2 Curriculum fields

| Field | Meaning |
|---|---|
| `curriculum_pack_id` | Approved curriculum pack used for grounding. |
| `educational_identity_id` | Canonical EUI identity where available. |
| `board` | Declared board for the supported scope. |
| `curriculum` | Declared curriculum family, such as `NCF2023`. |
| `curriculum_version` | Version label of the curriculum source. |
| `grade` | Grade/class level. |
| `subject` | Subject name. |
| `chapter` | Chapter label when mapped. |
| `topic` | Topic label or canonical topic reference. |
| `concepts` | Concepts assessed by the question. |
| `learning_objectives` | Learning objectives assessed by the question. |

### 3.3 Blueprint fields

| Field | Meaning |
|---|---|
| `paper_type` | `unit_test`, `slip_test`, `term_exam`, `practice`, or supported equivalent. |
| `blueprint_id` | Blueprint declaration used to create or validate the paper. |
| `section_id` | Stable section reference. |
| `section_title` | Human-visible section title. |
| `question_type` | `mcq`, `very_short`, `short`, `long`, `diagram`, `map`, or supported equivalent. |
| `marks` | Marks allocated to the question. |
| `marks_posture` | `fixed`, `internal_choice`, `rubric_split`, or `manual_review`. |
| `required_count` | Questions required in the section. |
| `answer_any_count` | Internal-choice answer count when applicable. |
| `duration_minutes` | Paper duration where applicable. |

### 3.4 Question fields

| Field | Meaning |
|---|---|
| `question_text` | Teacher-visible question text. |
| `options` | MCQ options when applicable. |
| `question_language` | Language used in the question text. |
| `question_script` | Script used in the question text. |
| `bilingual_mode` | `none`, `parallel`, `assist`, `manual_review`, or `unsupported`. |
| `visual_requirement` | Diagram, graph, map, table, chemical structure, or none. |
| `input_modality_expected` | `typed`, `scanned`, `handwritten`, `diagram`, `mixed`, or equivalent. |

### 3.5 Answer key fields

| Field | Meaning |
|---|---|
| `answer_key` | Objective key or concise expected answer. |
| `model_answer` | Teacher-visible model answer for subjective questions. |
| `acceptable_answers` | Equivalent answer variants. |
| `numeric_tolerance` | Tolerance for deterministic numeric evaluation. |
| `unit_posture` | Unit requirement or conversion posture. |
| `scientific_notation_posture` | Expected handling of scientific notation. |

### 3.6 Rubric fields

| Field | Meaning |
|---|---|
| `rubric_id` | Stable rubric reference where available. |
| `rubric_posture` | `objective_key`, `numeric_answer`, `model_answer`, `criterion_rubric`, `checklist`, `manual_review`, or `unsupported`. |
| `criteria` | Teacher-reviewable criteria and marks allocation. |
| `checklist_items` | Checklist items for diagrams, maps, science structures, or visual assists. |
| `manual_review_reason` | Why teacher review is required. |
| `unsupported_reason` | Why automated/assist behavior is unsupported. |

### 3.7 Provenance fields

| Field | Meaning |
|---|---|
| `generated_by` | `ai`, `teacher`, `question_bank`, `import`, or equivalent. |
| `source_paper_id` | Original paper if reused or duplicated. |
| `source_question_bank_item_id` | Original question bank item if reused. |
| `grounded` | Whether approved curriculum grounding exists. |
| `grounding_sources` | Curriculum sources/citations used to create or validate the item. |
| `approval_status` | `draft`, `edited`, `pending_approval`, `approved`, `rejected`. |
| `approved_by` | Teacher/incharge/admin approval reference where available. |
| `approved_at` | Approval timestamp where available. |

### 3.8 Evaluation linkage fields

| Field | Meaning |
|---|---|
| `aei_capability_mode` | `supported`, `assist`, `checklist`, `manual_review`, `unsupported`, or `expansion`. |
| `expected_answer_type` | `objective`, `numeric`, `subjective`, `diagram`, `science`, `language`, or equivalent. |
| `teacher_review_required` | Whether human review is required before authority. |
| `evaluation_pipeline` | Must be `AEI` for academic answer evaluation. |
| `approved_evidence_required` | Whether downstream consumers require teacher-approved evidence. |

### 3.9 Support posture fields

| Field | Meaning |
|---|---|
| `support_mode` | `supported`, `assist`, `checklist`, `manual_review`, `unsupported`, or `expansion`. |
| `support_scope_id` | Capability matrix declaration reference. |
| `product_claim_allowed` | Whether the product may claim support in this scope. |
| `fallback_behavior` | `refuse`, `manual_review`, `teacher_only`, or equivalent. |
| `runtime_authority` | Always `teacher_final` for authoritative assessment outcomes. |

---

## 4. Invariants

The following invariants apply to all future implementations:

1. Tenant identity must be derived server-side.
2. Generated papers are non-authoritative until teacher/incharge approval.
3. Reused questions re-enter review when context changes.
4. Answer evaluation must flow through AEI.
5. Unsupported or weakly-supported capability must not be marketed as supported.
6. Parent/student/principal consumers may receive only approved evidence.
7. LLM output may assist but must not become authority without teacher approval.
8. Blueprint, rubric, and support posture must be explicit for supported claims.

---

## 5. Minimal contract example

```json
{
  "tenant_id": "school-uuid",
  "assessment_id": "paper-uuid",
  "question_number": "1",
  "curriculum_pack_id": "pack-uuid",
  "educational_identity_id": "ei://cbse/ncf2023/g6/science/ch05/concept08",
  "board": "CBSE",
  "curriculum": "NCF2023",
  "grade": "6",
  "subject": "Science",
  "paper_type": "unit_test",
  "blueprint_id": "assessment://blueprint/cbse/ncf2023/g6/science/unit-test/v1",
  "section_title": "Section A",
  "question_type": "short",
  "marks": 2,
  "question_text": "Why are standard units important?",
  "answer_key": "Standard units make measurements consistent and comparable.",
  "rubric_posture": "model_answer",
  "grounded": true,
  "approval_status": "approved",
  "aei_capability_mode": "assist",
  "evaluation_pipeline": "AEI",
  "approved_evidence_required": true,
  "support_mode": "supported",
  "runtime_authority": "teacher_final"
}
```

---

## 6. Batch A boundary

Batch A freezes this contract vocabulary only.

It does not require runtime mapping, schema migration, API expansion, UI display,
or source-of-truth switching. Those belong to later authorized batches.
