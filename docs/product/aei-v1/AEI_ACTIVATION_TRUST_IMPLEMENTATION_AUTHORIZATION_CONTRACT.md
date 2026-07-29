# AEI Activation / Trust Implementation Authorization Contract

- **Program:** Academic Evaluation Intelligence v1.0 product-facing readiness
- **Gate:** AEI Activation / Trust
- **Classification:** Implementation authorization contract
- **Authorization ID:** AEI-ACTIVATION-TRUST-AUTH-001
- **Status:** Accepted
- **Implementation:** Authorized for AEI Activation / Trust only
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_ACTIVATION_TRUST_DESIGN_BRIEF.md`](./AEI_ACTIVATION_TRUST_DESIGN_BRIEF.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Teacher evaluation experience baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **Operational Proof baseline:** [`../operational-proof/OPERATIONAL_PROOF_CERTIFICATION_REPORT.md`](../operational-proof/OPERATIONAL_PROOF_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Authorization status

ARM accepts this contract and authorizes implementation only for the AEI
Activation / Trust gate described below.

Completion of this gate does not authorize UX-D, source-of-truth switching,
product rollout, public capability claim expansion, or any later gate.

---

## 2. Purpose

Authorize a controlled AEI Activation / Trust implementation gate that proves
the certified AEI v1.0 supported capabilities can execute together, remain
teacher-governed, and produce trustworthy runtime evidence.

The guiding question is:

> Can StudyNexs run the supported AEI v1.0 capability set under a controlled
> activation profile while preserving teacher authority, approved-evidence-only
> downstream posture, and rollback safety?

---

## 3. Implementation scope

Implementation is authorized only for:

1. defining a controlled AEI v1.0 activation profile using existing default-off
   AEI feature flags;
2. adding a default-off manual-review acknowledgement enforcement gate if
   needed for safe rollout;
3. executing the certified AEI v1.0 capability families together in controlled
   runtime proof;
4. ensuring manual-review-required suggestions cannot be approved silently when
   acknowledgement enforcement is enabled;
5. recording manual-review acknowledgement evidence through existing evaluation
   metadata shapes;
6. expanding the AEI Golden Harness with a teacher-marked or
   teacher-modeled trust dataset;
7. adding focused backend tests for activation, rollback, acknowledgement,
   capability execution, and approved-evidence boundaries;
8. adding or updating browser proof for UX-A, UX-B, and UX-C teacher evaluation
   surfaces;
9. adding operational metrics/structured logs for activation/trust execution;
10. producing the AEI Activation / Trust certification report.

This gate is an activation/trust proof. It is not a broad product rollout.

---

## 4. Authorized repository boundary

### 4.1 Backend configuration

Implementation may modify:

- `apps/api/app/core/config.py`

Allowed configuration changes:

- preserve all existing AEI feature-flag defaults as `False`;
- add at most one new default-false gate for manual-review acknowledgement
  enforcement if implementation needs a separate rollback switch.

Recommended flag name if needed:

```text
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=false
```

No feature flag may default to `true` in committed code.

### 4.2 Backend evaluation runtime

Implementation may modify:

- `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py`
- `apps/api/app/modules/examinations/endpoints/evaluation.py`
- `apps/api/app/modules/examinations/schemas/evaluation.py`

Allowed changes:

- additive, backward-compatible acknowledgement handling in the existing
  approval flow;
- validation that blocks approval only when the acknowledgement gate is enabled
  and AEI metadata marks one or more questions as manual-review-required;
- safe metadata capture using existing `teacher_overrides` or additive
  optional schema fields;
- no change to mark calculation except preventing silent approval of
  review-required cases when the acknowledgement gate is enabled.

Any schema change must be additive and backward-compatible under the `/api/v1`
stability policy.

### 4.3 Backend AEI services

Implementation may add:

- `apps/api/app/modules/examinations/services/aei_activation_trust.py`

Implementation may modify only as needed:

- `apps/api/app/modules/examinations/services/aei_v1_math_normalization.py`
- `apps/api/app/modules/examinations/services/aei_v1_review_policy.py`
- `apps/api/app/modules/examinations/services/aei_v1_evidence_ledger.py`
- `apps/api/app/modules/examinations/services/aei_v1_language_ocr_assist.py`
- `apps/api/app/modules/examinations/services/aei_v1_visual_science_assist.py`
- `apps/api/app/modules/examinations/services/aei_passive_integration.py`

Allowed changes:

- orchestration or proof helpers;
- extraction of common review-required detection;
- deterministic metadata handling for supported cases;
- safe observability around activation/trust execution.

These files must not introduce broader grading logic, new AI inference,
provider calls, OCR engine calls, or source-of-truth switching.

### 4.4 AEI data and Golden Harness

Implementation may add or modify:

- `apps/api/tests/golden/aei_v1/*activation*trust*.json`
- `apps/api/tests/golden/aei_v1/*teacher*marked*.json`
- `apps/api/tests/test_golden_evaluation_harness.py`

Allowed changes:

- teacher-marked or teacher-modeled cases;
- stable case IDs;
- expected manual-review acknowledgement posture;
- expected supported/assist/checklist capability modes;
- expected approved-evidence posture.

Golden data must not contain real student PII, real teacher PII, or real school
secrets.

### 4.5 Backend tests

Implementation may add:

- `apps/api/tests/test_aei_activation_trust.py`

Implementation may modify focused existing tests only where directly related:

- `apps/api/tests/test_answer_sheet_eval.py`
- `apps/api/tests/test_evaluation_engine.py`
- `apps/api/tests/test_aei_v1_math_normalization.py`
- `apps/api/tests/test_aei_v1_review_policy.py`
- `apps/api/tests/test_aei_v1_evidence_ledger.py`
- `apps/api/tests/test_aei_v1_language_ocr_assist.py`
- `apps/api/tests/test_aei_v1_visual_science_assist.py`

### 4.6 Frontend teacher evaluation proof

Implementation may modify the existing teacher evaluation surface only as
needed for acknowledgement and proof:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`

Implementation may modify the existing display helper if needed:

- `apps/admin-web/src/lib/aei-evaluation-display.ts`

Allowed frontend changes:

- show or require manual-review acknowledgement for review-required questions;
- preserve UX-A trust metadata display;
- preserve UX-B teacher-authored override reason workflow;
- preserve UX-C evidence and approved-decision panel;
- render safe disabled/no-metadata fallbacks;
- add browser-proof selectors or test-friendly labels if needed.

Frontend changes must not implement UX-D, add a new route, add new product
analytics, or expose unapproved evidence to student/parent/principal surfaces.

### 4.7 Browser proof artifacts

Implementation may add or modify existing smoke/e2e proof artifacts only for
the teacher evaluation route.

Allowed locations:

- `apps/admin-web/e2e-smoke.cjs`
- `apps/admin-web/tests/**`
- `docs/product/aei-v1/browser-proof/**`

If the existing project structure does not support automated browser proof, the
certification report must record the exact limitation and provide manual or
screenshot-based proof only if ARM accepts that caveat.

### 4.8 Documentation

Implementation may add:

- `docs/product/aei-v1/AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md`

Post-publication status updates must be committed separately:

- `docs/STATUS.md`

---

## 5. Protected repository areas

The following must not be changed without separate ARM authorization:

- database models;
- Alembic migrations;
- student portal;
- parent portal;
- principal/admin intelligence surfaces;
- billing/payment code;
- tenant management code;
- RBAC/authentication primitives;
- EUI source adoption / Phase 7F implementation;
- Platform Capability Registry product-claim surfaces;
- OCR provider integration;
- LLM gateway/provider integration;
- report-card generation;
- public marketing pages.

---

## 6. Feature-flag posture

### 6.1 Existing AEI flags

Existing AEI v1.0 feature flags remain default-off in committed code:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
```

The implementation may document and test a staging/internal activation profile
that enables these flags through environment configuration.

### 6.2 Manual-review acknowledgement gate

If a separate enforcement gate is added, it must default to false:

```text
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=false
```

When false:

- existing approval behavior remains unchanged;
- no manual-review acknowledgement is required;
- rollback is immediate by disabling the flag.

When true:

- any question marked `manual_review_required = true` must be acknowledged by
  the teacher before approval;
- the acknowledgement must be captured in an auditable metadata shape;
- marks remain teacher-controlled.

### 6.3 Production rollout

No production rollout is authorized by this contract.

Enabling flags in a real school production environment requires separate ARM
rollout authorization after certification evidence is accepted.

---

## 7. Runtime constraints

Implementation must be:

- deterministic for all deterministic supported cases;
- feature-flag guarded;
- rollback-safe;
- tenant-safe;
- exception-safe;
- bounded to existing teacher evaluation flow;
- non-authoritative for assist/checklist outputs;
- compatible with legacy evaluations without AEI metadata;
- compatible with existing approved evaluations;
- aligned with the supported scope matrix.

Implementation must not:

- change marks without teacher action;
- approve manual-review-required cases silently when acknowledgement enforcement
  is enabled;
- expose unapproved AEI evidence to students, parents, or principals;
- introduce new AI inference;
- introduce new OCR execution;
- introduce broad asynchronous workflows;
- weaken tenant scoping.

---

## 8. Manual-review acknowledgement contract

Manual-review acknowledgement is authorized only as a teacher-governance
mechanism.

It may record:

- question identifier;
- review-required reason;
- teacher acknowledgement boolean;
- teacher action such as `accepted`, `adjusted`, or `rejected`;
- override reason where marks are changed;
- reviewer identifier where already available in the approval flow;
- timestamp where already available in the approval flow.

It must not record:

- raw OCR text in unsafe logs;
- raw student PII in metrics;
- new persistent audit tables;
- hidden auto-approval decisions;
- model/provider outputs beyond existing suggestion metadata.

If acknowledgement data is stored inside existing `teacher_overrides`, the
shape must be documented in the certification report and tested.

---

## 9. Observability requirements

Implementation should add low-cardinality operational evidence for:

```text
aei_activation.invoked
aei_activation.completed
aei_activation.failed
aei_activation.duration
aei_activation.manual_review.required
aei_activation.manual_review.acknowledged
aei_activation.teacher_override.recorded
aei_activation.approved_evidence.emitted
```

Capability-family counters may be added if the repository already has a safe
metrics pattern for them:

```text
aei_activation.capability.math.normalization_applied
aei_activation.capability.language_ocr.assist_applied
aei_activation.capability.visual_science.assist_applied
```

Metrics and logs must not include:

- raw answer text;
- OCR text;
- student names;
- teacher names;
- school names;
- uploaded filenames;
- high-cardinality tenant/student/question identifiers.

If existing observability primitives are insufficient, implementation should
prefer structured logs over introducing a new metrics subsystem.

---

## 10. Golden Harness requirements

The Golden Harness must include teacher-trust cases covering:

- deterministic Maths equivalence;
- acceptable answers;
- unit/tolerance/scientific notation edge cases;
- blank or low-confidence answers;
- unsupported/ambiguous cases;
- language/OCR assist posture;
- visual/science checklist posture;
- manual-review acknowledgement expectation;
- teacher override expectation;
- approved-evidence downstream posture.

Each case must include:

- stable ID;
- subject;
- capability family;
- input shape;
- expected supported/assist/checklist/manual-review mode;
- expected `manual_review_required` posture;
- expected acknowledgement posture;
- expected evidence posture;
- safe notes explaining the trust scenario.

---

## 11. Browser proof requirements

Browser proof must cover the canonical route:

```text
apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx
```

Required proof:

- UX-A trust metadata remains visible;
- UX-B override reason workflow remains usable;
- UX-C evidence and approved-decision panel remains visible;
- manual-review-required questions show acknowledgement affordance;
- approval cannot proceed silently for review-required questions when the
  acknowledgement gate is enabled;
- disabled/no-AEI metadata fallback remains safe;
- no console errors on the covered path if automated browser proof is available.

This contract does not authorize UX-D.

---

## 12. Validation requirements

Before ARM acceptance, implementation must provide evidence for:

### 12.1 Backend validation

```text
python -m ruff check <changed API files and focused tests>
python -m pytest tests/test_aei_activation_trust.py -q
python -m pytest tests/test_golden_evaluation_harness.py -q
python -m pytest <affected AEI/evaluation regression slice> -q
python -c "import app.main; print('API_IMPORT_PASS')"
git diff --check
```

### 12.2 Frontend validation

If frontend files are changed:

```text
npm run build
npm run lint
```

If browser/e2e proof is available:

```text
node e2e-smoke.cjs
```

If frontend validation is blocked by pre-existing debt, the certification
report must record the exact blocker, evidence that it predates the
implementation, and the reduced proof that was executed.

### 12.3 Regression validation

Required regression evidence:

- existing evaluation behavior unchanged with all AEI flags disabled;
- teacher approval behavior unchanged when acknowledgement gate is disabled;
- existing AEI v1.0 tests pass;
- existing UX-A, UX-B, and UX-C behavior preserved;
- parent/student evidence boundary preserved.

---

## 13. Rollback proof

Rollback must be proven by disabling the activation profile.

Expected rollback state:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=false   # if added
```

Rollback proof must show:

- existing approval behavior returns to prior behavior;
- existing evaluation output remains available;
- no migration rollback is needed;
- no consumer/source switch rollback is needed;
- no data cleanup is required beyond ignoring optional metadata.

---

## 14. Certification deliverable

Implementation must produce:

```text
docs/product/aei-v1/AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md
```

The report must include:

- implementation summary;
- changed-file inventory;
- feature-flag posture;
- manual-review acknowledgement evidence;
- Golden Harness results;
- browser proof results;
- backend validation results;
- frontend validation results if applicable;
- regression evidence;
- rollback evidence;
- explicit statement that UX-D remains unauthorized;
- explicit statement that production rollout remains unauthorized;
- explicit statement that parent/student evidence remains approved-only.

---

## 15. Explicit exclusions

This contract does not authorize:

- production flag enablement;
- real school rollout;
- Teacher Evaluation UX-D;
- source-of-truth switching from AEI to EUI;
- EUI Phase 7F source adoption;
- new database tables;
- Alembic migrations;
- breaking `/api/v1` changes;
- new public API routes;
- new frontend routes;
- student/parent/principal UI changes;
- automatic marks for assist/checklist/manual-review cases;
- new OCR provider integration;
- new LLM/model inference;
- universal OCR or handwriting claims;
- autonomous language grading;
- autonomous visual grading;
- report-card automation;
- product marketing claim expansion;
- billing, tenant-management, or school-operations changes.

---

## 16. Exit criteria

AEI Activation / Trust is complete only when all of the following are true:

1. controlled activation profile is documented and tested;
2. all existing AEI v1.0 flags remain default-off in committed code;
3. manual-review acknowledgement enforcement works when enabled and is absent
   when disabled;
4. certified AEI v1.0 capability families execute in controlled runtime proof;
5. teacher-marked Golden set passes;
6. browser proof for UX-A, UX-B, and UX-C is completed or accepted with a
   clearly documented caveat;
7. approved-evidence-only downstream boundary is preserved;
8. parent/student views do not consume unapproved AEI suggestions;
9. rollback by disabling flags is proven;
10. certification report is complete;
11. ARM accepts the implementation before commit.

---

## 17. Recommended commit metadata

If implementation is later accepted by ARM, recommended metadata is:

```text
Commit: feat(aei): add activation trust runtime proof foundation
Tag: aei-activation-trust-certified
```

Do not commit or tag until ARM reviews and accepts the completed
implementation.
