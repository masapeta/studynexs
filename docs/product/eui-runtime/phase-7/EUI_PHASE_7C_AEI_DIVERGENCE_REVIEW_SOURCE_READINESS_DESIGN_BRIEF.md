# EUI Runtime Phase 7C Design Brief - AEI Divergence Review and Source Readiness

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7C - AEI Divergence Review and Source Readiness
- **Roadmap mapping:** Phase 7 - Consumer Migration
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized by this design brief
- **Date:** 2026-07-28
- **Architecture baseline:** [`../../../architecture/EUI.md`](../../../architecture/EUI.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)
- **Phase 7 baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Phase 7A baseline:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7B baseline:** [`EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md`](./EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md)
- **Depends on:** Phase 7A - AEI passive dual-read foundation; Phase 7B - AEI rich EUI evidence binding

---

## 1. Purpose

Phase 7A proved that AEI can run a passive dual-read comparison beside the
existing evaluation path.

Phase 7B enriched that comparison with EUI evidence:

- Educational Context;
- Educational Identity evidence where available;
- Platform Capability posture;
- Trust Report posture.

Phase 7C answers the next question:

> How should StudyNexs review AEI/EUI divergence evidence and decide whether a
> future, narrow source-readiness phase is even eligible for authorization?

Phase 7C is not a source switch. It is a review and readiness design phase.

---

## 2. Core principle

Evidence precedes authority.

EUI may become a source for a consumer only after repeated passive evidence
shows that doing so is safe, explainable, reversible, and narrower than the
certified capability boundary.

The governing rule remains:

```text
Existing AEI/evaluation behavior remains source of truth.
```

---

## 3. Why Phase 7C exists

After Phase 7B, AEI has richer internal comparison evidence, but richer evidence
alone does not justify a source switch.

Without a formal divergence review model, the program risks one of two bad
outcomes:

1. switching too early because evidence exists; or
2. never switching because evidence is not summarized into a decision framework.

Phase 7C should define the decision framework.

It should make future ARM reviews answerable with evidence rather than
intuition.

---

## 4. Responsibilities

Phase 7C is responsible for designing:

- the AEI/EUI divergence review lifecycle;
- the source-readiness scorecard;
- blocker classifications;
- required evidence windows;
- minimum confidence and safety gates;
- rollback expectations for any later source-readiness implementation;
- the boundary between passive review and source switching;
- what evidence is sufficient to authorize a future source-readiness contract.

Phase 7C is not responsible for:

- switching AEI to EUI;
- changing evaluation results;
- changing marks, grading, scoring, or policy;
- changing teacher review routing;
- changing evidence ledger behavior;
- exposing Trust Reports;
- adding UI/API/schema changes;
- migrating non-AEI consumers.

---

## 5. Inputs to the review model

Phase 7C should consume only internal evidence from already-published phases.

Allowed evidence inputs:

| Evidence | Source |
|---|---|
| Legacy evaluation summary | Existing evaluation path |
| AEI passive capture summary | AEI passive integration |
| Phase 7A dual-read comparison | AEI consumer migration observer |
| Educational Context presence/status | Phase 7B rich evidence |
| Educational Identity presence | Phase 7B rich evidence |
| Capability mode/match/conflict | Platform Capability Registry via Phase 7B |
| Trust Report posture | Phase 7B rich evidence |
| Difference classification | Phase 7A comparison taxonomy |
| Runtime metrics | Phase 7A/7B operational metrics |

Not allowed as Phase 7C evidence:

- raw student answers;
- raw OCR text;
- uploaded document contents;
- teacher free text;
- student/parent names;
- tenant slugs;
- public product claims;
- unsupported manual analysis not captured in certification evidence.

---

## 6. Divergence taxonomy

Phase 7C should preserve the Phase 7A taxonomy and add review posture.

Existing difference types:

| Difference type | Source-switch posture |
|---|---|
| Equivalent | Potentially eligible after repeated clean evidence |
| EUI richer | Potentially eligible only if richness is non-behavioral |
| EUI missing | Not eligible until missing signal is resolved or explicitly accepted |
| Legacy ambiguous | Requires human review; not automatically eligible |
| Product-impacting | Blocks source readiness |
| Unsafe | Blocks source readiness |

Recommended review posture:

| Review posture | Meaning |
|---|---|
| `eligible` | Evidence supports future source-readiness authorization for a narrow scope |
| `needs_more_evidence` | No blocker, but evidence window or coverage is insufficient |
| `needs_capability_work` | EUI is missing required representation or support |
| `blocked_product_impacting` | EUI would alter product behavior |
| `blocked_unsafe` | EUI would violate trust, tenant, role, or authority boundaries |

---

## 7. Source-readiness scorecard

Phase 7C should define a scorecard rather than a single pass/fail flag.

Recommended dimensions:

| Dimension | Question |
|---|---|
| Behavior equivalence | Would the user-visible evaluation result remain unchanged? |
| Evidence completeness | Are required EUI evidence classes present? |
| Capability posture | Is the capability supported for the declared scope? |
| Trust posture | Is Trust Report posture internal-only and non-blocking? |
| Tenant safety | Are tenant signals consistent and scoped? |
| Product-impacting divergence | Are product-impacting differences absent? |
| Unsafe divergence | Are unsafe differences absent? |
| Performance | Is comparison overhead within budget? |
| Rollback | Can the source path be disabled immediately? |
| Regression coverage | Are Golden Harness and evaluation regressions sufficient? |

Source-readiness should require all blocker dimensions to pass. Non-blocking
dimensions may recommend additional evidence or capability work.

---

## 8. Evidence window

Phase 7C should define a minimum evidence window before any source-readiness
contract may be considered.

Suggested baseline:

```text
At least two certified passive dual-read cycles with rich evidence enabled for
the same narrow AEI scope, with no product-impacting or unsafe divergence.
```

This is intentionally conservative.

A "cycle" may be a certified test/Golden Harness cycle, a controlled internal
runtime validation cycle, or a future explicitly authorized production-shadow
cycle. The source of the cycle must be documented in the certification report.

---

## 9. Narrow scope requirement

Any future source-readiness phase must be scoped narrowly.

Examples of acceptable narrow scopes:

- AEI context metadata only;
- specific board/grade/subject;
- specific assessment mode;
- specific capability mode;
- specific evidence class, such as Educational Context only.

Examples of unacceptable scopes:

- all AEI evaluation;
- all subjects;
- all schools;
- all Trust Report use;
- marks, scoring, grading, or teacher review routing;
- parent/student-facing intelligence.

---

## 10. Feature flag strategy

Phase 7C should keep the existing Phase 7 flag posture:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- dual-read remains passive;
- rich-evidence remains internal;
- source flag remains inert unless a later source-readiness contract explicitly
  changes its behavior;
- no new broad migration flag should be introduced;
- no source-readiness behavior is authorized by this design brief.

---

## 11. Observability design

Phase 7C should design review observability as operational evidence, not
product analytics.

Suggested future signals:

```text
eui_consumer_migration.readiness_review.invoked
eui_consumer_migration.readiness_review.completed
eui_consumer_migration.readiness_review.blocked
eui_consumer_migration.readiness_review.needs_more_evidence
eui_consumer_migration.readiness_review.duration
```

Allowed low-cardinality labels:

- consumer: `aei`;
- review posture;
- blocker category;
- capability mode;
- trust posture;
- evidence completeness bucket.

Forbidden labels:

- tenant identifiers;
- student identifiers;
- raw content;
- free-text educational material;
- parent/student names;
- tenant slugs.

---

## 12. Testing strategy

If Phase 7C later receives implementation authorization, tests should cover:

- scorecard model strictness;
- deterministic review posture;
- equivalent evidence eligibility;
- EUI-richer non-behavioral eligibility;
- EUI-missing non-eligibility;
- legacy-ambiguous review posture;
- product-impacting blocker;
- unsafe blocker;
- insufficient evidence window;
- source flag inertness;
- no behavior change;
- Golden Harness readiness cases.

This design brief itself does not authorize those tests or implementation.

---

## 13. Certification criteria for a future implementation

A future Phase 7C implementation should be accepted only if certification can
truthfully state:

- review logic stayed within its authorization contract;
- no AEI/evaluation behavior changed;
- no source switch occurred;
- source flag remained inert;
- scorecard output is internal only;
- product-impacting and unsafe differences block readiness;
- missing evidence does not silently pass readiness;
- raw educational content is not captured;
- no API/UI/schema changes occurred;
- regression slices pass;
- rollback is documented;
- certification report and retrospective are complete.

---

## 14. Explicit non-goals

Phase 7C is not attempting to:

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
- remove legacy AEI paths.

---

## 15. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/eui-runtime/phase-7/
EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended implementation scope for that future contract:

- internal AEI source-readiness scorecard model;
- deterministic review service over Phase 7A/7B comparison evidence;
- Golden Harness readiness cases;
- default-off/passive review hook only if needed;
- no source switch;
- no marks, routing, ledger, API, UI, or schema changes.

---

## 16. ARM review gate

This design brief has been accepted by ARM as the Phase 7C design baseline.

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

Implementation may begin only under a separate accepted Phase 7C implementation
authorization contract.
