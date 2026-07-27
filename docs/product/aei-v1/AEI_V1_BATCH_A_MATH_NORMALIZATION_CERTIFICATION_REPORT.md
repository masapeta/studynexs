# AEI v1.0 Batch A Certification Report - Maths Normalization

- **Program:** Academic Evaluation Intelligence v1.0
- **Batch:** Batch A - Maths normalization and deterministic equivalence
- **Authorization:** AEI v1.0 implementation authorized for Batch A only
- **Classification:** Implementation certification report
- **Status:** Ready for ARM acceptance review
- **Date:** 2026-07-28
- **Implementation posture:** Feature-flagged, default-off, production-seam integration
- **Recommended commit:** `feat(aei): add maths normalization foundation`
- **Recommended tag:** `aei-v1-batch-a-maths-normalization-certified`

---

## 1. Executive result

Batch A implements deterministic Maths normalization for the supported AEI v1.0
scope while preserving existing behavior when the feature flag is disabled.

The implementation adds a narrow adapter from the existing answer-sheet
evaluation service into the certified AEI pipeline:

```text
AcademicAnswer
    -> Academic Understanding
    -> Academic Reasoning
    -> Evaluation Policy
    -> existing draft suggestion shape
```

It supports deterministic handling of:

- fractions, decimals, mixed numbers, Unicode fractions;
- percentages;
- scientific notation;
- explicit numeric tolerance;
- simple same-dimension unit equivalence;
- acceptable answer variants;
- manual-review metadata for inconclusive supported Maths cases.

**Certification decision:** PASS
**Runtime behavior with flag OFF:** UNCHANGED
**Risk:** Low-to-medium, controlled by default-off feature flag
**Recommendation:** Approved for ARM acceptance review and commit review.

---

## 2. Authorized deliverables

| Deliverable | Status | Evidence |
|---|---:|---|
| Default-off feature flag | PASS | `Settings.AEI_V1_MATH_NORMALIZATION_ENABLED = False` |
| Maths normalization adapter | PASS | `apps/api/app/modules/examinations/services/aei_v1_math_normalization.py` |
| AEI pipeline reuse | PASS | Adapter uses AcademicAnswer, Understanding, Reasoning, Policy |
| Fraction/decimal/mixed-number equivalence | PASS | Reasoner + adapter + Golden Harness tests |
| Percentage normalization | PASS | Reasoner + adapter tests |
| Scientific notation equivalence | PASS | Reasoner + Golden Harness tests |
| Explicit numeric tolerance | PASS | Reasoner + adapter + Golden Harness tests |
| Unit equivalence | PASS | Reasoner + adapter + Golden Harness tests |
| Acceptable answer variants | PASS | Existing rubric field consumed when present |
| Production-seam integration | PASS | `AnswerSheetEvalService._grade_exam(...)` behind feature flag |
| Golden Harness expansion | PASS | `batch_a_math_normalization_cases.json` |
| Certification report | PASS | This document |

---

## 3. Scope boundary verification

| Boundary | Result |
|---|---:|
| Batch A only | PASS |
| No Batch B review workflow implementation | PASS |
| No evidence-ledger migration | PASS |
| No language/OCR assist implementation | PASS |
| No visual/science assist implementation | PASS |
| No UI changes | PASS |
| No public API endpoint changes | PASS |
| No database schema changes | PASS |
| No Alembic migrations | PASS |
| No LLM inference added | PASS |
| No autonomous grading for inconclusive Maths cases | PASS |
| Existing exact-match behavior preserved with flag OFF | PASS |

---

## 4. Runtime behavior verification

### 4.1 Feature flag

PASS.

`AEI_V1_MATH_NORMALIZATION_ENABLED` defaults to `False`.

When disabled:

- the Maths adapter is not invoked;
- the extra `QuestionPaper` subject lookup is not performed;
- existing objective exact-match grading remains the production path.

### 4.2 Deterministic match behavior

PASS.

When enabled, the adapter awards full draft marks only when:

1. the subject resolves to Maths/Mathematics;
2. the question type is within the supported deterministic Maths scope;
3. the rubric context is mathematical;
4. AEI reasoning produces a supported match/equivalence result;
5. Evaluation Policy returns a supported decision without manual review.

### 4.3 Inconclusive behavior

PASS.

Inconclusive supported Maths cases do not receive autonomous marks. They produce
manual-review metadata inside the existing suggestion payload.

This is intentionally metadata only in Batch A. It does not implement Batch B
teacher-review routing or UI behavior.

---

## 5. Rollback proof

PASS.

Rollback is achieved by setting:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=false
```

Verified rollback characteristics:

- legacy objective exact-match grading remains active;
- no persisted Batch A state exists;
- no database rollback is required;
- no API/UI rollback is required;
- answer-sheet evaluation outputs remain legacy-shaped when disabled.

---

## 6. Validation evidence

### 6.1 Focused static validation

```text
python -m ruff check app/core/config.py \
  app/modules/examinations/services/academic_reasoning_engine.py \
  app/modules/examinations/services/aei_v1_math_normalization.py \
  app/modules/examinations/services/answer_sheet_eval_service.py \
  tests/test_academic_reasoning_engine.py \
  tests/test_aei_v1_math_normalization.py \
  tests/test_answer_sheet_eval.py \
  tests/test_golden_evaluation_harness.py
```

Result: PASS.

```text
All checks passed!
```

### 6.2 Focused tests and production-seam regression

```text
python -m pytest tests/test_academic_reasoning_engine.py \
  tests/test_aei_v1_math_normalization.py \
  tests/test_golden_evaluation_harness.py \
  tests/test_answer_sheet_eval.py -q
```

Result: PASS.

```text
40 passed in 80.02s (0:01:20)
```

### 6.3 API import

```text
python -c "import app.main; print('API_IMPORT_PASS')"
```

Result: PASS.

```text
API_IMPORT_PASS
```

### 6.4 Diff hygiene

```text
git diff --check
```

Result: PASS.

Git emitted a line-ending normalization warning for one touched test file, but
reported no whitespace errors.

---

## 7. Certification notes

- The implementation deliberately keeps Batch A as a Maths-only production-seam
  adapter and does not expand AEI into new language, OCR, visual, science, or
  review-workflow behavior.
- Unit equivalence is intentionally limited to simple length, mass, and volume
  dimensions.
- The adapter ignores textual Maths short answers and MCQ/true-false answers so
  legacy behavior remains responsible for those cases.
- Manual-review metadata added by Batch A is internal suggestion metadata only;
  teacher-review routing remains Batch B.

---

## 8. ARM recommendation

Batch A is ready for ARM implementation review.

If accepted, the recommended next steps are:

1. Commit the Batch A implementation and certification artifacts.
2. Create the annotated certification tag.
3. Publish.
4. Update `docs/STATUS.md` separately as a docs-only post-publication commit.
5. Do not begin Batch B until separately authorized.
