# EUI Runtime Phase 7 Design Brief - Consumer Migration

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7 - Consumer Migration
- **Roadmap mapping:** Consumer Migration runtime phase
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Architecture baseline:** [`../../../architecture/EUI.md`](../../../architecture/EUI.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)
- **Depends on:** Phase 1 - Educational Identity; Phase 2 - Educational Context Engine; Phase 3 - Platform Capability Registry; Phase 4 - Knowledge Acquisition Intelligence Candidate Foundation; Phase 5 - Educational Knowledge Graph Proposal Foundation; Phase 6 - Trust Framework
- **ARM review:** Accepted with AEI-first, passive-dual-read-only, difference-reporting, divergence-gate, and per-consumer authorization clarifications incorporated

---

## 1. Purpose

Phase 7 answers:

> How should existing StudyNexs consumers begin using EUI foundations without
> changing production behavior prematurely?

The first six EUI runtime phases established the shared platform substrate:

```text
Educational Identity
        |
        v
Educational Context
        |
        v
Platform Capability Registry
        |
        v
Knowledge Acquisition Intelligence
        |
        v
Educational Knowledge Graph Proposals
        |
        v
Trust Reports
```

Those foundations are now available, but no product consumer should switch to
them directly. Phase 7 defines the migration discipline for consumers such as
AEI, Teacher Copilot, AI Tutor, Question Generator, dashboards, analytics, and
parent-facing experiences.

This design brief does not authorize implementation or consumer migration.

---

## 2. Core principle

Consumer migration is a verification program, not a feature rollout.

Every consumer must prove that it can read EUI beside its existing logic before
it is allowed to depend on EUI.

The governing rule is:

```text
Legacy behavior remains source of truth until dual-read evidence is accepted.
```

This prevents a foundational platform improvement from becoming an accidental
product behavior change.

---

## 3. Why Consumer Migration is needed now

EUI now has passive foundations for:

- canonical educational identity;
- educational context;
- capability posture;
- acquisition candidates;
- graph relationship proposals;
- trust reporting.

If consumers continue building private understanding logic, StudyNexs will drift
back toward duplicated AI features.

If consumers migrate too quickly, StudyNexs risks changing evaluation,
tutoring, reporting, or parent communication behavior without enough evidence.

Phase 7 exists to take the middle path:

- reuse EUI;
- migrate one consumer at a time;
- start in passive/dual-read mode;
- compare outputs;
- switch only after certification.

---

## 4. Responsibilities

Phase 7 is responsible for designing how consumers migrate to EUI contracts.

It should define:

- migration order;
- consumer readiness criteria;
- compatibility-layer expectations;
- dual-read strategy;
- difference classification;
- feature flag strategy;
- rollback expectations;
- observability requirements;
- certification gates;
- consumer-specific risk boundaries.

It is not responsible for:

- changing consumer behavior;
- switching any consumer to EUI;
- altering AEI evaluation outcomes;
- adding UI surfaces;
- exposing Trust Reports to users;
- changing APIs;
- changing database schemas;
- expanding product capability claims;
- removing legacy paths.

---

## 5. Standard migration lifecycle

Every consumer should move through the same lifecycle.

```text
Current Consumer
        |
        v
Preparation
        |
        v
Compatibility Layer
        |
        v
Dual Read
        |
        v
Difference Classification
        |
        v
Verification
        |
        v
Switch
        |
        v
Cleanup
```

### 5.1 Current Consumer

Existing logic remains source of truth.

Required evidence:

- current behavior tests;
- current input/output shape;
- known failure modes;
- current observability posture.

### 5.2 Preparation

Confirm required EUI foundations are available for the consumer.

Required evidence:

- Educational Identity coverage;
- Educational Context coverage;
- Capability Registry entries, where applicable;
- EKG relationship availability, where applicable;
- Trust Report mapping, where applicable.

### 5.3 Compatibility Layer

Translate EUI outputs into the consumer's existing internal shape without
changing behavior.

The compatibility layer should be narrow and reversible.

### 5.4 Dual Read

Run legacy and EUI-backed paths side by side.

Rules:

- legacy output remains authoritative;
- EUI output is captured for comparison only;
- no user-visible behavior changes;
- no downstream consumer depends on EUI output.

### 5.5 Difference Classification

Every divergence should be classified.

Suggested classifications:

| Difference type | Meaning |
|---|---|
| Equivalent | Different internal representation, same product behavior. |
| EUI richer | EUI adds useful metadata without changing behavior. |
| EUI missing | EUI cannot represent a required legacy signal yet. |
| Legacy ambiguous | Existing logic was under-specified or inconsistent. |
| Product-impacting | Output would change if EUI became source of truth. |
| Unsafe | EUI output would violate trust, tenant, role, or authority rules. |

Product-impacting or unsafe differences block switching.

### 5.6 Verification

ARM accepts the dual-read evidence and certification report.

### 5.7 Switch

Only after separate authorization, the consumer may use EUI as source of truth
for a defined scope behind a feature flag.

### 5.8 Cleanup

Legacy logic may be removed only after a stable rollback window and separate
cleanup approval.

---

## 6. Recommended migration order

The accepted roadmap lists this initial order:

1. AEI;
2. Teacher Copilot;
3. AI Tutor;
4. Question Generator;
5. Lesson Planner;
6. Principal Dashboard;
7. Parent Assistant;
8. School Analytics.

This design brief recommends preserving that order, with one clarification:

AEI should migrate first only in passive/dual-read mode. AEI must remain
protected and feature-frozen until explicit integration evidence proves that EUI
does not alter evaluation outcomes.

---

## 7. Consumer readiness matrix

| Consumer | Initial migration posture | Primary risk | First safe migration mode |
|---|---|---|---|
| AEI | First candidate | Evaluation behavior drift | Passive dual-read only |
| Teacher Copilot | After AEI preparation | Teacher-facing incorrect grounding | Passive recommendation comparison |
| AI Tutor | After teacher-safe grounding rules | Student-facing unsupported guidance | Passive response comparison |
| Question Generator | After capability/identity coverage | Curriculum mismatch | Passive generation comparison |
| Lesson Planner | After EKG/context maturity | Pedagogical overreach | Passive plan comparison |
| Principal Dashboard | After evidence mapping | Misleading aggregate insights | Internal aggregate dual-read |
| Parent Assistant | Late migration | Parent trust loss | Approved-evidence-only comparison |
| School Analytics | Late migration | Metric drift | Metric-group dual-read |

---

## 8. First consumer recommendation: AEI

AEI is the recommended first consumer because:

- AEI is already governed and certified;
- AEI has strong regression coverage;
- AEI already has passive integration discipline;
- evaluation behavior is high-risk, making it a good test of migration rigor.

However, AEI migration must begin with passive comparison only.

Conceptual Phase 7A flow:

```text
Existing Evaluation Input
        |
        +--> Existing AEI / Evaluation Path --> Production Result
        |
        +--> EUI Context + Trust Read --------> Internal Comparison Only
```

Phase 7A should not:

- change marks;
- change teacher review routing;
- change evidence ledger output;
- change student/parent/principal intelligence;
- replace AEI contracts;
- expose Trust Reports to users.

Phase 7A must not introduce an EUI source-of-truth switch. It may only compare
EUI-derived evidence against the existing AEI/evaluation path. Any future
source switch requires a later, separate ARM authorization after dual-read
certification evidence is accepted.

The first AEI migration artifact should be an implementation authorization
contract, not code.

---

## 9. Feature flag strategy

Each consumer migration requires its own flag or internal control.

Suggested naming pattern:

```text
EUI_CONSUMER_<CONSUMER>_DUAL_READ_ENABLED=false
EUI_CONSUMER_<CONSUMER>_SOURCE_ENABLED=false
```

Examples:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- dual-read flags may enable passive comparison only;
- source flags may switch behavior only after separate ARM authorization;
- all flags default OFF;
- rollback must be possible by disabling the relevant flag;
- no consumer should share a broad global migration flag.

---

## 10. Trust and visibility rules

Phase 7 must preserve the Phase 6 boundary:

> Trust visibility labels are classification metadata, not permission to display.

Migration rules:

- internal comparison may use full Trust Reports;
- teacher-facing surfaces require teacher-safe copy authorization;
- principal-facing surfaces require school-leader-safe copy authorization;
- parent/student-facing surfaces require approved evidence and separate
  messaging review;
- unsupported or manual-review-required trust posture must not become polished
  authoritative output.

No Phase 7 migration may expose Trust Reports directly to users unless a
consumer-specific authorization explicitly approves the surface and copy.

---

## 11. Difference reporting

Phase 7 should introduce internal difference reporting as a design requirement.

Reports should capture:

- consumer name;
- feature flag state;
- legacy output hash or summary;
- EUI output hash or summary;
- divergence type;
- Trust Report posture, where available;
- educational identity/context presence;
- capability mode, where applicable;
- duration;
- failure category.

Reports must not capture:

- raw student answers;
- raw OCR text;
- uploaded document content;
- free-text teacher notes;
- parent/student names;
- tenant slugs;
- sensitive educational evidence.

The first implementation authorization should decide whether difference reports
are in-memory, structured logs, or test-only artifacts. Persistent storage is
not authorized by this design brief.

---

## 12. Observability

Consumer migration observability should be operational, not product analytics.

Suggested metrics:

```text
eui_consumer_migration.invoked
eui_consumer_migration.completed
eui_consumer_migration.failed
eui_consumer_migration.diverged
eui_consumer_migration.unsafe_difference
eui_consumer_migration.duration
```

Suggested labels should remain low-cardinality:

- consumer;
- mode: `dual_read` or `source`;
- status;
- divergence type;
- trust posture;
- capability mode.

Labels must not include tenant identifiers, student identifiers, raw content, or
free-text educational material.

---

## 13. Testing strategy

Each consumer migration should include:

- consumer-specific compatibility tests;
- dual-read equivalence tests;
- difference-classification tests;
- feature-flag disabled tests;
- rollback tests;
- Trust Report visibility tests, where applicable;
- Golden Harness additions for supported cases;
- regression tests for the legacy consumer behavior.

For AEI, required regression protection should include:

- existing evaluation regression slice;
- Golden Evaluation Harness;
- AEI architecture guard tests;
- passive integration tests;
- evidence ledger tests;
- teacher review/override tests where touched.

---

## 14. Certification criteria

A consumer migration should be accepted only if certification can truthfully
state:

- consumer migration stayed within its authorization contract;
- legacy behavior remains unchanged with migration disabled;
- dual-read output is captured without becoming authoritative;
- differences are classified;
- unsafe/product-impacting differences block switching;
- rollback is proven;
- observability exists;
- no unauthorized schema/API/UI changes occurred;
- no Trust Report is exposed to users without authorization;
- no AEI behavior changes occurred unless separately authorized;
- regression slices pass;
- certification report and retrospective are complete.

---

## 15. Explicit non-goals

Phase 7 is deliberately not attempting to:

- migrate all consumers at once;
- switch AEI to EUI as source of truth immediately;
- change evaluation behavior;
- change tutor behavior;
- change teacher/copilot recommendations;
- expose Trust Reports to users;
- add UI trust badges;
- create parent/student trust messaging;
- introduce public capability claims;
- remove legacy consumer paths;
- persist migration comparison reports;
- alter EUI architecture;
- alter AEI contracts;
- bypass feature flags;
- skip dual-read validation.

---

## 16. Open design questions for ARM review

Before implementation authorization, ARM should decide:

1. Should AEI be confirmed as the first consumer migration target?
2. Should Phase 7A be limited to AEI dual-read only?
3. Should initial difference reports be in-memory/test-only or structured logs?
4. What divergence threshold is acceptable before a consumer can switch?
5. Should each consumer receive a separate design brief, or only a separate
   implementation authorization contract?

Recommended default:

- Confirm AEI as the first consumer.
- Start with AEI passive dual-read only.
- Use bounded in-memory capture plus structured logs for initial evidence.
- Treat product-impacting and unsafe differences as blockers.
- Require a separate implementation authorization contract per consumer.

### ARM decisions incorporated

For Phase 7A planning, this design brief adopts the recommended defaults:

1. AEI is the first consumer migration target.
2. Phase 7A is limited to AEI passive dual-read only.
3. Initial difference reports should use bounded in-memory capture plus
   structured logs.
4. Product-impacting and unsafe differences are blockers. Equivalent,
   EUI-richer, EUI-missing, and legacy-ambiguous differences may proceed only
   after classification and ARM acceptance of certification evidence.
5. Each consumer requires a separate implementation authorization contract.

These decisions do not authorize implementation.

---

## 17. Recommended first implementation authorization

If this design brief is accepted, the first implementation authorization should
be:

```text
EUI Phase 7A - AEI Consumer Migration: Passive Dual-Read
```

Recommended scope:

- AEI compatibility adapter from EUI outputs to AEI comparison shape;
- dual-read observer;
- default-off feature flag;
- internal difference classification;
- bounded in-memory capture;
- operational metrics;
- Golden Harness comparison cases;
- certification report.

Recommended exclusions:

- no marks changes;
- no evaluation policy changes;
- no teacher review routing changes;
- no evidence ledger changes;
- no UI/API/schema changes;
- no parent/student/principal-facing behavior;
- no Trust Report display;
- no cleanup of legacy AEI paths.

---

## 18. ARM review gate

This design brief has been accepted by ARM as the Phase 7 Consumer Migration
design baseline.

It does not authorize:

- implementation;
- production code changes;
- schema changes;
- API changes;
- UI changes;
- consumer migration;
- AEI behavior changes;
- EUI contract changes;
- Trust Report display;
- source-of-truth switching;
- cleanup of legacy paths;
- product capability claim changes.

If ARM accepts this brief, the next governance action should be a Phase 7A AEI
Consumer Migration implementation authorization contract defining:

- exact implementation scope;
- permitted files/modules;
- feature flag names;
- dual-read behavior;
- comparison artifact shape;
- observability requirements;
- Golden Harness requirements;
- rollback proof;
- certification evidence;
- explicit exclusions.
