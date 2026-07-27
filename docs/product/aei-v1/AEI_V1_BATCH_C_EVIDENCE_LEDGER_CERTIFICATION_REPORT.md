# AEI v1.0 Batch C Certification Report - Evidence Ledger

- **Program:** Academic Evaluation Intelligence v1.0
- **Batch:** Batch C - Evidence ledger and approved evidence propagation
- **Authorization:** AEI v1.0 implementation authorized for Batch C only
- **Classification:** Implementation certification report
- **Status:** Ready for ARM acceptance review
- **Date:** 2026-07-28
- **Implementation posture:** Feature-flagged, default-off, additive evidence metadata only
- **Recommended commit:** `feat(aei): add approved evidence ledger metadata`
- **Recommended tag:** `aei-v1-batch-c-evidence-ledger-certified`

---

## 1. Executive result

Batch C adds a safe, teacher-approved evidence contract to the existing
evaluation evidence ledger without changing marks, grading, schemas, UI, or
downstream consumers.

The implementation adds a default-off evidence-ledger metadata layer that:

- distinguishes unapproved AI suggestions from teacher-approved evidence;
- records sanitized original-suggestion metadata;
- records final teacher-decision metadata;
- separates original AI suggestion from final teacher decision;
- marks the teacher decision as the downstream source of truth;
- excludes raw student answers from the approved-evidence contract;
- preserves existing evaluation and corrections behavior when disabled.

**Certification decision:** PASS
**Runtime behavior with flag OFF:** UNCHANGED
**Risk:** Low, controlled by default-off feature flag and additive metadata
**Recommendation:** Approved for ARM acceptance review and commit review.

---

## 2. Authorized deliverables

| Deliverable | Status | Evidence |
|---|---:|---|
| Default-off feature flag | PASS | `Settings.AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED = False` |
| Approved-evidence metadata service | PASS | `apps/api/app/modules/examinations/services/aei_v1_evidence_ledger.py` |
| Safe AEI metadata in evidence ledger responses | PASS | Additive `aei_v1_approved_evidence` object when flag is ON |
| Original suggestion vs final teacher decision metadata | PASS | `original_suggestion` and `final_teacher_decision` are separate |
| Approved evidence contract hardening | PASS | `source_of_truth = teacher_decision` and downstream contract metadata |
| Parent/student-safe evidence regression | PASS | Raw answer keys are excluded and tested |
| Learning-intelligence approved-evidence check | PASS | Metadata marks only teacher-approved evidence as downstream-eligible |
| Golden Harness expansion | PASS | `batch_c_approved_evidence_cases.json` |
| Certification report | PASS | This document |

---

## 3. Scope boundary verification

| Boundary | Result |
|---|---:|
| Batch C only | PASS |
| No new grading logic | PASS |
| No marks calculation changes | PASS |
| No teacher-review routing changes | PASS |
| No Batch D language/OCR assist implementation | PASS |
| No Batch E visual/science assist implementation | PASS |
| No report-card automation | PASS |
| No broad downstream consumer migration | PASS |
| No parent/student UI expansion | PASS |
| No public API endpoint changes | PASS |
| No database schema changes | PASS |
| No Alembic migrations | PASS |
| Existing behavior preserved with flag OFF | PASS |

---

## 4. Runtime behavior verification

### 4.1 Feature flag

PASS.

`AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED` defaults to `False`.

When disabled:

- `EvaluationOut.evidence_ledger` remains in its existing legacy shape;
- no Batch C metadata is added;
- no approval behavior changes;
- no corrections-history behavior changes;
- no database or UI behavior changes.

### 4.2 Unapproved suggestions

PASS.

When the flag is enabled but an evaluation is still `suggested`, Batch C emits
only a non-authoritative summary:

- `approved_evidence = false`;
- `approved_for_downstream = false`;
- `questions = {}`;
- raw student answers remain excluded.

This prevents unapproved AI suggestions from becoming downstream evidence.

### 4.3 Teacher-approved evidence

PASS.

After teacher approval, Batch C emits per-question evidence metadata:

- sanitized original suggestion;
- final teacher marks;
- override reason when provided;
- override audit metadata where Batch B produced it;
- manual-review posture of the original suggestion;
- source-of-truth declaration set to teacher decision.

The metadata is additive inside the existing `evidence_ledger` response object.

### 4.4 Parent/student-safe evidence posture

PASS.

The approved-evidence contract excludes raw-answer keys such as:

- `student_answer`;
- `raw_answer`;
- `raw_input`;
- `ocr_text`;
- `transcript`;
- `answer_text`.

Focused tests and Golden Harness cases verify the exclusion recursively.

---

## 5. Rollback proof

PASS.

Rollback is achieved by setting:

```text
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
```

Verified rollback characteristics:

- existing evidence-ledger response shape is preserved when disabled;
- no persisted Batch C state exists;
- no database rollback is required;
- no API/UI rollback is required;
- existing evaluation regression slice passes.

---

## 6. Validation evidence

### 6.1 Focused static validation

```text
python -m ruff check app/core/config.py \
  app/modules/examinations/endpoints/evaluation.py \
  app/modules/examinations/services/aei_v1_evidence_ledger.py \
  tests/test_aei_v1_evidence_ledger.py \
  tests/test_golden_evaluation_harness.py \
  tests/test_answer_sheet_eval.py
```

Result: PASS.

```text
All checks passed!
```

### 6.2 Focused Batch C + Golden Harness tests

```text
python -m pytest tests/test_aei_v1_evidence_ledger.py \
  tests/test_golden_evaluation_harness.py -q
```

Result: PASS.

```text
10 passed in 0.38s
```

### 6.3 Answer-sheet integration regression

```text
python -m pytest tests/test_answer_sheet_eval.py -q
```

Result: PASS.

```text
19 passed in 103.48s (0:01:43)
```

### 6.4 AEI v1.0 evaluation regression slice

```text
python -m pytest tests/test_answer_sheet_eval.py \
  tests/test_evaluation_engine.py \
  tests/test_golden_evaluation_harness.py \
  tests/test_aei_v1_review_policy.py \
  tests/test_aei_v1_math_normalization.py -q
```

Result: PASS.

```text
50 passed in 136.26s (0:02:16)
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
apps/api/app/modules/examinations/endpoints/evaluation.py
apps/api/app/modules/examinations/services/aei_v1_evidence_ledger.py
```

### Tests and Golden Harness

```text
apps/api/tests/golden/aei_v1/batch_c_approved_evidence_cases.json
apps/api/tests/test_aei_v1_evidence_ledger.py
apps/api/tests/test_answer_sheet_eval.py
apps/api/tests/test_golden_evaluation_harness.py
```

### Documentation

```text
docs/product/aei-v1/AEI_V1_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/aei-v1/AEI_V1_BATCH_C_EVIDENCE_LEDGER_CERTIFICATION_REPORT.md
```

---

## 8. Unchanged surfaces

| Surface | Status |
|---|---:|
| Database schema | UNCHANGED |
| Alembic migrations | UNCHANGED |
| Public API routes | UNCHANGED |
| UI/frontend | UNCHANGED |
| Marks calculation | UNCHANGED |
| Teacher review routing | UNCHANGED |
| Evidence persistence | UNCHANGED |
| Parent/student surfaces | UNCHANGED |
| Language/OCR assist | UNCHANGED |
| Visual/science assist | UNCHANGED |

---

## 9. Risks and follow-ups

| Risk | Assessment | Mitigation |
|---|---|---|
| Consumers could misread unapproved suggestions as evidence | Reduced | Unapproved metadata has `approved_for_downstream = false` and no per-question evidence |
| Raw answer leakage in approved evidence | Reduced | Sanitized allowlist and recursive unsafe-key tests |
| Confusion between AI suggestion and teacher decision | Reduced | Separate `original_suggestion` and `final_teacher_decision` objects |
| Future parent/student views using uncertified AI | Still requires vigilance | Downstream contract declares teacher-approved-only visibility |

Future batches should continue to verify that student, parent, and learning
intelligence surfaces consume only teacher-approved evidence.

---

## 10. Retrospective

Batch C reused the existing evidence-ledger response seam instead of creating a
parallel evidence store. That kept the change small, rollbackable, and aligned
with the AEI constitution.

The most important design choice was treating unapproved suggestions as
non-evidence, even when Batch C metadata is enabled. This preserves the product
principle that AI may recommend, but teachers decide.

---

## 11. Recommendation

ARM review recommendation:

```text
ACCEPT Batch C for commit if implementation review confirms the diff matches
this certification evidence.
```

Suggested implementation commit:

```text
feat(aei): add approved evidence ledger metadata
```

Suggested annotated tag:

```text
aei-v1-batch-c-evidence-ledger-certified
```
