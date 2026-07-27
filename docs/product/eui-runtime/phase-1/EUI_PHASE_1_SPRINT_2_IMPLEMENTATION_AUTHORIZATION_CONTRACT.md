# EUI Phase 1 Sprint 2 Implementation Authorization Contract — Educational Context

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 1 - Educational Identity and Context
- **Sprint:** Sprint 2 - Educational Context
- **Classification:** Implementation Authorization Contract
- **Status:** Accepted
- **Implementation authorization:** Authorized
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_1_SPRINT_2_EDUCATIONAL_CONTEXT_DESIGN_BRIEF.md`](./EUI_PHASE_1_SPRINT_2_EDUCATIONAL_CONTEXT_DESIGN_BRIEF.md)
- **Prior runtime baseline:** Phase 1 Sprint 1 - Educational Identity passive runtime foundation
- **Authorization ID:** `EUI-PH1-SP2-AUTH-001`
- **ARM review:** Accepted; implementation authorized within this contract boundary

---

## 1. Authorization boundary

This contract authorizes Sprint 2 implementation only within the boundaries
defined below.

This authorization does not permit:

- no schema, API, UI, runtime behavior, consumer migration, or AEI behavior may
  change;
- no work outside the repository boundary may be performed without additional
  ARM approval.

---

## 2. Purpose

Sprint 2 exists to implement a passive Educational Context runtime foundation.

Educational Identity answers:

> What educational object is this?

Educational Context answers:

> In what educational situation is this object being used?

The purpose of Sprint 2 is to introduce a canonical, deterministic, passive
Educational Context capability that can resolve the surrounding context for
supported educational artifacts without changing existing product behavior.

The runtime objective is:

```text
Existing runtime input
        |
        v
Educational Identity reference, where available
        |
        v
Educational Context Resolver
        |
        v
Canonical EducationalContext
        |
        v
Metrics / logs / Golden Harness
        |
        v
Captured for verification only
        |
        v
No consumer uses the result
```

---

## 3. Implementation scope

If authorized, Sprint 2 implementation is limited to the following work.

### 3.1 Canonical Educational Context domain model

Implement a runtime/domain model representing passive educational context.

The model may include fields for:

- tenant scope;
- academic year or term, where available;
- board, curriculum, curriculum version, grade, section, and subject;
- CurriculumPack and Educational Identity references;
- chapter, topic, concepts, competencies, and learning objectives;
- assessment mode;
- language medium;
- evidence or review posture;
- resolution status;
- conflict and ambiguity metadata;
- provenance;
- non-sensitive metadata.

The model must be immutable, JSON-serializable, and strict about unknown
top-level fields.

### 3.2 Educational Context resolver

Implement a deterministic resolver that accepts existing runtime references and
produces a canonical `EducationalContext` object or a structured unresolved /
ambiguous result.

The resolver may read existing repository data needed for passive resolution.

The resolver must not:

- write to the database;
- call an LLM;
- grade, score, recommend, or route;
- modify CurriculumPack, Knowledge Graph, assessment, lesson, homework, or
  evaluation workflows;
- become a source of truth for any consumer.

### 3.3 Read-only context source adapters

Implement read-only adapters only where needed to resolve context from existing
data.

Permitted source categories:

- Educational Identity;
- CurriculumPack metadata;
- existing Knowledge Graph references;
- existing artifact metadata;
- trusted server-side tenant/session context where already available.

Adapters must preserve tenant isolation and must not trust client-supplied
school identifiers.

### 3.4 Context resolution precedence

Implement the precedence model accepted in the design brief:

1. tenant and authenticated runtime scope derived from trusted server-side
   session context;
2. explicit artifact references, such as CurriculumPack ID, EducationalIdentity
   ID, assessment ID, lesson plan ID, question paper ID, or homework ID;
3. approved CurriculumPack metadata and existing Knowledge Graph references;
4. existing runtime metadata attached to the artifact;
5. derived or inferred labels from non-authoritative text fields.

Lower-precedence sources must not silently override higher-precedence sources.
Conflicts must be recorded as passive evidence without changing product
behavior.

### 3.5 Ambiguity behavior

Implement ambiguity handling as non-authoritative passive evidence.

When context cannot resolve to one deterministic context, the implementation
must:

- return an unresolved or partial context result where safe;
- include non-sensitive candidate references where appropriate;
- record ambiguity reasons;
- record source fields that caused ambiguity;
- emit operational metrics and structured logs;
- preserve legacy behavior;
- avoid exposing the ambiguous context to any consumer.

### 3.6 In-process cache

An in-process cache is authorized if needed for resolver efficiency.

Constraints:

- process-local only;
- no distributed cache;
- no persistence;
- no background warming jobs;
- cache behavior must be testable and observable.

### 3.7 Passive observer

Implement a passive observer that can execute context resolution behind a
feature flag and capture results for validation only.

The observer must:

- be no-op when disabled;
- isolate exceptions;
- preserve legacy product behavior when enabled;
- avoid writing product state;
- avoid exposing output to consumers.

### 3.8 Feature flag

Add one settings-based feature flag:

```text
EUI_CONTEXT_PASSIVE_ENABLED: bool = False
```

Default state must be `False`.

Rollback is achieved by disabling or leaving disabled this flag.

### 3.9 Observability

Add operational metrics and structured logs for passive context resolution.

Metrics should use low-cardinality status labels only.

Expected task name:

```text
eui_context_resolver
```

Expected statuses include:

- `invoked`;
- `completed`;
- `failed`;
- `ambiguous`;
- `not_found`;
- `conflict`;
- `cache_hit`;
- `cache_miss`.

Metrics and logs must not expose student names, parent data, tenant slugs,
free-text answers, uploaded content, or other sensitive educational content.

### 3.10 Golden Harness

Add Golden Harness cases for deterministic Educational Context resolution.

Expected dataset:

```text
apps/api/tests/golden/eui_v1/educational_context_cases.json
```

Coverage should include:

- CBSE context;
- ICSE context;
- State Board Telugu-medium context;
- same Educational Identity used in different assessment modes;
- same chapter label across different boards or subjects;
- missing optional context;
- ambiguous grade or section references;
- language medium differences;
- precedence conflict cases;
- passive resolution without consumer migration.

### 3.11 Certification

Produce a Sprint 2 certification report:

```text
docs/product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_2_EDUCATIONAL_CONTEXT_CERTIFICATION_REPORT.md
```

The report must include certification evidence, validation commands, behavior
identity evidence, rollback proof, risk register, conditions, recommendation,
and phase retrospective.

---

## 4. Repository boundary

If authorized, changes are limited to the following repository areas.

### 4.1 Permitted source files

Allowed:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/__init__.py
apps/api/app/modules/eui/schemas/educational_context.py
apps/api/app/modules/eui/services/__init__.py
apps/api/app/modules/eui/services/educational_context_cache.py
apps/api/app/modules/eui/services/educational_context_passive.py
apps/api/app/modules/eui/services/educational_context_resolver.py
apps/api/app/modules/eui/services/educational_context_sources.py
```

Notes:

- `educational_context_cache.py` is optional and should be added only if useful.
- `educational_context_sources.py` is optional and should be added only if the
  resolver needs adapter separation.
- Existing Educational Identity modules may be imported, but their behavior
  must not be changed without explicit ARM approval.

### 4.2 Permitted test and Golden Harness files

Allowed:

```text
apps/api/tests/golden/eui_v1/educational_context_cases.json
apps/api/tests/test_educational_context_model.py
apps/api/tests/test_educational_context_resolver.py
apps/api/tests/test_educational_context_passive.py
apps/api/tests/test_eui_golden_harness.py
```

`test_eui_golden_harness.py` may be updated to load Educational Context cases
alongside Educational Identity cases.

### 4.3 Permitted documentation files

Allowed:

```text
docs/product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_2_EDUCATIONAL_CONTEXT_CERTIFICATION_REPORT.md
docs/product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_2_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

After implementation is certified, ARM may separately authorize a Master Status
update before publication.

### 4.4 Protected areas

Sprint 2 does not authorize changes to:

```text
apps/api/alembic/
apps/api/app/api/
apps/api/app/db/
apps/api/app/modules/aei/
apps/api/app/modules/assessment*/
apps/api/app/modules/evaluation*/
apps/api/app/modules/tutor*/
apps/api/app/modules/curriculum*/
apps/admin-web/
infra/
sites/
```

Any change outside the permitted boundary requires explicit ARM approval before
implementation.

---

## 5. Permitted artifacts

Permitted artifacts:

- EUI runtime/domain model code;
- read-only resolver and adapters;
- in-process cache if justified;
- passive observer code;
- one settings flag;
- operational metrics/logging;
- focused tests;
- Golden Harness data;
- certification report;
- phase retrospective inside the certification report.

Not permitted:

- migrations;
- database tables;
- API schemas used by existing consumers;
- routers;
- UI components;
- background workers;
- product analytics dashboards;
- model/provider integrations;
- prompt files;
- consumer migrations;
- AEI contract changes.

---

## 6. Runtime constraints

Sprint 2 implementation must be:

- passive;
- read-only;
- deterministic for supported deterministic inputs;
- exception-isolated;
- tenant-safe;
- invisible to users;
- non-authoritative for every consumer.

If context resolution fails, legacy behavior must continue unchanged.

When disabled, the passive observer must return without executing context
resolution or recording captures.

When enabled, passive execution must not change production output.

---

## 7. Explicit exclusions

The following remain out of scope:

- database schema changes;
- persistent context storage;
- database migrations;
- API contract changes;
- public endpoint changes;
- UI changes;
- consumer migration;
- AEI runtime behavior changes;
- EUI consumer behavior changes;
- grading, scoring, or evaluation logic;
- Trust Framework implementation;
- Platform Capability Registry implementation;
- Knowledge Acquisition Intelligence;
- Educational Knowledge Graph expansion;
- Institutional Memory runtime behavior;
- LLM inference;
- prompt changes;
- approval workflow changes;
- CurriculumPack publishing changes;
- distributed cache infrastructure;
- background workers;
- product capability claim expansion.

---

## 8. Validation requirements

Before ARM acceptance, implementation evidence must include the following.

### 8.1 Focused lint

Expected command:

```text
cd apps/api
ruff check app/modules/eui tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_eui_golden_harness.py
```

### 8.2 Focused Sprint 2 tests

Expected command:

```text
cd apps/api
python -m pytest tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_eui_golden_harness.py
```

### 8.3 Sprint 1 regression

Expected command:

```text
cd apps/api
python -m pytest tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_eui_golden_harness.py
```

### 8.4 AEI / evaluation / KG regression slice

Expected command:

```text
cd apps/api
python -m pytest tests/test_aei_architecture.py tests/test_aei_passive_integration.py tests/test_evaluation_policy.py tests/test_golden_evaluation_harness.py tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py tests/test_knowledge_graph.py tests/test_graph_queries.py tests/test_question_concept_links.py
```

### 8.5 API import

Expected command:

```text
cd apps/api
python -c "import app.main; print('api import ok')"
```

### 8.6 Whitespace check

Expected command:

```text
git diff --check
```

If broader repository lint remains blocked by pre-existing unrelated lint debt,
the certification report must document that explicitly and show that the Sprint
2 files and affected regression neighborhood are clean.

---

## 9. Rollback proof

Certification must prove:

- `EUI_CONTEXT_PASSIVE_ENABLED` defaults to `False`;
- disabled state executes no context resolution;
- disabled state records no passive capture;
- enabled state does not change product output;
- exceptions are isolated;
- no schema, persistence, API, UI, or consumer migration exists to roll back.

Rollback mechanism:

```text
Set EUI_CONTEXT_PASSIVE_ENABLED=false
```

Because Sprint 2 must not introduce persistence, rollback must not require data
repair.

---

## 10. Certification deliverables

Certification must include:

- scope certified;
- contracts evidence;
- runtime behavior evidence;
- feature flag evidence;
- observability evidence;
- rollback evidence;
- AEI impact evidence;
- schema/API/UI unchanged evidence;
- test commands and results;
- behavior identity evidence;
- risks and mitigations;
- conditions, if any;
- phase retrospective;
- ARM recommendation.

Certification status may be:

- `PASS`;
- `PASS WITH CONDITIONS`;
- `FAIL`.

Commit authorization should not occur until ARM reviews the implementation
evidence and accepts the sprint.

---

## 11. Exit criteria

Sprint 2 implementation may be considered complete only when all of the
following are true:

- canonical Educational Context model exists as authorized;
- deterministic context resolver exists as authorized;
- context precedence is implemented and tested;
- ambiguity handling is implemented and tested;
- read-only source adapters are used where needed;
- feature flag defaults off;
- passive observer is no-op when disabled;
- enabled passive mode does not change product behavior;
- no consumer depends on Educational Context;
- no schema/API/UI changes are introduced;
- no AEI behavior changes;
- Golden Harness context cases pass;
- observability records invocation, completion, failure, ambiguity, conflict,
  cache behavior if applicable, and duration;
- rollback by disabling the flag is verified;
- focused tests and regression slices pass;
- certification report is complete;
- phase retrospective is complete;
- ARM accepts the implementation before commit.

---

## 12. Commit, tag, and publication guidance

If implementation is later authorized, completed, certified, and accepted, the
recommended commit message is:

```text
feat(eui): add educational context passive runtime foundation
```

Recommended annotated tag:

```text
eui-runtime-phase1-sprint2-educational-context-certified
```

Publication requires separate ARM approval after certification and commit.

---

## 13. ARM implementation review gate

After implementation, ARM may choose one of:

1. accept the implementation and authorize commit;
2. accept with conditions;
3. request implementation revisions;
4. reject the implementation as outside scope or insufficiently certified.

Until ARM accepts the implementation evidence, no Sprint 2 commit may be
created.
