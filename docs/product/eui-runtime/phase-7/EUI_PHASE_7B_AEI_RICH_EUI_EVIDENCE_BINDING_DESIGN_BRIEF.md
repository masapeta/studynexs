# EUI Runtime Phase 7B Design Brief - AEI Rich EUI Evidence Binding

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7B - AEI Rich EUI Evidence Binding
- **Roadmap mapping:** Phase 7 - Consumer Migration
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Architecture baseline:** [`../../../architecture/EUI.md`](../../../architecture/EUI.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)
- **Depends on:** Phase 7A - AEI Consumer Migration passive dual-read foundation
- **ARM review:** Accepted with performance/query budget, no Trust Report schema extension, per-evidence graceful degradation, and source-flag inertness recommendations incorporated

---

## 1. Purpose

Phase 7A proved that AEI can run an EUI consumer-migration comparison beside
the existing evaluation path without changing production behavior.

Phase 7B answers the next question:

> Can AEI's passive dual-read comparison receive richer EUI evidence
> - Educational Identity, Educational Context, Capability posture, and Trust
> Report - without changing evaluation behavior?

Phase 7B is still a migration-preparation phase. It is not a source switch.

---

## 2. Why Phase 7B exists

The Phase 7A implementation introduced the safe comparison shell:

```text
Existing AEI / Evaluation Path
        |
        v
Production Result remains source of truth
        |
        +--> EUI AEI Consumer Migration Comparison
```

That comparison currently uses sanitized legacy/evaluation and AEI passive
summary evidence. The adapter is already capable of accepting richer EUI
objects, but the live evaluation hook does not yet bind those objects into the
comparison.

Phase 7B should enrich the passive comparison evidence by binding existing EUI
foundations into the AEI migration comparison in a controlled, read-only,
default-off manner.

This makes future divergence reports more meaningful without changing marks,
review routing, evidence, APIs, UI, or source-of-truth behavior.

---

## 3. Core principle

Richer evidence is not authority.

Phase 7B may improve internal comparison evidence. It may not make EUI
authoritative for AEI.

The governing rule remains:

```text
Existing AEI/evaluation behavior remains source of truth.
```

---

## 4. Scope

Phase 7B should design how AEI passive dual-read receives richer EUI evidence
from already-published foundations:

- Educational Identity;
- Educational Context;
- Platform Capability Registry lookup;
- Trust Report;
- existing Phase 7A comparison model and observer.

The output remains the existing Phase 7A comparison/capture posture:

```text
AEIConsumerMigrationComparison
AEIConsumerMigrationCapture
```

If implementation is later authorized, Phase 7B should prefer extending the
Phase 7A adapter/hook rather than introducing a second migration path.

---

## 5. Responsibilities

Phase 7B is responsible for designing:

- which EUI evidence objects AEI may passively bind;
- where evidence resolution occurs;
- how evidence is summarized safely;
- how missing/ambiguous EUI evidence is represented;
- how Trust Report visibility remains internal-only;
- how feature flags protect runtime behavior;
- how rollback is proven;
- what Golden Harness additions are required;
- what certification evidence is required.

Phase 7B is not responsible for:

- changing AEI marks;
- changing AEI grading;
- changing AEI policy decisions;
- changing teacher review routing;
- writing to the evidence ledger;
- displaying Trust Reports;
- switching AEI to EUI as source of truth;
- migrating non-AEI consumers.

---

## 6. Conceptual flow

Phase 7B should preserve the existing evaluation flow.

```text
Answer Sheet Evaluation
        |
        +--> Existing Evaluation / AEI Path
        |       |
        |       v
        |   Production Result
        |
        +--> Passive EUI Evidence Binding
                |
                +--> Educational Identity
                +--> Educational Context
                +--> Platform Capability Lookup
                +--> Trust Report
                |
                v
          AEI Consumer Migration Comparison
                |
                v
          Internal Capture / Metrics Only
```

The production result must never depend on the passive EUI evidence binding in
Phase 7B.

---

## 7. Evidence binding model

### 7.1 Educational Identity

Educational Identity answers:

```text
What educational object is this evaluation/question/artifact connected to?
```

In Phase 7B, identity evidence may be resolved from existing available context,
such as:

- question paper metadata;
- curriculum pack reference;
- chapter/topic metadata;
- existing Phase 1 Educational Identity resolver where suitable;
- already-available deterministic identifiers.

The identity binding must remain:

- read-only;
- deterministic;
- non-authoritative;
- nullable when unsupported or ambiguous.

### 7.2 Educational Context

Educational Context answers:

```text
In what educational situation is this evaluation happening?
```

Context evidence may include:

- tenant/school scope;
- board;
- curriculum;
- curriculum version;
- grade;
- subject;
- chapter/topic;
- assessment mode;
- language medium where available.

Conflicts and ambiguity must be represented as passive evidence, not errors
that affect evaluation.

### 7.3 Platform Capability Registry lookup

Capability lookup should answer:

```text
What does the platform currently claim internally for this subject/scope/capability?
```

Phase 7B may look up relevant capability posture for AEI comparison evidence,
for example:

- mathematics numeric normalization;
- unit handling;
- diagram checklist posture;
- language/OCR assist posture where applicable;
- science expression assist posture where applicable.

Capability lookup must not:

- alter AEI policy decisions;
- alter public capability claims;
- display UI badges;
- replace the AEI Subject Capability Registry.

### 7.4 Trust Report

Trust Report should summarize the internal trust posture of EUI evidence used
for comparison.

Trust Report handling rules:

- internal-only visibility is required;
- non-internal visibility is unsafe for Phase 7B;
- Trust Reports are not displayed to teachers, students, parents, principals,
  or administrators;
- Trust Report posture is comparison evidence only.

---

## 8. Where evidence binding should occur

Phase 7B should avoid scattering EUI lookups across the evaluation service.

Preferred design:

```text
AnswerSheetEvalService
        |
        v
Single guarded passive hook
        |
        v
AEI Consumer Migration Evidence Binder
        |
        v
Existing Phase 7A Adapter / Observer
```

The evaluation service should remain thin. It should invoke one guarded
passive hook and continue existing behavior regardless of hook success/failure.

The evidence binder should own:

- collecting available metadata;
- invoking read-only EUI resolvers/lookups where authorized;
- handling missing/ambiguous evidence;
- building safe summaries;
- forwarding evidence to the existing Phase 7A comparison adapter.

---

## 9. Feature flag strategy

Phase 7B should not introduce a source switch.

Recommended flags:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- all flags default OFF;
- dual-read flag enables Phase 7A comparison only;
- rich-evidence flag may enrich comparison evidence only;
- source flag remains inert in Phase 7B;
- disabling rich-evidence must fall back to Phase 7A comparison behavior;
- disabling dual-read must disable all Phase 7A/7B passive comparison behavior.

If implementation prefers not to add a separate rich-evidence flag, the
implementation authorization contract must explicitly justify why the existing
dual-read flag is sufficient. The design preference is a separate flag for
clean rollback and safer phased rollout.

---

## 10. Runtime behavior

Phase 7B runtime must be:

- passive;
- default-off;
- read-only;
- deterministic where possible;
- exception-isolated;
- tenant-safe;
- hidden from users;
- rollbackable by feature flag;
- non-authoritative.

Failure behavior:

```text
EUI evidence binding fails
        |
        v
record internal failure metric/log/capture
        |
        v
continue existing evaluation behavior unchanged
```

Each evidence class must degrade independently:

- missing Educational Identity becomes passive missing-identity evidence;
- missing Educational Context becomes passive missing-context evidence;
- missing Capability lookup becomes passive missing-capability evidence;
- missing Trust Report becomes passive missing-trust evidence.

No missing or ambiguous evidence class may fail evaluation.

---

## 11. Difference classification impact

Phase 7B may improve difference classification quality by making EUI evidence
richer.

It may classify:

- equivalent;
- EUI richer;
- EUI missing;
- legacy ambiguous;
- product-impacting;
- unsafe.

However:

- product-impacting and unsafe differences remain blockers for any future
  source switch;
- Phase 7B does not authorize a source switch;
- differences are internal certification evidence only.

---

## 12. Observability

Observability should remain operational and low-cardinality.

Suggested metrics:

```text
eui_consumer_migration.rich_evidence.invoked
eui_consumer_migration.rich_evidence.completed
eui_consumer_migration.rich_evidence.failed
eui_consumer_migration.rich_evidence.missing_identity
eui_consumer_migration.rich_evidence.missing_context
eui_consumer_migration.rich_evidence.capability_lookup_completed
eui_consumer_migration.rich_evidence.trust_report_completed
eui_consumer_migration.rich_evidence.duration
```

Labels must not include:

- tenant identifiers;
- student identifiers;
- raw answers;
- raw OCR text;
- uploaded content;
- teacher free text;
- parent/student names;
- tenant slugs.

### 12.1 Performance and query budget

Phase 7B implementation must define and certify a bounded performance/query
budget because rich evidence binding may execute read-only resolution and lookup
work beside the evaluation path.

The implementation authorization contract should require evidence for:

- bounded number of resolver/lookups per evaluation;
- no unbounded per-question database traversal;
- no N+1 query pattern introduced by rich evidence binding;
- measured duration for rich-evidence binding;
- graceful timeout/failure posture that preserves existing evaluation behavior.

---

## 13. Testing strategy

If implementation is later authorized, Phase 7B should include:

- evidence binder model/service tests;
- feature flag disabled tests;
- rich-evidence disabled fallback tests;
- rich-evidence enabled tests;
- missing identity/context tests;
- ambiguity/conflict tests;
- Trust Report internal-only tests;
- source flag inertness tests;
- exception isolation tests;
- production evaluation output equality tests;
- Golden Harness additions;
- AEI/evaluation regression slice;
- EUI Trust/Golden regression slice.

Golden Harness should cover:

- identity present;
- identity missing;
- context resolved;
- context ambiguous;
- capability supported;
- capability manual-review/assist;
- Trust Report trusted;
- Trust Report manual-review-required;
- Trust Report visibility unsafe;
- product-impacting difference still blocked;
- source switch still inactive.

---

## 14. Certification criteria

Phase 7B should be accepted only if certification can truthfully state:

- AEI remains source of truth;
- Phase 7A comparison still works;
- rich EUI evidence is bound passively;
- rich-evidence flag defaults OFF;
- source flag remains inert;
- production evaluation output is unchanged with all Phase 7B flags OFF;
- production evaluation output is unchanged with rich evidence ON;
- missing/ambiguous EUI evidence does not fail evaluation;
- Trust Report visibility remains internal-only;
- no Trust Report schema changes unless separately authorized;
- no marks, policy, teacher review, evidence ledger, API, UI, or schema changes;
- no non-AEI consumer migration occurred;
- rollback by disabling rich-evidence and/or dual-read is proven;
- focused tests and regression slices pass;
- certification report and retrospective are complete.

---

## 15. Explicit non-goals

Phase 7B is not attempting to:

- switch AEI to EUI source of truth;
- change marks;
- change grading;
- change teacher review routing;
- change evidence ledger output;
- expose Trust Reports;
- add UI trust badges;
- change `/api/v1`;
- add schema migrations;
- persist comparison reports;
- migrate Teacher Copilot, AI Tutor, Question Generator, Lesson Planner,
  Principal Dashboard, Parent Assistant, or School Analytics;
- replace the AEI Subject Capability Registry;
- expand public product capability claims;
- introduce LLM inference for migration comparison;
- make EUI evidence authoritative.
- extend the Trust Report schema without separate authorization.

---

## 16. Recommended implementation authorization shape

If this design brief is accepted, the next artifact should be:

```text
EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended implementation scope:

- evidence binder service;
- optional rich-evidence feature flag;
- read-only identity/context/capability/trust binding;
- extension of the existing Phase 7A adapter/observer path;
- Golden Harness additions;
- focused tests;
- certification report.

Recommended repository boundary:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/
apps/api/app/modules/eui/services/
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
apps/api/tests/golden/eui_v1/
apps/api/tests/test_eui_consumer_*.py
apps/api/tests/test_aei_passive_integration.py
apps/api/tests/test_eui_golden_harness.py
docs/product/eui-runtime/phase-7/
```

The evaluation service should be touched only for a single guarded passive hook
or to pass already-available metadata into the evidence binder.

---

## 17. ARM review questions

ARM should decide:

1. Should Phase 7B introduce a separate
   `EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED` flag?
2. Should rich evidence binding occur in a dedicated evidence binder service?
3. Which EUI objects are required for Phase 7B certification: Identity,
   Context, Capability, Trust, or all four?
4. Should Phase 7B remain in-memory/log-only, with no persistent comparison
   storage?
5. What evidence quality is required before any future AEI source-switch design
   may even be discussed?

Recommended defaults:

- introduce a separate rich-evidence flag;
- use a dedicated evidence binder service;
- include all four evidence classes where available;
- keep capture in-memory/log-only;
- require multiple certified dual-read cycles before source-switch design.

---

## 18. ARM gate

This design brief is submitted for ARM review.

It does not authorize:

- implementation;
- production code changes;
- schema changes;
- API changes;
- UI changes;
- marks changes;
- teacher review routing changes;
- evidence ledger changes;
- Trust Report display;
- EUI source-of-truth switching;
- non-AEI consumer migration;
- product capability claim changes.

If ARM accepts this brief, the next governance action should be a Phase 7B
implementation authorization contract defining exact scope, permitted files,
feature flags, validation requirements, rollback proof, and certification
criteria.
