# EUI Runtime Phase 5 Implementation Authorization Contract - Educational Knowledge Graph Expansion

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 5 - Educational Knowledge Graph Expansion
- **Authorization ID:** EUI-PH5-EKG-AUTH-001
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_5_EDUCATIONAL_KNOWLEDGE_GRAPH_EXPANSION_DESIGN_BRIEF.md`](./EUI_PHASE_5_EDUCATIONAL_KNOWLEDGE_GRAPH_EXPANSION_DESIGN_BRIEF.md)
- **Architecture baseline:** [`../../../architecture/eui/EDUCATIONAL_KNOWLEDGE_GRAPH.md`](../../../architecture/eui/EDUCATIONAL_KNOWLEDGE_GRAPH.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)

---

## 1. Authorization status

This document is the accepted implementation authorization contract for Phase 5.

Implementation is authorized only within the scope and repository boundary
defined here.

The following remain prohibited:

- production code changes for Phase 5;
- database schema changes;
- persisted enum changes;
- API changes;
- UI changes;
- runtime behavior changes;
- graph writes;
- consumer migration;
- AEI behavior changes;
- KAI behavior expansion.

---

## 2. Purpose

Phase 5 implementation should introduce a passive Educational Knowledge Graph
Expansion foundation that can deterministically propose graph relationships
without changing existing Knowledge Graph behavior.

The first implementation should answer:

> Can StudyNexs safely map Educational Identity and KAI candidates to graph relationship proposals while keeping all existing product behavior unchanged?

This implementation is proposal-first. It does not make new graph knowledge
authoritative.

---

## 3. Authorized implementation scope

If accepted, this contract authorizes only the following work.

### 3.1 Graph relationship proposal model

Introduce a canonical immutable runtime/domain model for graph relationship
proposals.

The model may represent:

- relationship category;
- tenant scope;
- source reference;
- target reference;
- Educational Identity reference;
- Educational Context summary;
- KAI candidate reference;
- capability mode;
- authority posture;
- provenance;
- trust placeholders;
- ambiguity metadata;
- deterministic proposal ID.

The model must be JSON-serializable and strict enough to prevent silent shape
drift.

### 3.2 Deterministic proposal ID generation

Introduce deterministic transient proposal IDs.

IDs should be stable for identical relationship proposal inputs.

IDs must not depend on database persistence.

### 3.3 Read-only graph relationship resolver

Implement read-only resolver/proposal logic that can:

- map an Educational Identity to an existing KG node where deterministic;
- represent missing graph target cases;
- represent ambiguous graph target cases;
- build candidate graph relationship proposals from KAI candidates;
- preserve provenance and authority posture;
- avoid converting candidates into trusted graph knowledge.

The resolver may read existing Knowledge Graph data if needed.

It may not create, update, or delete graph records.

### 3.4 Existing KG compatibility

The implementation may use existing Knowledge Graph modules and schemas for
read-only lookups.

It must preserve:

- existing KG query behavior;
- existing spine build behavior;
- existing question-to-concept behavior;
- existing student weak-concept behavior.

### 3.5 Passive observer

If runtime observation is introduced, implement a passive observer guarded by a
default-off feature flag.

The observer may:

- invoke proposal generation;
- record operational metrics;
- capture bounded in-memory evidence for validation;
- isolate exceptions.

The observer may not:

- change production results;
- write graph relationships;
- expose output to users;
- migrate consumers.

### 3.6 Feature flag

Implement or wire the Phase 5 feature flag:

```text
EUI_EKG_EXPANSION_ENABLED=false
```

Requirements:

- disabled by default;
- environment configurable through existing settings patterns;
- no-op when disabled;
- rollback by disabling the flag;
- no product-visible behavior change.

### 3.7 Observability

Implement operational observability consistent with the Phase 0 baseline.

Allowed metrics/log signals include:

```text
eui_ekg.resolve_invoked
eui_ekg.resolve_completed
eui_ekg.resolve_failed
eui_ekg.identity_link_found
eui_ekg.identity_link_missing
eui_ekg.candidate_relationship_proposed
eui_ekg.ambiguous
eui_ekg.unsupported
eui_ekg.duration
```

Metrics and logs must avoid PII, raw educational content, uploaded text, raw
OCR text, tenant slugs, student answers, and parent data.

### 3.8 Golden Harness

Add Golden Harness data and tests for deterministic graph relationship proposal
behavior.

The harness should cover:

- identity-to-existing-concept proposal;
- KAI candidate-to-concept proposal;
- ambiguous graph target;
- missing graph target;
- unsupported relationship;
- candidate posture preservation;
- cross-board similar chapter names not collapsing into one graph target;
- no trusted graph relationship produced from KAI candidate input.

### 3.9 Certification

Produce a Phase 5 certification report demonstrating:

- deterministic proposal behavior;
- no trusted graph writes;
- no schema or persisted enum changes;
- no API/UI/product behavior change;
- existing KG regression safety;
- EUI regression safety;
- AEI regression safety;
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

Conditionally permitted for read-only integration:

```text
apps/api/app/modules/knowledge_graph/
```

Any change under `apps/api/app/modules/knowledge_graph/` must be strictly
backward-compatible and must not change existing graph behavior.

### 4.2 Tests and Golden Harness

Permitted:

```text
apps/api/tests/golden/eui_v1/
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/test_educational_graph_relationship_*.py
apps/api/tests/test_eui_ekg_*.py
```

Existing Knowledge Graph regression tests may be run but should not be modified
unless a test-only compatibility assertion is needed and ARM accepts the reason.

### 4.3 Documentation

Permitted:

```text
docs/product/eui-runtime/phase-5/
```

`docs/STATUS.md` should be updated only after certification/publication, not in
the implementation commit.

---

## 5. Explicit exclusions

The following are not authorized:

- database schema changes;
- Alembic migrations;
- persisted enum expansion;
- new graph database;
- second graph store;
- graph writes;
- trusted graph edge creation;
- KAI candidate approval;
- Trust Framework implementation;
- API endpoint changes;
- UI changes;
- consumer migration;
- AEI behavior changes;
- KAI behavior expansion beyond candidate inputs already supported;
- CurriculumPack approval flow changes;
- existing Knowledge Graph spine behavior changes;
- student evidence graph writes;
- mastery calculation changes;
- student weak-concept behavior changes;
- LLM/OCR/ASR provider integration;
- product capability claim changes.

Any of these require a separate ARM authorization and, where architectural,
possibly an ADR.

---

## 6. Runtime constraints

The implementation must be:

- passive;
- read-only against existing product data;
- deterministic where possible;
- proposal-only;
- exception-isolated;
- tenant-safe;
- backward-compatible;
- hidden from users;
- non-authoritative.

If the Phase 5 path fails, existing production behavior must continue unchanged.

---

## 7. Rollback proof

Rollback must be proven by demonstrating:

- feature flag disabled path is a no-op;
- existing KG behavior remains unchanged with the flag disabled;
- existing KG behavior remains unchanged with the flag enabled;
- no persisted graph data is created;
- no schema rollback is required;
- existing evaluation and EUI regressions continue to pass.

---

## 8. Validation requirements

Before ARM acceptance, the implementation must provide evidence for:

### 8.1 Focused validation

- model tests;
- proposal ID tests;
- resolver tests;
- ambiguity tests;
- missing target tests;
- passive observer tests if observer is implemented;
- Golden Harness EKG expansion tests.

### 8.2 Regression validation

Required regression slices:

- existing Knowledge Graph tests;
- graph query tests;
- question-concept link tests;
- student weak-concept link tests;
- Educational Identity tests;
- Educational Context tests;
- Platform Capability Registry tests;
- KAI tests;
- AEI/evaluation regression slice;
- API import.

### 8.3 Static validation

- focused Ruff for touched API files;
- `git diff --check`;
- write-scan proving no graph writes were introduced unless separately
  authorized.

---

## 9. Acceptance criteria

Phase 5 implementation may be accepted only if all of the following are true:

- graph relationship proposal model exists as authorized;
- deterministic proposal IDs are stable;
- read-only resolver produces deterministic proposal outcomes;
- KAI-derived proposals remain non-authoritative;
- ambiguity and missing targets are explicit;
- no schema or persisted enum changes exist;
- no graph writes exist;
- no API/UI/product behavior changes exist;
- no consumer depends on EKG expansion output;
- no AEI behavior changes exist;
- existing KG regressions pass;
- EUI and AEI regressions pass;
- observability evidence exists if passive runtime observer is implemented;
- rollback proof is documented;
- certification report is complete;
- phase retrospective is complete.

---

## 10. Commit, tag, and publication expectation

If implementation is later accepted, recommended metadata:

```text
Commit: feat(eui): add educational knowledge graph proposal foundation
Tag: eui-runtime-phase5-ekg-proposal-foundation-certified
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

Phase 5 implementation is authorized only within this contract. Any expansion
beyond proposal-only, passive, read-only EKG behavior requires a separate ARM
authorization.
