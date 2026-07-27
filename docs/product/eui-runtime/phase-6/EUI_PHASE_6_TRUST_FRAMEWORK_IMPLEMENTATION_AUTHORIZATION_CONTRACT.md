# EUI Runtime Phase 6 Implementation Authorization Contract - Trust Framework

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 6 - Trust Framework
- **Authorization ID:** EUI-PH6-TRUST-AUTH-001
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_6_TRUST_FRAMEWORK_DESIGN_BRIEF.md`](./EUI_PHASE_6_TRUST_FRAMEWORK_DESIGN_BRIEF.md)
- **Architecture baseline:** [`../../../architecture/eui/TRUST_FRAMEWORK.md`](../../../architecture/eui/TRUST_FRAMEWORK.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)

---

## 1. Authorization status

This document is the accepted implementation authorization contract for Phase 6.

Implementation is authorized only within the scope and repository boundary
defined here.

The following remain prohibited:

- production behavior changes for Phase 6;
- database schema changes;
- API changes;
- UI changes;
- runtime behavior changes;
- consumer migration;
- AEI behavior changes;
- KAI behavior expansion;
- EKG behavior expansion;
- Trust Report persistence;
- LLM-based trust generation.

---

## 2. Purpose

Phase 6 implementation should introduce a passive Trust Report foundation that
can deterministically explain trust posture for selected EUI outputs without
changing existing product behavior.

The first implementation should answer:

> Can StudyNexs produce structured Trust Reports beside existing confidence and
> review signals without changing any consumer behavior?

This implementation is report-first and non-authoritative.

---

## 3. Authorized implementation scope

If accepted, this contract authorizes only the following work.

### 3.1 Trust Report model

Introduce canonical immutable runtime/domain models for:

- `TrustReport`;
- `TrustDimension`;
- trust warning entries;
- provenance references;
- overall trust posture;
- consumer visibility classification.

The models must be JSON-serializable and strict enough to prevent silent shape
drift.

### 3.2 Deterministic Trust Report IDs

Introduce deterministic transient Trust Report IDs.

IDs should be stable for identical trust subjects and input signals.

IDs must not depend on database persistence.

### 3.3 Conservative posture calculation

Implement deterministic posture derivation using conservative precedence:

1. `unsupported`
2. `manual_review_required`
3. `insufficient_evidence`
4. `review_recommended`
5. `trusted`

The implementation must not average dimension scores into authority.

### 3.4 Trust mappers for EUI-owned subjects

Implement deterministic Trust Report builders/mappers for selected EUI outputs:

- Educational Context;
- Platform Capability Registry lookup result;
- KAI candidate;
- EKG relationship proposal.

AEI Trust Report integration is not authorized in this contract.

### 3.5 Existing confidence compatibility

Trust Reports must run alongside existing confidence fields.

The implementation may map existing confidence/review signals into Trust
dimensions, but it may not remove, rename, reinterpret, or replace existing
fields.

### 3.6 Passive observer

If runtime observation is introduced, implement a passive observer guarded by a
default-off feature flag.

The observer may:

- generate Trust Reports;
- record operational metrics;
- capture bounded in-memory evidence for validation;
- isolate exceptions.

The observer may not:

- change production results;
- enforce workflow;
- expose output to users;
- migrate consumers.

### 3.7 Feature flag

Implement or wire the Phase 6 feature flag:

```text
EUI_TRUST_REPORT_ENABLED=false
```

Requirements:

- disabled by default;
- environment configurable through existing settings patterns;
- no-op when disabled;
- rollback by disabling the flag;
- no product-visible behavior change.

### 3.8 Observability

Implement operational observability consistent with the Phase 0 baseline.

Allowed metrics/log signals include:

```text
eui_trust_report.invoked
eui_trust_report.completed
eui_trust_report.failed
eui_trust_report.manual_review
eui_trust_report.unsupported
eui_trust_report.insufficient_evidence
eui_trust_report.duration
```

Metrics and logs must avoid PII, raw educational content, raw answers, uploaded
text, raw OCR text, tenant slugs, student names, parent data, and free-text
teacher notes.

### 3.9 Golden Harness

Add Golden Harness data and tests for deterministic Trust Report behavior.

The harness should cover:

- high-quality KAI candidate trust report;
- low-confidence OCR candidate requiring review;
- Educational Context ambiguity warning;
- unsupported capability posture;
- EKG candidate proposal remaining non-authoritative;
- provenance references separate from trust dimensions;
- consumer visibility not authorizing display;
- unsupported dimension dominating otherwise strong signals;
- deterministic Trust Report IDs.

### 3.10 Certification

Produce a Phase 6 certification report demonstrating:

- Trust Report contracts exist as authorized;
- trust and provenance remain separate;
- posture precedence is conservative;
- trust generation is deterministic;
- no LLM/provider call is used to decide trust;
- existing confidence consumers remain functional;
- no consumer depends on Trust Reports;
- rollback proof;
- observability evidence;
- phase retrospective.

---

## 4. Authorized repository boundary

If accepted, repository changes are limited to the following areas.

### 4.1 Source modules

Permitted:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/
apps/api/app/modules/eui/services/
```

Not permitted:

```text
apps/api/app/modules/knowledge_graph/
apps/api/app/modules/ai/
apps/api/app/modules/evaluations/
apps/api/app/modules/exams/
apps/admin-web/
```

Any change outside the permitted source boundary requires separate ARM
authorization.

### 4.2 Tests and Golden Harness

Permitted:

```text
apps/api/tests/golden/eui_v1/
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/test_trust_report_*.py
apps/api/tests/test_eui_trust_*.py
```

Existing EUI, KG, and AEI regression tests may be run but should not be modified
unless a test-only compatibility assertion is needed and ARM accepts the reason.

### 4.3 Documentation

Permitted:

```text
docs/product/eui-runtime/phase-6/
```

`docs/STATUS.md` should be updated only after certification/publication, not in
the implementation commit.

---

## 5. Explicit exclusions

The following are not authorized:

- database schema changes;
- Alembic migrations;
- Trust Report persistence;
- API endpoint changes;
- UI changes;
- consumer migration;
- AEI behavior changes;
- AEI Trust Report integration;
- KAI behavior expansion;
- EKG behavior expansion;
- workflow enforcement;
- parent/student/principal-facing explanations;
- public trust badges;
- LLM calls to generate trust posture;
- LLM calls to generate trust explanations;
- external AI provider integration;
- removal or replacement of existing confidence fields;
- product capability claim changes.

Any of these require a separate ARM authorization and, where architectural,
possibly an ADR.

---

## 6. Runtime constraints

The implementation must be:

- passive;
- default-off;
- deterministic;
- report-only;
- provenance-aware;
- non-authoritative;
- exception-isolated;
- tenant-safe;
- hidden from users;
- compatible with existing confidence fields.

If the Phase 6 path fails, existing production behavior must continue unchanged.

---

## 7. Rollback proof

Rollback must be proven by demonstrating:

- feature flag disabled path is a no-op;
- existing confidence fields remain active;
- existing EUI outputs remain unchanged with the flag disabled;
- existing EUI outputs remain unchanged with the flag enabled;
- no persisted Trust Report data exists;
- no schema rollback is required;
- existing EUI, KG, and AEI regressions continue to pass.

---

## 8. Validation requirements

Before ARM acceptance, the implementation must provide evidence for:

### 8.1 Focused validation

- Trust Report model tests;
- Trust Dimension model tests;
- deterministic Trust Report ID tests;
- posture precedence tests;
- KAI candidate trust mapping tests;
- EKG proposal trust mapping tests;
- Educational Context trust mapping tests;
- Platform Capability Registry trust mapping tests;
- passive observer tests if observer is implemented;
- Golden Harness Trust Framework tests.

### 8.2 Regression validation

Required regression slices:

- Educational Identity tests;
- Educational Context tests;
- Platform Capability Registry tests;
- KAI tests;
- EKG proposal tests;
- existing Knowledge Graph tests;
- AEI/evaluation regression slice;
- API import.

### 8.3 Static validation

- focused Ruff for touched API files;
- `git diff --check`;
- scan proving no AI/LLM provider call was introduced in Trust Framework files;
- scan proving no persistence/write path was introduced in Trust Framework files.

---

## 9. Acceptance criteria

Phase 6 implementation may be accepted only if all of the following are true:

- Trust Report model exists as authorized;
- Trust Dimension model exists as authorized;
- deterministic Trust Report IDs are stable;
- posture precedence is conservative and tested;
- provenance references remain separate from trust dimensions;
- Trust Reports run beside existing confidence fields;
- existing confidence consumers remain functional;
- no consumer depends on Trust Reports;
- no AEI behavior changes exist;
- no API/UI/product behavior changes exist;
- no persistence or schema changes exist;
- no LLM/provider call decides trust;
- EUI, KG, and AEI regressions pass;
- observability evidence exists if passive runtime observer is implemented;
- rollback proof is documented;
- certification report is complete;
- phase retrospective is complete.

---

## 10. Commit, tag, and publication expectation

If implementation is later accepted, recommended metadata:

```text
Commit: feat(eui): add trust report passive foundation
Tag: eui-runtime-phase6-trust-report-foundation-certified
```

Publication should follow the established lifecycle:

```text
ARM Authorization
      ↓
Implementation
      ↓
Validation
      ↓
Certification
      ↓
ARM Acceptance
      ↓
Commit
      ↓
Annotated Tag
      ↓
Publish
      ↓
Update Master Status
```

---

## 11. ARM decision gate

This contract has been accepted by ARM.

Phase 6 implementation is authorized only within this contract. Any expansion
beyond passive, deterministic, report-only Trust Framework behavior requires a
separate ARM authorization.
