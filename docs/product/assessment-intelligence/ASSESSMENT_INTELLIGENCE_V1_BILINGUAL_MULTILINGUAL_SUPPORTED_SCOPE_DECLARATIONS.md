# Assessment Intelligence v1.0 Bilingual / Multilingual Supported Scope Declarations

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Batch F foundation
> Authorization: ASSESSMENT-V1-BATCH-F-AUTH-001
> Runtime behavior: Unchanged
> Scope: Static bilingual / multilingual assessment posture declarations

---

## 1. Purpose

This document declares the initial bilingual and multilingual posture for
Assessment Intelligence v1.0.

It is intentionally conservative. StudyNexs may be multilingual over time, but
v1.0 product claims must be complete inside the supported scope rather than
universal.

---

## 2. Declaration summary

| Declaration ID | Posture | Mode | Product claim posture |
|---|---|---|---|
| `assessment-language://supported/english-assessment-contract/v1` | English assessment contract | `supported` | Product claim allowed | Yes, inside this declared scope only |
| `assessment-language://supported/english-grounded-paper/v1` | English grounded paper | `supported` | Product claim allowed | Yes, when Batch A-E readiness requirements are met |
| `assessment-language://supported/english-answer-context/v1` | English answer key, model answer, rubric, checklist context | `supported` | Product claim allowed | Yes, aligned with Batch C posture and teacher authority |
| `assessment-language://manual-review/teacher-authored-bilingual-paper/v1` | Teacher-authored bilingual paper | `manual_review` | Product claim allowed | No |
| `assessment-language://manual-review/ai-assisted-bilingual-draft/v1` | AI-assisted bilingual draft | `manual_review` | Product claim allowed | No |
| `assessment-language://assist/bilingual-rendering-reviewed-content/v1` | Bilingual rendering of reviewed teacher content | `assist` | Product claim allowed | No |
| `assessment-language://assist/aei-hindi-answer-language/v1` | Hindi answer-language assist through AEI | `assist` | Product claim allowed | No |
| `assessment-language://assist/aei-telugu-handwriting-ocr-answer/v1` | Telugu handwriting/OCR answer assist through AEI | `assist` | Product claim allowed | No |
| `assessment-language://assist/code-mixed-answer-input/v1` | Hinglish, Tinglish, or code-mixed answer input | `assist` | Product claim allowed | No |
| `assessment-language://manual-review/local-language-answer-context/v1` | Local-language answer key/model answer without reviewed source | `manual_review` | Product claim allowed | No |
| `assessment-language://unsupported/automatic-question-paper-translation/v1` | Automatic question-paper translation | `unsupported` | Product claim allowed | No |
| `assessment-language://unsupported/automatic-rubric-model-answer-translation/v1` | Automatic rubric/model-answer translation | `unsupported` | Product claim allowed | No |
| `assessment-language://unsupported/universal-multilingual-assessment/v1` | Universal multilingual assessment | `unsupported` | Product claim allowed | No |
| `assessment-language://expansion/telugu-medium-state-board-assessment/v1` | Telugu-medium/state-board assessment packs | `expansion` | Product claim allowed | No |

---

## 3. Supported English scope

### `assessment-language://supported/english-assessment-contract/v1`

| Field | Declaration |
|---|---|
| Support mode | `supported` |
| Assessment language posture | `english_assessment_contract` |
| Primary language | English |
| Secondary language | None |
| Script | Latin |
| Language medium | English |
| Question text language | English |
| Instructions language | English |
| Answer key language | English |
| Model answer language | English |
| Rubric language | English |
| Translation source | `not_applicable` |
| Code-mixed allowed | No |
| AEI language/OCR relationship | Not required |
| Teacher review required | Yes |
| Approved evidence required | Yes |
| Product claim allowed | Yes, inside this declared scope only |
| Runtime behavior change | No |

### `assessment-language://supported/english-grounded-paper/v1`

| Field | Declaration |
|---|---|
| Support mode | `supported` |
| Assessment language posture | `english_grounded_paper` |
| Scope | English grounded papers where Batch A-E requirements are satisfied |
| Translation source | `not_applicable` |
| Teacher review required | Yes |
| Approved evidence required | Yes |
| Product claim allowed | Yes, inside this declared scope only |
| Runtime behavior change | No |

### `assessment-language://supported/english-answer-context/v1`

| Field | Declaration |
|---|---|
| Support mode | `supported` |
| Assessment language posture | `english_answer_context` |
| Scope | English answer keys, model answers, rubrics, and checklists aligned with Batch C |
| Translation source | `not_applicable` |
| Teacher review required | Yes |
| Approved evidence required | Yes |
| Product claim allowed | Yes, inside this declared scope only |
| Runtime behavior change | No |

---

## 4. Manual-review bilingual scope

### `assessment-language://manual-review/teacher-authored-bilingual-paper/v1`

Teacher-authored bilingual content may be stored, reviewed, or used where the
existing workflow already permits teacher-owned content. It is not an automatic
bilingual generation claim.

| Field | Declaration |
|---|---|
| Support mode | `manual_review` |
| Assessment language posture | `teacher_authored_bilingual_review` |
| Translation source | Teacher-authored / teacher-approved |
| Teacher review required | Yes |
| Approved evidence required | Yes |
| Product claim allowed | No |
| Runtime behavior change | No |

### `assessment-language://manual-review/ai-assisted-bilingual-draft/v1`

AI-assisted bilingual drafts are review-only. They must not be treated as
production-authoritative paper content.

| Field | Declaration |
|---|---|
| Support mode | `manual_review` |
| Assessment language posture | `ai_assisted_bilingual_draft_review` |
| Translation source | AI-assisted draft |
| Teacher review required | Yes |
| Approved evidence required | Yes |
| Product claim allowed | No |
| Runtime behavior change | No |

### `assessment-language://assist/bilingual-rendering-reviewed-content/v1`

Bilingual rendering of already-reviewed teacher content is assist-only. It is
not automatic translation authority.

| Field | Declaration |
|---|---|
| Support mode | `assist` |
| Assessment language posture | `bilingual_rendering_assist` |
| Translation source | Already-reviewed teacher content |
| Teacher review required | Yes |
| Approved evidence required | Yes |
| Product claim allowed | No |
| Runtime behavior change | No |

---

## 5. AEI language/OCR assist relationship

These declarations reference AEI language/OCR assist posture. They do not
duplicate AEI, do not change AEI, and do not create assessment-generation
support claims.

| Declaration ID | Support mode | AEI relationship |
|---|---|---|
| `assessment-language://assist/aei-hindi-answer-language/v1` | `assist` | Hindi answer-language assist through AEI where separately certified |
| `assessment-language://assist/aei-telugu-handwriting-ocr-answer/v1` | `assist` | Telugu handwriting/OCR answer assist through AEI where separately certified |
| `assessment-language://assist/code-mixed-answer-input/v1` | `assist` | Hinglish, Tinglish, and code-mixed answer input remains AEI assist / teacher-review posture |

These declarations must not be used to claim:

- bilingual paper generation;
- multilingual paper generation;
- autonomous language grading;
- autonomous marks;
- direct parent visibility;
- direct mastery updates.

---

## 6. Manual-review local-language context

### `assessment-language://manual-review/local-language-answer-context/v1`

Local-language answer keys or model answers without a reviewed source are
manual-review-only.

| Field | Declaration |
|---|---|
| Support mode | `manual_review` |
| Assessment language posture | `local_language_answer_context_review` |
| Translation source | Missing reviewed source |
| Teacher review required | Yes |
| Approved evidence required | Yes |
| Product claim allowed | No |
| Runtime behavior change | No |

---

## 7. Unsupported language claims

The following are explicitly unsupported for Assessment Intelligence v1.0:

- `assessment-language://unsupported/automatic-question-paper-translation/v1`
- `assessment-language://unsupported/automatic-rubric-model-answer-translation/v1`
- `assessment-language://unsupported/universal-multilingual-assessment/v1`

Unsupported declarations must block:

- automatic question-paper translation;
- automatic rubric/model-answer translation;
- universal multilingual assessment generation;
- universal multilingual assessment evaluation;
- autonomous grading;
- autonomous marks;
- direct parent evidence;
- direct mastery updates;
- EUI source-of-truth adoption.

---

## 8. Expansion posture

### `assessment-language://expansion/telugu-medium-state-board-assessment/v1`

Telugu-medium/state-board assessment packs are future expansion.

Future support requires:

- approved CurriculumPack;
- Educational Identity and Context mapping;
- bilingual/multilingual assessment declaration update;
- AEI language/OCR evidence where answers are evaluated;
- teacher-reviewed golden set;
- separate ARM authorization;
- certification before product claims.

---

## 9. Product claim rules

Assessment Intelligence v1.0 may claim:

- English assessment contract support inside declared scope;
- English grounded paper readiness where Batch A-E requirements are met;
- English answer key, model answer, rubric, and checklist posture aligned with
  Batch C;
- teacher-final authority.

Assessment Intelligence v1.0 must not claim:

- universal bilingual assessment generation;
- universal multilingual assessment generation;
- automatic question-paper translation;
- automatic rubric/model-answer translation;
- autonomous language grading;
- autonomous marks;
- parent/student visibility before approved evidence;
- mastery updates before approved marks and evidence.
