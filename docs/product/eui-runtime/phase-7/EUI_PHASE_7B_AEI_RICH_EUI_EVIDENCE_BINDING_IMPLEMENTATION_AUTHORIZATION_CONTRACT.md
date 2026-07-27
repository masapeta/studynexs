# EUI Runtime Phase 7B Implementation Authorization Contract - AEI Rich EUI Evidence Binding

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7B - AEI Rich EUI Evidence Binding
- **Authorization ID:** EUI-PH7B-AEI-RICH-EVIDENCE-AUTH-001
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md`](./EUI_PHASE_7B_AEI_RICH_EUI_EVIDENCE_BINDING_DESIGN_BRIEF.md)
- **Phase 7 baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Phase 7A baseline:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Consumer migration baseline:** [`../EUI_CONSUMER_MIGRATION_PLAN.md`](../EUI_CONSUMER_MIGRATION_PLAN.md)

---

## 1. Authorization status

This document is the accepted implementation authorization contract for Phase 7B.

ARM has explicitly authorized Phase 7B implementation within this contract only.

The following remain prohibited outside this accepted contract:

- production code changes;
- schema changes;
- API changes;
- UI changes;
- marks changes;
- evaluation behavior changes;
- teacher review routing changes;
- evidence ledger changes;
- Trust Report display;
- EUI source-of-truth switching;
- non-AEI consumer migration.

---

## 2. Purpose

Phase 7B should enrich the already-published Phase 7A AEI passive dual-read
comparison with richer EUI evidence:

- Educational Identity;
- Educational Context;
- Platform Capability Registry lookup;
- Trust Report posture.

The purpose is to make internal divergence evidence more meaningful while
preserving existing AEI/evaluation behavior unchanged.

This is evidence binding only. It is not a source switch.

---

## 3. Authorized implementation scope

If accepted, this contract authorizes only the following work.

### 3.1 Rich evidence feature flag

Add a dedicated default-off flag:

```text
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
```

Existing flags must retain their Phase 7A semantics:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Rules:

- dual-read flag enables passive comparison;
- rich-evidence flag enriches comparison evidence only;
- source flag remains inert;
- disabling rich-evidence falls back to Phase 7A comparison behavior;
- disabling dual-read disables all Phase 7A/7B comparison behavior.

### 3.2 AEI rich evidence binder

Introduce a dedicated evidence binder service responsible for collecting
already-available EUI evidence for AEI passive comparison.

Suggested contract:

```text
AEIConsumerMigrationEvidenceBinder
```

The binder may:

- read available evaluation/question-paper metadata;
- invoke read-only EUI identity/context/capability/trust services where
  already available and appropriate;
- construct safe EUI evidence summaries;
- pass evidence to the existing Phase 7A adapter/observer;
- record missing/ambiguous evidence passively.

The binder may not:

- assign marks;
- alter grading;
- alter AEI policy;
- modify teacher review routing;
- write evidence ledger data;
- persist migration data;
- expose Trust Reports to users;
- call LLMs or external AI providers.

### 3.3 Evidence summary model

Introduce a strict internal summary object only if needed.

Suggested contract:

```text
AEIConsumerMigrationEvidenceBundle
```

If introduced, it must be:

- immutable;
- JSON-serializable;
- non-authoritative;
- free of raw answers, OCR text, uploaded content, teacher free text, student
  names, parent data, tenant slugs, or sensitive educational evidence.

The implementation may alternatively use the existing Phase 7A comparison
summary fields if no new model is needed.

### 3.4 Educational Identity binding

Bind Educational Identity evidence where deterministically available.

Allowed sources:

- existing question paper metadata;
- curriculum pack reference;
- chapter/topic metadata;
- existing Educational Identity resolver;
- deterministic identity IDs already available.

Missing or ambiguous identity must be captured as passive missing/ambiguous
evidence and must not fail evaluation.

### 3.5 Educational Context binding

Bind Educational Context evidence where deterministically available.

Allowed context fields include:

- school/tenant scope;
- board;
- curriculum;
- curriculum version;
- grade;
- subject;
- chapter/topic;
- assessment mode;
- language medium where available.

Conflicts or ambiguity must be represented as passive evidence only.

### 3.6 Platform Capability lookup binding

Bind Platform Capability lookup evidence where relevant.

Allowed capability domains/keys should be derived from existing evaluation
metadata and EUI registry posture.

Capability lookup may not:

- replace the AEI Subject Capability Registry;
- alter AEI policy decisions;
- alter public claims;
- display capability badges;
- change evaluation behavior.

### 3.7 Trust Report binding

Bind Trust Report posture for internal comparison only.

Rules:

- Trust Report visibility must remain `internal_only`;
- non-internal visibility must be classified as unsafe evidence;
- no Trust Report display is authorized;
- no Trust Report schema changes are authorized;
- existing Trust Report contracts should be reused.

### 3.8 Phase 7A adapter/observer integration

Extend the existing Phase 7A path rather than creating a parallel migration
path.

Allowed changes:

- pass richer evidence into the existing Phase 7A adapter/observer;
- extend tests and Golden Harness cases;
- extend certification evidence.

Not allowed:

- replacing Phase 7A comparison contracts;
- removing Phase 7A behavior;
- switching AEI to EUI source of truth.

---

## 4. Authorized repository boundary

If accepted, repository changes are limited to the following areas.

### 4.1 Source modules

Permitted:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/
apps/api/app/modules/eui/services/
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
```

`answer_sheet_eval_service.py` may be touched only to keep a single guarded
passive hook or pass already-available metadata into the evidence binder.

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

Tests may be updated only to prove passive rich evidence binding, source-flag
inertness, and unchanged evaluation behavior.

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
- Trust Report schema changes;
- teacher-facing trust summaries;
- parent/student/principal-facing behavior;
- EUI source-of-truth switching;
- migration of Teacher Copilot, AI Tutor, Question Generator, Lesson Planner,
  Principal Dashboard, Parent Assistant, or School Analytics;
- cleanup/removal of legacy AEI paths;
- LLM calls for migration comparison;
- external AI provider integration;
- product capability claim changes;
- replacement of the AEI Subject Capability Registry.

Any of these require separate ARM authorization.

---

## 6. Runtime constraints

The implementation must be:

- passive;
- default-off;
- rich-evidence-only;
- read-only;
- deterministic where possible;
- comparison-only;
- non-authoritative;
- exception-isolated;
- tenant-safe;
- hidden from users;
- rollbackable by feature flag.

If rich evidence binding fails, existing production evaluation behavior must
continue unchanged.

---

## 7. Graceful degradation requirements

Each evidence class must degrade independently:

| Evidence class | Failure/missing behavior |
|---|---|
| Educational Identity | Record passive missing/ambiguous identity evidence |
| Educational Context | Record passive missing/ambiguous context evidence |
| Capability lookup | Record passive missing/unsupported capability evidence |
| Trust Report | Record passive missing/unsafe trust evidence |

No missing, ambiguous, unsupported, or failed evidence class may fail the
evaluation flow.

---

## 8. Performance and query budget

Phase 7B must include a bounded performance/query posture.

Implementation must demonstrate:

- no unbounded per-question database traversal;
- no N+1 query pattern introduced by rich evidence binding;
- bounded resolver/lookup calls per evaluation;
- measured duration for rich evidence binding;
- exception/timeout handling that preserves evaluation behavior.

Recommended initial budget:

```text
Rich evidence binding should use O(1) resolver/lookup orchestration per
evaluation wherever possible, not O(question_count) database traversal.
```

If implementation needs per-question enrichment, that requires separate ARM
authorization.

---

## 9. Observability

Allowed operational metrics/log signals include:

```text
eui_consumer_migration.rich_evidence.invoked
eui_consumer_migration.rich_evidence.completed
eui_consumer_migration.rich_evidence.failed
eui_consumer_migration.rich_evidence.missing_identity
eui_consumer_migration.rich_evidence.missing_context
eui_consumer_migration.rich_evidence.missing_capability
eui_consumer_migration.rich_evidence.missing_trust
eui_consumer_migration.rich_evidence.duration
```

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

## 10. Golden Harness requirements

Add Golden Harness data and tests for rich EUI evidence binding.

The harness should cover:

- identity present;
- identity missing;
- context resolved;
- context ambiguous;
- capability supported;
- capability manual-review/assist;
- Trust Report trusted;
- Trust Report manual-review-required;
- Trust Report visibility unsafe;
- product-impacting difference remains blocked;
- source switch remains inactive.

---

## 11. Validation requirements

Before ARM acceptance, implementation must provide evidence for:

### 11.1 Focused validation

- evidence binder tests;
- optional evidence bundle model tests;
- feature flag default-off tests;
- rich-evidence disabled fallback tests;
- rich-evidence enabled tests;
- source flag inertness tests;
- missing/ambiguous evidence tests;
- Trust Report internal-only tests;
- exception isolation tests;
- Golden Harness tests;
- output equality tests.

### 11.2 Regression validation

Required regression slices:

- Phase 7A comparison tests;
- AEI passive integration tests;
- AEI/evaluation regression slice;
- EUI Trust Framework tests;
- EUI Golden Harness tests;
- API import.

### 11.3 Static validation

- focused Ruff for touched API files;
- `git diff --check`;
- scan proving no Trust Report display or UI exposure;
- scan proving no persistence/write path in Phase 7B files;
- scan proving no LLM/provider call in Phase 7B files;
- scan proving no API/router/schema migration changes.

---

## 12. Rollback proof

Rollback must be proven by demonstrating:

- rich-evidence flag disabled falls back to Phase 7A behavior;
- dual-read flag disabled disables all comparison behavior;
- source flag does not affect runtime behavior;
- evaluation outputs are unchanged with rich evidence disabled;
- evaluation outputs are unchanged with rich evidence enabled;
- no persisted rich evidence exists;
- no schema rollback is required;
- regression slices pass.

---

## 13. Acceptance criteria

Phase 7B may be accepted only if all of the following are true:

- AEI remains source of truth;
- Phase 7A comparison remains intact;
- rich EUI evidence binding exists as authorized;
- rich-evidence flag defaults OFF;
- source flag remains inert;
- production evaluation output is unchanged with rich evidence disabled;
- production evaluation output is unchanged with rich evidence enabled;
- missing/ambiguous evidence is passive only;
- Trust Report visibility remains internal-only;
- no Trust Report schema changes;
- no marks, scoring, grading, policy, teacher review, or evidence-ledger
  changes;
- no API/UI/schema changes;
- no EUI source-of-truth switch;
- no non-AEI consumer migration;
- performance/query budget is certified;
- regression slices pass;
- rollback proof is documented;
- certification report and retrospective are complete.

---

## 14. Commit, tag, and publication expectation

If implementation is later accepted, recommended metadata:

```text
Commit: feat(eui): add AEI rich evidence binding foundation
Tag: eui-runtime-phase7b-aei-rich-evidence-binding-certified
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

## 15. ARM decision gate

This contract has been accepted by ARM for implementation.

Phase 7B implementation is authorized only within this contract. Any expansion
beyond AEI passive rich evidence binding requires separate ARM authorization.
