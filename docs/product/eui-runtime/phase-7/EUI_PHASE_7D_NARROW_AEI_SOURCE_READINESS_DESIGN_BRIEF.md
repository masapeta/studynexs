# EUI Runtime Phase 7D Design Brief - Narrow AEI Source Readiness

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7D - Narrow AEI Source Readiness
- **Roadmap mapping:** Phase 7 - Consumer Migration
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-28
- **Architecture baseline:** [`../../../architecture/EUI.md`](../../../architecture/EUI.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)
- **Phase 7 baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Phase 7A baseline:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7B baseline:** [`EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md`](./EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md)
- **Phase 7C baseline:** [`EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md`](./EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md)
- **Depends on:** Phase 7C - AEI divergence readiness review foundation

---

## 1. Purpose

Phase 7C introduced a deterministic internal readiness scorecard for AEI/EUI
divergence evidence.

Phase 7D answers the next question:

> What is the narrowest AEI source-readiness candidate that can be safely
> prepared without changing marks, grading, teacher review routing, evidence
> ledger behavior, API, UI, schema, or production source of truth?

Phase 7D is not a source switch.

It is a source-readiness design phase for a deliberately tiny candidate scope.

---

## 2. Core principle

Readiness is not adoption.

Phase 7D may design the preparation required for a future source-readiness
implementation, but it must not make EUI authoritative for AEI.

The governing rule remains:

```text
Existing AEI/evaluation behavior remains source of truth.
```

---

## 3. Why Phase 7D exists

Phase 7C made readiness review measurable, but it still leaves one important
question unanswered:

```text
If a scorecard says a narrow scope is eligible, what exactly becomes eligible?
```

Without Phase 7D, a later implementation could accidentally treat "eligible" as
permission for broad adoption.

Phase 7D prevents that by defining the smallest possible source-readiness
candidate and the rules for preparing it.

---

## 4. Candidate scope

The recommended Phase 7D candidate is:

```text
AEI context/evidence metadata only
```

This means EUI may be prepared as a candidate source for internal AEI metadata
such as:

- Educational Identity reference;
- Educational Context reference;
- Platform Capability posture;
- Trust Report reference/posture;
- readiness scorecard reference;
- safe evidence availability flags.

It explicitly does not include:

- marks;
- scoring;
- grading;
- answer correctness;
- policy decisions;
- teacher review routing;
- evidence ledger writes;
- parent/student/principal-facing intelligence;
- source-of-truth switching.

---

## 5. Responsibilities

Phase 7D is responsible for designing:

- the narrow AEI metadata source-readiness candidate;
- eligibility requirements based on Phase 7C scorecards;
- source-readiness candidate contract;
- source-readiness failure posture;
- rollback model;
- feature flag posture;
- certification requirements for any future implementation;
- boundaries for Phase 7E controlled adoption.

Phase 7D is not responsible for:

- switching AEI to EUI;
- changing runtime evaluation results;
- changing marks, grading, scoring, or policy;
- changing teacher review routing;
- changing evidence ledger persistence;
- exposing Trust Reports;
- adding UI/API/schema changes;
- migrating non-AEI consumers.

---

## 6. Inputs

Allowed inputs:

| Input | Source |
|---|---|
| Phase 7A comparison | AEI consumer migration observer |
| Phase 7B rich evidence bundle | AEI rich EUI evidence binder |
| Phase 7C readiness scorecard | AEI divergence readiness review service |
| Existing AEI/evaluation summary | Existing evaluation path |
| Existing feature flag posture | Settings |
| Golden Harness readiness cases | Phase 7C Golden Harness |

Not allowed:

- raw student answers;
- raw OCR text;
- uploaded document contents;
- teacher free text;
- student/parent names;
- tenant slugs;
- public product claims;
- unsupported manual analysis outside certification evidence.

---

## 7. Source-readiness candidate contract

Phase 7D should define a candidate object rather than changing AEI behavior.

Suggested future contract:

```text
AEISourceReadinessCandidate
```

The candidate should represent:

- candidate ID;
- tenant ID;
- consumer: `aei`;
- subject type;
- scope reference;
- candidate scope, for example `context_metadata_only`;
- readiness scorecard reference;
- eligible evidence classes;
- blocked evidence classes;
- source flag status;
- source switch active: always false in Phase 7D;
- internal-only posture;
- rollback posture;
- metadata.

The candidate must be:

- immutable;
- JSON-serializable;
- internal-only;
- non-authoritative;
- deterministic;
- free of raw answer/content/PII.

---

## 8. Eligibility rules

Phase 7D source-readiness candidate creation should require:

```text
Phase 7C scorecard review_posture == eligible
```

and:

- candidate scope is explicitly narrow;
- no unsafe blocker;
- no product-impacting blocker;
- evidence window is satisfied;
- required EUI evidence classes are present;
- capability posture is supported for the declared candidate scope;
- Trust Report visibility remains `internal_only`;
- rollback posture is certified;
- source switch remains inactive.

If any requirement fails, the candidate should not be source-ready.

---

## 9. Non-authoritative candidate states

Recommended candidate states:

| State | Meaning |
|---|---|
| `ready_for_internal_trial` | Eligible for a future controlled internal source-readiness trial |
| `not_ready_more_evidence` | Evidence window or coverage is insufficient |
| `not_ready_capability_work` | EUI capability posture is insufficient |
| `blocked_product_impacting` | Candidate would alter product behavior |
| `blocked_unsafe` | Candidate violates trust, tenant, role, or authority boundary |

None of these states should change AEI behavior.

---

## 10. Feature flag posture

Phase 7D should preserve the existing Phase 7 flags:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- dual-read remains passive;
- rich evidence remains internal;
- source flag remains inert;
- candidate creation must not activate source behavior;
- no user-visible behavior is authorized.

If a candidate-specific flag is later introduced, it must:

- default to `false`;
- be internal-only;
- not activate source-of-truth switching;
- be rollbackable by disablement.

---

## 11. Runtime behavior

Any future Phase 7D implementation should behave as:

```text
Phase 7A/7B comparison evidence
        |
        v
Phase 7C readiness scorecard
        |
        v
Phase 7D source-readiness candidate
        |
        v
Internal capture / certification only
        |
        v
No AEI behavior change
```

The candidate must not be consumed by AEI as source of truth in Phase 7D.

---

## 12. Observability design

Suggested operational signals:

```text
eui_consumer_migration.source_readiness_candidate.invoked
eui_consumer_migration.source_readiness_candidate.completed
eui_consumer_migration.source_readiness_candidate.blocked
eui_consumer_migration.source_readiness_candidate.not_ready
eui_consumer_migration.source_readiness_candidate.duration
```

Allowed low-cardinality labels:

- consumer: `aei`;
- candidate scope;
- candidate state;
- blocker category;
- evidence completeness bucket.

Forbidden labels:

- tenant identifiers;
- student identifiers;
- raw content;
- free-text educational material;
- parent/student names;
- tenant slugs.

---

## 13. Testing strategy

If Phase 7D later receives implementation authorization, tests should cover:

- candidate model strictness;
- candidate ID determinism;
- candidate remains non-authoritative;
- source switch remains inactive;
- eligible Phase 7C scorecard creates ready internal candidate;
- insufficient evidence scorecard creates not-ready candidate;
- capability-work scorecard creates not-ready candidate;
- product-impacting scorecard blocks candidate;
- unsafe scorecard blocks candidate;
- Trust Report visibility is not exposed;
- no behavior change;
- Golden Harness candidate cases.

This design brief itself does not authorize those tests or implementation.

---

## 14. Certification criteria for a future implementation

A future Phase 7D implementation should be accepted only if certification can
truthfully state:

- implementation stayed within its authorization contract;
- no AEI/evaluation behavior changed;
- no source switch occurred;
- source flag remained inert;
- candidate output is internal-only;
- only the declared narrow candidate scope was modeled;
- product-impacting and unsafe scorecards block candidate readiness;
- missing evidence does not silently pass readiness;
- raw educational content is not captured;
- no API/UI/schema changes occurred;
- no evidence ledger writes occurred;
- regression slices pass;
- rollback is documented;
- certification report and retrospective are complete.

---

## 15. Explicit non-goals

Phase 7D is not attempting to:

- switch AEI to EUI as source of truth;
- modify AEI contracts;
- modify EUI contracts;
- alter marks, grading, policy, or teacher review;
- write evidence ledger data;
- expose Trust Reports;
- add teacher/principal/parent/student UI;
- migrate Teacher Copilot, AI Tutor, Question Generator, Lesson Planner,
  Principal Dashboard, Parent Assistant, or School Analytics;
- create public capability claims;
- decide production launch scope;
- remove legacy AEI paths;
- authorize Phase 7E adoption.

---

## 16. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/eui-runtime/phase-7/
EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended implementation scope for that future contract:

- internal AEI source-readiness candidate model;
- deterministic candidate builder over Phase 7C scorecards;
- Golden Harness candidate cases;
- no source switch;
- no marks, routing, ledger, API, UI, or schema changes.

---

## 17. ARM review gate

This design brief has been accepted by ARM as the Phase 7D design baseline.

It does not authorize:

- implementation;
- production code changes;
- schema changes;
- API changes;
- UI changes;
- AEI behavior changes;
- EUI source-of-truth switching;
- Trust Report display;
- non-AEI consumer migration;
- cleanup of legacy paths.

If ARM accepts this brief, implementation may begin only after a separate Phase
7D implementation authorization contract is accepted.
