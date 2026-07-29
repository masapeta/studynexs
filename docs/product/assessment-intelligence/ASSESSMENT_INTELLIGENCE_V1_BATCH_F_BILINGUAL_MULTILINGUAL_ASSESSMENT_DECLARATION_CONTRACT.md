# Assessment Intelligence v1.0 Batch F Bilingual / Multilingual Assessment Declaration Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Batch F foundation
> Authorization: ASSESSMENT-V1-BATCH-F-AUTH-001
> Runtime behavior: Unchanged
> Scope: Bilingual / multilingual assessment declaration contract only

---

## 1. Purpose

This contract defines the static declaration shape used to describe bilingual
and multilingual assessment readiness for Assessment Intelligence v1.0.

It exists to prevent product overclaiming.

Batch F does not translate papers, grade multilingual answers, execute OCR,
render multilingual papers, or change any production workflow. It declares the
language posture that future implementation and product claims must respect.

---

## 2. Core principle

Assessment language posture is readiness metadata, not translation authority.

An assessment language declaration may say:

- a scenario is supported inside a declared scope;
- a scenario is assist-only;
- a scenario requires manual review;
- a scenario is unsupported;
- a scenario is future expansion.

It must not imply autonomous paper approval, autonomous language grading,
automatic translation, parent-visible evidence, mastery updates, marks changes,
or AEI bypass.

---

## 3. Stable identifier pattern

Every declaration uses a stable identifier:

```text
assessment-language://<support-mode>/<posture>/<version>
```

Examples:

```text
assessment-language://supported/english-assessment-contract/v1
assessment-language://manual-review/teacher-authored-bilingual-paper/v1
assessment-language://unsupported/universal-multilingual-assessment/v1
```

Names and labels may change. Declaration identifiers should remain stable unless
the underlying supported scope changes.

---

## 4. Supported modes

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared scope only. |
| `assist` | System may assist, but teacher review and cautious product language remain required. |
| `manual_review` | Teacher-only authority; the system may record that review is required. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future roadmap candidate; no v1.0 product claim. |

---

## 5. Assessment language postures

| Posture | Mode | Meaning |
|---|---|---|
| `english_assessment_contract` | `supported` | English is the current assessment contract baseline for declared v1.0 scope. |
| `english_grounded_paper` | `supported` | English grounded paper readiness where earlier Assessment batches are satisfied. |
| `english_answer_context` | `supported` | English answer key, model answer, rubric, and checklist context follows Batch C posture. |
| `teacher_authored_bilingual_review` | `manual_review` | Teacher-authored bilingual paper content requires teacher review and approval. |
| `ai_assisted_bilingual_draft_review` | `manual_review` | AI-assisted bilingual draft content is review-only and not production-authoritative. |
| `bilingual_rendering_assist` | `assist` | Rendering already-reviewed teacher content in bilingual form is assist-only. |
| `aei_language_answer_assist` | `assist` | AEI language/OCR may assist answer understanding where separately certified. |
| `code_mixed_answer_assist` | `assist` | Hinglish, Tinglish, or code-mixed answer input remains AEI assist / teacher-review posture. |
| `local_language_answer_context_review` | `manual_review` | Local-language answer keys or model answers without reviewed source require teacher review. |
| `unsupported_translation` | `unsupported` | Automatic translation of question papers, rubrics, or model answers is unsupported. |
| `unsupported_multilingual` | `unsupported` | Universal multilingual assessment generation/evaluation is unsupported. |
| `future_expansion` | `expansion` | Future Telugu-medium, state-board, or other multilingual assessment packs. |

---

## 6. Required declaration fields

Every declaration should include:

- `language_declaration_id`
- `support_mode`
- `assessment_language_posture`
- `school_id`
- `board`
- `curriculum`
- `curriculum_version`
- `grade`
- `subject`
- `paper_type`
- `primary_language`
- `secondary_language`
- `script`
- `language_medium`
- `question_text_language`
- `instructions_language`
- `answer_key_language`
- `model_answer_language`
- `rubric_language`
- `translation_source`
- `code_mixed_allowed`
- `aei_language_ocr_posture`
- `teacher_review_required`
- `approved_evidence_required`
- `product_claim_allowed`
- `runtime_behavior_change`

Optional metadata may include:

- `notes`
- `unsupported_reason`
- `expansion_trigger`
- `source_batches`
- `review_posture`

---

## 7. Deterministic validation rules

Language readiness validation must be deterministic.

Minimum invariants:

1. `language_declaration_id` must be stable and unique.
2. `support_mode` must be one of the declared support modes.
3. `assessment_language_posture` must map to the declared support mode.
4. `supported` declarations must include explicit board, curriculum, grade,
   subject, paper type, and language scope.
5. English support must not imply bilingual or universal multilingual support.
6. `manual_review`, `assist`, `unsupported`, and `expansion` declarations must
   not permit unrestricted product claims.
7. Automatic translation must remain unsupported unless separately authorized
   and certified.
8. AEI language/OCR assist must be referenced, not duplicated.
9. Teacher authority remains required for consequential assessment outcomes.
10. Approved evidence is required before parent/student visibility.
11. Batch F declarations must not change runtime behavior.

---

## 8. AEI relationship

AEI remains the only academic answer-evaluation pipeline.

Batch F may reference AEI language/OCR assist posture, but it must not:

- duplicate AEI language/OCR logic;
- alter AEI marks;
- alter AEI confidence or manual-review routing;
- alter teacher review;
- alter approved evidence behavior;
- authorize autonomous language grading.

Assessment language declarations describe assessment-readiness posture only.

---

## 9. Example declaration

```json
{
  "language_declaration_id": "assessment-language://supported/english-assessment-contract/v1",
  "support_mode": "supported",
  "assessment_language_posture": "english_assessment_contract",
  "school_id": "declared-tenant-scope",
  "board": "CBSE",
  "curriculum": "NCF2023",
  "curriculum_version": "v1",
  "grade": "6",
  "subject": "Science",
  "paper_type": "unit_test",
  "primary_language": "English",
  "secondary_language": null,
  "script": "Latin",
  "language_medium": "English",
  "question_text_language": "English",
  "instructions_language": "English",
  "answer_key_language": "English",
  "model_answer_language": "English",
  "rubric_language": "English",
  "translation_source": "not_applicable",
  "code_mixed_allowed": false,
  "aei_language_ocr_posture": "not_required",
  "teacher_review_required": true,
  "approved_evidence_required": true,
  "product_claim_allowed": true,
  "runtime_behavior_change": false
}
```

---

## 10. Batch F boundary

This contract is a static readiness artifact.

It does not authorize:

- runtime execution;
- feature flags;
- database changes;
- API changes;
- UI changes;
- question-paper generation changes;
- translation changes;
- OCR changes;
- LLM calls;
- marks changes;
- evidence-ledger changes;
- mastery updates;
- parent/student visibility changes.
