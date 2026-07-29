# Assessment Intelligence v1.0 Batch D Question Bank and Reuse Declaration Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Batch D foundation
> Authorization: ASSESSMENT-V1-BATCH-D-AUTH-001
> Runtime behavior: Unchanged
> Scope: Question-bank and reuse declaration contract only

---

## 1. Purpose

This document defines the static question-bank and reuse declaration contract
for Assessment Intelligence v1.0.

Question-bank reuse declarations describe source, suitability, approval lineage,
and reuse posture. They do not approve a question for a new paper, grade student
answers, publish evidence, update mastery, or change runtime behavior.

---

## 2. Contract principle

Previous approval is provenance, not authority.

```text
Approved Question Paper
        |
        v
School-Private Question Bank
        |
        v
Question Reuse Declaration
        |
        v
Draft Question Paper
        |
        v
Teacher Review and Approval
```

The bank stores approved school-private assets. Reuse declarations make those
assets auditable. Teachers remain final authority for each new paper context.

AEI remains the only academic answer-evaluation pipeline.

---

## 3. Declaration identity

Each declaration must have a stable `reuse_declaration_id`.

Recommended ID shape:

```text
assessment-bank-reuse://<scope>/<posture>/<version>
```

Examples:

```text
assessment-bank-reuse://school-private/approved-paper-ingestion/v1
assessment-bank-reuse://school-private/blueprint-slot-compose/v1
assessment-bank-reuse://unsupported/cross-tenant-reuse/v1
```

Names may change over time. Stable IDs should not change for the same declared
reuse posture.

---

## 4. Declaration fields

| Field | Required | Purpose |
|---|---:|---|
| `reuse_declaration_id` | Yes | Stable reuse posture identifier. |
| `support_mode` | Yes | Supported, assist, manual review, unsupported, or expansion. |
| `bank_item_id` | Conditional | Stable reusable question identifier when a concrete bank item is referenced. |
| `source_paper_id` | Conditional | Original approved paper that created the bank item. |
| `source_question_bank_item_id` | Conditional | Source bank item when reused into a new draft paper. |
| `school_id` | Yes | Tenant boundary, always server-derived. |
| `class_id` | Where available | Class scope. |
| `subject_id` | Where available | Subject scope. |
| `board` | Where available | Board scope. |
| `grade` | Where available | Grade scope. |
| `topics` | Where available | Topic tags carried from source or target context. |
| `concepts` | Where available | Concept links where available. |
| `educational_identity_id` | Where available | Canonical EUI identity when resolved. |
| `section_title` | Where available | Source or target section title. |
| `question_number` | Where available | Source or target question number. |
| `question_text` | Conditional | Required when validating a concrete question. |
| `marks` | Conditional | Required when validating blueprint-slot suitability. |
| `question_type` | Conditional | Required when validating blueprint-slot suitability. |
| `options` | Optional | MCQ options where applicable. |
| `source` | Yes | AI, teacher, previous paper, or composed. |
| `approval_status` | Yes | Approved, draft, rejected, unsupported, or future equivalent. |
| `approved_by` | Conditional | Required for approved source posture where available. |
| `approved_at` | Conditional | Required for approved source posture where available. |
| `content_fingerprint` | Conditional | Stable content hash for concrete question provenance. |
| `usage_count` | Optional | Operational reuse count. |
| `used_in_paper_ids` | Optional | Papers where the item has been used. |
| `answer_context_available` | Yes | Whether answer key/model/rubric/checklist context exists. |
| `rubric_posture` | Where available | Batch C answer-context posture. |
| `blueprint_slot_id` | Where available | Target blueprint slot. |
| `marks_match` | Conditional | Whether item marks match the target slot. |
| `type_match` | Conditional | Whether item type matches the target slot. |
| `topic_overlap` | Optional | Topic/concept overlap evidence. |
| `gap_fill_provenance` | Conditional | Required when a question is generated to fill a bank gap. |
| `reuse_review_required` | Yes | Must be true before authority. |
| `evaluation_pipeline` | Yes | Must be `AEI` for answer evaluation. |
| `approved_evidence_required` | Yes | Must be true before downstream consumption. |
| `product_claim_allowed` | Yes | Whether StudyNexs may claim support for the posture. |
| `runtime_behavior_change` | Yes | Must be false for Batch D. |

---

## 5. Reuse postures

| Posture | Meaning |
|---|---|
| `approved_paper_ingestion` | Approved paper is split into reusable bank items. |
| `idempotent_reapproval` | Re-approval replaces prior bank rows for the same paper. |
| `same_school_reuse` | Approved item is reused within the same school/class/subject scope. |
| `blueprint_slot_compose` | Approved item is selected for a matching blueprint slot. |
| `gap_fill_assist` | Generation fills a missing bank slot and remains visibly non-bank. |
| `changed_context_review` | Reuse in a changed context requires teacher review. |
| `unsupported_reuse` | Requested reuse violates support or governance boundaries. |
| `future_expansion` | Future roadmap posture only. |

---

## 6. Support modes

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared school-private scope. |
| `assist` | System may help compose or gap-fill, but teacher review remains required. |
| `manual_review` | Teacher must approve suitability before authority. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future scope only. |

Supported reuse means provenance and suitability are declared and validated. It
does not mean a reused question is automatically approved in a new paper.

---

## 7. Deterministic validation rules

Question-bank reuse validation must be deterministic and non-runtime in Batch D.

Required checks:

1. `reuse_declaration_id` is stable and unique.
2. `support_mode` is known.
3. `reuse_posture` is known.
4. Tenant/school scope is explicit and server-derived.
5. Supported reuse requires approved source posture.
6. Same-school reuse is the only supported reuse scope.
7. Cross-tenant reuse is unsupported.
8. Draft or unapproved bank item reuse is unsupported.
9. Source paper lineage is required when the source is an approved paper.
10. Source bank item lineage is required when a bank item is reused.
11. `content_fingerprint` posture is explicit for concrete questions.
12. Blueprint compose support requires marks and type match posture.
13. Gap-fill provenance is distinguishable from bank reuse.
14. Changed-context reuse requires teacher review.
15. Product claims are blocked for non-supported modes.
16. `reuse_review_required` remains true.
17. `evaluation_pipeline` remains `AEI`.
18. `approved_evidence_required` remains true.

---

## 8. Batch D invariants

1. Question-bank/reuse declarations are read-only artifacts.
2. Question-bank/reuse declarations do not change runtime question-bank behavior.
3. Product claims are allowed only for declared supported postures.
4. Previous approval remains provenance, not authority.
5. Draft papers remain draft until teacher approval.
6. Cross-school/global/marketplace reuse is not a v1.0 supported claim.
7. Gap-fill questions must not be represented as approved bank reuse.
8. Teachers remain the final authority for paper approval.
9. AEI remains the only academic answer-evaluation pipeline.
10. Parent/student/principal consumers receive only approved evidence.
11. Batch D introduces no schema, API, UI, feature flag, or runtime behavior
    change.

---

## 9. Minimal declaration example

```json
{
  "reuse_declaration_id": "assessment-bank-reuse://school-private/blueprint-slot-compose/v1",
  "support_mode": "supported",
  "reuse_posture": "blueprint_slot_compose",
  "school_id": "server-derived",
  "class_id": "available-when-concrete",
  "subject_id": "available-when-concrete",
  "source_paper_id": "required-when-concrete",
  "source_question_bank_item_id": "required-when-reused",
  "approval_status": "approved",
  "source": "previous_paper",
  "marks_match": true,
  "type_match": true,
  "answer_context_available": true,
  "gap_fill_provenance": "not_gap_fill",
  "reuse_review_required": true,
  "evaluation_pipeline": "AEI",
  "approved_evidence_required": true,
  "product_claim_allowed": true,
  "runtime_behavior_change": false
}
```

---

## 10. Batch D boundary

This contract defines question-bank and reuse declarations only.

It does not authorize runtime question-bank behavior changes, question-paper
generation changes, paper approval changes, schema changes, API changes, UI
changes, feature flags, source switching, autonomous approval, autonomous
grading, cross-school marketplace reuse, or product claim expansion.
