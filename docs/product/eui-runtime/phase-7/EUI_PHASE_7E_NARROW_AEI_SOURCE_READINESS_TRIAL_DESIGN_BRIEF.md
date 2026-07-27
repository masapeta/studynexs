# EUI Runtime Phase 7E Design Brief - Narrow AEI Source-Readiness Trial

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7E - Narrow AEI Source-Readiness Trial
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
- **Phase 7D baseline:** [`EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_DESIGN_BRIEF.md`](./EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_DESIGN_BRIEF.md)
- **Depends on:** Phase 7D - Narrow AEI source-readiness candidate foundation

---

## 1. Purpose

Phase 7D introduced an internal source-readiness candidate for the narrow
`context_metadata_only` AEI scope.

Phase 7E answers the next question:

> Can a ready Phase 7D candidate be exercised in an internal trial path without
> making EUI authoritative for AEI or changing any product behavior?

Phase 7E is not a production source switch.

It is a design phase for a narrow, internal, reversible trial that proves source
readiness mechanics while preserving the legacy AEI/evaluation source of truth.

---

## 2. Core principle

Trial is not adoption.

The governing rule remains:

```text
Existing AEI/evaluation behavior remains source of truth.
```

Phase 7E may design an internal trial of EUI-derived metadata as a candidate
source for AEI context/evidence metadata only.

It must not make EUI authoritative for marks, grading, scoring, policy,
teacher review routing, evidence ledger writes, or user-facing outputs.

---

## 3. Why Phase 7E exists

Phase 7D tells us that a narrow candidate may be ready for internal trial.

Without Phase 7E, the next step could accidentally become a source switch.

Phase 7E creates a deliberately constrained trial layer:

```text
Phase 7D candidate
        |
        v
Internal source-readiness trial
        |
        v
Trial evidence / certification only
        |
        v
No AEI behavior change
```

The trial should answer:

- Can the candidate be selected deterministically?
- Can EUI metadata be shaped into an AEI-compatible internal metadata view?
- Does the trial remain reversible and invisible?
- Does the trial preserve legacy AEI output exactly?
- Does trial evidence remain internal-only and free of raw content?

---

## 4. Trial scope

The only recommended Phase 7E trial scope is:

```text
AEI context/evidence metadata internal trial
```

Allowed trial metadata classes:

- Educational Identity reference;
- Educational Context reference;
- Platform Capability posture;
- Trust Report reference/posture;
- readiness scorecard reference;
- source-readiness candidate reference;
- safe evidence availability flags;
- bounded trial status.

Explicitly excluded:

- marks;
- scoring;
- grading;
- answer correctness;
- policy decisions;
- teacher review routing;
- evidence ledger writes;
- parent/student/principal-facing intelligence;
- source-of-truth switching;
- public capability claims.

---

## 5. Responsibilities

Phase 7E is responsible for designing:

- internal trial eligibility gates;
- trial candidate selection rules;
- internal trial result contract;
- trial failure posture;
- trial rollback model;
- source-flag inertness rules;
- observability and certification requirements;
- boundaries for any future Phase 7F source-switch design.

Phase 7E is not responsible for:

- switching AEI to EUI;
- changing runtime evaluation results;
- changing marks, grading, scoring, or policy;
- changing teacher review routing;
- writing evidence ledger data;
- exposing Trust Reports;
- adding UI/API/schema changes;
- migrating non-AEI consumers;
- deciding production adoption.

---

## 6. Inputs

Allowed inputs:

| Input | Source |
|---|---|
| Phase 7A comparison | AEI consumer migration observer |
| Phase 7B rich evidence bundle | AEI rich EUI evidence binder |
| Phase 7C readiness scorecard | AEI divergence readiness review service |
| Phase 7D source-readiness candidate | AEI source-readiness candidate service |
| Existing AEI/evaluation summary | Existing evaluation path |
| Existing feature flag posture | Settings |
| Golden Harness trial cases | Phase 7E Golden Harness |

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

## 7. Trial result contract

Phase 7E should define a trial result object rather than changing AEI behavior.

Suggested future contract:

```text
AEISourceReadinessTrialResult
```

The result should represent:

- trial ID;
- tenant ID;
- consumer: `aei`;
- subject type;
- scope reference;
- candidate reference;
- candidate scope: `context_metadata_only`;
- trial mode: `internal_metadata_trial`;
- trial state;
- selected evidence classes;
- blocked evidence classes;
- legacy source-of-truth confirmation;
- source flag status;
- source switch active: always false in Phase 7E;
- internal-only posture;
- rollback posture;
- metadata.

The result must be:

- immutable;
- JSON-serializable;
- internal-only;
- non-authoritative;
- deterministic;
- free of raw answer/content/PII;
- unable to affect evaluation output.

---

## 8. Trial states

Recommended trial states:

| State | Meaning |
|---|---|
| `trial_ready` | Candidate is eligible and internal trial evidence can be produced |
| `trial_not_ready` | Candidate is not ready for trial |
| `trial_blocked_product_impacting` | Trial would alter product behavior |
| `trial_blocked_unsafe` | Trial violates trust, tenant, role, or source-boundary rules |
| `trial_skipped` | Trial disabled or candidate absent |

None of these states should change AEI behavior.

---

## 9. Trial eligibility rules

Phase 7E trial execution should require:

```text
Phase 7D candidate_state == ready_for_internal_trial
```

and:

- candidate scope is `context_metadata_only`;
- source switch remains inactive;
- Trust Report visibility remains `internal_only`;
- required EUI evidence classes are present;
- rollback posture is certified;
- no product-impacting blocker;
- no unsafe blocker;
- legacy AEI/evaluation remains source of truth.

If any requirement fails, the trial must not be ready.

---

## 10. Feature flag posture

Phase 7E should preserve the existing Phase 7 flags:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- dual-read remains passive;
- rich evidence remains internal;
- source flag remains inert;
- trial must not activate source behavior;
- no user-visible behavior is authorized.

If a trial-specific flag is later introduced, it must:

- default to `false`;
- be internal-only;
- not activate source-of-truth switching;
- be rollbackable by disablement;
- produce `trial_skipped` when disabled.

---

## 11. Runtime behavior

Any future Phase 7E implementation should behave as:

```text
Phase 7D source-readiness candidate
        |
        v
Phase 7E internal trial result
        |
        v
Internal capture / certification only
        |
        v
Legacy AEI output remains source of truth
```

The trial result must not be consumed by AEI as source of truth in Phase 7E.

---

## 12. Observability design

Suggested operational signals:

```text
eui_consumer_migration.source_readiness_trial.invoked
eui_consumer_migration.source_readiness_trial.completed
eui_consumer_migration.source_readiness_trial.skipped
eui_consumer_migration.source_readiness_trial.blocked
eui_consumer_migration.source_readiness_trial.not_ready
eui_consumer_migration.source_readiness_trial.duration
```

Allowed low-cardinality labels:

- consumer: `aei`;
- trial mode;
- candidate scope;
- trial state;
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

If Phase 7E later receives implementation authorization, tests should cover:

- trial result model strictness;
- trial ID determinism;
- trial remains non-authoritative;
- source switch remains inactive;
- ready Phase 7D candidate creates `trial_ready`;
- not-ready candidate produces `trial_not_ready`;
- product-impacting candidate blocks trial;
- unsafe candidate blocks trial;
- missing candidate produces `trial_skipped` or `trial_not_ready`;
- source flag remains inert;
- trial-specific disabled behavior, if a new flag is introduced;
- no behavior change;
- Golden Harness trial cases.

This design brief itself does not authorize those tests or implementation.

---

## 14. Certification criteria for a future implementation

A future Phase 7E implementation should be accepted only if certification can
truthfully state:

- implementation stayed within its authorization contract;
- no AEI/evaluation behavior changed;
- no source switch occurred;
- source flag remained inert;
- trial output is internal-only;
- only the declared narrow trial scope was modeled;
- product-impacting and unsafe candidates block trial readiness;
- missing or not-ready candidates do not silently pass trial readiness;
- raw educational content is not captured;
- no API/UI/schema changes occurred;
- no evidence ledger writes occurred;
- regression slices pass;
- rollback is documented;
- certification report and retrospective are complete.

---

## 15. Explicit non-goals

Phase 7E is not attempting to:

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
- authorize Phase 7F source switching.

---

## 16. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/eui-runtime/phase-7/
EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended implementation scope for that future contract:

- internal AEI source-readiness trial result model;
- deterministic trial service over Phase 7D candidates;
- Golden Harness trial cases;
- no source switch;
- no marks, routing, ledger, API, UI, or schema changes.

---

## 17. ARM review gate

This design brief has been accepted by ARM as the Phase 7E design baseline.

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

Implementation may begin only after a separate Phase 7E implementation
authorization contract is accepted.
