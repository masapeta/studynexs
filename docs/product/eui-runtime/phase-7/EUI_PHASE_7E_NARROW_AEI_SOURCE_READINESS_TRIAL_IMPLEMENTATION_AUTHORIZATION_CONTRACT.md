# EUI Runtime Phase 7E Implementation Authorization Contract - Narrow AEI Source-Readiness Trial

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7E - Narrow AEI Source-Readiness Trial
- **Authorization ID:** EUI-PH7E-NARROW-AEI-SOURCE-READINESS-TRIAL-AUTH-001
- **Roadmap mapping:** Phase 7 - Consumer Migration
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-28
- **Design baseline:** [`EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_DESIGN_BRIEF.md`](./EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_DESIGN_BRIEF.md)
- **Phase 7 baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Phase 7A baseline:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7B baseline:** [`EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7C baseline:** [`EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Phase 7D baseline:** [`EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)

---

## 1. Authorization status

This document is the accepted implementation authorization contract for Phase
7E.

ARM has explicitly authorized Phase 7E implementation within this contract
only.

The following remain prohibited unless explicitly authorized in a later
contract:

- EUI source-of-truth switching;
- marks, grading, scoring, policy, or teacher review routing changes;
- evidence ledger changes or writes;
- schema changes;
- API changes;
- UI changes;
- Trust Report display;
- non-AEI consumer migration;
- product capability claim changes;
- cleanup or removal of legacy AEI paths.

---

## 2. Purpose

Phase 7D introduced a non-authoritative source-readiness candidate for the
narrow `context_metadata_only` AEI scope.

Phase 7E should introduce an internal trial result foundation that proves a
ready Phase 7D candidate can be exercised as internal metadata evidence without
making EUI authoritative for AEI.

The production rule remains:

```text
Existing AEI/evaluation behavior remains source of truth.
```

Phase 7E is a trial foundation only. It is not a source switch, adoption phase,
or behavior change.

---

## 3. Authorized implementation scope

This contract authorizes only the following work.

### 3.1 Internal AEI source-readiness trial result model

Introduce an internal model representing a narrow AEI source-readiness trial
result.

Suggested contract:

```text
AEISourceReadinessTrialResult
```

The model should represent:

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

### 3.2 Deterministic source-readiness trial service

Introduce a deterministic service that consumes Phase 7D candidates and
produces internal trial results.

Suggested contract:

```text
AEISourceReadinessTrialService
```

The service may:

- consume Phase 7D source-readiness candidates;
- classify narrow trial state;
- select bounded internal evidence-class labels;
- verify that the candidate scope is explicitly narrow;
- verify that the source switch remains inactive;
- verify that legacy AEI/evaluation remains source of truth;
- record passive operational metrics/logs.

The service may not:

- call LLMs or external AI providers;
- inspect raw student answers or uploaded content;
- assign marks;
- change grading;
- change AEI policy;
- change teacher review routing;
- write evidence ledger data;
- persist trial decisions;
- switch AEI to EUI as source of truth;
- expose trial output to users.

### 3.3 Trial state taxonomy

Implement a strict trial state taxonomy aligned with the Phase 7E design brief.

Expected values:

```text
trial_ready
trial_not_ready
trial_blocked_product_impacting
trial_blocked_unsafe
trial_skipped
```

Rules:

- `trial_blocked_unsafe` must dominate all other states;
- `trial_blocked_product_impacting` must block trial readiness;
- not-ready candidates must produce `trial_not_ready`;
- missing candidate input may produce `trial_skipped` or `trial_not_ready`;
- `trial_ready` may be returned only when the Phase 7D candidate is
  `ready_for_internal_trial` and all Phase 7E blockers pass.

No state may change AEI behavior.

### 3.4 Trial ID generation

Implement deterministic trial IDs for the internal trial result model.

IDs must be stable for the same:

- consumer;
- tenant ID;
- subject type;
- scope reference;
- candidate reference;
- candidate scope;
- trial mode.

IDs must not include:

- student identifiers;
- parent identifiers;
- tenant slugs;
- raw answer text;
- raw OCR text;
- uploaded content;
- free-text educational material.

### 3.5 Source flag inertness

Phase 7E must preserve the existing Phase 7 flag posture:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- dual-read remains passive;
- rich evidence remains internal;
- source flag remains inert;
- trial result creation must not activate source behavior;
- source switch active must remain false in all Phase 7E outputs;
- disabled trial posture must produce `trial_skipped` if a trial-specific flag
  is introduced.

If a new trial-specific flag is introduced, it must:

- default to `false`;
- be passive/internal only;
- never activate source behavior;
- be documented in certification evidence.

### 3.6 Passive/internal hook

A passive/internal hook may be added only if needed to connect Phase 7E trial
logic to existing Phase 7D internal candidate evidence.

Rules:

- hook must be guarded by existing Phase 7 consumer-migration flags and any
  trial-specific flag if introduced;
- hook output must be internal-only;
- hook failure must be exception-isolated;
- hook must not affect production evaluation output;
- hook must not make AEI depend on the trial result as source of truth.

No source-readiness adoption behavior is authorized.

### 3.7 Golden Harness trial cases

Add Golden Harness data and tests for narrow AEI source-readiness trial results.

The harness should cover:

- ready Phase 7D candidate produces `trial_ready`;
- not-ready candidate produces `trial_not_ready`;
- product-impacting candidate produces `trial_blocked_product_impacting`;
- unsafe candidate produces `trial_blocked_unsafe`;
- missing candidate produces `trial_skipped` or `trial_not_ready`;
- candidate scope broader than `context_metadata_only` is blocked;
- source flag active/source switch attempt is blocked or remains inert;
- trial ID determinism;
- no raw content capture;
- source flag inertness.

### 3.8 Certification report

Produce Phase 7E certification evidence.

Required report:

```text
docs/product/eui-runtime/phase-7/
EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_CERTIFICATION_REPORT.md
```

The report must include:

- authorization scope review;
- changed-file inventory;
- trial result model validation;
- deterministic trial service validation;
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
passive hook or pass already-available Phase 7D candidate evidence into the
trial service.

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

Tests may be updated only to prove deterministic trial result creation,
passive operation, source-flag inertness, no raw-content capture, and unchanged
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
- LLM calls for trial execution;
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
- trial-only;
- non-authoritative;
- internal-only;
- exception-isolated;
- tenant-safe;
- hidden from users;
- rollbackable by feature flag if a hook/flag is introduced.

If trial result creation fails, existing production evaluation behavior must
continue unchanged.

---

## 7. Blocker rules

Phase 7E must fail closed for trial readiness.

| Evidence condition | Required trial state |
|---|---|
| Missing candidate | `trial_skipped` or `trial_not_ready` |
| Candidate state is `blocked_unsafe` | `trial_blocked_unsafe` |
| Candidate state is `blocked_product_impacting` | `trial_blocked_product_impacting` |
| Candidate state is `not_ready_more_evidence` | `trial_not_ready` |
| Candidate state is `not_ready_capability_work` | `trial_not_ready` |
| Candidate scope broader than `context_metadata_only` | `trial_blocked_product_impacting` |
| Source switch active or attempted | `trial_blocked_unsafe` |
| Legacy source-of-truth confirmation missing | `trial_blocked_unsafe` |
| Ready candidate with all blockers passing | `trial_ready` |

No missing or ambiguous signal may be treated as trial-ready by default.

---

## 8. Performance and query budget

Phase 7E must include a bounded performance posture.

Implementation must demonstrate:

- no unbounded per-question database traversal;
- no N+1 query pattern introduced by trial result creation;
- bounded trial orchestration per candidate;
- measured duration for trial result creation where hooked passively;
- exception/timeout handling that preserves evaluation behavior.

Recommended initial budget:

```text
Trial result creation should be O(1) over an already-produced Phase 7D
candidate wherever possible.
```

Any implementation requiring raw per-answer, per-upload, or per-artifact
traversal requires separate ARM authorization.

---

## 9. Observability

Allowed operational metrics/log signals include:

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

- trial result model tests;
- trial state taxonomy tests;
- deterministic trial service tests;
- blocker precedence tests;
- candidate scope strictness tests;
- source flag inertness tests;
- source switch active false tests;
- legacy source-of-truth confirmation tests;
- no raw-content capture tests;
- passive hook disabled behavior tests, if a hook is introduced;
- exception isolation tests, if a hook is introduced;
- Golden Harness trial tests.

### 10.2 Regression validation

Required regression slices:

- Phase 7A comparison tests;
- Phase 7B rich evidence binding tests;
- Phase 7C divergence readiness tests;
- Phase 7D source-readiness candidate tests;
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
- scan proving no persistence/write path in Phase 7E files;
- scan proving no LLM/provider call in Phase 7E files;
- scan proving no raw content capture in Phase 7E files;
- scan proving no API/router/schema migration changes.

---

## 11. Rollback proof

Rollback must be proven by demonstrating:

- trial-specific flag disabled produces `trial_skipped`, if such a flag is
  introduced;
- dual-read/rich-evidence/source flags remain passive/inert;
- trial output is internal-only;
- evaluation outputs are unchanged with trial result creation disabled;
- evaluation outputs are unchanged with trial result creation enabled, if a
  passive hook is introduced;
- no persisted trial evidence exists;
- no schema rollback is required;
- regression slices pass.

---

## 12. Acceptance criteria

Phase 7E may be accepted only if all of the following are true:

- AEI remains source of truth;
- Phase 7A comparison remains intact;
- Phase 7B rich evidence binding remains intact;
- Phase 7C divergence readiness remains intact;
- Phase 7D source-readiness candidate foundation remains intact;
- internal source-readiness trial result model exists as authorized;
- deterministic trial service exists as authorized;
- trial scope is limited to `context_metadata_only`;
- source flag remains inert;
- source switch active remains false;
- no source switch occurred;
- trial output is internal-only;
- product-impacting and unsafe candidates block trial readiness;
- missing or not-ready candidates do not silently pass trial readiness;
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
Commit: feat(eui): add narrow AEI source-readiness trial foundation
Tag: eui-runtime-phase7e-narrow-aei-source-readiness-trial-certified
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

Phase 7E implementation may begin only within this contract. Any expansion
beyond internal AEI context/evidence metadata source-readiness trial
preparation requires separate ARM authorization.
