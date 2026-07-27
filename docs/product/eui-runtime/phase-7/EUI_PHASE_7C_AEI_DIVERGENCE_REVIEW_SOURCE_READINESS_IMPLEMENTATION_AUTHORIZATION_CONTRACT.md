# EUI Runtime Phase 7C Implementation Authorization Contract - AEI Divergence Review and Source Readiness

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7C - AEI Divergence Review and Source Readiness
- **Authorization ID:** EUI-PH7C-AEI-DIVERGENCE-READINESS-AUTH-001
- **Roadmap mapping:** Phase 7 - Consumer Migration
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-28
- **Design baseline:** [`EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md`](./EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md)
- **Phase 7 baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Phase 7A baseline:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7B baseline:** [`EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)

---

## 1. Authorization status

This document is the accepted implementation authorization contract for Phase 7C.

ARM has explicitly authorized Phase 7C implementation within this contract only.

The following remain prohibited unless explicitly authorized in a later contract:

- EUI source-of-truth switching;
- marks, grading, scoring, policy, or teacher review routing changes;
- evidence ledger changes;
- schema changes;
- API changes;
- UI changes;
- Trust Report display;
- non-AEI consumer migration;
- product capability claim changes;
- cleanup or removal of legacy AEI paths.

---

## 2. Purpose

Phase 7A introduced AEI passive dual-read comparison.

Phase 7B enriched that comparison with internal EUI evidence.

Phase 7C should introduce the internal review layer that answers:

> Is the collected AEI/EUI divergence evidence mature enough to justify a
> future, narrow source-readiness authorization?

Phase 7C is a review and readiness foundation only. It is not a source switch.

The production rule remains:

```text
Existing AEI/evaluation behavior remains source of truth.
```

---

## 3. Authorized implementation scope

This contract authorizes only the following work.

### 3.1 Internal source-readiness scorecard model

Introduce an internal model representing readiness review output.

Suggested contract:

```text
AEISourceReadinessScorecard
```

The model should represent review dimensions such as:

- behavior equivalence;
- evidence completeness;
- capability posture;
- Trust Report posture;
- tenant safety;
- product-impacting divergence;
- unsafe divergence;
- performance posture;
- rollback posture;
- regression coverage;
- evidence window status.

The model must be:

- immutable;
- JSON-serializable;
- deterministic;
- internal-only;
- non-authoritative;
- free of raw student answers, OCR text, uploaded content, teacher free text,
  student names, parent data, tenant slugs, or public product claims.

It may not contain:

- marks;
- scores;
- grading decisions;
- teacher review routing decisions;
- source-of-truth switches;
- UI display metadata.

### 3.2 Deterministic divergence review service

Introduce a deterministic service that consumes Phase 7A/7B internal comparison
evidence and produces a scorecard.

Suggested contract:

```text
AEIDivergenceReadinessReviewService
```

The service may:

- consume Phase 7A dual-read comparison summaries;
- consume Phase 7B rich EUI evidence bundles;
- classify review posture;
- identify blocker categories;
- verify minimum evidence-window requirements;
- produce internal readiness recommendations;
- record passive operational metrics/logs.

The service may not:

- call LLMs or external AI providers;
- inspect raw student answers or uploaded content;
- assign marks;
- change grading;
- change AEI policy;
- change teacher review routing;
- write evidence ledger data;
- persist readiness decisions;
- switch AEI to EUI as source of truth;
- expose readiness output to users.

### 3.3 Review posture taxonomy

Implement a strict review posture taxonomy aligned with the Phase 7C design
brief.

Expected values:

```text
eligible
needs_more_evidence
needs_capability_work
blocked_product_impacting
blocked_unsafe
```

Rules:

- `blocked_unsafe` must dominate all other postures;
- `blocked_product_impacting` must block source readiness;
- missing required EUI evidence must not silently pass readiness;
- insufficient evidence window must result in `needs_more_evidence`;
- `eligible` may be returned only for a narrow certified scope with no unsafe
  or product-impacting blockers.

### 3.4 Evidence-window evaluation

Implement deterministic evidence-window checks.

Baseline rule:

```text
At least two certified passive dual-read cycles with rich evidence enabled for
the same narrow AEI scope, with no product-impacting or unsafe divergence.
```

For Phase 7C, the implementation may model these cycles from Golden Harness or
test fixtures only. It must not introduce production persistence or runtime
storage of evidence cycles.

### 3.5 Passive review hook

A passive/internal review hook may be added only if needed to connect Phase 7C
review logic to the existing Phase 7A/7B passive path.

Rules:

- hook must be guarded by existing Phase 7 consumer-migration flags;
- hook must not execute unless dual-read/rich evidence posture allows it;
- hook output must be internal-only;
- hook failure must be exception-isolated;
- hook must not affect production evaluation output.

No new source-readiness behavior is authorized.

### 3.6 Feature flag posture

Phase 7C must preserve the existing Phase 7 flag posture:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- dual-read remains passive;
- rich evidence remains internal;
- source flag remains inert;
- no source-readiness flag may activate source behavior;
- disabling dual-read must disable Phase 7 review activity;
- disabling rich evidence must prevent readiness eligibility.

If a new review-specific flag is introduced, it must:

- default to `false`;
- be passive/internal only;
- never activate source behavior;
- be documented in certification evidence.

### 3.7 Golden Harness readiness cases

Add Golden Harness data and tests for source-readiness review.

The harness should cover:

- equivalent evidence with sufficient window;
- equivalent evidence with insufficient window;
- EUI richer but non-behavioral evidence;
- EUI missing required evidence;
- legacy ambiguous evidence;
- product-impacting divergence;
- unsafe divergence;
- capability unsupported/manual-review posture;
- Trust Report non-internal visibility as unsafe;
- tenant-safety mismatch;
- performance/rollback posture not satisfied;
- source flag inertness.

### 3.8 Certification report

Produce Phase 7C certification evidence.

Required report:

```text
docs/product/eui-runtime/phase-7/
EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_CERTIFICATION_REPORT.md
```

The report must include:

- authorization scope review;
- changed-file inventory;
- scorecard model validation;
- deterministic review service validation;
- Golden Harness evidence;
- feature-flag/source-flag inertness proof;
- no behavior-change proof;
- no persistence/schema/API/UI proof;
- no Trust Report display proof;
- no LLM/provider-call proof;
- rollback proof;
- regression results;
- retrospective.

---

## 4. Authorized repository boundary

Repository changes are limited to the following areas.

### 4.1 Source modules

Permitted:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/
apps/api/app/modules/eui/services/
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
```

`answer_sheet_eval_service.py` may be touched only to keep a single guarded
passive hook or pass already-available Phase 7A/7B evidence into the review
service.

Not permitted:

```text
apps/api/app/modules/ai/
apps/api/app/modules/knowledge_graph/
apps/api/app/modules/exams/
apps/admin-web/
```

Any change outside this boundary requires separate ARM authorization.

### 4.2 Tests and Golden Harness

Permitted:

```text
apps/api/tests/golden/eui_v1/
apps/api/tests/test_eui_consumer_*.py
apps/api/tests/test_aei_passive_integration.py
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/test_evaluation_engine.py
apps/api/tests/test_answer_sheet_eval.py
```

Tests may be updated only to prove deterministic readiness review, passive
operation, source-flag inertness, and unchanged evaluation behavior.

### 4.3 Documentation

Permitted:

```text
docs/product/eui-runtime/phase-7/
```

`docs/STATUS.md` should be updated only after certification/publication, not in
the implementation commit.

---

## 5. Explicit exclusions

The following are not authorized:

- AEI source switch to EUI;
- marks changes;
- grading changes;
- scoring changes;
- evaluation policy changes;
- teacher review routing changes;
- evidence ledger changes;
- database schema changes;
- Alembic migrations;
- API endpoint changes;
- UI changes;
- Trust Report display;
- Trust Report schema changes;
- teacher-facing readiness summaries;
- parent/student/principal-facing behavior;
- non-AEI consumer migration;
- migration of Teacher Copilot, AI Tutor, Question Generator, Lesson Planner,
  Principal Dashboard, Parent Assistant, or School Analytics;
- cleanup/removal of legacy AEI paths;
- LLM calls for readiness review;
- external AI provider integration;
- public capability claim changes;
- product launch scope decisions;
- replacement of the AEI Subject Capability Registry.

Any of these require separate ARM authorization.

---

## 6. Runtime constraints

The implementation must be:

- passive;
- default-off where flagged;
- read-only;
- deterministic;
- review-only;
- non-authoritative;
- internal-only;
- exception-isolated;
- tenant-safe;
- hidden from users;
- rollbackable by feature flag.

If readiness review fails, existing production evaluation behavior must continue
unchanged.

---

## 7. Blocker rules

Phase 7C must fail closed for source readiness.

| Evidence condition | Required readiness posture |
|---|---|
| Unsafe divergence present | `blocked_unsafe` |
| Product-impacting divergence present | `blocked_product_impacting` |
| Trust Report visibility not internal-only | `blocked_unsafe` |
| Tenant-safety mismatch | `blocked_unsafe` |
| Required EUI evidence missing | `needs_capability_work` or `needs_more_evidence` |
| Evidence window insufficient | `needs_more_evidence` |
| Capability unsupported | `needs_capability_work` |
| Legacy ambiguous | `needs_more_evidence` |
| Equivalent and sufficient evidence | `eligible`, only if all blockers pass |

No missing or ambiguous signal may be treated as eligible by default.

---

## 8. Performance and query budget

Phase 7C must include a bounded performance posture.

Implementation must demonstrate:

- no unbounded per-question database traversal;
- no N+1 query pattern introduced by readiness review;
- bounded review orchestration per evaluation/comparison;
- measured duration for readiness review where hooked passively;
- exception/timeout handling that preserves evaluation behavior.

Recommended initial budget:

```text
Readiness review should be O(1) over already-collected Phase 7A/7B summary
evidence wherever possible.
```

Any implementation requiring raw per-answer or per-upload traversal requires
separate ARM authorization.

---

## 9. Observability

Allowed operational metrics/log signals include:

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

Metrics/logs must avoid:

- tenant identifiers;
- student identifiers;
- raw student answers;
- raw OCR text;
- uploaded content;
- teacher free text;
- parent/student names;
- tenant slugs;
- sensitive educational evidence.

---

## 10. Validation requirements

Before ARM acceptance, implementation must provide evidence for the following.

### 10.1 Focused validation

- scorecard model tests;
- review posture taxonomy tests;
- deterministic review service tests;
- blocker precedence tests;
- evidence-window tests;
- insufficient-evidence tests;
- Trust Report visibility safety tests;
- tenant-safety mismatch tests;
- source flag inertness tests;
- passive hook disabled behavior tests, if a hook is introduced;
- exception isolation tests, if a hook is introduced;
- Golden Harness readiness tests.

### 10.2 Regression validation

Required regression slices:

- Phase 7A comparison tests;
- Phase 7B rich evidence binding tests;
- AEI passive integration tests;
- AEI/evaluation regression slice;
- EUI Trust Framework tests;
- EUI Golden Harness tests;
- API import.

### 10.3 Static validation

- focused Ruff for touched API files;
- `git diff --check`;
- scan proving no source switch behavior;
- scan proving source flag remains inert;
- scan proving no Trust Report display or UI exposure;
- scan proving no persistence/write path in Phase 7C files;
- scan proving no LLM/provider call in Phase 7C files;
- scan proving no API/router/schema migration changes.

---

## 11. Rollback proof

Rollback must be proven by demonstrating:

- dual-read flag disabled disables Phase 7 review activity;
- rich-evidence flag disabled prevents readiness eligibility;
- source flag remains inert;
- readiness review output is internal-only;
- evaluation outputs are unchanged with review disabled;
- evaluation outputs are unchanged with review enabled, if a passive hook is
  introduced;
- no persisted readiness evidence exists;
- no schema rollback is required;
- regression slices pass.

---

## 12. Acceptance criteria

Phase 7C may be accepted only if all of the following are true:

- AEI remains source of truth;
- Phase 7A comparison remains intact;
- Phase 7B rich evidence binding remains intact;
- internal readiness scorecard exists as authorized;
- deterministic review service exists as authorized;
- source flag remains inert;
- no source switch occurred;
- scorecard output is internal-only;
- product-impacting and unsafe differences block readiness;
- missing evidence does not silently pass readiness;
- evidence-window requirements are enforced;
- raw educational content is not captured;
- no marks, scoring, grading, policy, teacher review, or evidence-ledger
  changes occurred;
- no API/UI/schema changes occurred;
- no non-AEI consumer migration occurred;
- performance/query budget is certified;
- rollback proof is documented;
- regression slices pass;
- certification report and retrospective are complete.

---

## 13. Commit, tag, and publication expectation

If implementation is later accepted, recommended metadata:

```text
Commit: feat(eui): add AEI divergence readiness review foundation
Tag: eui-runtime-phase7c-aei-divergence-readiness-certified
```

Publication should follow the established lifecycle:

```text
ARM Authorization
      |
      v
Implementation
      |
      v
Validation
      |
      v
Certification
      |
      v
ARM Acceptance
      |
      v
Commit
      |
      v
Annotated Tag
      |
      v
Publish
      |
      v
Update Master Status
```

---

## 14. ARM decision gate

This contract has been accepted by ARM for implementation.

Phase 7C implementation may begin only within this contract. Any expansion
beyond internal AEI divergence review and
source-readiness scorecarding requires separate ARM authorization.
