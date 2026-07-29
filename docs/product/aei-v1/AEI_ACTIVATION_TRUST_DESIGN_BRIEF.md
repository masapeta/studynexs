# AEI Activation / Trust Design Brief

- **Program:** Academic Evaluation Intelligence v1.0 product-facing readiness
- **Gate:** AEI Activation / Trust
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized by this document
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Architecture baseline:** [`../../architecture/AEI.md`](../../architecture/AEI.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Teacher evaluation experience baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **Operational Proof baseline:** [`../operational-proof/OPERATIONAL_PROOF_CERTIFICATION_REPORT.md`](../operational-proof/OPERATIONAL_PROOF_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)
- **ARM review:** Accepted; implementation remains separately gated

---

## 1. Purpose

AEI v1.0 is certified for the declared supported scope, and Operational Proof
has shown that StudyNexs can run, observe, back up, restore, and smoke-test a
production-like runtime.

The next trust question is different:

> Can the supported AEI v1.0 capabilities be activated in a controlled runtime
> profile, produce trustworthy evidence, and remain governed by teacher review
> before any broader product-facing expansion?

This design brief defines the AEI Activation / Trust gate.

It does not authorize implementation, feature-flag enablement, production
rollout, API changes, schema changes, UI changes, source switching, or product
claim expansion. Those require a separate ARM implementation authorization
contract.

---

## 2. Core principle

The purpose of this gate is not to make AEI exciting.

The purpose is to make AEI safe enough to trust.

```text
Supported AEI capability
        |
        v
Controlled activation profile
        |
        v
Runtime evidence
        |
        v
Teacher review acknowledgement
        |
        v
Approved evidence only
```

The product rule remains:

```text
AI recommends. Teacher decides. Evidence explains.
```

---

## 3. Why this gate is needed now

AEI v1.0 batches established the foundations:

- Maths normalization and deterministic equivalence metadata;
- confidence, manual-review, and teacher-override metadata;
- approved-evidence ledger metadata;
- language/OCR assist metadata;
- visual/science checklist metadata;
- teacher-facing UX-A, UX-B, and UX-C evidence display surfaces.

However, most AEI runtime flags remain default-off. That was correct during
foundation work.

Before UX-D or any broader school-visible workflow expansion, StudyNexs needs
runtime proof that the supported capabilities actually execute together under a
controlled profile, that uncertainty is not hidden, and that teacher authority
is operationally enforced.

This gate bridges:

```text
Certified foundations
        |
        v
Controlled runtime activation evidence
        |
        v
Product-facing completion work
```

---

## 4. Product outcome

After this gate is completed and certified, the engineering team should be able
to truthfully state:

1. AEI v1.0 supported capabilities can be enabled in a controlled runtime
   profile without changing public product claims;
2. deterministic Maths normalization/equivalence executes for supported cases;
3. language/OCR assist and visual/science assist execute only within their
   declared assist/checklist boundaries;
4. uncertain, unsupported, low-confidence, blank, or ambiguous outputs require
   teacher review;
5. teacher manual-review acknowledgement is enforced before final approval
   where review is required;
6. teacher-approved evidence remains the only downstream authority;
7. UX-A, UX-B, and UX-C surfaces render the trust, override, and evidence
   posture correctly in browser proof;
8. rollback is simple: disable the activation profile and return to the
   previous default-off posture.

---

## 5. Responsibilities

AEI Activation / Trust is responsible for proving:

- controlled AEI v1.0 flag enablement under an explicitly named profile;
- runtime execution of the certified AEI v1.0 capability families;
- teacher-review acknowledgement enforcement for manual-review-required cases;
- real or representative teacher-marked Golden set coverage;
- browser proof for existing teacher evaluation UX-A, UX-B, and UX-C surfaces;
- operational metrics and structured logs for activation/trust execution;
- rollback by disabling activation flags;
- preservation of teacher authority and approved-evidence-only downstream
  posture.

AEI Activation / Trust is not responsible for:

- expanding AEI beyond the declared supported scope;
- introducing autonomous grading;
- enabling universal OCR, handwriting, language grading, or visual grading;
- implementing Teacher Evaluation UX-D;
- changing student, parent, or principal experiences;
- switching AEI to EUI as a source of truth;
- introducing new database schema;
- changing public API contracts;
- adding a new OCR, LLM, or AI provider;
- changing marks without teacher authority;
- changing gradebook, mastery, report-card, or evidence-ledger source
  semantics outside the accepted AEI v1.0 contracts.

---

## 6. Existing foundations to reuse

The implementation must reuse the existing AEI and teacher-evaluation
foundations. It must not create a parallel evaluation path.

| Existing asset | Expected role |
|---|---|
| `apps/api/app/core/config.py` | Existing AEI feature flags and default-off posture. |
| `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py` | Existing evaluation integration point. |
| `apps/api/app/modules/examinations/services/aei_v1_math_normalization.py` | Certified Maths normalization/equivalence foundation. |
| `apps/api/app/modules/examinations/services/aei_v1_review_policy.py` | Certified confidence/manual-review/override metadata foundation. |
| `apps/api/app/modules/examinations/services/aei_v1_evidence_ledger.py` | Certified approved-evidence metadata foundation. |
| `apps/api/app/modules/examinations/services/aei_v1_language_ocr_assist.py` | Certified language/OCR assist metadata foundation. |
| `apps/api/app/modules/examinations/services/aei_v1_visual_science_assist.py` | Certified visual/science checklist metadata foundation. |
| `apps/api/app/modules/examinations/services/aei_passive_integration.py` | Existing passive AEI runtime integration posture. |
| `apps/api/app/modules/examinations/data/subject_capability_registry.v1.json` | AEI supported-scope source of truth. |
| `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx` | Canonical teacher evaluation surface. |
| `apps/admin-web/src/app/dashboard/exams/[examId]/evaluate/page.tsx` | Legacy redirect surface. |
| `apps/api/tests/test_golden_evaluation_harness.py` | Existing AEI Golden Harness entry point. |

---

## 7. Design scope

### 7.1 Controlled activation profile

This gate should define a controlled AEI activation profile that can enable the
existing AEI v1.0 capability flags together in a staging/internal runtime
without changing code defaults.

Existing flags remain default-off in code:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
```

The activation profile should be explicit, environment-configurable, and easy
to disable.

The design preference is:

```text
code defaults remain false
        |
        v
staging/internal env profile enables selected AEI flags
        |
        v
runtime proof executes supported capabilities
        |
        v
certification records evidence
```

No implementation may silently enable AEI capabilities in production.

### 7.2 Supported capability execution

The gate should prove execution for the certified AEI v1.0 capability families:

| Capability family | Required runtime proof |
|---|---|
| Maths normalization | Fractions, decimals, mixed numbers, percentages, tolerance, scientific notation, units, and acceptable answers execute for supported cases. |
| Review policy | Low-confidence, blank, unsupported, ambiguous, and assist/checklist cases produce manual-review signals. |
| Evidence ledger metadata | Original suggestion and final teacher decision remain separate; approved evidence is teacher-decision sourced. |
| Language/OCR assist | Hindi/Telugu/Sanskrit and code-mixed/romanized assist posture remains non-authoritative and teacher-reviewed. |
| Visual/science assist | Diagram, graph, map, chemistry, and science evidence remains checklist/assist only. |

The proof must stay inside the supported scope matrix.

### 7.3 Manual-review acknowledgement

Manual review must become operationally visible and enforceable before broader
product-facing expansion.

For any item where AEI marks `manual_review_required = true`, the future
implementation should require a teacher acknowledgement before final approval.

The acknowledgement should record:

- that the teacher reviewed the uncertain item;
- the reason review was required, if available;
- whether the teacher accepted, changed, or rejected the suggestion;
- teacher-authored override reason when marks are changed;
- timestamp/source metadata where available through existing contracts.

This acknowledgement must not:

- award marks automatically;
- replace teacher approval;
- expose uncertain evidence to students or parents;
- mutate raw AEI suggestions;
- bypass the existing approval flow.

### 7.4 Real teacher-marked Golden set

The existing Golden Harness contains deterministic and synthetic capability
coverage. This gate should introduce or prepare a teacher-marked Golden set that
better represents the school trust moment.

The dataset should include anonymized or synthetic-safe cases modeled from real
teacher-marked examples, covering:

- supported deterministic Maths cases;
- tolerance and unit edge cases;
- acceptable-answer variants;
- blank answers;
- illegible or low-confidence extraction;
- language/OCR assist cases;
- visual/science checklist cases;
- teacher override cases;
- approved-evidence downstream posture.

The dataset must be safe to commit:

- no real student PII;
- no real school secrets;
- stable case IDs;
- stable expected outcomes;
- clear capability labels;
- clear review-required expectations.

### 7.5 Browser proof for UX-A, UX-B, and UX-C

This gate should provide browser-level proof that the existing teacher
evaluation experience surfaces show the trust posture correctly.

The proof should cover:

- trust metadata display from UX-A;
- teacher-authored override reason workflow from UX-B;
- evidence and approved-decision panel from UX-C;
- manual-review-required indicators;
- approved-vs-suggested distinction;
- safe behavior when AEI metadata is absent or disabled;
- responsive teacher workflow path at the canonical teaching route.

This gate should not implement UX-D.

### 7.6 Parent/student evidence boundary

The gate should explicitly verify that unapproved AEI suggestions, assist
metadata, OCR uncertainty, checklist observations, and manual-review-required
outputs do not become parent/student-facing evidence.

Only teacher-approved evidence may flow downstream.

---

## 8. Runtime modes

### 8.1 Default-off mode

Default-off remains the baseline:

```text
AEI activation flags off
        |
        v
existing product behavior
        |
        v
no user-visible change
```

This mode must remain the rollback posture.

### 8.2 Controlled activation mode

Controlled activation mode is internal/staging-first:

```text
selected AEI v1.0 flags enabled by environment
        |
        v
evaluation runs with AEI metadata generation
        |
        v
manual-review acknowledgement required where applicable
        |
        v
certification evidence collected
```

The activation mode may be used for controlled runtime proof only after a
separate implementation authorization contract.

### 8.3 Product rollout mode

Product rollout mode is not authorized by this design brief.

Moving from controlled activation to school-visible rollout requires separate
ARM authorization and must be based on certification evidence from this gate.

---

## 9. Observability

The gate should define operational observability for AEI activation and trust,
without product analytics or PII exposure.

Useful metrics include:

```text
aei_activation.invoked
aei_activation.completed
aei_activation.failed
aei_activation.duration
aei_activation.capability.math.normalization_applied
aei_activation.capability.language_ocr.assist_applied
aei_activation.capability.visual_science.assist_applied
aei_activation.manual_review.required
aei_activation.manual_review.acknowledged
aei_activation.teacher_override.recorded
aei_activation.approved_evidence.emitted
```

Metric labels must remain low-cardinality and must not include:

- student names;
- teacher names;
- school names;
- raw answers;
- OCR text;
- answer sheet filenames;
- tenant identifiers unless represented in an approved low-cardinality,
  privacy-safe form.

Structured logs may include internal request correlation IDs and capability
families, but must avoid raw student answer content unless already governed by
existing safe logging policy.

---

## 10. Testing strategy

The future implementation should include:

### 10.1 Focused backend tests

Required areas:

- activation profile default-off behavior;
- selected-flags-enabled behavior;
- deterministic Maths runtime proof;
- manual-review-required metadata;
- teacher-review acknowledgement enforcement;
- evidence ledger approved-vs-suggested separation;
- language/OCR assist remains non-authoritative;
- visual/science assist remains checklist/assist only;
- rollback by disabling flags.

### 10.2 Golden Harness

Required Golden Harness additions:

- teacher-marked Golden dataset;
- stable IDs;
- supported capability labels;
- expected manual-review posture;
- expected evidence posture;
- expected teacher override/acknowledgement posture.

### 10.3 Browser proof

Required browser proof:

- UX-A trust metadata;
- UX-B override reason workflow;
- UX-C evidence and approved-decision panel;
- manual-review-required display;
- disabled/no-metadata fallback;
- approval path remains teacher-controlled.

### 10.4 Regression validation

Required regression posture:

- existing AEI v1.0 tests pass;
- existing teacher evaluation regression tests pass;
- API import passes;
- admin-web build passes if frontend/browser proof is touched;
- no schema migration is introduced unless separately authorized;
- `git diff --check` passes.

---

## 11. Certification criteria

AEI Activation / Trust may be accepted only when certification can truthfully
state:

1. AEI v1.0 supported capabilities execute under a controlled activation
   profile;
2. code defaults remain rollback-safe and default-off unless separately
   authorized;
3. deterministic Maths supported cases produce expected metadata;
4. assist/checklist language, OCR, visual, and science cases remain
   teacher-reviewed and non-authoritative;
5. manual-review-required cases cannot be silently treated as final teacher
   decisions;
6. teacher acknowledgement and override reason behavior are verified where
   review is required;
7. original AI suggestions remain separate from final teacher decisions;
8. approved evidence remains teacher-decision sourced;
9. parent/student-facing views do not consume unapproved AEI evidence;
10. the teacher-marked Golden set passes;
11. browser proof for UX-A, UX-B, and UX-C passes or any caveat is explicitly
    documented and accepted;
12. rollback by disabling the activation profile is proven;
13. no unsupported product claim is introduced.

---

## 12. Explicit exclusions

This design brief does not authorize:

- implementation;
- production flag enablement;
- public product rollout;
- Teacher Evaluation UX-D;
- new database tables or migrations;
- public API changes;
- new frontend routes;
- student/parent/principal UI changes;
- source-of-truth switching from AEI to EUI;
- EUI Phase 7F source adoption;
- new OCR engine integration;
- new LLM inference or provider integration;
- universal handwriting OCR;
- autonomous language grading;
- autonomous visual grading;
- automatic marks for assist/checklist/manual-review cases;
- public sales/support documentation claim expansion;
- changes to billing, tenant management, or school operations.

---

## 13. Risks

| Risk | Mitigation |
|---|---|
| Activating flags creates a perception of autonomous grading. | Keep copy and workflow explicit: AI recommends, teacher decides. |
| Assist/checklist outputs are mistaken for correctness. | Require manual review and label non-authoritative evidence clearly. |
| Browser proof validates UI but not real runtime capability execution. | Require backend runtime proof and Golden Harness evidence in the same gate. |
| Golden cases are too synthetic to represent teacher trust. | Add teacher-marked or teacher-modeled cases with stable expected outcomes. |
| Rollout pressure turns staging proof into production enablement. | Keep rollout separately authorized and default-off in code. |
| Metrics accidentally expose PII. | Use low-cardinality operational metrics and safe structured logs only. |

---

## 14. Recommended implementation slices

The implementation authorization contract may choose one combined batch or split
this gate into smaller slices. A safe default sequence is:

1. activation profile and rollback proof;
2. teacher-marked Golden set expansion;
3. manual-review acknowledgement enforcement;
4. runtime capability proof for AEI v1.0 supported scope;
5. browser proof for UX-A, UX-B, and UX-C;
6. certification report.

Any split must preserve the rule that no later product-facing UX expansion is
authorized merely because this design brief exists.

---

## 15. ARM gate

This design brief is ready for ARM review.

If accepted, the next artifact should be:

```text
docs/product/aei-v1/AEI_ACTIVATION_TRUST_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

That contract must define:

- exact repository boundary;
- exact feature-flag posture;
- exact implementation scope;
- observability requirements;
- Golden Harness additions;
- browser proof expectations;
- rollback evidence;
- certification deliverables;
- explicit exclusions.

Implementation must not begin until that contract is accepted.
