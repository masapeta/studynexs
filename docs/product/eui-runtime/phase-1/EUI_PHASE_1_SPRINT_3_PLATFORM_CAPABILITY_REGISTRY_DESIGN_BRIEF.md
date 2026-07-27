# EUI Phase 1 Sprint 3 Design Brief — Platform Capability Registry

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 1 - Educational Identity, Context, and Capability Foundations
- **Sprint:** Sprint 3 - Platform Capability Registry
- **Roadmap mapping:** Platform Capability Registry runtime phase
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Depends on:** Phase 1 Sprint 1 - Educational Identity; Phase 1 Sprint 2 - Educational Context
- **ARM review:** Accepted with clarification recommendations incorporated

---

## 1. Purpose

The Platform Capability Registry answers:

> What can StudyNexs honestly claim it supports, for which educational scope, and in which mode?

Educational Identity identifies the educational object.

Educational Context identifies the educational situation.

Platform Capability Registry identifies the supported capability boundary.

The registry exists so StudyNexs does not imply universal support where it only supports a bounded scenario. A product can be production-ready for its supported scope without claiming every possible board, language, handwriting style, diagram, subject, or classroom edge case.

---

## 2. Why AEI Subject Capability Registry is not enough

AEI's Subject Capability Registry is evaluation-specific.

It can describe capabilities such as:

- numeric equivalence;
- unit tolerance;
- diagram checklist support;
- manual review posture.

The platform needs a broader registry that can also describe:

- language support;
- OCR support;
- code-mixed text support;
- tutor support;
- acquisition support;
- visual understanding;
- communication support;
- analytics support;
- production claim posture.

Sprint 3 does not replace the AEI registry. It establishes the design baseline for a parent platform registry that can later map to AEI-specific capabilities without changing AEI behavior.

---

## 3. Responsibilities

The Platform Capability Registry is responsible for declaring capability support across StudyNexs.

It should eventually provide a stable source of truth for:

- capability modes;
- supported boards, grades, subjects, languages, and input types;
- scope statements;
- unsupported scenarios;
- expansion areas;
- teacher expectation messaging;
- product claim discipline;
- certification coverage requirements;
- future Trust Report capability references.

It is not responsible for implementing the capability itself.

For example:

```text
Registry says:
  Hindi handwritten OCR = assist

OCR/KAI later does:
  extraction, confidence, review routing
```

The registry declares what may be claimed. Capability providers do the work.

---

## 4. Capability modes

Sprint 3 should preserve the accepted EUI capability modes.

| Mode | Meaning |
|---|---|
| `supported` | Production-quality for the declared scope. |
| `assist` | Helps extract, describe, or suggest; human review remains required. |
| `checklist` | Produces structured observations for teacher confirmation. |
| `manual_review` | Must route to human review before academic use. |
| `unsupported` | Must not claim capability. |
| `expansion` | Planned capability area, not part of current production claim. |

These modes are product-trust controls, not UI labels by themselves.

No user-facing claim should be generated from a capability entry until a later consumer or documentation flow is explicitly authorized to consume the registry.

---

## 5. Conceptual registry shape

The registry should remain declarative.

It should not embed business logic, subject-specific branching, provider calls, or UI behavior.

Conceptual shape:

```yaml
version: eui-platform-capability-registry-v1
domains:
  language:
    hindi:
      printed_ocr:
        mode: supported
        scope: clear printed Devanagari within configured input-quality limits
        review_required: false
      handwriting_ocr:
        mode: assist
        scope: confidence-based extraction with teacher correction
        review_required: true

  mathematics:
    class_10:
      numeric_normalization:
        mode: supported
      unit_conversion:
        mode: supported
      graph_grading:
        mode: checklist

  visual:
    biology_diagrams:
      mode: checklist
    pixel_perfect_diagram_grading:
      mode: unsupported
```

The eventual implementation may choose JSON instead of YAML if that better matches repository patterns.

---

## 6. Capability dimensions

The registry should be able to represent capabilities across dimensions such as:

- board;
- curriculum;
- curriculum version;
- grade;
- subject;
- language;
- script;
- input type;
- artifact type;
- assessment mode;
- capability domain;
- provider requirement;
- review requirement;
- certification status;
- expansion status.

It should not require every dimension for every capability. Sparse, declarative entries are preferred over forcing a giant matrix.

---

## 7. Capability resolution safety

Capability lookup may eventually match more than one registry entry.

Sprint 3 should follow a safety-first resolution model rather than choosing the most optimistic claim.

Expected principles:

1. More specific entries may refine broader entries only when they are explicit.
2. Unsupported, manual-review, and assist modes must not be silently upgraded to supported by a broader entry.
3. If two matching entries conflict and no deterministic precedence exists, the result should be non-authoritative and require review or remain passive.
4. Missing capability entries should resolve to `unsupported` or `manual_review`, never to `supported`.
5. Registry lookup should prefer under-claiming over over-claiming.

Example:

```text
General capability:
  Mathematics numeric_normalization = supported

Specific capability:
  Class 10 graph_grading = checklist

Result:
  Graph grading remains checklist, not supported.
```

This protects StudyNexs from accidental capability overclaiming.

---

## 8. Product-claim boundary

The Platform Capability Registry is an internal source of truth for capability posture.

It does not automatically create public product claims.

Before any registry entry appears in UI badges, sales material, parent-safe explanations, support documentation, or production scope documents, a later consumer/documentation flow must be explicitly authorized.

Sprint 3 may declare and validate capability posture internally. It must not publish, expose, or market capability claims.

---

## 9. Relationship to Educational Identity and Context

Educational Identity and Educational Context are foundational inputs to capability resolution.

Conceptually:

```text
EducationalIdentity
        |
        v
EducationalContext
        |
        v
Platform Capability Registry
        |
        v
Passive capability declaration
```

Example:

```text
Context:
  Board = CBSE
  Grade = 10
  Subject = Mathematics
  Assessment mode = Unit Test

Capability lookup:
  numeric_normalization = supported
  graph_grading = checklist
  handwritten_sanskrit_ocr = unsupported
```

Sprint 3 should design for this dependency but must not migrate any consumer to use capability results.

---

## 10. Relationship to AEI registry

AEI remains protected and feature-frozen except for separately authorized integration waves or fixes.

Sprint 3 must not remove, replace, or alter the AEI Subject Capability Registry.

The Platform Capability Registry should eventually become a parent capability source, but the near-term posture is compatibility-only:

```text
Platform Capability Registry
        |
        v
AEI compatibility mapping
        |
        v
No AEI behavior change
```

Sprint 3 may define how AEI capabilities would be represented in the platform registry. It must not switch AEI consumers to the platform registry.

---

## 11. Dependencies

Sprint 3 depends on:

- accepted EUI architecture baseline;
- accepted Platform Capability Registry architecture;
- Phase 0 feature flag, observability, certification, and rollback guidance;
- Phase 1 Sprint 1 Educational Identity;
- Phase 1 Sprint 2 Educational Context;
- AEI Subject Capability Registry as an existing protected compatibility source;
- existing Golden Harness patterns.

Sprint 3 should not introduce dependencies on:

- Knowledge Acquisition Intelligence;
- Trust Framework runtime behavior;
- Educational Knowledge Graph expansion;
- Institutional Memory;
- LLM inference;
- UI surfaces;
- API consumers.

---

## 12. Sprint 3 scope

Sprint 3 should be scoped to the design baseline for a passive Platform Capability Registry foundation.

The future implementation authorization may allow:

- declarative platform capability registry data;
- registry schema/contract;
- registry loader;
- registry validation;
- read-only lookup service;
- AEI registry compatibility mapping tests;
- default-off feature flag, if passive runtime loading is introduced;
- operational metrics and structured logs;
- Golden Harness capability cases;
- certification report.

The design intent is:

```text
Educational Context
        |
        v
Capability Registry lookup
        |
        v
CapabilityDeclaration
        |
        v
Metrics / logs / Golden Harness
        |
        v
Captured for verification only
        |
        v
No consumer uses the result
```

---

## 13. Explicit exclusions

Sprint 3 does not authorize:

- runtime implementation without a separate ARM authorization;
- database schema changes;
- database migrations;
- persistent registry storage;
- API contract changes;
- public endpoint changes;
- UI changes;
- consumer migration;
- AEI registry replacement;
- AEI runtime behavior changes;
- EUI consumer behavior changes;
- Trust Framework implementation;
- Knowledge Acquisition Intelligence;
- Educational Knowledge Graph expansion;
- LLM inference;
- prompt changes;
- product capability claim expansion;
- public documentation generated from the registry;
- support documentation generated from the registry;
- automatic review routing;
- policy enforcement.

---

## 14. Non-goals

Sprint 3 is deliberately not attempting to:

- implement OCR;
- implement language understanding;
- implement visual understanding;
- implement tutor behavior;
- evaluate answers;
- route teacher review;
- decide production rollout scope;
- create UI badges;
- expose capability claims to schools;
- replace the AEI registry;
- become a provider-routing system;
- become the Trust Framework.

The registry declares capability posture; it does not perform the capability.

---

## 15. Feature flag strategy

Sprint 3 should follow the Phase 0 feature flag strategy.

If future implementation includes passive runtime loading, expected posture:

- default-off;
- environment-configurable;
- passive lookup only;
- rollback by disabling the flag;
- no product-visible behavior when enabled;
- no downstream consumer dependency on the output.

Possible future flag name:

```text
EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED=false
```

The exact flag name should be finalized in the implementation authorization, not by this design brief.

---

## 16. Runtime behavior

Sprint 3 runtime behavior, if later authorized, must be:

- passive;
- read-only;
- deterministic;
- exception-isolated;
- tenant-safe where tenant context is involved;
- invisible to users;
- non-authoritative for every consumer.

If registry loading or lookup fails, legacy behavior must continue unchanged.

No consumer may use registry output for product behavior until a later migration is explicitly authorized.

---

## 17. Observability

Sprint 3 should define operational observability, not product analytics.

Expected metrics may include:

```text
eui_capability_registry.loaded
eui_capability_registry.validation_failed
eui_capability_registry.lookup_invoked
eui_capability_registry.lookup_completed
eui_capability_registry.lookup_failed
eui_capability_registry.unsupported
eui_capability_registry.duration
```

Structured logs should capture:

- registry version;
- lookup status;
- capability mode;
- validation failure reason;
- fallback behavior;
- non-sensitive correlation metadata.

Metrics and logs must not use student names, parent data, tenant slugs, free-text answers, uploaded content, or sensitive educational content as labels.

---

## 18. Testing strategy

Sprint 3 should be backed by focused tests and Golden Harness coverage.

### Unit tests

Expected coverage:

- registry schema validation;
- accepted capability modes;
- rejection of invalid modes;
- deterministic lookup;
- unsupported capability behavior;
- expansion capability behavior;
- conflicting match behavior;
- missing capability defaults;
- read-only registry behavior;
- AEI compatibility mapping;
- disabled feature flag behavior if a flag is introduced;
- exception isolation if passive runtime loading is introduced.

### Golden Harness

Golden cases should cover:

- CBSE Grade 10 Mathematics numeric normalization as `supported`;
- Hindi printed OCR as `supported` for declared scope;
- Hindi handwriting OCR as `assist`;
- Telugu handwriting OCR as `assist`;
- Sanskrit handwriting OCR as `assist` or `manual_review`, depending on declared scope;
- biology diagrams as `checklist`;
- pixel-perfect diagram grading as `unsupported`;
- unsupported capability not leaking as supported;
- missing capability resolving safely;
- conflicting capability entries resolving safely;
- AEI registry compatibility for current evaluation capability entries.

### Regression verification

Before certification, validation should demonstrate:

- existing product behavior unchanged;
- existing AEI behavior unchanged;
- Educational Identity tests still pass;
- Educational Context tests still pass;
- API import succeeds;
- focused lint for Sprint 3 files passes;
- `git diff --check` passes.

---

## 19. Certification criteria

Sprint 3 should be accepted only if certification can truthfully state:

- platform capability registry contract exists as authorized;
- registry is declarative and read-only;
- supported modes validate deterministically;
- unsupported and expansion modes cannot be mistaken for supported;
- missing capabilities do not resolve as supported;
- conflicting capability entries do not overclaim support;
- registry output remains internal and does not create public product claims;
- AEI compatibility mapping exists without changing AEI behavior;
- feature flag defaults off if introduced;
- passive lookup, if implemented, does not affect product behavior;
- no consumer depends on Platform Capability Registry;
- no schema/API/UI changes were introduced;
- no AEI behavior changed;
- Golden Harness capability cases pass;
- observability evidence exists for loading, validation, lookup, unsupported, failure, and duration if runtime loading is introduced;
- rollback is verified;
- certification report is complete;
- phase retrospective is complete.

---

## 20. Master Status update requirement

Every published sprint must end by updating the Master Status before the next sprint begins.

For Sprint 3, the post-publication Master Status update should record:

- Phase 1 Sprint 3 status;
- commit and annotated tag, if implementation is later authorized and published;
- whether runtime behavior remained unchanged;
- whether AEI registry replacement remains unauthorized;
- whether consumer migration remains unauthorized;
- next gated milestone.

---

## 21. ARM review gate

This design brief has been accepted by ARM.

It does not authorize implementation.

The next governance action should be a separate Sprint 3 implementation
authorization contract defining repository boundaries, permitted files/modules,
feature flag names, validation evidence, rollback proof, and certification
requirements.

No Sprint 3 code should be written until ARM separately authorizes implementation.
