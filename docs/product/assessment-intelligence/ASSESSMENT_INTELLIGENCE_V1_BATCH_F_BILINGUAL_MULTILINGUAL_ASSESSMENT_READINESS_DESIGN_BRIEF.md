# Assessment Intelligence v1.0 Batch F Design Brief

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Program: Assessment Intelligence v1.0
> Batch: F - Bilingual / Multilingual Assessment Readiness
> Status: Accepted
> Classification: Product implementation design
> Implementation: Not authorized
> Runtime behavior changes: Not authorized by this document
> Previous baseline: Batch E - Paper-to-Evaluation Linkage Readiness
> ARM review: Accepted as the Batch F Bilingual / Multilingual Assessment Readiness design baseline

---

## 1. Purpose

Batch F should make Assessment Intelligence language posture explicit,
reviewable, and honest.

It answers:

> Which assessment-language scenarios may StudyNexs claim as supported, which
> are assist-only or teacher-review-only, and how do we prevent bilingual or
> multilingual convenience from becoming an unsupported product promise?

This document is design-only. It does not authorize implementation.

---

## 2. Why Batch F exists

Assessment Intelligence v1.0 Batch A established the canonical assessment
contract and a conservative supported-scope capability matrix.

Batch B made blueprint readiness explicit.

Batch C made rubric and model-answer readiness explicit.

Batch D made question-bank reuse explicit and provenance-backed.

Batch E made approved-paper-to-evaluation linkage explicit.

Batch F is the next dependency because schools often need assessment workflows
across English, local-language, bilingual, and code-mixed classroom contexts.
StudyNexs must support this honestly:

- English assessment contracts can be supported where already certified.
- Bilingual or multilingual paper generation must not be implied as universal.
- Teacher-authored local-language or bilingual material needs review posture.
- Answer keys, rubrics, model answers, and evaluation context need language
  posture too, not only question text.
- AEI language/OCR assist can help evaluation, but it does not certify
  multilingual assessment generation.

Without Batch F, assessment language support could drift into accidental claims
such as "universal bilingual generation" or "automatic multilingual grading."

---

## 3. Repository foundations to reuse

Batch F should extend existing Assessment, AEI, and EUI language foundations
rather than creating a separate multilingual assessment system.

Relevant foundations include:

- `ASSESSMENT_INTELLIGENCE_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`;
- Assessment Intelligence Batch A-E contracts and supported-scope declarations;
- `apps/api/app/modules/eui/registry/platform_capability_registry.v1.json`;
- `apps/api/app/modules/eui/schemas/platform_capability.py`;
- `apps/api/app/modules/eui/schemas/educational_context.py`;
- `apps/api/app/modules/eui/schemas/trust_report.py`;
- `apps/api/app/modules/examinations/schemas/academic_answer.py`;
- `apps/api/app/modules/examinations/services/academic_understanding_engine.py`;
- `apps/api/app/modules/examinations/services/aei_v1_language_ocr_assist.py`;
- AEI v1.0 Batch D Language/OCR Assist metadata;
- Teacher Evaluation UX-D language/OCR assist display baseline.

Relevant current posture includes:

- English is the declared supported language for the initial assessment
  contract;
- bilingual paper generation is currently `manual_review` in the capability
  matrix;
- universal multilingual assessment is currently `unsupported`;
- AEI can attach language/OCR assist metadata for selected evaluation scenarios;
- EUI can represent language medium, detected language, and language confidence
  in related contracts;
- teachers remain final authority for consequential assessment outputs.

Batch F should document and test the posture first. Runtime behavior changes
require a later implementation authorization.

---

## 4. Product outcome

After Batch F is eventually implemented and certified, StudyNexs should be able
to say:

> For the declared supported scope, assessment language posture is explicit:
> English assessment contracts are supported, bilingual/local-language scenarios
> are routed through declared assist or manual-review modes, and universal
> multilingual assessment is not claimed.

Teachers should know whether a paper, answer key, rubric, model answer, or
evaluation context is:

- supported in the declared assessment language;
- assistive but teacher-review required;
- manual-review only;
- unsupported;
- future expansion.

---

## 5. Design principle

Language posture is part of assessment readiness, not a decoration.

```text
Curriculum Language / School Medium
        |
        v
Question Paper Language Posture
        |
        v
Answer Key / Rubric Language Posture
        |
        v
Evaluation Language Assist
        |
        v
Teacher Review and Approval
```

A paper can be structurally valid but still not production-ready for a claimed
language posture. Conversely, teacher-entered bilingual content can be useful
without becoming an AI-certified bilingual generation claim.

---

## 6. Relationship to earlier Assessment Intelligence batches

Batch F should consume earlier Assessment Intelligence contracts instead of
redefining them.

### Batch A fields

Language posture should preserve or reference:

- `assessment_id`;
- `paper_id`;
- `school_id`;
- `board`;
- `curriculum`;
- `grade`;
- `subject`;
- `paper_type`;
- `language`;
- `language_medium`;
- `product_claim_allowed`;
- `teacher_review_required`;
- `approved_evidence_required`.

### Batch B fields

Blueprint readiness should remain language-aware:

- `blueprint_id`;
- section instructions language;
- printed language posture;
- bilingual rendering posture;
- answer-required marks versus printed marks;
- internal-choice instructions.

### Batch C fields

Rubric and model-answer readiness should declare:

- answer-key language;
- model-answer language;
- acceptable-answer language variants;
- rubric criteria language;
- checklist language;
- translation posture;
- manual-review reason when language context is weak.

### Batch D fields

Question-bank reuse should preserve:

- source question language posture;
- target paper language posture;
- changed-language context review;
- gap-fill language provenance;
- reuse review requirement.

### Batch E fields

Paper-to-evaluation linkage should preserve:

- linked paper language posture;
- exam schema language posture;
- OCR/manual input language posture;
- AEI language/OCR assist posture;
- approved evidence language posture.

---

## 7. Bilingual / multilingual declaration model

A bilingual/multilingual assessment declaration should describe language support
posture without generating, translating, evaluating, or approving content.

Minimum declaration fields:

| Field | Purpose |
|---|---|
| `language_declaration_id` | Stable language posture identifier. |
| `support_mode` | Supported, assist, manual review, unsupported, or expansion. |
| `assessment_language_posture` | Specific language posture. |
| `school_id` | Tenant boundary, derived server-side only. |
| `board` | Board scope. |
| `curriculum` | Curriculum family/version. |
| `grade` | Grade scope. |
| `subject` | Subject scope. |
| `paper_type` | Unit test, slip test, term exam, practice, or equivalent. |
| `primary_language` | Primary paper language. |
| `secondary_language` | Secondary language when bilingual. |
| `script` | Script posture where relevant. |
| `language_medium` | School/class/section medium where available. |
| `question_text_language` | Language posture for question text. |
| `instructions_language` | Language posture for paper and section instructions. |
| `answer_key_language` | Language posture for answer keys. |
| `model_answer_language` | Language posture for model answers. |
| `rubric_language` | Language posture for rubrics/checklists. |
| `translation_source` | Teacher, approved pack, AI assist, unsupported, or future. |
| `code_mixed_allowed` | Whether code-mixed text is expected or review-only. |
| `aei_language_ocr_posture` | Relationship to AEI language/OCR assist. |
| `teacher_review_required` | Whether teacher review is required before authority. |
| `approved_evidence_required` | Whether downstream evidence must wait for approval. |
| `product_claim_allowed` | Whether the product may claim support. |
| `runtime_behavior_change` | Must be false for Batch F. |

---

## 8. Support modes

Batch F should use explicit support modes instead of implying universal language
coverage.

| Mode | Meaning |
|---|---|
| `supported` | Product may claim support inside the declared language scope. |
| `assist` | System may assist, but teacher review remains required and product claims must be cautious. |
| `manual_review` | Teacher-only authority; no production support claim beyond review workflow. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future roadmap candidate, not v1.0 claim. |

---

## 9. Initial language posture

Batch F should begin conservatively.

| Scenario | Posture |
|---|---|
| English assessment contract for declared supported scopes | `supported` |
| English question paper from approved CurriculumPack for declared supported scopes | `supported` when earlier generation/readiness requirements are met |
| English answer keys, model answers, and rubrics for declared supported scopes | `supported` or `assist` according to Batch C posture |
| Teacher-authored bilingual paper content | `manual_review` |
| AI-assisted bilingual draft generation | `manual_review` / no production claim |
| Bilingual paper rendering from already-reviewed teacher content | `assist` until browser/product proof exists |
| Hindi/Telugu/Sanskrit answer-language detection during evaluation | AEI `assist` or `manual_review`, not Assessment generation support |
| Hinglish/Tinglish/code-mixed answer input | AEI `assist` / teacher review only |
| Local-language answer key or model answer without reviewed source | `manual_review` |
| Automatic translation of question papers | `unsupported` for v1.0 |
| Automatic translation of rubrics/model answers | `unsupported` for v1.0 |
| Universal multilingual assessment generation | `unsupported` |
| Future Telugu-medium/state-board assessment packs | `expansion` |

---

## 10. Deterministic validation expectations

Batch F should define deterministic validation rules for language readiness.

At minimum:

- language declarations must have stable IDs;
- support modes must be explicit;
- supported claims must name board, curriculum, grade, subject, paper type, and
  language;
- English supported posture must not imply bilingual support;
- bilingual/manual-review posture must not allow production support claims;
- unsupported universal multilingual declarations must block product claims;
- question text, instructions, answer keys, model answers, and rubrics must have
  separate language posture;
- translation source must be explicit where translation is claimed or assisted;
- code-mixed answer posture must route to AEI language/OCR assist or teacher
  review, not automatic assessment-language authority;
- approved evidence remains required before downstream consumption;
- teacher review remains required for assist and manual-review modes.

---

## 11. Relationship to AEI language/OCR assist

Batch F must not duplicate AEI language/OCR logic.

AEI language/OCR assist answers:

> What language/script/input uncertainty exists in a student's answer?

Assessment Batch F answers:

> What language posture is safe to claim for question papers, answer keys,
> rubrics, model answers, and paper-to-evaluation context?

The relationship should remain:

```text
Assessment Language Posture
        |
        v
Question / Rubric / Paper Context
        |
        v
AEI Language/OCR Assist for Student Answers
        |
        v
Teacher Review
```

AEI may help inspect student answer language. It must not be used as proof that
Assessment Intelligence supports bilingual paper generation.

---

## 12. Current runtime migration posture

Existing runtime behavior should remain unchanged during Batch F.

Current useful posture includes:

- Assessment Batch A capability matrix already declares English as the initial
  supported assessment language;
- bilingual generation is already marked manual-review in the capability
  matrix;
- universal multilingual assessment is already unsupported;
- AEI Batch D language/OCR assist metadata exists for evaluation suggestions;
- Teacher Evaluation UX-D can display language/OCR assist metadata when present.

Batch F should turn this into a declared, testable Assessment Intelligence
language foundation before any product-facing multilingual claim is made.

---

## 13. Recommended future implementation scope

The future Batch F implementation authorization should remain narrow.

Recommended authorized scope:

- bilingual/multilingual assessment declaration contract;
- static supported-scope language declarations;
- deterministic Golden Harness language-readiness cases;
- focused static tests validating language posture and no overclaiming;
- certification report.

The implementation should remain non-runtime. It should not add translation,
paper rendering, OCR, LLM inference, or evaluation behavior.

---

## 14. Explicit exclusions

Batch F design does not authorize:

- runtime behavior changes;
- database schema changes;
- API changes;
- UI changes;
- feature flags;
- translation engine integration;
- new OCR behavior;
- LLM inference;
- provider changes;
- prompt changes;
- bilingual paper generation behavior changes;
- multilingual paper rendering behavior changes;
- answer-sheet evaluation behavior changes;
- AEI language/OCR behavior changes;
- autonomous language grading;
- marks changes;
- teacher-review routing changes;
- evidence-ledger behavior changes;
- mastery-source changes;
- parent/student/principal visibility changes;
- public bilingual/multilingual product claim expansion;
- Assessment Intelligence Batch G browser proof.

---

## 15. Golden Harness expectations

Batch F Golden Harness cases should validate language posture.

Minimum scenarios:

- English assessment contract supported for declared scope;
- English grounded paper posture supported where earlier requirements are met;
- English answer-key/model-answer/rubric posture aligned with Batch C;
- teacher-authored bilingual paper manual-review posture;
- AI-assisted bilingual draft manual-review posture;
- bilingual rendering assist posture only;
- Hindi language-answer evaluation assist relationship to AEI;
- Telugu handwriting/OCR answer assist relationship to AEI;
- Hinglish/Tinglish/code-mixed answer assist posture;
- local-language answer key without reviewed source manual-review posture;
- automatic question-paper translation unsupported;
- automatic rubric/model-answer translation unsupported;
- universal multilingual assessment unsupported;
- future Telugu-medium/state-board assessment expansion posture.

---

## 16. Observability expectations

If Batch F later introduces runtime helpers, operational observability should
measure language-posture health rather than educational outcomes.

Useful future metrics include:

- `assessment_language_posture.invoked`;
- `assessment_language_posture.completed`;
- `assessment_language_posture.unsupported`;
- `assessment_language_posture.manual_review`;
- `assessment_language_posture.duration`.

Logs should avoid student PII and must not include raw answer text.

---

## 17. Certification criteria

Batch F should not be accepted until it can demonstrate:

- bilingual/multilingual assessment declaration contract exists;
- static language supported-scope declarations exist;
- support modes are explicit;
- English supported posture is declared without implying universal support;
- bilingual/manual-review posture blocks production claims;
- universal multilingual assessment is explicitly unsupported;
- AEI language/OCR assist relationship is declared without duplication;
- Golden Harness cases validate supported, assist, manual-review, unsupported,
  and expansion scenarios;
- no schema, API, UI, runtime, AEI language/OCR, or evidence-ledger behavior
  changes were introduced unless separately authorized;
- existing Assessment Intelligence Batch A-E tests continue to pass;
- existing AEI language/OCR assist regression slice continues to pass;
- certification report is completed.

---

## 18. ARM gate

This design brief may be accepted as the Batch F Bilingual / Multilingual
Assessment Readiness design baseline.

Acceptance of this brief does not authorize implementation.

The next artifact should be:

```text
docs/product/assessment-intelligence/
ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

That contract should define the exact repository boundary, permitted artifacts,
validation commands, Golden Harness additions, rollback posture, and
certification evidence before any Batch F implementation begins.
