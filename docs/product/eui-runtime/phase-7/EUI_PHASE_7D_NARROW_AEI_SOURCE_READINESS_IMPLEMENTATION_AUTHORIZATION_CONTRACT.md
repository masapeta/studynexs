# EUI Runtime Phase 7D Implementation Authorization Contract - Narrow AEI Source Readiness

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7D - Narrow AEI Source Readiness
- **Authorization ID:** EUI-PH7D-NARROW-AEI-SOURCE-READINESS-AUTH-001
- **Roadmap mapping:** Phase 7 - Consumer Migration
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-28
- **Design baseline:** [`EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_DESIGN_BRIEF.md`](./EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_DESIGN_BRIEF.md)
- **Phase 7 baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Phase 7A baseline:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7B baseline:** [`EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7C baseline:** [`EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)

---

## 1. Authorization status

This document is the accepted implementation authorization contract for Phase
7D.

ARM has explicitly authorized Phase 7D implementation within this contract
only.

The following remain prohibited unless explicitly authorized in a later
contract:

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

Phase 7C introduced deterministic internal divergence readiness review.

Phase 7D should define the narrowest internal source-readiness candidate that
can be prepared from Phase 7C evidence without making EUI authoritative.

The production rule remains:

```text
Existing AEI/evaluation behavior remains source of truth.
```

Phase 7D is a candidate foundation only. It is not a source switch, adoption
phase, or behavior change.

---

## 3. Authorized implementation scope

This contract authorizes only the following work.

### 3.1 Internal AEI source-readiness candidate model

Introduce an internal model representing a narrow AEI source-readiness
candidate.

Suggested contract:

```text
AEISourceReadinessCandidate
```

The model should represent:

- candidate ID;
- tenant ID;
- consumer: `aei`;
- subject type;
- scope reference;
- candidate scope, initially `context_metadata_only`;
- readiness scorecard reference;
- eligible evidence classes;
- blocked evidence classes;
- candidate state;
- source flag status;
- source switch active: always false in Phase 7D;
- internal-only posture;
- rollback posture;
- metadata.

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
- answer correctness;
- teacher review routing decisions;
- evidence ledger write instructions;
- source-of-truth switches;
- UI display metadata.

### 3.2 Deterministic source-readiness candidate service

Introduce a deterministic service that consumes Phase 7C readiness scorecards
and produces internal candidate output.

Suggested contract:

```text
AEISourceReadinessCandidateService
```

The service may:

- consume Phase 7C readiness scorecards;
- consume Phase 7B internal evidence-bundle metadata where already available;
- classify the narrow candidate state;
- identify eligible and blocked evidence classes;
- verify that the candidate scope is explicitly narrow;
- verify that the source switch remains inactive;
- record passive operational metrics/logs.

The service may not:

- call LLMs or external AI providers;
- inspect raw student answers or uploaded content;
- assign marks;
- change grading;
- change AEI policy;
- change teacher review routing;
- write evidence ledger data;
- persist candidate decisions;
- switch AEI to EUI as source of truth;
- expose candidate output to users.

### 3.3 Candidate state taxonomy

Implement a strict candidate state taxonomy aligned with the Phase 7D design
brief.

Expected values:

```text
ready_for_internal_trial
not_ready_more_evidence
not_ready_capability_work
blocked_product_impacting
blocked_unsafe
```

Rules:

- `blocked_unsafe` must dominate all other states;
- `blocked_product_impacting` must block source readiness;
- insufficient evidence must result in `not_ready_more_evidence`;
- insufficient capability posture must result in `not_ready_capability_work`;
- `ready_for_internal_trial` may be returned only when Phase 7C posture is
  `eligible` and all Phase 7D blockers pass.

No state may change AEI behavior.

### 3.4 Candidate ID generation

Implement deterministic candidate IDs for the internal candidate model.

IDs must be stable for the same:

- consumer;
- tenant ID;
- subject type;
- scope reference;
- candidate scope;
- readiness scorecard reference.

IDs must not include:

- student identifiers;
- parent identifiers;
- tenant slugs;
- raw answer text;
- raw OCR text;
- uploaded content;
- free-text educational material.

### 3.5 Source flag inertness

Phase 7D must preserve the existing Phase 7 flag posture:

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
- source switch active must remain false in all Phase 7D outputs;
- disabling dual-read/rich-evidence posture must prevent eligible candidate
  output where applicable.

If a new candidate-specific flag is introduced, it must:

- default to `false`;
- be passive/internal only;
- never activate source behavior;
- be documented in certification evidence.

### 3.6 Passive/internal hook

A passive/internal hook may be added only if needed to connect Phase 7D
candidate logic to existing Phase 7A/7B/7C internal evidence.

Rules:

- hook must be guarded by existing Phase 7 consumer-migration flags;
- hook output must be internal-only;
- hook failure must be exception-isolated;
- hook must not affect production evaluation output;
- hook must not make AEI depend on the candidate as source of truth.

No source-readiness adoption behavior is authorized.

### 3.7 Golden Harness candidate cases

Add Golden Harness data and tests for narrow AEI source-readiness candidates.

The harness should cover:

- eligible Phase 7C scorecard produces `ready_for_internal_trial`;
- insufficient evidence produces `not_ready_more_evidence`;
- insufficient capability posture produces `not_ready_capability_work`;
- product-impacting divergence produces `blocked_product_impacting`;
- unsafe divergence produces `blocked_unsafe`;
- candidate scope broader than `context_metadata_only` is blocked;
- Trust Report visibility that is not internal-only is blocked;
- source flag active/source switch attempt is blocked;
- candidate ID determinism;
- no raw content capture;
- source flag inertness.

### 3.8 Certification report

Produce Phase 7D certification evidence.

Required report:

```text
docs/product/eui-runtime/phase-7/
EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_CERTIFICATION_REPORT.md
```

The report must include:

- authorization scope review;
- changed-file inventory;
- candidate model validation;
- deterministic candidate service validation;
- Golden Harness evidence;
- feature-flag/source-flag inertness proof;
- no behavior-change proof;
- no persistence/schema/API/UI proof;
- no Trust Report display proof;
- no LLM/provider-call proof;
- no raw-content capture proof;
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
passive hook or pass already-available Phase 7A/7B/7C evidence into the
candidate service.

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

Tests may be updated only to prove deterministic candidate creation, passive
operation, source-flag inertness, no raw-content capture, and unchanged
evaluation behavior.

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
- EUI source-of-truth adoption;
- marks changes;
- grading changes;
- scoring changes;
- evaluation policy changes;
- teacher review routing changes;
- evidence ledger changes or writes;
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
- LLM calls for candidate creation;
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
- candidate-only;
- non-authoritative;
- internal-only;
- exception-isolated;
- tenant-safe;
- hidden from users;
- rollbackable by feature flag.

If candidate creation fails, existing production evaluation behavior must
continue unchanged.

---

## 7. Blocker rules

Phase 7D must fail closed for source readiness.

| Evidence condition | Required candidate state |
|---|---|
| Unsafe divergence present | `blocked_unsafe` |
| Product-impacting divergence present | `blocked_product_impacting` |
| Trust Report visibility not internal-only | `blocked_unsafe` |
| Tenant-safety mismatch | `blocked_unsafe` |
| Candidate scope broader than `context_metadata_only` | `blocked_product_impacting` |
| Source switch active or attempted | `blocked_unsafe` |
| Required EUI evidence missing | `not_ready_more_evidence` or `not_ready_capability_work` |
| Evidence window insufficient | `not_ready_more_evidence` |
| Capability unsupported | `not_ready_capability_work` |
| Phase 7C posture not eligible | matching non-ready or blocked candidate state |
| Eligible and sufficient evidence | `ready_for_internal_trial`, only if all blockers pass |

No missing or ambiguous signal may be treated as ready by default.

---

## 8. Performance and query budget

Phase 7D must include a bounded performance posture.

Implementation must demonstrate:

- no unbounded per-question database traversal;
- no N+1 query pattern introduced by candidate creation;
- bounded candidate orchestration per evaluation/comparison;
- measured duration for candidate creation where hooked passively;
- exception/timeout handling that preserves evaluation behavior.

Recommended initial budget:

```text
Candidate creation should be O(1) over already-collected Phase 7C scorecard
evidence wherever possible.
```

Any implementation requiring raw per-answer, per-upload, or per-artifact
traversal requires separate ARM authorization.

---

## 9. Observability

Allowed operational metrics/log signals include:

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

- candidate model tests;
- candidate state taxonomy tests;
- deterministic candidate service tests;
- blocker precedence tests;
- evidence-window / evidence-completeness tests;
- candidate scope strictness tests;
- Trust Report visibility safety tests;
- source flag inertness tests;
- source switch active false tests;
- no raw-content capture tests;
- passive hook disabled behavior tests, if a hook is introduced;
- exception isolation tests, if a hook is introduced;
- Golden Harness candidate tests.

### 10.2 Regression validation

Required regression slices:

- Phase 7A comparison tests;
- Phase 7B rich evidence binding tests;
- Phase 7C divergence readiness tests;
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
- scan proving no persistence/write path in Phase 7D files;
- scan proving no LLM/provider call in Phase 7D files;
- scan proving no raw content capture in Phase 7D files;
- scan proving no API/router/schema migration changes.

---

## 11. Rollback proof

Rollback must be proven by demonstrating:

- dual-read flag disabled disables Phase 7 candidate activity where hooked;
- rich-evidence flag disabled prevents ready candidate output;
- source flag remains inert;
- candidate output is internal-only;
- evaluation outputs are unchanged with candidate creation disabled;
- evaluation outputs are unchanged with candidate creation enabled, if a
  passive hook is introduced;
- no persisted candidate evidence exists;
- no schema rollback is required;
- regression slices pass.

---

## 12. Acceptance criteria

Phase 7D may be accepted only if all of the following are true:

- AEI remains source of truth;
- Phase 7A comparison remains intact;
- Phase 7B rich evidence binding remains intact;
- Phase 7C divergence readiness remains intact;
- internal source-readiness candidate model exists as authorized;
- deterministic candidate service exists as authorized;
- candidate scope is limited to `context_metadata_only`;
- source flag remains inert;
- source switch active remains false;
- no source switch occurred;
- candidate output is internal-only;
- product-impacting and unsafe differences block candidate readiness;
- missing evidence does not silently pass readiness;
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
Commit: feat(eui): add narrow AEI source-readiness candidate foundation
Tag: eui-runtime-phase7d-narrow-aei-source-readiness-certified
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

Phase 7D implementation may begin only within this contract. Any expansion
beyond internal AEI context/evidence metadata source-readiness candidate
preparation requires separate ARM authorization.
