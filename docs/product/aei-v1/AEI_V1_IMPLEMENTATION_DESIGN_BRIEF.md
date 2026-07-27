# AEI v1.0 Implementation Design Brief

- **Program:** Academic Evaluation Intelligence v1.0
- **Artifact:** Implementation design brief
- **Classification:** Product implementation design
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Architecture baseline:** [`../../architecture/AEI.md`](../../architecture/AEI.md)
- **EUI baseline:** [`../../architecture/EUI.md`](../../architecture/EUI.md)
- **Readiness baseline:** [`./AEI_PRODUCTION_READINESS_REVIEW.md`](./AEI_PRODUCTION_READINESS_REVIEW.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

This design brief converts the accepted AEI Production Readiness Review into a
concrete implementation design for Academic Evaluation Intelligence v1.0.

AEI v1.0 should make the teacher evaluation workflow production-grade for the
supported scope.

The work should now move from protected/passive AEI foundations to
school-visible teacher-trust behavior.

This design does not authorize implementation.

---

## 2. Product outcome

AEI v1.0 should let a teacher evaluate supported academic answers with:

- natural Maths equivalence;
- unit, tolerance, scientific-notation, and acceptable-answer handling;
- confidence and manual-review visibility;
- clear teacher override;
- evidence-backed suggestions;
- approved-evidence-only downstream propagation;
- honest assist/checklist handling for language/OCR, visual, and science cases.

The teacher remains the final authority.

---

## 3. Core principle

AEI v1.0 must follow the product loop:

```text
Curriculum
    |
    v
Question Paper
    |
    v
Evaluation
    |
    v
Teacher Review
    |
    v
Learning Gaps
    |
    v
Student / Parent / Principal Intelligence
```

Everything in AEI v1.0 should strengthen this loop.

Nothing in AEI v1.0 should create autonomous grading authority.

---

## 4. Architecture posture

The frozen AEI architecture remains in force:

```text
Evaluation Service
        |
        v
Subject Capability Registry
        |
        v
AcademicAnswer
        |
        v
Academic Understanding Engine
        |
        v
Academic Reasoning Layer
        |
        v
Evaluation Policy
        |
        v
Teacher Review
        |
        v
Evidence Ledger
        |
        v
Learning Intelligence
```

AEI v1.0 is not a new subsystem.

AEI v1.0 is production integration and hardening of the protected AEI
subsystem for teacher-trust evaluation.

---

## 5. Existing foundations to reuse

### 5.1 AEI foundation

Reuse:

- `AcademicAnswer`;
- Academic Understanding Engine;
- Academic Reasoning Engine;
- Evaluation Policy;
- Teacher Review contract;
- Subject Capability Registry;
- Golden Harness;
- Passive/shadow integration evidence.

Do not introduce parallel evaluation logic.

### 5.2 Existing evaluation runtime

Reuse:

- answer-sheet evaluation lifecycle;
- approved question-paper linkage;
- rubric fetch;
- existing objective/subjective suggestion shape;
- teacher approval endpoint;
- teacher overrides;
- evidence ledger response;
- exam mark persistence;
- misconception extraction.

### 5.3 EUI support layers

Reuse where internal metadata is helpful:

- Educational Identity;
- Educational Context;
- Platform Capability Registry;
- Trust Report foundation;
- AEI rich evidence binding;
- divergence/readiness evidence.

Do not perform EUI source adoption in AEI v1.0. Phase 7F remains deferred.

---

## 6. Supported-scope policy

AEI v1.0 must be complete inside declared support boundaries.

Supported means:

- capability is declared in the capability registry;
- deterministic or assist/checklist behavior is implemented;
- Golden Harness coverage exists;
- manual-review fallback is defined;
- teacher authority is preserved;
- product claims match certified behavior.

AEI v1.0 must not claim universal grading.

---

## 7. Production behavior design

### 7.1 Deterministic first

Use deterministic AEI reasoning where possible:

- fractions;
- decimals;
- mixed numbers;
- Unicode fractions;
- scientific notation;
- configured acceptable answers;
- configured units;
- configured numeric tolerance.

LLMs may support subjective/rubric suggestions, but deterministic cases should
not depend on LLMs.

### 7.2 Confidence as workflow, not marks

Confidence should influence review state and teacher messaging.

Confidence should not directly award marks outside deterministic supported
rules.

### 7.3 Manual review on uncertainty

Any unsupported, ambiguous, low-confidence, assist-only, checklist-only, or
manual-review capability must route to teacher review.

### 7.4 Teacher certification

Suggestions become authoritative only after teacher approval.

Teacher override must remain available and auditable.

### 7.5 Approved evidence only

Downstream student, parent, and principal intelligence must use approved
evidence only.

---

## 8. Data and API posture

AEI v1.0 should avoid schema/API changes unless a batch-specific authorization
explicitly permits them.

Preferred first posture:

- additive suggestion metadata where existing JSON payloads already support it;
- no breaking `/api/v1` changes;
- no public endpoint changes unless separately authorized;
- no database migration unless a batch demonstrates necessity;
- no parent/student UI exposure of uncertified AI.

If a schema/API/UI change becomes necessary, it must be isolated into the
relevant implementation authorization contract.

---

## 9. Suggested production suggestion metadata

AEI v1.0 should converge production suggestions toward a stable metadata shape.

Candidate fields:

```text
aei_enabled
aei_method
aei_reasoning_type
aei_policy_decision
manual_review_required
manual_review_reason
capability_mode
matched_acceptable_answer
normalized_answer
interpreted_value
matched_value
unit_result
tolerance_result
confidence_reason
evidence_summary
teacher_review_status
```

These fields should remain internal/teacher-facing unless explicitly approved
for downstream views.

---

## 10. Implementation batch design

### Batch A - Maths normalization and deterministic equivalence

Goal:

Make supported Maths objective and short-answer evaluation production-grade.

Design:

- build a production AEI adapter for objective/short supported Maths answers;
- convert rubric/answer-key data into `AcademicAnswer` reasoning context;
- use Academic Understanding + Reasoning + Policy;
- award marks only for deterministic supported equivalence;
- route ambiguous/unsupported cases to manual review;
- preserve existing production behavior where AEI cannot safely apply.

Capabilities:

- numeric equivalence;
- fraction/decimal/mixed-number equivalence;
- Unicode fractions;
- scientific notation;
- acceptable answers;
- numeric tolerance;
- required/allowed units.

Expected tests:

- exact existing objective behavior preserved;
- `1/2`, `0.5`, `50%`, `½` where rubric allows;
- `11/2`, `5.5`, `5½` where rubric allows;
- scientific notation equivalence;
- unit match/mismatch;
- tolerance edge cases;
- unsupported symbolic answers route to review;
- no autonomous grading for ambiguous cases.

### Batch B - Confidence, manual review, and teacher override

Goal:

Make uncertainty and teacher authority explicit in production suggestions.

Design:

- expose AEI policy output as suggestion metadata;
- add manual-review flags and reasons;
- keep low-confidence and assist/checklist cases review-required;
- strengthen teacher override audit metadata;
- ensure override reason is available where teacher changes suggestion.

Expected tests:

- low confidence routes to manual review;
- unsupported capability routes to manual review;
- assist/checklist routes to manual review;
- override preserves final marks;
- override reason/audit metadata is retained;
- production marks are not finalized without teacher approval.

### Batch C - Evidence ledger and approved evidence propagation

Goal:

Make AEI evidence safe for downstream intelligence.

Design:

- include safe AEI metadata in evaluation evidence where appropriate;
- distinguish AI suggestion, teacher decision, and final approved marks;
- ensure parent/student downstream surfaces use only approved evidence;
- preserve existing evidence ledger contract.

Expected tests:

- original suggestion visible internally;
- final teacher decision recorded;
- approved evidence flows to correction/learning evidence;
- parent/student-facing outputs do not expose uncertified AI;
- existing evidence ledger tests continue to pass.

### Batch D - Language and OCR assist support boundary

Goal:

Make language/OCR assist useful without overclaiming.

Design:

- declare supported OCR/language posture through capability registry;
- attach OCR/language confidence metadata where available;
- route handwriting/low-confidence Indic extraction to teacher review;
- keep Hindi/Telugu/Sanskrit grading manual-review unless explicitly supported;
- support code-mixed language metadata as assistive context only.

Expected tests:

- printed OCR assist metadata;
- low-confidence OCR manual review;
- Hindi/Telugu/Sanskrit handwriting assist manual review;
- language/script/code-mixed metadata does not finalize marks;
- teacher correction path remains authoritative.

### Batch E - Visual and science assist support boundary

Goal:

Make visual/science support useful as checklist/assist evidence.

Design:

- keep chemistry equations/reaction balancing as assist unless supported;
- keep chemistry structures manual-review;
- keep diagrams, maps, graphs, circuits as checklist/manual-review;
- include bounded evidence summaries;
- prevent full marks from checklist-only evidence without teacher confirmation.

Expected tests:

- chemical equation balanced/unbalanced evidence;
- graph/map checklist evidence;
- biology/geometry visual checklist evidence;
- structures route to manual review;
- checklist-only output cannot certify marks autonomously.

### Batch F - AEI v1.0 certification

Goal:

Certify product readiness for the supported AEI v1.0 scope.

Design:

- capability matrix;
- Golden Harness expansion;
- runtime proof;
- browser proof for changed teacher surfaces;
- evidence ledger proof;
- approved-evidence downstream proof;
- rollback proof;
- performance proof;
- security/tenant-safety proof.

---

## 11. Recommended implementation order

```text
Batch A - Maths normalization and deterministic equivalence
Batch B - Confidence, manual review, and teacher override
Batch C - Evidence ledger and approved evidence propagation
Batch D - Language and OCR assist support boundary
Batch E - Visual and science assist support boundary
Batch F - AEI v1.0 certification
```

Batch A should come first because obvious Maths equivalence failures are the
fastest way to damage teacher trust.

Batch B should follow immediately because every uncertain result must become
reviewable.

---

## 12. Feature flag posture

AEI v1.0 production integration should use explicit flags where behavior
changes.

Recommended initial flags:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
```

Each batch contract may refine the exact flag names.

Flag requirements:

- default false unless a batch proves safe default-on behavior;
- tenant-safe if used for rollout;
- rollback by disabling flag;
- no hidden source-of-truth switch;
- behavior identity proof where flag is off.

---

## 13. Golden Harness strategy

AEI v1.0 should expand Golden Harness from architecture/regression foundation
to product-readiness certification.

Required case families:

- Maths equivalence;
- units;
- tolerance;
- scientific notation;
- acceptable answers;
- low confidence/manual review;
- teacher override;
- language/OCR assist;
- visual checklist;
- chemistry/science assist;
- evidence ledger approved-evidence propagation.

Golden cases should include stable IDs, subject, grade/board context where
available, input, expected AEI behavior, expected review posture, and notes.

---

## 14. UI posture

This design does not authorize UI implementation.

If a batch later touches UI, teacher-facing UI should show:

- suggested marks;
- confidence/review posture;
- reason for match or review;
- capability mode;
- evidence summary;
- teacher override action and reason.

UI should not show:

- raw technical traces;
- uncertified parent/student evidence;
- autonomous grading language;
- unsupported capability claims.

---

## 15. Runtime and browser proof expectations

Each behavior-changing batch should provide runtime proof.

UI-changing batches should provide browser proof.

Certification should include:

- focused tests;
- existing evaluation regression;
- AEI/EUI regression slice;
- API import;
- `git diff --check`;
- feature flag off/on behavior;
- rollback proof;
- no schema/API/UI change proof where excluded.

---

## 16. Explicit non-goals

AEI v1.0 is not:

- an autonomous grading engine;
- a universal OCR system;
- a full handwriting solver;
- a universal visual grader;
- a full symbolic algebra/CAS engine;
- a full chemistry structure evaluator;
- a report-card automation release;
- an ERP expansion;
- an EUI source-adoption phase.

---

## 17. Risks and controls

| Risk | Control |
|---|---|
| Maths overengineering | Keep Batch A to deterministic supported equivalence and rubric config |
| Low-confidence output looking final | Batch B manual-review metadata and UI/copy discipline |
| Evidence leakage downstream | Batch C approved-evidence-only certification |
| OCR overclaiming | Batch D assist/manual-review boundaries |
| Visual/science hallucination | Batch E checklist/manual-review-only posture |
| Regression in certified evaluation | Batch-by-batch flags, tests, and rollback |
| Architecture drift | All evaluation behavior must flow through AEI pipeline |

---

## 18. ARM decision

ARM review result:

```text
Accepted - proceed to AEI v1.0 Implementation Authorization Contract.
```

This acceptance applies to the implementation design brief only.

It does not authorize implementation.

---

## 19. Next artifact if accepted

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/aei-v1/AEI_V1_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

That contract must define:

- exact batch authorization model;
- permitted repository boundary;
- feature flags;
- validation requirements;
- rollback requirements;
- certification deliverables;
- explicit exclusions.

No implementation may begin until that contract is accepted by ARM.
