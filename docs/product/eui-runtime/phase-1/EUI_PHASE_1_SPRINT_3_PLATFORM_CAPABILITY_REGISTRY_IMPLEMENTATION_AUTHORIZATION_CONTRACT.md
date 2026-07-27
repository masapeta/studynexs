# EUI Phase 1 Sprint 3 Implementation Authorization Contract — Platform Capability Registry

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 1 - Educational Identity, Context, and Capability Foundations
- **Sprint:** Sprint 3 - Platform Capability Registry
- **Classification:** Implementation Authorization Contract
- **Status:** Accepted
- **Implementation authorization:** Authorized
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_DESIGN_BRIEF.md`](./EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_DESIGN_BRIEF.md)
- **Prior runtime baseline:** Phase 1 Sprint 2 - Educational Context passive runtime foundation
- **Authorization ID:** `EUI-PH1-SP3-AUTH-001`

---

## 1. Authorization boundary

ARM has accepted this contract and authorized Sprint 3 implementation within
the scope, repository boundary, runtime constraints, validation requirements,
and explicit exclusions defined below.

This authorization permits:

- passive Platform Capability Registry implementation;
- focused validation and certification evidence;
- no product-visible behavior change.

It does not permit:

- schema, API, UI, runtime behavior, consumer migration, or AEI behavior
  changes;
- any work outside the repository boundary without separate ARM approval.

---

## 2. Purpose

Sprint 3 exists to implement a passive Platform Capability Registry foundation.

The registry answers:

> What can StudyNexs honestly claim it supports, for which educational scope, and in which mode?

The purpose of Sprint 3 is to establish a declarative, read-only registry that
can represent platform-wide capability posture without changing product
behavior or replacing the AEI Subject Capability Registry.

The runtime objective is:

```text
Educational Context
        |
        v
Platform Capability Registry lookup
        |
        v
CapabilityDeclaration
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

If authorized, Sprint 3 implementation is limited to the following work.

### 3.1 Capability registry data

Add a declarative platform capability registry dataset.

The dataset must be static, versioned, and read-only at runtime.

Expected location:

```text
apps/api/app/modules/eui/registry/platform_capability_registry.v1.json
```

The registry may include representative capability entries for:

- mathematics normalization;
- units;
- graph or diagram checklist posture;
- Hindi printed OCR;
- Hindi/Telugu/Sanskrit handwriting OCR assist/manual-review posture;
- biology diagram checklist posture;
- explicitly unsupported pixel-perfect diagram grading;
- AEI-compatible evaluation capability entries.

Registry entries must not expand public product claims.

### 3.2 Capability registry contracts

Implement strict runtime/domain contracts for capability declarations.

Required concepts:

- capability mode;
- capability domain;
- capability key;
- scope;
- review requirement;
- certification status;
- metadata;
- registry version.

Permitted modes:

```text
supported
assist
checklist
manual_review
unsupported
expansion
```

Invalid modes must fail validation.

### 3.3 Registry loader and validation

Implement a deterministic loader that reads the registry data and validates it.

The loader must:

- be read-only;
- avoid provider calls;
- avoid database access;
- reject invalid modes;
- reject malformed entries;
- expose registry version;
- avoid modifying loaded data.

### 3.4 Read-only lookup service

Implement a read-only lookup service that can find capability declarations using
Educational Context-like inputs and capability keys.

Lookup must be deterministic and passive.

The lookup service must not:

- enforce behavior;
- route review;
- change evaluation;
- alter UI;
- make public product claims;
- replace AEI registry behavior.

### 3.5 Capability resolution safety

Implement safe resolution behavior for missing or conflicting capabilities.

Required behavior:

- missing capability entries must not resolve as `supported`;
- unsupported, manual-review, and assist modes must not be silently upgraded by
  broader entries;
- conflicting matching entries must not overclaim support;
- the safest lower-claim result must win when deterministic resolution is
  possible;
- unresolved conflicts must produce non-authoritative passive evidence.

### 3.6 AEI compatibility mapping

Implement tests or mapping helpers showing that current AEI Subject Capability
Registry concepts can be represented in the platform registry.

This must not:

- remove the AEI registry;
- change AEI registry data;
- switch AEI consumers to the platform registry;
- change AEI behavior.

### 3.7 Passive observer

If passive runtime lookup is introduced, implement a passive observer guarded by
a default-off feature flag.

The observer must:

- be no-op when disabled;
- isolate exceptions;
- preserve legacy product behavior when enabled;
- avoid writing product state;
- avoid exposing output to consumers.

### 3.8 Feature flag

If passive runtime lookup is introduced, add one settings-based feature flag:

```text
EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED: bool = False
```

Default state must be `False`.

Rollback is achieved by disabling or leaving disabled this flag.

### 3.9 Observability

Add operational metrics and structured logs if passive runtime lookup is
introduced.

Metrics should use low-cardinality status labels only.

Expected task name:

```text
eui_capability_registry
```

Expected statuses include:

- `loaded`;
- `validation_failed`;
- `lookup_invoked`;
- `lookup_completed`;
- `lookup_failed`;
- `unsupported`;
- `conflict`;
- `fallback`.

Metrics and logs must not expose student names, parent data, tenant slugs,
free-text answers, uploaded content, or other sensitive educational content.

### 3.10 Golden Harness

Add Golden Harness cases for deterministic capability declarations.

Expected dataset:

```text
apps/api/tests/golden/eui_v1/platform_capability_registry_cases.json
```

Coverage should include:

- CBSE Grade 10 Mathematics numeric normalization as `supported`;
- unit conversion as `supported` for declared scope;
- Hindi printed OCR as `supported` for declared scope;
- Hindi handwriting OCR as `assist`;
- Telugu handwriting OCR as `assist`;
- Sanskrit handwriting OCR as `assist` or `manual_review`;
- biology diagrams as `checklist`;
- pixel-perfect diagram grading as `unsupported`;
- missing capability resolving safely;
- conflicting capability entries resolving safely;
- AEI compatibility for current evaluation capability concepts.

### 3.11 Certification

Produce a Sprint 3 certification report:

```text
docs/product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_CERTIFICATION_REPORT.md
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
apps/api/app/modules/eui/registry/platform_capability_registry.v1.json
apps/api/app/modules/eui/schemas/platform_capability.py
apps/api/app/modules/eui/schemas/__init__.py
apps/api/app/modules/eui/services/platform_capability_registry.py
apps/api/app/modules/eui/services/platform_capability_lookup.py
apps/api/app/modules/eui/services/platform_capability_passive.py
apps/api/app/modules/eui/services/__init__.py
```

Notes:

- `platform_capability_passive.py` is optional if passive runtime lookup is
  included.
- Existing Educational Identity and Educational Context modules may be imported,
  but their behavior must not be changed without explicit ARM approval.
- AEI modules may be read for compatibility understanding but must not be
  changed.

### 4.2 Permitted test and Golden Harness files

Allowed:

```text
apps/api/tests/golden/eui_v1/platform_capability_registry_cases.json
apps/api/tests/test_platform_capability_registry.py
apps/api/tests/test_platform_capability_lookup.py
apps/api/tests/test_platform_capability_passive.py
apps/api/tests/test_eui_golden_harness.py
```

`test_platform_capability_passive.py` is required only if passive runtime lookup
is introduced.

`test_eui_golden_harness.py` may be updated to load Platform Capability Registry
cases alongside existing EUI Golden Harness cases.

### 4.3 Permitted documentation files

Allowed:

```text
docs/product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_CERTIFICATION_REPORT.md
docs/product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_DESIGN_BRIEF.md
docs/product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

After implementation is certified, ARM may separately authorize a Master Status
update before publication.

### 4.4 Protected areas

Sprint 3 does not authorize changes to:

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

- declarative platform capability registry data;
- strict registry contracts;
- read-only loader/validator;
- read-only lookup service;
- optional passive observer;
- one settings flag if passive runtime lookup is implemented;
- operational metrics/logging if passive runtime lookup is implemented;
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
- AEI contract changes;
- public product-claim generation.

---

## 6. Runtime constraints

Sprint 3 implementation must be:

- passive;
- read-only;
- deterministic;
- exception-isolated if runtime lookup is introduced;
- tenant-safe where tenant context is involved;
- invisible to users;
- non-authoritative for every consumer.

If registry loading or lookup fails, legacy behavior must continue unchanged.

When disabled, any passive observer must return without executing lookup or
recording captures.

When enabled, passive lookup must not change production output.

---

## 7. Explicit exclusions

The following remain out of scope:

- database schema changes;
- persistent registry storage;
- database migrations;
- API contract changes;
- public endpoint changes;
- UI changes;
- consumer migration;
- AEI registry replacement;
- AEI runtime behavior changes;
- EUI consumer behavior changes;
- Trust Framework implementation;
- Knowledge Acquisition Intelligence;
- Educational Knowledge Graph expansion;
- LLM inference;
- prompt changes;
- approval workflow changes;
- CurriculumPack publishing changes;
- distributed cache infrastructure;
- background workers;
- public product capability claim expansion;
- support documentation generated from registry data;
- UI badges generated from registry data.

---

## 8. Validation requirements

Before ARM acceptance, implementation evidence must include the following.

### 8.1 Focused lint

Expected command:

```text
cd apps/api
ruff check app/modules/eui tests/test_platform_capability_registry.py tests/test_platform_capability_lookup.py tests/test_eui_golden_harness.py
```

If passive runtime lookup is implemented, also include:

```text
tests/test_platform_capability_passive.py
```

### 8.2 Focused Sprint 3 tests

Expected command:

```text
cd apps/api
python -m pytest tests/test_platform_capability_registry.py tests/test_platform_capability_lookup.py tests/test_eui_golden_harness.py
```

If passive runtime lookup is implemented, also include:

```text
tests/test_platform_capability_passive.py
```

### 8.3 Sprint 1 and Sprint 2 regression

Expected command:

```text
cd apps/api
python -m pytest tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_eui_golden_harness.py
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
the certification report must document that explicitly and show that Sprint 3
files and the affected regression neighborhood are clean.

---

## 9. Rollback proof

If a feature flag is introduced, certification must prove:

- `EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED` defaults to `False`;
- disabled state executes no passive lookup;
- disabled state records no passive capture;
- enabled state does not change product output;
- exceptions are isolated;
- no schema, persistence, API, UI, or consumer migration exists to roll back.

Rollback mechanism, if flag is introduced:

```text
Set EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED=false
```

Because Sprint 3 must not introduce persistence, rollback must not require data
repair.

If no runtime passive observer is introduced, rollback is limited to reverting
the isolated registry data/contracts/tests before publication.

---

## 10. Certification deliverables

Certification must include:

- scope certified;
- registry contract evidence;
- registry data validation evidence;
- lookup behavior evidence;
- capability mode safety evidence;
- unsupported/missing/conflict behavior evidence;
- AEI compatibility evidence;
- feature flag evidence if applicable;
- observability evidence if applicable;
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

Sprint 3 implementation may be considered complete only when all of the
following are true:

- platform capability registry data exists as authorized;
- registry contracts exist as authorized;
- registry loader is deterministic and read-only;
- invalid modes are rejected;
- missing capabilities do not resolve as supported;
- conflicting entries do not overclaim support;
- unsupported and expansion entries are handled safely;
- AEI compatibility mapping exists without changing AEI behavior;
- no consumer depends on Platform Capability Registry;
- no public product claims are generated from registry data;
- no schema/API/UI changes are introduced;
- Golden Harness capability cases pass;
- observability and rollback are verified if passive runtime lookup is
  introduced;
- focused tests and regression slices pass;
- certification report is complete;
- phase retrospective is complete;
- ARM accepts the implementation before commit.

---

## 12. Commit, tag, and publication guidance

If implementation is later authorized, completed, certified, and accepted, the
recommended commit message is:

```text
feat(eui): add platform capability registry foundation
```

Recommended annotated tag:

```text
eui-runtime-phase1-sprint3-platform-capability-registry-certified
```

Publication requires separate ARM approval after certification and commit.

---

## 13. ARM decision options

ARM decision:

```text
Decision: Accepted
Implementation authorization: Granted
Authorization ID: EUI-PH1-SP3-AUTH-001
```

Sprint 3 implementation may proceed only within this contract. Completion of
Sprint 3 does not authorize commit, publication, consumer migration, AEI
registry replacement, or the next sprint.
