# AEI Production Readiness Review

- **Program:** Academic Evaluation Intelligence v1.0
- **Artifact:** Production readiness review
- **Classification:** Readiness-to-design review
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Architecture baseline:** [`../../architecture/AEI.md`](../../architecture/AEI.md)
- **EUI baseline:** [`../../architecture/EUI.md`](../../architecture/EUI.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Executive decision

AEI is architecturally ready, but not yet product-complete.

The repository now contains the protected AEI pipeline, certified AEI
foundation batches, passive/shadow integration, EUI support layers, teacher
approval, and evidence-ledger surfaces.

However, the production evaluation workflow still relies primarily on the
legacy evaluation path:

```text
objective exact match / MCQ key match
        +
LLM or heuristic subjective suggestion
        +
teacher approval
```

AEI v1.0 should now move from protected/passive subsystem to production-grade
teacher-trust evaluation for the supported scope.

ARM decision:

```text
Accepted - proceed to AEI v1.0 Design Brief.
Do not begin implementation until ARM accepts the design brief and a separate
implementation authorization contract.
```

---

## 2. What this review is

This review answers:

> What must be implemented now to make AEI v1.0 product-complete for the
> teacher-trust evaluation workflow?

This is not a new broad gap analysis.

It is a readiness review against the already-defined AEI v1.0 production scope.

---

## 3. Product goal

Complete Academic Evaluation Intelligence v1.0.

Goal:

```text
Production-grade evaluation for the supported scope.
```

The teacher remains the final authority.

AEI v1.0 should make the evaluation workflow feel trustworthy, explainable,
reviewable, and complete inside declared support boundaries.

---

## 4. Product-success definition

AEI v1.0 is product-ready when:

- teachers trust the evaluation workflow;
- deterministic Maths equivalence works for supported cases;
- supported unit, tolerance, scientific notation, and acceptable-answer rules
  are applied consistently;
- uncertain cases route to teacher review;
- teacher override is clear, auditable, and reflected in final marks;
- evidence shows why a suggestion exists;
- parent/student views consume only teacher-approved evidence;
- language/OCR assist is honest about confidence and review posture;
- visual/science assist remains checklist/manual-review where appropriate;
- Golden Harness coverage protects supported academic behavior.

---

## 5. Current repository baseline

### 5.1 AEI architecture

Frozen architecture exists:

```text
docs/architecture/AEI.md
```

Implemented AEI layers exist under:

```text
apps/api/app/modules/examinations/schemas/
apps/api/app/modules/examinations/services/
```

Current certified AEI artifacts include:

- Batch 0 foundation / registry / Golden Harness;
- Batch 1 `AcademicAnswer`;
- Batch 2 Academic Understanding Engine;
- Batch 3 Academic Reasoning Layer;
- Batch 4 Evaluation Policy;
- Batch 5 Teacher Review Layer;
- Wave 1 passive integration;
- Wave 2 shadow mode.

Assessment:

```text
Architecture foundation: READY
Production evaluation use: PARTIAL
```

### 5.2 EUI support foundation

EUI runtime foundations now exist through Phase 7E:

- Educational Identity;
- Educational Context;
- Platform Capability Registry;
- KAI candidate foundation;
- EKG proposal foundation;
- Trust Report foundation;
- AEI consumer dual-read;
- rich EUI evidence binding;
- divergence readiness review;
- narrow source-readiness candidate;
- source-readiness trial.

Phase 7 is closed at 7E. 7F source adoption is deferred future scope.

Assessment:

```text
EUI support for AEI: AVAILABLE AS INTERNAL FOUNDATION
EUI source-of-truth switch: NOT AUTHORIZED
```

### 5.3 Current production evaluation path

Current production answer-sheet evaluation is centered in:

```text
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
```

Current marking engine:

```text
apps/api/app/modules/ai/services/evaluation_engine.py
```

Existing production behavior includes:

- answer-sheet evaluation lifecycle;
- image answer extraction path;
- objective MCQ / true-false / fill-blank exact matching;
- very-short factual key exact matching;
- subjective LLM rubric suggestion via LLM gateway;
- heuristic fallback;
- teacher approval and override;
- exam marks creation;
- misconception extraction;
- evaluation evidence ledger exposure;
- EUI/AEI passive observation and shadow comparison.

Assessment:

```text
Current evaluation workflow: FUNCTIONAL
AEI v1.0 production-grade trust behavior: INCOMPLETE
```

---

## 6. Readiness by production capability

| Capability | Current state | Production readiness | Required next action |
|---|---|---|---|
| Maths normalization | AEI reasoners support numeric equivalence, fractions, mixed numbers, and scientific notation in tests | Partial | Integrate deterministic AEI result into production suggestions for supported objective/short Maths |
| Units | Unit interpretation reasoner exists | Partial | Add rubric-driven unit config integration and manual-review fallback |
| Tolerance | Registry declares support; production path does not apply tolerance broadly | Partial | Define and implement rubric fields and deterministic tolerance comparison |
| Scientific notation | Reasoner exists and tests pass | Partial | Wire into Maths/Science answer evaluation for supported cases |
| Acceptable answers | Subjective item supports `acceptable_answers`; AEI reasoning tests use it | Partial | Make deterministic acceptable-answer handling consistent across objective/short answers |
| Confidence/manual review | AEI policy exists; production suggestions carry confidence | Partial | Convert AEI policy decisions into production manual-review metadata |
| Teacher override | Approval override exists | Partial | Add AEI-aware override reason/audit clarity and review-state metadata |
| Evidence ledger | Evaluation evidence ledger exists and tests cover approval evidence | Partial | Ensure downstream views consume approved evidence only and include AEI metadata where safe |
| Golden Harness | AEI and EUI Golden Harness foundations exist | Partial | Expand with production AEI v1.0 cases and supported-scope regression sets |
| Language/OCR assist | OCR paths and language capability registry entries exist; EUI Trust/OCR confidence foundation exists | Assist only | Define supported input quality, teacher correction, confidence, and review posture |
| Visual/science assist | Visual/science understanding and reasoning foundations exist | Assist/checklist only | Keep as checklist/manual-review, not autonomous marking |
| Parent/student approved evidence | Evidence-ledger and learning evidence tests exist | Partial | Certify no raw/uncertified AI reaches parent/student surfaces |

---

## 7. Key finding

The main remaining work is not more architecture.

The main remaining work is controlled production integration of AEI into the
teacher evaluation workflow:

```text
Answer / OCR / typed input
        |
        v
AEI deterministic understanding and reasoning
        |
        v
Evaluation policy and confidence/manual review
        |
        v
Teacher review / override
        |
        v
Approved evidence
        |
        v
Learning, student, parent, principal intelligence
```

AEI should now become visible through product behavior, but only inside the
supported scope and only with teacher authority preserved.

---

## 8. Recommended AEI v1.0 implementation batches

### Batch A - Maths normalization and deterministic equivalence

Purpose:

Make supported Maths objective/short-answer evaluation feel natural to teachers.

Scope:

- fraction / decimal / mixed-number equivalence;
- Unicode fraction handling;
- scientific notation;
- acceptable answers;
- rubric-driven numeric tolerance;
- rubric-driven units;
- deterministic confidence for exact supported matches;
- manual review for ambiguous/unsupported inputs.

Expected source areas:

```text
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
apps/api/app/modules/examinations/services/academic_understanding_engine.py
apps/api/app/modules/examinations/services/academic_reasoning_engine.py
apps/api/app/modules/examinations/services/evaluation_policy.py
apps/api/app/modules/examinations/data/subject_capability_registry.v1.json
apps/api/tests/test_answer_sheet_eval.py
apps/api/tests/test_academic_reasoning_engine.py
apps/api/tests/test_golden_evaluation_harness.py
```

Non-goals:

- full CAS;
- proof checking;
- symbolic algebra beyond supported cases;
- autonomous marks for uncertain cases.

### Batch B - Confidence, manual review, and teacher override

Purpose:

Make uncertainty visible and enforce teacher authority.

Scope:

- production suggestion metadata for AEI policy decisions;
- `manual_review_required`;
- `manual_review_reason`;
- capability mode;
- confidence reason;
- teacher override reason enforcement where needed;
- override audit metadata;
- low-confidence routing.

Non-goals:

- new UI redesign;
- source-of-truth switch;
- automatic grading for weak/uncertain cases.

### Batch C - Evidence ledger and approved evidence propagation

Purpose:

Ensure only teacher-approved evidence powers downstream intelligence.

Scope:

- AEI metadata in evidence ledger where safe;
- original suggestion vs final teacher decision;
- approved evidence contract;
- parent/student-safe evidence posture;
- regression tests for no raw uncertified AI downstream.

Non-goals:

- changing report-card rules;
- changing parent/student UI without separate authorization;
- evidence-ledger schema migration unless explicitly authorized.

### Batch D - Language and OCR assist support boundary

Purpose:

Support language/OCR reality honestly without overclaiming.

Scope:

- printed OCR assist boundary for supported languages;
- handwriting OCR assist boundary for Hindi/Telugu/Sanskrit;
- teacher correction before evaluation;
- OCR confidence metadata;
- language/script/code-mixed metadata;
- Hinglish/Tinglish tutor/evaluation assist boundaries where applicable;
- manual-review routing for low-confidence extraction.

Non-goals:

- universal handwriting OCR;
- autonomous language grading;
- voice tutor;
- dialect/slang completeness.

### Batch E - Visual and science assist support boundary

Purpose:

Make diagrams, graphs, maps, and science expressions useful but safe.

Scope:

- visual checklist metadata;
- chemistry equation assist;
- chemical symbols assist;
- chemistry structures as manual review unless explicitly supported;
- graph/map checklist assist;
- physics formula recognition assist;
- manual-review routing for all partial/checklist modes.

Non-goals:

- pixel-perfect visual grading;
- organic structure grading;
- full graph/map marks automation;
- circuit correctness automation beyond checklist support.

### Batch F - AEI v1.0 certification

Purpose:

Certify AEI v1.0 as production-ready for the declared supported scope.

Scope:

- supported-scope capability matrix;
- Golden Harness expansion;
- runtime proof;
- browser proof where UI surfaces are touched;
- evidence-ledger proof;
- parent/student approved-evidence proof;
- rollback proof;
- performance proof;
- security/tenant-safety proof.

---

## 9. Recommended order

Recommended sequence:

```text
1. AEI Production Readiness Review
2. AEI v1.0 Design Brief
3. AEI v1.0 Implementation Authorization Contract
4. Batch A - Maths normalization and deterministic equivalence
5. Batch B - Confidence, manual review, and teacher override
6. Batch C - Evidence ledger and approved evidence propagation
7. Batch D - Language and OCR assist support boundary
8. Batch E - Visual and science assist support boundary
9. AEI v1.0 Certification
```

Rationale:

- Maths normalization is the highest-frequency teacher-trust failure.
- Confidence/manual review must wrap every uncertain output.
- Evidence propagation must be safe before downstream intelligence expands.
- Language/OCR and visual/science assist should be bounded by trust policy.
- Certification should prove the declared scope, not universal capability.

---

## 10. Explicit exclusions for AEI v1.0

AEI v1.0 should not attempt:

- universal grading;
- fully autonomous marks for uncertain cases;
- full handwriting OCR reliability for every handwriting style;
- universal visual grading;
- full chemistry structure grading;
- full graph/map marks automation;
- broad EUI source adoption;
- replacing teacher authority;
- changing parent/student surfaces to show uncertified AI;
- report-card automation beyond approved evidence;
- ERP expansion.

---

## 11. Supported-scope framing

AEI v1.0 should be described as:

```text
Production-ready for supported scenarios.
```

Not:

```text
Universal AI grading.
```

Supported means:

- capability appears in the Subject Capability Registry or Platform Capability
  Registry;
- Golden Harness cases exist;
- deterministic behavior is tested;
- manual-review fallback is defined;
- teacher authority is preserved;
- product claims match actual behavior.

---

## 12. Certification expectations

AEI v1.0 certification should prove:

- deterministic Maths supported cases pass;
- unit/tolerance/scientific notation supported cases pass;
- ambiguous/unsupported cases route to manual review;
- low-confidence OCR/language cases route to manual review;
- visual/science assist does not finalize uncertain marks;
- teacher override updates final marks and audit metadata;
- evidence ledger records original suggestion and final approval;
- parent/student downstream outputs use only approved evidence;
- existing evaluation regression suite passes;
- EUI/AEI passive foundations remain stable;
- API compatibility is preserved;
- tenant isolation is preserved;
- performance remains acceptable for answer-sheet evaluation.

---

## 13. Risks

| Risk | Mitigation |
|---|---|
| Overbuilding a general Maths/CAS engine | Limit Batch A to syllabus-supported deterministic equivalence |
| Treating assist/checklist as final grading | Route partial/assist/manual-review modes to teacher confirmation |
| OCR overclaiming | Define supported input-quality boundaries and confidence/manual review |
| Parent/student seeing uncertified AI | Certify approved-evidence-only downstream propagation |
| AEI/EUI source-adoption creep | Keep 7F deferred unless real product need appears |
| UI trust overload | Show concise confidence/reason/review state, not raw technical traces |
| Regression in existing evaluation | Keep batch-by-batch certification and existing evaluation tests |

---

## 14. ARM decision

ARM review result:

```text
Accepted.
```

This acceptance applies to the readiness review only.

It does not authorize implementation.

---

## 15. Next artifact if accepted

If ARM accepts this review, the next artifact should be:

```text
docs/product/aei-v1/AEI_V1_IMPLEMENTATION_DESIGN_BRIEF.md
```

That design brief should convert this readiness review into a concrete product
design and batch implementation strategy.

Implementation remains not authorized until a later implementation
authorization contract is accepted.
