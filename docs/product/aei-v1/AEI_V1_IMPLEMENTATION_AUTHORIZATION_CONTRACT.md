# AEI v1.0 Implementation Authorization Contract

- **Program:** Academic Evaluation Intelligence v1.0
- **Artifact:** Implementation authorization contract
- **Classification:** Runtime implementation contract
- **Status:** Accepted
- **Implementation:** Authorized for Batch A only
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Architecture baseline:** [`../../architecture/AEI.md`](../../architecture/AEI.md)
- **EUI baseline:** [`../../architecture/EUI.md`](../../architecture/EUI.md)
- **Readiness baseline:** [`./AEI_PRODUCTION_READINESS_REVIEW.md`](./AEI_PRODUCTION_READINESS_REVIEW.md)
- **Design baseline:** [`./AEI_V1_IMPLEMENTATION_DESIGN_BRIEF.md`](./AEI_V1_IMPLEMENTATION_DESIGN_BRIEF.md)

---

## 1. Authorization status

This document is the accepted implementation authorization contract for AEI
v1.0 batch-by-batch implementation.

ARM accepts the contract and authorizes Batch A only.

Later batches require separate ARM continuation after the prior batch is
implemented, certified, reviewed, committed, tagged, and published.

---

## 2. Purpose

Authorize controlled, batch-by-batch implementation of Academic Evaluation
Intelligence v1.0 for teacher-trust evaluation.

AEI v1.0 should make supported evaluation scenarios production-grade without
turning AI into an autonomous grading authority.

The teacher remains the final evaluator.

---

## 3. Implementation model

Implementation must proceed batch-by-batch.

Each batch requires:

```text
Batch implementation
        |
        v
Focused validation
        |
        v
Regression validation
        |
        v
Certification report
        |
        v
ARM review
        |
        v
Commit
        |
        v
Annotated tag
        |
        v
Publication
        |
        v
docs/STATUS.md update if published
```

Completion of one batch does not authorize the next batch unless ARM explicitly
continues the program.

---

## 4. Authorized batch sequence

This contract defines the full AEI v1.0 batch sequence, but only Batch A is
authorized to begin now.

The approved AEI v1.0 sequence is:

```text
Batch A - Maths normalization and deterministic equivalence
Batch B - Confidence, manual review, and teacher override
Batch C - Evidence ledger and approved evidence propagation
Batch D - Language and OCR assist support boundary
Batch E - Visual and science assist support boundary
Batch F - AEI v1.0 certification
```

Each batch must remain independently reviewable and certifiable.

Authorization state:

| Batch | Authorization |
|---|---|
| Batch A - Maths normalization and deterministic equivalence | Authorized |
| Batch B - Confidence, manual review, and teacher override | Not authorized until Batch A is accepted |
| Batch C - Evidence ledger and approved evidence propagation | Not authorized until separately continued |
| Batch D - Language and OCR assist support boundary | Not authorized until separately continued |
| Batch E - Visual and science assist support boundary | Not authorized until separately continued |
| Batch F - AEI v1.0 certification | Not authorized until separately continued |

---

## 5. Batch A authorization boundary

### 5.1 Purpose

Make supported Maths objective and short-answer evaluation production-grade.

### 5.2 Authorized scope

Batch A may implement:

- fraction / decimal / mixed-number equivalence;
- Unicode fraction equivalence;
- scientific notation equivalence;
- acceptable-answer matching;
- rubric-driven numeric tolerance;
- rubric-driven required/allowed units;
- deterministic confidence for supported matches;
- manual-review metadata for ambiguous or unsupported Maths answers;
- Golden Harness production cases.

### 5.3 Explicit exclusions

Batch A must not implement:

- full symbolic algebra;
- proof checking;
- broad CAS behavior;
- autonomous marks for ambiguous answers;
- UI redesign;
- evidence ledger migration;
- language/OCR support;
- visual/science checklist support.

---

## 6. Batch B authorization boundary

### 6.1 Purpose

Make uncertainty visible and teacher authority enforceable.

### 6.2 Authorized scope

Batch B may implement:

- AEI policy metadata on production suggestions;
- `manual_review_required`;
- `manual_review_reason`;
- `capability_mode`;
- `confidence_reason`;
- low-confidence review routing;
- teacher override audit metadata;
- override reason validation where needed.

### 6.3 Explicit exclusions

Batch B must not implement:

- new grading logic;
- new UI redesign;
- source-of-truth switching;
- evidence ledger schema migration unless separately authorized;
- parent/student visibility changes.

---

## 7. Batch C authorization boundary

### 7.1 Purpose

Ensure only teacher-approved evidence powers downstream intelligence.

### 7.2 Authorized scope

Batch C may implement:

- safe AEI metadata in evidence ledger responses;
- original suggestion vs final teacher decision metadata;
- approved evidence contract hardening;
- parent/student-safe evidence regression tests;
- learning-intelligence approved-evidence checks.

### 7.3 Explicit exclusions

Batch C must not implement:

- report-card automation;
- parent/student UI expansion unless separately authorized;
- evidence ledger destructive migrations;
- broad downstream consumer migration.

---

## 8. Batch D authorization boundary

### 8.1 Purpose

Define and implement honest language/OCR assist behavior for supported inputs.

### 8.2 Authorized scope

Batch D may implement:

- printed OCR assist posture for supported languages;
- handwriting OCR assist posture for Hindi/Telugu/Sanskrit;
- OCR confidence metadata;
- teacher-correction-before-evaluation posture;
- language/script/code-mixed metadata;
- low-confidence manual-review routing;
- Golden Harness cases for supported language/OCR scenarios.

### 8.3 Explicit exclusions

Batch D must not implement:

- universal handwriting OCR;
- autonomous language grading;
- voice tutor;
- dialect/slang completeness;
- public universal OCR claims.

---

## 9. Batch E authorization boundary

### 9.1 Purpose

Define and implement safe visual/science assist boundaries.

### 9.2 Authorized scope

Batch E may implement:

- visual checklist metadata;
- graph/map checklist assist;
- diagram checklist assist;
- chemistry equation/reaction-balancing assist;
- chemical-symbol assist;
- physics formula-recognition assist;
- manual-review routing for partial/checklist capabilities.

### 9.3 Explicit exclusions

Batch E must not implement:

- pixel-perfect visual grading;
- full chemistry structure grading;
- graph/map automatic marks;
- circuit correctness automation beyond checklist support;
- autonomous marks for checklist-only evidence.

---

## 10. Batch F authorization boundary

### 10.1 Purpose

Certify AEI v1.0 for the declared supported scope.

### 10.2 Authorized scope

Batch F may produce:

- AEI v1.0 certification report;
- supported-scope capability matrix;
- Golden Harness summary;
- runtime proof;
- browser proof for changed UI surfaces;
- evidence-ledger proof;
- approved-evidence downstream proof;
- rollback proof;
- performance proof;
- tenant/security proof.

Batch F should not introduce new product behavior unless separately authorized.

---

## 11. Authorized repository boundary

### 11.1 Backend source

Permitted areas:

```text
apps/api/app/modules/examinations/schemas/
apps/api/app/modules/examinations/services/
apps/api/app/modules/examinations/endpoints/
apps/api/app/modules/examinations/data/
apps/api/app/modules/ai/services/evaluation_engine.py
apps/api/app/modules/files/services/document_ocr.py
apps/api/app/modules/files/services/file_validation.py
apps/api/app/modules/eui/schemas/
apps/api/app/modules/eui/services/
apps/api/app/core/config.py
```

Endpoint changes are permitted only if additive and explicitly justified by the
batch.

### 11.2 Tests

Permitted areas:

```text
apps/api/tests/test_answer_sheet_eval.py
apps/api/tests/test_evaluation_engine.py
apps/api/tests/test_academic_reasoning_engine.py
apps/api/tests/test_academic_understanding_engine.py
apps/api/tests/test_evaluation_policy.py
apps/api/tests/test_teacher_review.py
apps/api/tests/test_golden_evaluation_harness.py
apps/api/tests/golden/
apps/api/tests/test_aei_passive_integration.py
apps/api/tests/test_eui_golden_harness.py
```

Additional focused tests may be added under `apps/api/tests/` when scoped to
AEI v1.0.

### 11.3 Documentation

Permitted areas:

```text
docs/product/aei-v1/
docs/STATUS.md
```

`docs/STATUS.md` should be updated only after publication milestones.

### 11.4 Frontend

Frontend changes are not generally authorized by this contract.

If a batch needs teacher-facing UI changes, the batch must explicitly authorize
the specific `apps/admin-web/` paths and include browser proof requirements.

---

## 12. Feature flags

Behavior-changing batches should use explicit feature flags.

Recommended initial flags:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
```

Flag requirements:

- default false unless a batch proves safe default-on behavior;
- behavior identity when off;
- rollback by disabling flag;
- no hidden source-of-truth switch;
- tenant-safe rollout posture where applicable.

Exact flag names may be refined in a batch implementation, but changes must be
recorded in the certification report.

---

## 13. Runtime constraints

All AEI v1.0 implementation must be:

- teacher-authority preserving;
- deterministic where deterministic evaluation is possible;
- confidence-aware;
- review-routing aware;
- tenant-safe;
- evidence-safe;
- rollbackable;
- API-compatible;
- scoped to supported capabilities.

No batch may introduce:

- autonomous grading for uncertain cases;
- broad source adoption from EUI;
- raw uncertified AI to parent/student surfaces;
- public unsupported capability claims.

---

## 14. Validation requirements

Each batch must run at minimum:

```text
python -m ruff check <changed python files and focused tests>
python -m pytest <focused batch tests> -q
python -m pytest tests/test_answer_sheet_eval.py tests/test_evaluation_engine.py tests/test_golden_evaluation_harness.py -q
python -c "import app.main; print('API_IMPORT_PASS')"
git diff --check
```

Additional required regression slices:

- AEI architecture/regression tests when AEI contracts are touched;
- EUI regression tests when EUI metadata is consumed;
- browser proof when UI is touched;
- security/tenant isolation tests when data access changes.

---

## 15. Golden Harness requirements

Every batch must add or update Golden Harness cases for its supported behavior.

Golden cases must include:

- stable case ID;
- subject;
- capability;
- input;
- expected reasoning/policy/review behavior;
- manual-review expectation;
- notes on supported scope.

Pulling behavior into production without Golden Harness coverage is not
allowed.

---

## 16. Rollback requirements

Each behavior-changing batch must prove rollback.

Rollback proof should include:

- flag-off behavior preserves previous output;
- no destructive schema change;
- no parent/student exposure of uncertified metadata;
- existing evaluation regression passes;
- if UI changed, browser proof with flag off.

---

## 17. Certification deliverables

Each implementation batch must produce a certification report under:

```text
docs/product/aei-v1/
```

Suggested report names:

```text
AEI_V1_BATCH_A_MATH_NORMALIZATION_CERTIFICATION_REPORT.md
AEI_V1_BATCH_B_REVIEW_POLICY_CERTIFICATION_REPORT.md
AEI_V1_BATCH_C_EVIDENCE_LEDGER_CERTIFICATION_REPORT.md
AEI_V1_BATCH_D_LANGUAGE_OCR_ASSIST_CERTIFICATION_REPORT.md
AEI_V1_BATCH_E_VISUAL_SCIENCE_ASSIST_CERTIFICATION_REPORT.md
AEI_V1_CERTIFICATION_REPORT.md
```

Each report must include:

- scope review;
- changed-file inventory;
- feature flag posture;
- focused tests;
- regression tests;
- Golden Harness evidence;
- behavior-change proof;
- rollback proof;
- explicit unchanged surfaces;
- risks and retrospective.

---

## 18. Explicitly not authorized

This contract does not authorize:

- universal grading;
- fully autonomous grading;
- EUI source adoption / Phase 7F implementation;
- report-card automation;
- ERP expansion;
- destructive database migrations;
- breaking `/api/v1` changes;
- parent/student exposure of uncertified AI;
- universal handwriting OCR;
- full visual grading;
- full chemistry structure grading;
- broad UI redesign;
- new third-party AI provider integration;
- bypassing the LLM gateway.

---

## 19. ARM decision

ARM review result:

```text
Accepted - authorize AEI v1.0 Batch A only.
```

This acceptance authorizes:

```text
AEI v1.0 Batch A - Maths normalization and deterministic equivalence
```

This acceptance does not authorize:

```text
Batch B, Batch C, Batch D, Batch E, Batch F, or any out-of-scope behavior
```

Batch A implementation may begin within this contract only.
