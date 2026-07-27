# AEI v1.0 Batch E Certification Report - Visual/Science Assist

- **Program:** Academic Evaluation Intelligence v1.0
- **Batch:** Batch E - Visual and science assist support boundary
- **Authorization:** AEI v1.0 implementation authorized for Batch E only
- **Classification:** Implementation certification report
- **Status:** Ready for ARM acceptance review
- **Date:** 2026-07-28
- **Implementation posture:** Feature-flagged, default-off, assist/checklist metadata only
- **Recommended commit:** `feat(aei): add visual science assist metadata`
- **Recommended tag:** `aei-v1-batch-e-visual-science-assist-certified`

---

## 1. Executive result

Batch E adds bounded visual/science assist metadata to production evaluation
suggestions without adding a visual grader, changing marks, changing schemas,
changing UI, or certifying checklist-only evidence.

The implementation adds a default-off metadata layer that:

- detects chemistry reaction-balancing signals as assistive evidence;
- detects chemical-symbol/formula-like science answers as assistive evidence;
- keeps chemistry structures in manual-review posture;
- records diagram, graph, map, and circuit-style questions as checklist-only
  evidence;
- summarizes checklist observations where deterministic text/checklist evidence
  is available;
- uses the AEI Subject Capability Registry as the support boundary;
- optionally records read-only Platform Capability Registry evidence where
  matching declarations already exist;
- explicitly records that autonomous visual/science grading and autonomous marks
  from checklist evidence are not enabled.

**Certification decision:** PASS
**Runtime behavior with flag OFF:** UNCHANGED
**Risk:** Low-to-medium, controlled by default-off feature flag and metadata-only behavior
**Recommendation:** Approved for ARM acceptance review and commit review.

---

## 2. Authorized deliverables

| Deliverable | Status | Evidence |
|---|---:|---|
| Default-off feature flag | PASS | `Settings.AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED = False` |
| Visual/science assist metadata service | PASS | `apps/api/app/modules/examinations/services/aei_v1_visual_science_assist.py` |
| Visual checklist metadata | PASS | Biology diagram and geography map checklist tests |
| Graph/map/diagram checklist assist | PASS | Golden Harness and focused tests cover map and diagram checklist posture |
| Chemistry reaction-balancing assist | PASS | Balanced and unbalanced reaction tests |
| Chemical-symbol / formula assist | PASS | Physics formula recognition test and chemistry symbol path |
| Chemistry structure manual-review posture | PASS | Structure test routes to manual review |
| Manual-review routing for checklist/assist | PASS | All Batch E enriched cases require teacher review |
| Golden Harness expansion | PASS | `batch_e_visual_science_assist_cases.json` |
| Certification report | PASS | This document |

---

## 3. Scope boundary verification

| Boundary | Result |
|---|---:|
| Batch E only | PASS |
| No pixel-perfect visual grading | PASS |
| No full chemistry structure grading | PASS |
| No graph/map automatic marks | PASS |
| No circuit correctness automation beyond checklist posture | PASS |
| No autonomous marks for checklist-only evidence | PASS |
| No new OCR/vision engine | PASS |
| No LLM inference added | PASS |
| No marks calculation changes | PASS |
| No teacher approval flow changes | PASS |
| No evidence-ledger behavior changes | PASS |
| No Batch F certification implementation | PASS |
| No UI changes | PASS |
| No API route changes | PASS |
| No database schema changes | PASS |
| No Alembic migrations | PASS |
| Existing behavior preserved with flag OFF | PASS |

---

## 4. Runtime behavior verification

### 4.1 Feature flag

PASS.

`AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED` defaults to `False`.

When disabled:

- suggestions do not include Batch E metadata;
- existing marks are unchanged;
- existing approval behavior is unchanged;
- no visual/science manual-review metadata is added.

### 4.2 Chemistry reaction-balancing assist

PASS.

When enabled, Batch E can summarize simple reaction-balancing evidence such as
balanced/unbalanced status using the existing deterministic AEI reasoning layer.
This evidence is assistive only and always requires teacher review.

### 4.3 Visual checklist posture

PASS.

Diagram, map, graph, circuit, and visual-style questions are treated as
checklist/manual-review posture. Batch E may summarize expected, observed,
present, and missing checklist items when deterministic text/checklist evidence
is available.

Checklist output cannot certify marks autonomously.

### 4.4 Science formula / symbol posture

PASS.

Formula-like and chemical-symbol-like answers can receive assist metadata. This
metadata is not grading and does not replace teacher judgment.

### 4.5 Chemistry structure posture

PASS.

Chemical structures remain manual-review posture in AEI v1. Batch E does not
attempt organic-structure grading or visual structure correctness.

### 4.6 Registry usage boundary

PASS.

Batch E uses the AEI Subject Capability Registry to determine support posture.
It also performs read-only Platform Capability Registry lookups where matching
declarations already exist. It does not switch AEI source of truth to EUI, does
not migrate consumers, and does not expose public capability claims.

---

## 5. Rollback proof

PASS.

Rollback is achieved by setting:

```text
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
```

Verified rollback characteristics:

- no Batch E metadata is added when disabled;
- no visual/science checklist behavior changes when disabled;
- no persisted Batch E state exists;
- no database rollback is required;
- no API/UI rollback is required;
- existing evaluation regression slice passes.

---

## 6. Validation evidence

### 6.1 Focused static validation

```text
python -m ruff check app/core/config.py \
  app/modules/examinations/services/answer_sheet_eval_service.py \
  app/modules/examinations/services/aei_v1_visual_science_assist.py \
  tests/test_aei_v1_visual_science_assist.py \
  tests/test_answer_sheet_eval.py \
  tests/test_golden_evaluation_harness.py
```

Result: PASS.

```text
All checks passed!
```

### 6.2 Focused Batch E + Golden Harness tests

```text
python -m pytest tests/test_aei_v1_visual_science_assist.py \
  tests/test_golden_evaluation_harness.py -q
```

Result: PASS.

```text
16 passed in 0.89s
```

### 6.3 Answer-sheet integration regression

```text
python -m pytest tests/test_answer_sheet_eval.py -q
```

Result: PASS.

```text
23 passed in 168.78s (0:02:48)
```

### 6.4 AEI v1.0 + OCR/visual-science regression slice

```text
python -m pytest tests/test_answer_sheet_eval.py \
  tests/test_evaluation_engine.py \
  tests/test_golden_evaluation_harness.py \
  tests/test_aei_v1_review_policy.py \
  tests/test_aei_v1_math_normalization.py \
  tests/test_aei_v1_evidence_ledger.py \
  tests/test_aei_v1_language_ocr_assist.py \
  tests/test_aei_v1_visual_science_assist.py \
  tests/test_answer_sheet_vision.py -q
```

Result: PASS.

```text
78 passed in 183.16s (0:03:03)
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
apps/api/app/modules/examinations/services/aei_v1_visual_science_assist.py
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
```

### Tests and Golden Harness

```text
apps/api/tests/golden/aei_v1/batch_e_visual_science_assist_cases.json
apps/api/tests/test_aei_v1_visual_science_assist.py
apps/api/tests/test_answer_sheet_eval.py
apps/api/tests/test_golden_evaluation_harness.py
```

### Documentation

```text
docs/product/aei-v1/AEI_V1_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/aei-v1/AEI_V1_BATCH_E_VISUAL_SCIENCE_ASSIST_CERTIFICATION_REPORT.md
```

---

## 8. Unchanged surfaces

| Surface | Status |
|---|---:|
| Database schema | UNCHANGED |
| Alembic migrations | UNCHANGED |
| Public API routes | UNCHANGED |
| UI/frontend | UNCHANGED |
| OCR/vision provider implementation | UNCHANGED |
| LLM provider usage | UNCHANGED |
| Marks calculation | UNCHANGED |
| Teacher approval flow | UNCHANGED |
| Evidence persistence | UNCHANGED |
| Parent/student surfaces | UNCHANGED |
| Public capability claims | UNCHANGED |
| EUI source adoption | UNCHANGED |

---

## 9. Risks and follow-ups

| Risk | Assessment | Mitigation |
|---|---|---|
| Checklist output mistaken for marks | Reduced | Metadata states checklist-only and autonomous marks false |
| Visual capability overclaiming | Reduced | No image model or pixel-perfect grading added |
| Chemistry structures overreach | Reduced | Structures remain manual-review posture |
| Formula recognition mistaken for correctness | Reduced | Formula metadata is assistive and review-required |
| EUI registry evidence mistaken for source adoption | Reduced | Read-only lookup only; no EUI source-of-truth switch |

Future visual/science work should introduce real extraction evidence and browser
proof only under a separately authorized product-facing scope.

---

## 10. Retrospective

Batch E deliberately does not make StudyNexs a visual grader. It creates honest,
bounded assist metadata so teachers can see when a visual/science answer needs
review and why. This preserves the teacher-trust posture while setting up AEI
v1.0 certification.

---

## 11. Recommendation

ARM review recommendation:

```text
ACCEPT Batch E for commit if implementation review confirms the diff matches
this certification evidence.
```

Suggested implementation commit:

```text
feat(aei): add visual science assist metadata
```

Suggested annotated tag:

```text
aei-v1-batch-e-visual-science-assist-certified
```
