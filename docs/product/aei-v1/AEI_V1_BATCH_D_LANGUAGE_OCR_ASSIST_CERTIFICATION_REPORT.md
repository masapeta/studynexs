# AEI v1.0 Batch D Certification Report - Language/OCR Assist

- **Program:** Academic Evaluation Intelligence v1.0
- **Batch:** Batch D - Language and OCR assist support boundary
- **Authorization:** AEI v1.0 implementation authorized for Batch D only
- **Classification:** Implementation certification report
- **Status:** Ready for ARM acceptance review
- **Date:** 2026-07-28
- **Implementation posture:** Feature-flagged, default-off, assist metadata only
- **Recommended commit:** `feat(aei): add language OCR assist metadata`
- **Recommended tag:** `aei-v1-batch-d-language-ocr-assist-certified`

---

## 1. Executive result

Batch D adds bounded language/OCR assist metadata to production evaluation
suggestions without changing OCR extraction, marks, grading, schemas, UI, or
downstream consumers.

The implementation adds a default-off metadata layer that:

- detects answer language/script/code-mixed posture deterministically;
- distinguishes teacher-entered text from image-derived OCR text;
- marks Hindi/Telugu/Sanskrit language grading as teacher-review posture;
- marks Indic handwriting OCR as assistive and teacher-correction-required;
- records OCR confidence posture where available;
- routes low/missing OCR confidence to manual review metadata;
- uses the platform capability registry as non-authoritative posture evidence;
- explicitly records that autonomous language grading is not enabled.

**Certification decision:** PASS
**Runtime behavior with flag OFF:** UNCHANGED
**Risk:** Low-to-medium, controlled by default-off feature flag and metadata-only behavior
**Recommendation:** Approved for ARM acceptance review and commit review.

---

## 2. Authorized deliverables

| Deliverable | Status | Evidence |
|---|---:|---|
| Default-off feature flag | PASS | `Settings.AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED = False` |
| Language/OCR assist metadata service | PASS | `apps/api/app/modules/examinations/services/aei_v1_language_ocr_assist.py` |
| Printed OCR assist posture | PASS | Golden Harness and service tests cover Hindi printed OCR posture |
| Handwriting OCR assist posture | PASS | Hindi/Telugu/Sanskrit handwriting cases covered |
| OCR confidence metadata | PASS | `ocr_confidence`, missing-confidence, and low-confidence tests |
| Teacher correction posture | PASS | Image-derived OCR marks `teacher_correction_required` |
| Language/script/code-mixed metadata | PASS | Hindi, Telugu, Sanskrit, and Tinglish-style tests |
| Low-confidence manual-review routing | PASS | Low OCR confidence routes to `manual_review_required` |
| Golden Harness expansion | PASS | `batch_d_language_ocr_assist_cases.json` |
| Certification report | PASS | This document |

---

## 3. Scope boundary verification

| Boundary | Result |
|---|---:|
| Batch D only | PASS |
| No new OCR engine | PASS |
| No LLM inference added | PASS |
| No autonomous language grading | PASS |
| No marks calculation changes | PASS |
| No teacher approval flow changes | PASS |
| No Batch E visual/science assist implementation | PASS |
| No universal handwriting OCR | PASS |
| No voice tutor | PASS |
| No dialect/slang completeness claim | PASS |
| No public OCR/product claim changes | PASS |
| No UI changes | PASS |
| No API route changes | PASS |
| No database schema changes | PASS |
| No Alembic migrations | PASS |
| Existing behavior preserved with flag OFF | PASS |

---

## 4. Runtime behavior verification

### 4.1 Feature flag

PASS.

`AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED` defaults to `False`.

When disabled:

- suggestions do not include Batch D metadata;
- existing transcription behavior is unchanged;
- existing marks are unchanged;
- existing approval behavior is unchanged;
- no language/OCR manual-review metadata is added.

### 4.2 Language/script/code-mixed metadata

PASS.

When enabled, Batch D annotates suggestions with:

- `answer_language`;
- `detected_script`;
- `code_mixed`;
- `language_confidence`;
- `answer_input_source`;
- `aei_v1_language_ocr_assist`.

Tinglish-style romanized Telugu-English text is recognized as code-mixed
assistive context without forcing review for a non-language, teacher-entered
answer.

### 4.3 OCR assist posture

PASS.

Image-derived OCR answers are classified as handwriting OCR posture. Batch D
does not change OCR extraction itself. It only records that:

- OCR-derived text requires teacher confirmation when confidence is missing or
  weak;
- Indic handwriting OCR remains assistive;
- capability registry posture is internal evidence only.

### 4.4 Language-subject review posture

PASS.

Hindi, Telugu, and Sanskrit language-subject answers are marked for teacher
review. This is metadata only and does not alter marks.

### 4.5 EUI registry usage boundary

PASS.

Batch D performs read-only platform capability lookups for internal posture
metadata. It does not switch AEI source of truth to EUI, does not migrate
consumers, and does not expose public capability claims.

---

## 5. Rollback proof

PASS.

Rollback is achieved by setting:

```text
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
```

Verified rollback characteristics:

- no Batch D metadata is added when disabled;
- no OCR/transcription behavior changes when disabled;
- no persisted Batch D state exists;
- no database rollback is required;
- no API/UI rollback is required;
- existing evaluation regression slice passes.

---

## 6. Validation evidence

### 6.1 Focused static validation

```text
python -m ruff check app/core/config.py \
  app/modules/examinations/services/aei_v1_language_ocr_assist.py \
  app/modules/examinations/services/answer_sheet_eval_service.py \
  tests/test_aei_v1_language_ocr_assist.py \
  tests/test_answer_sheet_eval.py \
  tests/test_golden_evaluation_harness.py
```

Result: PASS.

```text
All checks passed!
```

### 6.2 Focused Batch D + Golden Harness tests

```text
python -m pytest tests/test_aei_v1_language_ocr_assist.py \
  tests/test_golden_evaluation_harness.py -q
```

Result: PASS.

```text
14 passed in 0.66s
```

### 6.3 Answer-sheet integration regression

```text
python -m pytest tests/test_answer_sheet_eval.py -q
```

Result: PASS.

```text
21 passed in 136.78s (0:02:16)
```

### 6.4 AEI v1.0 + OCR regression slice

```text
python -m pytest tests/test_answer_sheet_eval.py \
  tests/test_evaluation_engine.py \
  tests/test_golden_evaluation_harness.py \
  tests/test_aei_v1_review_policy.py \
  tests/test_aei_v1_math_normalization.py \
  tests/test_aei_v1_evidence_ledger.py \
  tests/test_aei_v1_language_ocr_assist.py \
  tests/test_answer_sheet_vision.py -q
```

Result: PASS.

```text
67 passed in 157.34s (0:02:37)
```

### 6.5 API import

```text
python -c "import app.main; print('API_IMPORT_PASS')"
```

Result: PASS.

```text
API_IMPORT_PASS
```

### 6.6 Diff whitespace check

```text
git diff --check
```

Result: PASS.

Note: Git emitted a line-ending warning for an existing touched test file:

```text
warning: in the working copy of 'apps/api/tests/test_golden_evaluation_harness.py',
CRLF will be replaced by LF the next time Git touches it
```

No whitespace errors were reported.

---

## 7. Changed-file inventory

### Backend source

```text
apps/api/app/core/config.py
apps/api/app/modules/examinations/services/aei_v1_language_ocr_assist.py
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
```

### Tests and Golden Harness

```text
apps/api/tests/golden/aei_v1/batch_d_language_ocr_assist_cases.json
apps/api/tests/test_aei_v1_language_ocr_assist.py
apps/api/tests/test_answer_sheet_eval.py
apps/api/tests/test_golden_evaluation_harness.py
```

### Documentation

```text
docs/product/aei-v1/AEI_V1_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/aei-v1/AEI_V1_BATCH_D_LANGUAGE_OCR_ASSIST_CERTIFICATION_REPORT.md
```

---

## 8. Unchanged surfaces

| Surface | Status |
|---|---:|
| Database schema | UNCHANGED |
| Alembic migrations | UNCHANGED |
| Public API routes | UNCHANGED |
| UI/frontend | UNCHANGED |
| OCR provider implementation | UNCHANGED |
| LLM provider usage | UNCHANGED |
| Marks calculation | UNCHANGED |
| Teacher approval flow | UNCHANGED |
| Evidence persistence | UNCHANGED |
| Parent/student surfaces | UNCHANGED |
| Visual/science assist | UNCHANGED |
| Public capability claims | UNCHANGED |

---

## 9. Risks and follow-ups

| Risk | Assessment | Mitigation |
|---|---|---|
| OCR assist could be mistaken for certified OCR | Reduced | Metadata states assist-only and autonomous language grading false |
| Missing OCR confidence in current vision path | Known | Missing confidence routes to teacher correction metadata |
| Romanized code-mixed language coverage is incomplete | Accepted | Common Hinglish/Tinglish-style hints only; no universal dialect claim |
| EUI registry coupling could imply source adoption | Reduced | Read-only lookup only; no EUI source-of-truth switch |

Future OCR work should introduce confidence at the extraction layer before
any stronger product claim is made.

---

## 10. Retrospective

Batch D deliberately did not improve OCR quality. It improved trust around OCR
and language inputs by making support posture visible and conservative. This is
the right sequence for teacher trust: first prevent overclaiming, then expand
capability only when evidence supports it.

---

## 11. Recommendation

ARM review recommendation:

```text
ACCEPT Batch D for commit if implementation review confirms the diff matches
this certification evidence.
```

Suggested implementation commit:

```text
feat(aei): add language OCR assist metadata
```

Suggested annotated tag:

```text
aei-v1-batch-d-language-ocr-assist-certified
```
