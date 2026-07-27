# EUI Runtime Implementation Roadmap v1

- **Program:** Educational Understanding Intelligence Runtime Implementation Roadmap v1
- **Classification:** Planning Baseline
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Architecture baseline:** [`../../architecture/EUI.md`](../../architecture/EUI.md)
- **ADR baseline:** [`../../decisions/ADR-0002-educational-understanding-intelligence-platform-architecture.md`](../../decisions/ADR-0002-educational-understanding-intelligence-platform-architecture.md)

---

## 1. Objective

This roadmap answers one question:

> How do we implement the accepted EUI architecture with minimal risk while preserving AEI stability?

It does not redefine EUI. The accepted architecture baseline already defines what EUI is.

This document defines sequencing, dependencies, migration strategy, certification gates, rollback posture, and runtime authorization checkpoints.

---

## 2. Implementation philosophy

> The implementation order follows dependency maturity, not feature popularity.

Exciting consumers must not lead foundational architecture. Teacher Copilot, AI Tutor, analytics, and advanced evaluation become stronger only after Educational Identity, context, capability declarations, knowledge graph relationships, trust reporting, and migration seams exist.

StudyNexs should implement EUI through small, contract-first runtime phases that preserve AEI and existing product behavior until each phase is explicitly authorized for use.

---

## 3. Non-implementation boundary

This roadmap is planning only.

It does not authorize:

- production code changes;
- database schema changes;
- API changes;
- UI changes;
- runtime behavior changes;
- contract changes to accepted AEI or EUI architecture;
- feature implementation;
- consumer migration.

Runtime implementation begins only after ARM approves this roadmap and authorizes Phase 1.

---

## 4. Protection rules

### AEI

AEI remains protected and feature-frozen except for:

- authorized controlled integration waves;
- approved production defects;
- security fixes;
- certification-driven corrections.

No EUI implementation phase may bypass AEI for evaluation behavior.

### EUI

EUI architecture is frozen. Runtime implementation may evolve behind the accepted contracts, but architecture changes require:

1. ADR update or new ADR;
2. ARM architecture review;
3. compatibility assessment;
4. versioning decision.

---

## 5. No-direct-feature gate

Every future implementation proposal must answer:

1. Which EUI subsystem owns this?
2. Does it require a contract change?
3. Does it require a Platform Capability Registry update?
4. Does it extend the Educational Knowledge Graph?
5. Does it affect AEI?
6. Is Educational Identity involved?
7. Does it require Trust Report changes?
8. Does it affect Institutional Memory?

Implementation should not proceed until those answers are explicit.

---

## 6. Curriculum-led delivery model

Curriculum Packs should lead runtime delivery.

Instead of planning isolated technical features such as OCR, tutor behavior, or reports, delivery should be anchored on a supported curriculum scope.

Example:

```text
CBSE Grade 8 Mathematics
        |
        v
Educational Identity
        |
        v
Educational Context
        |
        v
Knowledge Graph
        |
        v
Capability Registry
        |
        v
AEI
        |
        v
Teacher Copilot
        |
        v
AI Tutor
        |
        v
Analytics
        |
        v
Parent-safe reporting
```

This aligns engineering with educational outcomes rather than disconnected technical components.

---

## 7. Runtime phases

### Phase 0 - Engineering Preparation

Purpose: verify implementation readiness before runtime EUI work begins.

Scope:

- feature flag framework verification;
- observability baseline;
- Golden Harness expansion plan;
- dependency inventory;
- implementation branch strategy;
- release cadence;
- certification report template;
- rollback proof pattern.

Constraints:

- no runtime EUI implementation;
- no consumer migration;
- no production behavior change.

Exit criteria:

- feature flag strategy documented;
- observability metrics/logging baseline identified;
- Golden Harness expansion needs documented;
- dependency inventory reviewed;
- implementation branch and release cadence documented;
- certification template ready.

Success metrics:

| Metric | Target |
|---|---|
| Runtime behavior changes | 0 |
| Missing phase prerequisites | 0 before Phase 1 starts |
| Rollback strategy coverage | 100% of planned runtime phases |
| Observability baseline coverage | Defined for every planned runtime phase |
| Certification template readiness | Complete before Phase 1 authorization |

### Phase 1 - Educational Identity

Purpose: establish stable educational identity references without behavior changes.

Scope:

- identity model;
- identity resolver;
- identity reference contract;
- compatibility with existing CurriculumPack and Knowledge Graph concepts.

Constraints:

- no consumer behavior changes;
- no AEI behavior changes;
- no user-visible change.

Exit criteria:

- identity can represent board, grade, subject, chapter, learning objective, concept, competency, curriculum version, and tenant scope;
- existing flows remain unchanged;
- rollback documented.

Success metrics:

| Metric | Target |
|---|---|
| Compatibility regressions | 0 |
| Runtime behavior changes | 0 |
| Identity resolver deterministic cases | 100% pass |
| Rollback proof | 100% documented and verified |
| Performance impact | Within defined budget |

### Phase 2 - Educational Context Engine

Purpose: resolve educational context through a single runtime contract.

Scope:

- context resolver;
- context provider interfaces;
- initial adapter returning existing context from current systems;
- conflict and missing-context reporting.

Constraints:

- initially read-only;
- no consumer switch yet;
- no policy behavior changes.

Exit criteria:

- existing context can be represented without loss;
- ambiguous context is detectable;
- consumers can dual-read context in later phases.

Success metrics:

| Metric | Target |
|---|---|
| Compatibility regressions | 0 |
| Existing context representation | 100% of supported current contexts |
| Ambiguous context detection | Covered by focused tests |
| Rollback proof | 100% documented and verified |
| Performance impact | Within defined budget |

### Phase 3 - Platform Capability Registry

Purpose: establish platform capability declarations while preserving the AEI Subject Capability Registry.

Scope:

- platform registry contract;
- compatibility mapping for AEI registry entries;
- modes: supported, assist, checklist, manual_review, unsupported, expansion;
- validation and documentation hooks.

Constraints:

- do not remove AEI registry;
- do not change user-facing capability claims until authorized;
- no behavior enforcement yet.

Exit criteria:

- platform capabilities can represent AEI evaluation capabilities and broader EUI capabilities;
- migration path to parent registry is documented;
- no existing registry consumers regress.

Success metrics:

| Metric | Target |
|---|---|
| AEI registry compatibility | 100% for current entries |
| Capability claim regressions | 0 |
| Unsupported capability leakage | 0 |
| Rollback proof | 100% documented and verified |
| Performance impact | Within defined budget |

### Phase 4 - Knowledge Acquisition Intelligence

Purpose: introduce acquisition contracts for educational artifacts.

Initial scope:

- PDFs;
- OCR inputs;
- worksheets;
- answer keys;
- teacher notes.

Constraints:

- produce candidates, not authoritative educational knowledge;
- provenance and Trust Report remain separate;
- no direct consumer use without review posture.

Exit criteria:

- artifacts can carry provenance, identity, extraction output, and trust signals;
- low-confidence acquisition routes to review;
- unsupported inputs are explicitly handled.

Success metrics:

| Metric | Target |
|---|---|
| Candidate-only acquisition behavior | 100% for unapproved inputs |
| Low-confidence review routing | 100% for defined low-confidence cases |
| Provenance/trust separation | 100% in contract tests |
| Rollback proof | 100% documented and verified |
| Performance impact | Within defined budget |

### Phase 5 - Educational Knowledge Graph Expansion

Purpose: expand the existing Knowledge Graph from curriculum spine into EUI educational backbone.

Scope:

- learning objectives;
- competencies;
- evidence relationships;
- misconceptions;
- prerequisite relationships;
- intervention mappings.

Constraints:

- preserve existing Knowledge Graph behavior;
- no second graph store without separate ADR;
- tenant scoping remains non-negotiable.

Exit criteria:

- supported curriculum scope has identity-linked graph relationships;
- evidence and misconception relationships are provenance-aware;
- consumers can query through approved services.

Success metrics:

| Metric | Target |
|---|---|
| Existing KG query regressions | 0 |
| Tenant isolation regressions | 0 |
| Identity-linked graph coverage | 100% for selected curriculum scope |
| Provenance coverage | 100% for new graph relationship types |
| Rollback proof | 100% documented and verified |

### Phase 6 - Trust Framework

Purpose: introduce Trust Report contracts alongside existing confidence fields.

Scope:

- input quality;
- extraction quality;
- OCR confidence;
- language confidence;
- understanding confidence;
- subject confidence;
- reasoning confidence;
- policy confidence;
- evidence availability;
- human review status;
- auditability;
- capability mode.

Constraints:

- do not remove existing confidence fields immediately;
- no UI change until authorized;
- Trust Report affects explanation and workflow readiness, not automatic academic authority.

Exit criteria:

- Trust Report can be produced for supported artifacts and evaluation flows;
- confidence-to-trust compatibility mapping exists;
- existing confidence consumers remain functional.

Success metrics:

| Metric | Target |
|---|---|
| Existing confidence consumer regressions | 0 |
| Trust Report contract coverage | 100% for supported flows |
| Provenance/trust conflation | 0 cases |
| Rollback proof | 100% documented and verified |
| Performance impact | Within defined budget |

### Phase 7 - Consumer Migration

Purpose: migrate consumers one at a time to EUI contracts.

Initial migration order:

1. AEI;
2. Teacher Copilot;
3. AI Tutor;
4. Question Generator;
5. Lesson Planner;
6. Principal Dashboard;
7. Parent Assistant;
8. School Analytics.

Constraints:

- each consumer migrates through preparation, compatibility layer, dual read, verification, switch, cleanup;
- no bulk migration;
- feature flags and rollback required.

Exit criteria:

- each migrated consumer uses EUI contracts instead of private understanding logic;
- production behavior remains verified;
- cleanup occurs only after dual-read evidence is accepted.

Success metrics:

| Metric | Target |
|---|---|
| Compatibility regressions | 0 |
| Dual-read divergence | Within approved threshold per consumer |
| Rollback success | 100% per consumer switch |
| Unauthorized capability claim expansion | 0 |
| Performance impact | Within defined budget per consumer |

---

## 8. Migration strategy

Runtime migration follows this pattern:

```text
Prepare contracts
  -> Add compatibility layer
  -> Dual read
  -> Compare
  -> Verify
  -> Switch
  -> Monitor
  -> Cleanup
```

No consumer should switch directly from legacy logic to EUI without dual-read validation unless ARM explicitly approves the exception.

---

## 9. Rollback strategy

Every runtime phase must include:

- feature flag or internal control where behavior can change;
- compatibility layer so legacy behavior can remain source of truth;
- data migration rollback plan if schemas are introduced;
- operational metric proving the phase is active or inactive;
- certification report documenting rollback test or rollback reasoning.

Early phases should be behavior-preserving whenever possible.

---

## 10. Certification gates

Each runtime phase requires:

- focused unit tests;
- integration tests for touched contracts;
- regression tests for existing consumers;
- tenant isolation verification where tenant-scoped data is touched;
- observability proof;
- rollback proof;
- certification report;
- ARM acceptance before publication.

If a phase changes evaluation behavior, AEI certification gates also apply.

---

## 11. Platform readiness scorecard

Each phase should report:

| Dimension | Status |
|---|---|
| Architecture | Not started / In progress / Complete |
| Contracts | Not started / In progress / Complete |
| Runtime | Not started / In progress / Complete |
| Tests | Not started / In progress / Complete |
| Observability | Not started / In progress / Complete |
| Documentation | Not started / In progress / Complete |
| Rollback | Not started / In progress / Complete |
| Certification | Not started / In progress / Complete |

---

## 12. Runtime authorization checkpoints

| Checkpoint | Required before |
|---|---|
| Roadmap ARM acceptance | Any runtime implementation |
| Phase-specific authorization | Phase implementation |
| Phase certification | Commit/publication |
| Consumer migration authorization | Consumer switch |
| Capability claim approval | User-facing product claim expansion |
| Architecture review | Any EUI contract-breaking change |

---

## 13. Supporting planning artifacts

| Artifact | Path |
|---|---|
| EUI Dependency Matrix | [`EUI_DEPENDENCY_MATRIX.md`](./EUI_DEPENDENCY_MATRIX.md) |
| Consumer Migration Plan | [`EUI_CONSUMER_MIGRATION_PLAN.md`](./EUI_CONSUMER_MIGRATION_PLAN.md) |
| Runtime Readiness Checklist | [`EUI_RUNTIME_READINESS_CHECKLIST.md`](./EUI_RUNTIME_READINESS_CHECKLIST.md) |
| Runtime Decision Log | [`EUI_RUNTIME_DECISION_LOG.md`](./EUI_RUNTIME_DECISION_LOG.md) |

---

## 14. Exit criterion for this planning program

This planning program is complete only when ARM accepts:

- the runtime implementation roadmap;
- the dependency matrix;
- the consumer migration plan;
- the readiness checklist;
- the runtime decision log structure.

Only then may Phase 1 runtime implementation be separately authorized.

---

## 15. Governance status

This roadmap is accepted as the EUI Runtime Planning Baseline.

Runtime remains not started. Phase 1 requires separate ARM authorization.
