# EUI Runtime Phase 7A Implementation Authorization Contract - AEI Consumer Migration

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7A - AEI Consumer Migration
- **Authorization ID:** EUI-PH7A-AEI-DUAL-READ-AUTH-001
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)
- **ARM review:** Accepted with source-flag inertness, AEI-source-of-truth, and no-behavior-change boundaries confirmed

---

## 1. Authorization status

This document is the accepted implementation authorization contract for Phase
7A.

Implementation is authorized only within the scope and repository boundary
defined here.

The following remain prohibited:

- marks changes;
- grading changes;
- evaluation policy changes;
- teacher review routing changes;
- evidence ledger changes;
- database schema changes;
- API changes;
- UI changes;
- Trust Report display;
- EUI source-of-truth switching;
- cleanup of legacy AEI paths.

---

## 2. Purpose

Phase 7A should introduce AEI consumer migration in the safest possible form:

> Run EUI-derived context/trust evidence beside the existing AEI/evaluation path
> and compare it internally without changing production evaluation behavior.

This is passive dual-read only.

The existing AEI/evaluation result remains the only source of truth.

---

## 3. Authorized implementation scope

If accepted, this contract authorizes only the following work.

### 3.1 AEI migration comparison model

Introduce strict, immutable runtime/domain models for internal comparison
evidence.

Suggested contracts:

- `AEIConsumerMigrationComparison`;
- `AEIConsumerMigrationDifference`;
- `AEIConsumerMigrationCapture`.

The models should be JSON-serializable and must not include raw student answers,
raw OCR text, uploaded document text, teacher free text, parent data, student
names, or tenant slugs.

### 3.2 AEI compatibility adapter

Introduce a narrow compatibility adapter that maps existing AEI/evaluation
inputs and available EUI outputs into an internal comparison shape.

The adapter may read:

- existing AEI/evaluation metadata already available on the execution path;
- Educational Context, where available;
- Platform Capability lookup result, where available;
- Trust Report, where available;
- deterministic EUI metadata already produced by earlier phases.

The adapter may not:

- modify `AcademicAnswer`;
- modify `AcademicReasoningResult`;
- modify `PolicyDecision`;
- modify `TeacherReviewDecision`;
- assign marks;
- alter evaluation policy;
- write to the evidence ledger;
- persist migration output.

### 3.3 Passive dual-read observer

Introduce a passive observer that can run AEI consumer migration comparison
behind a default-off feature flag.

The observer may:

- execute comparison logic;
- classify differences;
- record operational metrics;
- capture bounded in-memory evidence for certification;
- isolate exceptions.

The observer may not:

- change production evaluation results;
- change teacher review routing;
- change evidence ledger output;
- expose output to users;
- make EUI authoritative;
- remove or replace existing AEI passive integration.

### 3.4 Difference classification

Implement deterministic difference classification using the accepted Phase 7
design categories:

- `equivalent`;
- `eui_richer`;
- `eui_missing`;
- `legacy_ambiguous`;
- `product_impacting`;
- `unsafe`.

Product-impacting and unsafe differences must be blockers for any future switch.

Phase 7A does not authorize switching, even when no blockers are present.

### 3.5 Feature flags

Implement or wire the Phase 7A flags:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Requirements:

- both disabled by default;
- dual-read flag enables passive comparison only;
- source flag may exist only as inert configuration and must not influence
  runtime behavior in Phase 7A;
- rollback by disabling the dual-read flag;
- no product-visible behavior change.

### 3.6 Observability

Implement operational observability consistent with the Phase 0 baseline and
Phase 7 design brief.

Allowed metrics/log signals include:

```text
eui_consumer_migration.invoked
eui_consumer_migration.completed
eui_consumer_migration.failed
eui_consumer_migration.diverged
eui_consumer_migration.unsafe_difference
eui_consumer_migration.duration
```

Metrics and logs must avoid PII, raw student answers, raw OCR text, uploaded
content, teacher free text, parent data, student names, tenant slugs, and
sensitive educational evidence.

### 3.7 Golden Harness

Add Golden Harness data and tests for AEI passive dual-read comparison.

The harness should cover:

- equivalent comparison;
- EUI-richer comparison;
- EUI-missing comparison;
- legacy-ambiguous comparison;
- product-impacting classification;
- unsafe classification;
- Trust Report internal-only visibility;
- deterministic comparison IDs, if IDs are introduced.

### 3.8 Certification

Produce a Phase 7A certification report demonstrating:

- AEI remains source of truth;
- production evaluation outputs are unchanged with dual-read disabled;
- production evaluation outputs are unchanged with dual-read enabled;
- differences are captured and classified internally;
- no marks, policy, teacher review, evidence ledger, UI, API, or schema changes;
- no Trust Report display;
- rollback proof;
- observability evidence;
- phase retrospective.

---

## 4. Authorized repository boundary

If accepted, repository changes are limited to the following areas.

### 4.1 Source modules

Permitted:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/
apps/api/app/modules/eui/services/
apps/api/app/modules/evaluations/
```

`apps/api/app/modules/evaluations/` may be touched only for a single guarded,
default-off passive observer hook or testable adapter integration point.

Not permitted:

```text
apps/api/app/modules/knowledge_graph/
apps/api/app/modules/ai/
apps/api/app/modules/exams/
apps/admin-web/
```

Any change outside the permitted source boundary requires separate ARM
authorization.

### 4.2 Tests and Golden Harness

Permitted:

```text
apps/api/tests/golden/eui_v1/
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/test_eui_consumer_*.py
apps/api/tests/test_aei_passive_integration.py
apps/api/tests/test_evaluation_engine.py
apps/api/tests/test_answer_sheet_eval.py
```

Existing AEI/evaluation tests may be updated only to assert unchanged behavior
with Phase 7A dual-read disabled/enabled. They may not be changed to accept new
marks, routing, policy, or evidence-ledger behavior.

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
- teacher-facing trust summaries;
- parent/student/principal-facing behavior;
- EUI source-of-truth switching;
- migration of Teacher Copilot, AI Tutor, Question Generator, Lesson Planner,
  Principal Dashboard, Parent Assistant, or School Analytics;
- cleanup/removal of legacy AEI paths;
- LLM calls for migration comparison;
- external AI provider integration;
- product capability claim changes.

Any of these require separate ARM authorization.

---

## 6. Runtime constraints

The implementation must be:

- passive;
- default-off;
- dual-read only;
- deterministic where possible;
- comparison-only;
- non-authoritative;
- exception-isolated;
- tenant-safe;
- hidden from users;
- rollbackable by feature flag.

If the Phase 7A path fails, existing production evaluation behavior must
continue unchanged.

---

## 7. Rollback proof

Rollback must be proven by demonstrating:

- dual-read feature flag disabled path is a no-op;
- existing evaluation outputs remain unchanged with dual-read disabled;
- existing evaluation outputs remain unchanged with dual-read enabled;
- source flag does not affect runtime behavior in Phase 7A;
- no persisted comparison data exists;
- no schema rollback is required;
- AEI/evaluation regression slice passes.

---

## 8. Validation requirements

Before ARM acceptance, the implementation must provide evidence for:

### 8.1 Focused validation

- comparison model tests;
- difference classification tests;
- compatibility adapter tests;
- passive observer disabled tests;
- passive observer enabled tests;
- exception isolation tests;
- source flag inertness tests;
- Golden Harness migration comparison tests.

### 8.2 Regression validation

Required regression slices:

- AEI architecture guard tests;
- AEI passive integration tests;
- evaluation policy tests;
- Golden Evaluation Harness;
- evaluation engine tests;
- answer-sheet evaluation tests;
- EUI Trust Framework tests;
- EUI Golden Harness tests;
- API import.

### 8.3 Static validation

- focused Ruff for touched API files;
- `git diff --check`;
- scan proving no Trust Report display or UI exposure was introduced;
- scan proving no persistence/write path was introduced in Phase 7A migration
  files;
- scan proving no LLM/provider call was introduced in Phase 7A migration files.

---

## 9. Acceptance criteria

Phase 7A implementation may be accepted only if all of the following are true:

- AEI remains source of truth;
- dual-read comparison exists as authorized;
- dual-read flag defaults OFF;
- source flag defaults OFF and remains behaviorally inert;
- production evaluation outputs are unchanged with dual-read disabled;
- production evaluation outputs are unchanged with dual-read enabled;
- differences are classified internally;
- product-impacting and unsafe differences are blockers for future switch;
- no marks, scoring, grading, policy, teacher review, or evidence-ledger changes;
- no API/UI/schema changes;
- no Trust Report display;
- no EUI source-of-truth switch;
- no consumer other than AEI is migrated;
- regression slices pass;
- rollback proof is documented;
- certification report is complete;
- phase retrospective is complete.

---

## 10. Commit, tag, and publication expectation

If implementation is later accepted, recommended metadata:

```text
Commit: feat(eui): add AEI consumer dual-read migration foundation
Tag: eui-runtime-phase7a-aei-consumer-dual-read-certified
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

## 11. ARM decision gate

This contract has been accepted by ARM.

Phase 7A implementation is authorized only within this contract. Any expansion
beyond AEI passive dual-read comparison requires separate ARM authorization.
