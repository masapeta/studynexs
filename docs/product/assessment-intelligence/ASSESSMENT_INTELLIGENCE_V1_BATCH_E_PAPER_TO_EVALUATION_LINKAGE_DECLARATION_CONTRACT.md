# Assessment Intelligence v1.0 Batch E Paper-to-Evaluation Linkage Declaration Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Batch E foundation
> Authorization: ASSESSMENT-V1-BATCH-E-AUTH-001
> Runtime behavior: Unchanged
> Scope: Paper-to-evaluation linkage declaration contract only

---

## 1. Purpose

This document defines the static paper-to-evaluation linkage declaration
contract for Assessment Intelligence v1.0.

Paper-to-evaluation linkage declarations describe whether an approved question
paper, exam question schema, answer-input method, rubric context, AEI assist,
teacher review, evidence, marks, and mastery path are evaluation-ready.

They do not approve marks, publish evidence, update mastery, route teacher
review, change answer-sheet evaluation behavior, or change runtime behavior.

---

## 2. Contract principle

Linkage creates readiness, not authority.

```text
Approved Question Paper
        |
        v
Exam Question Schema
        |
        v
AEI Evaluation Assist
        |
        v
Teacher Review and Approval
        |
        v
Approved Evidence / Marks / Mastery
```

The linked paper and question schema define which academic context may be used
for evaluation assist. Teachers remain the final authority for marks and
downstream evidence.

AEI remains the only academic answer-evaluation pipeline.

---

## 3. Declaration identity

Each declaration must have a stable `linkage_declaration_id`.

Recommended ID shape:

```text
assessment-linkage://<scope>/<posture>/<version>
```

Examples:

```text
assessment-linkage://same-tenant/approved-paper-schema/v1
assessment-linkage://same-tenant/source-paper-schema-evaluation-ready/v1
assessment-linkage://unsupported/cross-tenant-source-paper/v1
```

Names may change over time. Stable IDs should not change for the same declared
linkage posture.

---

## 4. Declaration fields

| Field | Required | Purpose |
|---|---:|---|
| `linkage_declaration_id` | Yes | Stable linkage posture identifier. |
| `support_mode` | Yes | Supported, assist, manual review, unsupported, or expansion. |
| `linkage_posture` | Yes | Specific paper-to-evaluation posture. |
| `school_id` | Yes | Tenant boundary, always server-derived. |
| `exam_id` | Conditional | Concrete linked exam when available. |
| `source_paper_id` | Conditional | Source paper used for schema or evaluation context. |
| `source_paper_status` | Yes | Approved, draft, rejected, unsupported, or future equivalent. |
| `question_schema_source` | Yes | Approved paper, manual, unsupported, or future equivalent. |
| `question_schema_required` | Yes | Whether a question schema is required for this posture. |
| `source_paper_required` | Yes | Whether a source paper is required for this posture. |
| `question_numbers_unique` | Conditional | Required for concrete schema validation. |
| `max_marks_preserved` | Conditional | Whether source max marks are preserved into schema. |
| `topic_posture` | Where available | Topic linkage posture. |
| `concept_posture` | Where available | Concept linkage posture. |
| `educational_identity_posture` | Where available | EUI identity availability or deferral. |
| `rubric_source` | Where available | Source of rubric, model answer, answer key, or checklist context. |
| `rubric_available` | Yes | Whether Batch C answer context exists. |
| `can_evaluate_sheets` | Yes | Whether evaluation assist readiness is declared. |
| `ocr_input_allowed` | Yes | Whether OCR may be used as input assist. |
| `manual_input_allowed` | Yes | Whether manual answer input may be used. |
| `input_authority` | Yes | Must distinguish input capture from marks authority. |
| `aei_assist_allowed` | Yes | Whether AEI may produce non-authoritative suggestions. |
| `teacher_review_required` | Yes | Must remain true before marks/evidence authority. |
| `approved_evidence_required` | Yes | Must remain true before downstream consumption. |
| `marks_source` | Yes | Expected source of authoritative marks. |
| `mastery_source` | Yes | Expected source of authoritative mastery evidence. |
| `product_claim_allowed` | Yes | Whether StudyNexs may claim support for this posture. |
| `runtime_behavior_change` | Yes | Must be false for Batch E. |

---

## 5. Linkage postures

| Posture | Meaning |
|---|---|
| `approved_paper_schema` | Approved same-tenant paper can define exam question schema. |
| `source_paper_schema_evaluation_ready` | Exam has source paper and question schema. |
| `linked_rubric_context` | Rubric/model-answer context is fetched through the linked source paper. |
| `ocr_input_assist` | OCR may provide answer input but cannot become marks authority. |
| `manual_input_assist` | Manual transcription may provide answer input but cannot become marks authority. |
| `manual_schema_review` | Exam has manual schema without approved paper and requires manual review posture. |
| `unsupported_linkage` | Requested linkage violates support or governance boundaries. |
| `future_expansion` | Future roadmap posture only. |

---

## 6. Support modes

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared scope. |
| `assist` | System may assist, but teacher review and approval remain required. |
| `manual_review` | Human review is required before any downstream authority. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future scope only. |

Supported linkage means the source paper, schema, and context path are declared
and validated. It does not mean marks, evidence, or mastery are automatically
approved.

---

## 7. Deterministic validation rules

Paper-to-evaluation linkage validation must be deterministic and non-runtime in
Batch E.

Required checks:

1. `linkage_declaration_id` is stable and unique.
2. `support_mode` is known.
3. `linkage_posture` is known.
4. Tenant/school scope is explicit and server-derived.
5. Supported schema linkage requires an approved source paper.
6. Same-tenant linkage is the only supported source-paper scope.
7. Cross-tenant source papers are unsupported.
8. Draft or unapproved source papers are unsupported.
9. Source paper lineage is required for evaluation readiness.
10. Question schema is required for evaluation readiness.
11. Question numbers must be unique when a concrete schema is validated.
12. Source max marks posture must be explicit.
13. Rubric/model-answer context must be sourced from the linked paper.
14. OCR input must be represented as input assist only.
15. Manual answer input must be represented as input assist only.
16. AEI suggestions remain non-authoritative.
17. Teacher review remains required before authority.
18. Approved evidence remains required before downstream consumption.
19. Marks source remains teacher-approved decision.
20. Mastery source remains approved marks/evidence.
21. Product claims are blocked for non-supported modes.
22. `runtime_behavior_change` remains false.

---

## 8. Batch E invariants

1. Paper-to-evaluation linkage declarations are read-only artifacts.
2. Declarations do not change runtime exam or evaluation behavior.
3. Product claims are allowed only for declared supported postures.
4. Approved paper linkage creates evaluation readiness, not marks authority.
5. OCR and manual transcription are input mechanisms, not marking engines.
6. AEI suggestions remain non-authoritative until teacher approval.
7. Teacher approval remains the point where marks and evidence become
   authoritative.
8. Parent, student, principal, and learning consumers receive only approved
   evidence.
9. AEI remains the only academic answer-evaluation pipeline.
10. EUI remains unchanged and is not switched to source-of-truth in Batch E.
11. Batch E introduces no schema, API, UI, feature flag, or runtime behavior
    change.

---

## 9. Minimal declaration example

```json
{
  "linkage_declaration_id": "assessment-linkage://same-tenant/source-paper-schema-evaluation-ready/v1",
  "support_mode": "supported",
  "linkage_posture": "source_paper_schema_evaluation_ready",
  "school_id": "server-derived",
  "source_paper_required": true,
  "source_paper_status": "approved",
  "question_schema_source": "approved_paper",
  "question_schema_required": true,
  "question_numbers_unique": true,
  "max_marks_preserved": true,
  "rubric_source": "linked_source_paper",
  "rubric_available": true,
  "can_evaluate_sheets": true,
  "ocr_input_allowed": true,
  "manual_input_allowed": true,
  "input_authority": "input_capture_only",
  "aei_assist_allowed": true,
  "teacher_review_required": true,
  "approved_evidence_required": true,
  "marks_source": "teacher_approved_decision",
  "mastery_source": "approved_marks_and_evidence",
  "product_claim_allowed": true,
  "runtime_behavior_change": false
}
```

---

## 10. Batch E boundary

This contract defines paper-to-evaluation linkage declarations only.

It does not authorize runtime paper-to-evaluation behavior changes, exam service
changes, answer-sheet evaluation service changes, teacher approval changes,
schema changes, API changes, UI changes, feature flags, source switching,
autonomous grading, evidence-ledger behavior changes, mastery updates, EUI
source adoption, or product claim expansion.
