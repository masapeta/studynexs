# AEI v1.0 Batch B Certification Report - Review Policy

- **Program:** Academic Evaluation Intelligence v1.0
- **Batch:** Batch B - Confidence, manual review, and teacher override
- **Authorization:** AEI v1.0 implementation authorized for Batch B only
- **Classification:** Implementation certification report
- **Status:** Ready for ARM acceptance review
- **Date:** 2026-07-28
- **Implementation posture:** Feature-flagged, default-off, metadata/audit only
- **Recommended commit:** `feat(aei): add review policy metadata foundation`
- **Recommended tag:** `aei-v1-batch-b-review-policy-certified`

---

## 1. Executive result

Batch B implements deterministic review-policy metadata for production
evaluation suggestions while preserving existing marks, evaluation behavior,
API contracts, UI behavior, evidence-ledger behavior, and schema.

The implementation adds a default-off review-policy layer that annotates
existing suggestions with:

- `manual_review_required`;
- `manual_review_reason`;
- `capability_mode`;
- `confidence_reason`;
- `aei_v1_review_policy` internal metadata.

It also strengthens teacher override governance behind the same flag by
requiring a reason when a teacher changes suggested marks and by storing
override audit metadata in the existing `teacher_overrides` JSON payload.

**Certification decision:** PASS
**Runtime behavior with flag OFF:** UNCHANGED
**Risk:** Low-to-medium, controlled by default-off feature flag
**Recommendation:** Approved for ARM acceptance review and commit review.

---

## 2. Authorized deliverables

| Deliverable | Status | Evidence |
|---|---:|---|
| Default-off feature flag | PASS | `Settings.AEI_V1_REVIEW_POLICY_ENABLED = False` |
| Review-policy metadata service | PASS | `apps/api/app/modules/examinations/services/aei_v1_review_policy.py` |
| Manual-review metadata | PASS | `manual_review_required`, `manual_review_reason` |
| Confidence explanation | PASS | `confidence_reason` |
| Capability mode metadata | PASS | `capability_mode` |
| Low-confidence review signal | PASS | Confidence threshold tests and Golden Harness cases |
| Missing-confidence review signal | PASS | Review policy tests and Golden Harness cases |
| Honest confidence wording | PASS | Existing manual-review cases do not mislabel high confidence as low |
| Teacher override reason enforcement | PASS | Enabled only when review-policy flag is ON |
| Teacher override audit metadata | PASS | Existing `teacher_overrides` JSON payload |
| Override reason sanitization | PASS | Reasons are sanitized even when marks do not change |
| Golden Harness expansion | PASS | `batch_b_review_policy_cases.json` |
| Certification report | PASS | This document |

---

## 3. Scope boundary verification

| Boundary | Result |
|---|---:|
| Batch B only | PASS |
| No new grading logic | PASS |
| No marks calculation changes | PASS |
| No Batch C evidence-ledger implementation | PASS |
| No evidence-ledger schema migration | PASS |
| No language/OCR assist implementation | PASS |
| No visual/science assist implementation | PASS |
| No UI redesign | PASS |
| No public API endpoint changes | PASS |
| No database schema changes | PASS |
| No Alembic migrations | PASS |
| No parent/student visibility changes | PASS |
| Existing behavior preserved with flag OFF | PASS |

---

## 4. Runtime behavior verification

### 4.1 Feature flag

PASS.

`AEI_V1_REVIEW_POLICY_ENABLED` defaults to `False`.

When disabled:

- review-policy metadata is not added to suggestions;
- override reason enforcement is not applied;
- override audit metadata is not added;
- existing approval behavior remains unchanged.

### 4.2 Review-policy metadata

PASS.

When enabled, existing suggestions receive review metadata without changing
marks:

- high-confidence suggestions remain non-review;
- low-confidence suggestions require teacher review metadata;
- missing-confidence suggestions require teacher review metadata;
- existing manual-review metadata is preserved.

### 4.3 Teacher override governance

PASS.

When enabled, changed teacher marks require a non-empty override reason. The
approved override payload records:

- original suggested marks;
- final teacher marks;
- whether an override was applied;
- manual-review posture of the original suggestion;
- reviewer identifier;
- review timestamp.

This uses the existing `teacher_overrides` JSON field and does not add
persistence schema.

---

## 5. Rollback proof

PASS.

Rollback is achieved by setting:

```text
AEI_V1_REVIEW_POLICY_ENABLED=false
```

Verified rollback characteristics:

- no review-policy metadata is added when disabled;
- no override reason enforcement is applied when disabled;
- no persisted Batch B state is required;
- no database rollback is required;
- no API/UI rollback is required;
- existing evaluation regression slice passes.

---

## 6. Validation evidence

### 6.1 Focused static validation

```text
python -m ruff check app/core/config.py \
  app/modules/examinations/services/aei_v1_review_policy.py \
  app/modules/examinations/services/answer_sheet_eval_service.py \
  tests/test_aei_v1_review_policy.py \
  tests/test_answer_sheet_eval.py \
  tests/test_golden_evaluation_harness.py
```

Result: PASS.

```text
All checks passed!
```

### 6.2 Focused tests

```text
python -m pytest tests/test_aei_v1_review_policy.py \
  tests/test_golden_evaluation_harness.py -q
```

Result: PASS.

```text
14 passed in 0.71s
```

### 6.3 Answer-sheet integration regression

```text
python -m pytest tests/test_answer_sheet_eval.py -q
```

Result: PASS.

```text
17 passed in 86.95s (0:01:26)
```

### 6.4 Batch A + Batch B AEI/evaluation regression slice

```text
python -m pytest tests/test_academic_reasoning_engine.py \
  tests/test_aei_v1_math_normalization.py \
  tests/test_aei_v1_review_policy.py \
  tests/test_golden_evaluation_harness.py \
  tests/test_answer_sheet_eval.py \
  tests/test_evaluation_policy.py \
  tests/test_teacher_review.py -q
```

Result: PASS.

```text
69 passed in 86.18s (0:01:26)
```

### 6.5 API import

```text
python -c "import app.main; print('API_IMPORT_PASS')"
```

Result: PASS.

```text
API_IMPORT_PASS
```

### 6.6 Diff hygiene

```text
git diff --check
```

Result: PASS.

Git emitted a line-ending normalization warning for one touched test file, but
reported no whitespace errors.

---

## 7. Certification notes

- Batch B is metadata/audit-only and does not change marks.
- Batch B does not implement evidence-ledger propagation; that remains Batch C.
- Batch B does not add UI behavior; teacher-facing presentation remains future
  UI/product work.
- Override reason enforcement is feature-flagged so rollback is immediate.
- Override reason text is sanitized before storage in existing override JSON.
- Review-policy metadata is internal suggestion metadata and does not authorize
  parent/student exposure.

---

## 8. ARM recommendation

Batch B is ready for ARM implementation review.

If accepted, the recommended next steps are:

1. Commit the Batch B implementation and certification artifacts.
2. Create the annotated certification tag.
3. Publish.
4. Update `docs/STATUS.md` separately as a docs-only post-publication commit.
5. Do not begin Batch C until separately authorized.
