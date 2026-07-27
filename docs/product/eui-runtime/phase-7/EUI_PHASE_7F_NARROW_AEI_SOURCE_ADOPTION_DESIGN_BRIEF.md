# EUI Runtime Phase 7F Design Brief - Narrow AEI Source Adoption

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7F - Narrow AEI Source Adoption
- **Roadmap mapping:** Phase 7 - Consumer Migration
- **Classification:** Design brief
- **Status:** Deferred / Future Scope
- **Implementation:** Not authorized
- **Deferral reason:** No immediate product-facing need after Phase 7E certification
- **Date:** 2026-07-28
- **Architecture baseline:** [`../../../architecture/EUI.md`](../../../architecture/EUI.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)
- **Phase 7 baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Phase 7A baseline:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7B baseline:** [`EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md`](./EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md)
- **Phase 7C baseline:** [`EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md`](./EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md)
- **Phase 7D baseline:** [`EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_DESIGN_BRIEF.md`](./EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_DESIGN_BRIEF.md)
- **Phase 7E baseline:** [`EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_DESIGN_BRIEF.md`](./EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_DESIGN_BRIEF.md)
- **Depends on:** Phase 7E - Narrow AEI source-readiness trial foundation

---

## 1. Governance note

Phase 7F was not part of the original Phase 7 naming sequence. It was drafted
as a possible future technical source-adoption slice after Phase 7E was
published.

ARM has decided not to implement Phase 7F now.

Phase 7 is closed at Phase 7E. Phase 7F remains deferred future scope.

This document does not reopen AEI or EUI architecture.

This document does not authorize implementation.

Phase 7F may be reopened only if source adoption solves a real product problem,
not merely because the architecture can support it.

Implementation remains not authorized.

---

## 1.1 Reopen conditions

Implement Phase 7F only when at least one of the following becomes true and ARM
explicitly authorizes a 7F implementation contract:

- a real product-facing flow needs EUI to become the selected metadata source;
- legacy AEI metadata starts blocking accuracy, consistency, or
  maintainability;
- Phase 7E trial evidence shows stable readiness across real usage;
- marks, routing, ledger, API, UI, and schema can be proven unchanged;
- rollback is simple: disable the flag and return to legacy AEI;
- ARM explicitly authorizes a 7F implementation contract.

Simple rule:

```text
Do 7F only when source adoption solves a real product problem, not because the
architecture can support it.
```

---

## 2. Purpose

Phase 7A through Phase 7E proved that AEI can passively consume, enrich, review,
candidate-rank, and internally trial EUI evidence without changing production
evaluation behavior.

Phase 7F asks the next, narrower question:

> Can EUI become the selected internal source for a strictly bounded AEI
> metadata scope while legacy AEI/evaluation remains authoritative for marks,
> grading, routing, ledger behavior, and user-facing output?

The answer must be designed before any code changes.

Phase 7F is not a full AEI source-of-truth switch. It is a design for possible
source adoption of internal metadata only.

---

## 3. Core principle

Narrow source adoption is not evaluation authority.

The governing rule remains:

```text
Legacy AEI/evaluation remains authoritative for academic outcomes.
```

If Phase 7F is later implemented, EUI may be allowed to supply selected,
non-authoritative metadata references to AEI for one narrow scope. EUI must not
become authoritative for:

- marks;
- grading;
- scoring;
- answer correctness;
- evaluation policy;
- teacher review routing;
- evidence ledger writes;
- student/parent/principal-facing output.

---

## 4. Why Phase 7F exists

Phase 7E established that a ready Phase 7D candidate can be exercised as an
internal trial result.

Without Phase 7F, the next change could blur trial and adoption.

Phase 7F creates a controlled design boundary between:

```text
trial_ready
        |
        v
narrow source adoption decision
        |
        v
internal metadata source selection only
        |
        v
no marks/routing/ledger/API/UI behavior change
```

The design should answer:

- Which exact metadata may use EUI as the selected source?
- Which AEI outputs must remain legacy-sourced?
- What readiness evidence is required before adoption?
- What feature flag posture controls adoption?
- What rollback means in practice?
- What divergence threshold blocks adoption?
- What certification proves user-visible behavior is unchanged?

---

## 5. Proposed source adoption scope

The only acceptable Phase 7F adoption scope is:

```text
context_metadata_only
```

Allowed internal metadata classes:

- Educational Identity reference;
- Educational Context reference;
- Platform Capability posture reference;
- Trust Report reference/posture;
- readiness scorecard reference;
- source-readiness candidate reference;
- source-readiness trial reference;
- safe evidence availability flags;
- bounded source selection status.

These fields may support internal AEI observability, comparison, certification,
and future migration planning.

They may not become user-facing or outcome-authoritative in Phase 7F.

---

## 6. Explicitly excluded source scopes

Phase 7F must not design adoption for:

- marks source;
- grading source;
- score calculation;
- answer correctness;
- rubric policy;
- teacher review routing;
- evidence ledger write source;
- student intelligence source;
- parent report source;
- principal dashboard source;
- public product capability claims;
- full AEI replacement.

If any of these are needed, they require a separate design brief and ARM
authorization.

---

## 7. Responsibilities

Phase 7F is responsible for designing:

- narrow source adoption eligibility;
- source adoption decision contract;
- source precedence for `context_metadata_only`;
- feature flag posture;
- fail-closed blocker rules;
- rollback model;
- behavior-equivalence proof;
- Golden Harness requirements;
- certification requirements.

Phase 7F is not responsible for:

- implementing source adoption;
- switching marks or grading;
- changing teacher review;
- writing evidence ledger data;
- exposing Trust Reports;
- changing public APIs or UI;
- introducing schema changes;
- migrating non-AEI consumers;
- changing product claims.

---

## 8. Inputs

Allowed inputs:

| Input | Source |
|---|---|
| Phase 7A comparison | AEI consumer migration observer |
| Phase 7B rich EUI evidence bundle | AEI rich EUI evidence binder |
| Phase 7C readiness scorecard | AEI divergence readiness review service |
| Phase 7D source-readiness candidate | AEI source-readiness candidate service |
| Phase 7E source-readiness trial result | AEI source-readiness trial service |
| Existing AEI/evaluation summary | Existing evaluation path |
| Existing feature flag posture | Settings |
| Golden Harness adoption cases | Phase 7F Golden Harness |

Not allowed:

- raw student answers;
- raw OCR text;
- uploaded document contents;
- teacher free text;
- student/parent names;
- tenant slugs;
- public product claims;
- LLM-generated adoption decisions.

---

## 9. Source adoption decision contract

Phase 7F should define a decision object rather than changing AEI behavior.

Suggested future contract:

```text
AEINarrowSourceAdoptionDecision
```

The decision should represent:

- decision ID;
- tenant ID;
- consumer: `aei`;
- subject type;
- scope reference;
- adoption scope: `context_metadata_only`;
- source mode;
- selected source;
- legacy source confirmation;
- source-readiness trial reference;
- source-readiness candidate reference;
- allowed metadata classes;
- blocked metadata classes;
- adoption state;
- feature flag posture;
- rollback posture;
- internal-only posture;
- metadata.

The decision must be:

- immutable;
- JSON-serializable;
- deterministic;
- internal-only;
- non-authoritative for academic outcomes;
- free of raw answer/content/PII;
- unable to affect marks, routing, ledger, API, UI, or schema.

---

## 10. Recommended adoption states

Recommended future states:

```text
adoption_not_enabled
adoption_ready
adoption_active_internal_metadata
adoption_blocked_not_ready
adoption_blocked_product_impacting
adoption_blocked_unsafe
```

State meanings:

| State | Meaning |
|---|---|
| `adoption_not_enabled` | Feature flag or rollout posture does not permit adoption. |
| `adoption_ready` | Evidence supports adoption, but source selection is not active. |
| `adoption_active_internal_metadata` | EUI is selected only for approved internal metadata classes. |
| `adoption_blocked_not_ready` | More evidence or capability work is required. |
| `adoption_blocked_product_impacting` | Adoption could affect product behavior or claims. |
| `adoption_blocked_unsafe` | Adoption is unsafe or could alter authoritative behavior. |

No state may authorize marks, routing, ledger, API, UI, or schema changes.

---

## 11. Source precedence model

The Phase 7F source precedence model should be explicit.

For `context_metadata_only`:

1. If source adoption is disabled, legacy AEI metadata remains selected.
2. If source adoption is enabled but trial readiness is not ready, legacy AEI
   metadata remains selected.
3. If trial readiness is blocked, legacy AEI metadata remains selected.
4. If EUI metadata is selected, selection is limited to approved internal
   metadata classes only.
5. If any conflict could affect academic outcomes, legacy AEI remains selected.

The default source is always legacy AEI unless all adoption gates pass.

---

## 12. Feature flag posture

Phase 7F should be controlled by an explicit source adoption flag if later
implemented.

Recommended future flag:

```text
EUI_CONSUMER_AEI_SOURCE_ADOPTION_ENABLED=false
```

Flag requirements:

- default false;
- tenant-safe;
- internal-only;
- reversible without data migration;
- cannot enable marks/routing/ledger behavior;
- cannot expose UI/API behavior;
- must fail closed to legacy AEI;
- disabling the flag must restore legacy metadata source selection.

Existing source-related flags must remain inert unless explicitly changed by a
future implementation contract.

---

## 13. Adoption eligibility gates

Phase 7F adoption readiness should require all of the following:

- Phase 7E trial result is `trial_ready`;
- candidate scope is exactly `context_metadata_only`;
- source switch for outcomes remains inactive;
- legacy AEI source-of-truth is confirmed;
- no product-impacting divergence is present;
- no unsafe divergence is present;
- Trust Report is internal and not displayed;
- Platform Capability posture permits internal metadata use;
- rollback path is proven;
- Golden Harness adoption cases pass;
- existing evaluation outputs remain unchanged.

Any missing gate must block adoption.

---

## 14. Divergence threshold

For Phase 7F, divergence tolerance should be strict:

```text
Any product-impacting or unsafe divergence blocks adoption.
```

Allowed differences may include only internal metadata representation
differences that do not affect:

- marks;
- grading;
- scoring;
- teacher review routing;
- evidence ledger writes;
- API responses;
- UI;
- student/parent/principal-facing output.

If a difference cannot be classified safely, it must be treated as blocked.

---

## 15. Failure posture

Phase 7F must fail closed.

If adoption evidence is missing, ambiguous, stale, or unsafe:

```text
selected source = legacy AEI
```

Failure must not:

- raise user-visible errors;
- block evaluation;
- alter marks;
- alter routing;
- write ledger data;
- expose internal readiness state to users.

---

## 16. Observability

Allowed operational metrics/log signals:

```text
eui_consumer_migration.source_adoption.invoked
eui_consumer_migration.source_adoption.ready
eui_consumer_migration.source_adoption.active_internal_metadata
eui_consumer_migration.source_adoption.blocked_not_ready
eui_consumer_migration.source_adoption.blocked_product_impacting
eui_consumer_migration.source_adoption.blocked_unsafe
eui_consumer_migration.source_adoption.rollback_to_legacy
eui_consumer_migration.source_adoption.duration_ms
```

Observability must not include:

- raw answers;
- OCR text;
- uploaded content;
- teacher free text;
- student/parent names;
- tenant slugs;
- public product claims.

---

## 17. Testing strategy

Future implementation should include:

- model strictness tests;
- deterministic adoption ID tests;
- source precedence tests;
- feature flag default-off tests;
- ready trial produces adoption-ready tests;
- ready trial plus enabled flag produces internal metadata adoption tests;
- product-impacting blocker tests;
- unsafe blocker tests;
- missing trial tests;
- rollback-to-legacy tests;
- no raw-content capture tests;
- no marks/routing/ledger/API/UI behavior change regression tests.

---

## 18. Golden Harness requirements

Future Golden Harness cases should cover:

- adoption disabled keeps legacy AEI selected;
- ready trial and enabled flag selects EUI for internal metadata only;
- not-ready trial keeps legacy AEI selected;
- product-impacting blocker keeps legacy AEI selected;
- unsafe blocker keeps legacy AEI selected;
- broad scope blocks adoption;
- missing legacy source confirmation blocks adoption;
- deterministic adoption IDs;
- no raw-content capture.

---

## 19. Certification criteria

Phase 7F implementation, if later authorized, may be accepted only if it proves:

- source adoption is limited to `context_metadata_only`;
- feature flag defaults off;
- rollback by disabling flag works;
- marks remain unchanged;
- grading remains unchanged;
- teacher review routing remains unchanged;
- evidence ledger behavior remains unchanged;
- API remains unchanged;
- UI remains unchanged;
- database schema remains unchanged;
- source adoption decisions are deterministic;
- source adoption decisions are internal-only;
- Golden Harness adoption cases pass;
- existing AEI/evaluation regression slice passes;
- no raw content or PII is captured;
- no LLM/provider calls are introduced.

---

## 20. Explicit non-goals

Phase 7F is not:

- a full AEI source switch;
- a marks engine change;
- a grading engine change;
- a policy engine change;
- a teacher review workflow change;
- an evidence ledger migration;
- a user-facing Trust Report launch;
- a public capability-claim update;
- a non-AEI consumer migration;
- a schema/API/UI migration;
- a replacement of AEI with EUI.

---

## 21. ARM gate

This design brief may be accepted, rejected, or revised by ARM.

Acceptance of this design brief does not authorize implementation.

The next artifact, if ARM accepts this design, should be:

```text
docs/product/eui-runtime/phase-7/
EUI_PHASE_7F_NARROW_AEI_SOURCE_ADOPTION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

That contract must define the exact implementation boundary before any runtime
code is written.
