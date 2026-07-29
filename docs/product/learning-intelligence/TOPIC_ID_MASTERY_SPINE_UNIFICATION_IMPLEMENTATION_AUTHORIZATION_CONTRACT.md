# Topic-ID / Mastery Spine Unification Implementation Authorization Contract

- **Program:** Product-facing learning intelligence readiness
- **Gate:** Topic-ID / mastery spine unification
- **Implementation slice:** Phase A — Passive mastery spine resolution
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized for Phase A passive mastery spine resolution only
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./TOPIC_ID_MASTERY_SPINE_UNIFICATION_DESIGN_BRIEF.md`](./TOPIC_ID_MASTERY_SPINE_UNIFICATION_DESIGN_BRIEF.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Authorization statement

This contract defines the permitted scope for the first implementation slice of
Topic-ID / mastery spine unification.

ARM has accepted this contract. Implementation is authorized only within this
contract.

Authorization is limited to:

```text
Phase A — Passive mastery spine resolution only
```

This phase may resolve existing exam/question/mastery topic labels into
canonical internal `MasterySpineReference` objects for evidence and readiness
proof only.

It must not change mastery calculations, persisted mastery rows, API responses,
UI behavior, tutor recommendations, parent/student/principal outputs, AEI
behavior, or source-of-truth selection.

---

## 2. Purpose

The purpose of Phase A is to answer one narrow question:

> Can StudyNexs deterministically resolve existing mastery topic signals to a
> canonical curriculum/EUI spine reference without changing product behavior?

The intended output is internal evidence only:

```text
Legacy topic signal
        |
        v
Passive mastery spine resolver
        |
        v
MasterySpineReference
        |
        v
Metrics / Golden Harness / Certification
        |
        v
No product-visible behavior change
```

---

## 3. Authorized implementation scope

If this contract is accepted, the following work is authorized.

### 3.1 Canonical `MasterySpineReference` model

Introduce an immutable runtime/domain model representing a passive resolved
learning-intelligence spine reference.

Representative fields:

- `tenant_id`
- `school_id`
- `academic_year_id`
- `class_id`
- `subject_id`
- `pack_id`
- `chapter_id`
- `topic_id`
- `concept_id`
- `learning_outcome_id`
- `educational_identity_id`
- `spine_level`
- `label`
- `resolution_status`
- `authority_posture`
- `provenance`
- `ambiguities`
- `metadata`

The model must be JSON-serializable, deterministic, and strict enough to avoid
shape drift.

### 3.2 Deterministic passive resolver

Implement a deterministic resolver that accepts current topic/evidence context
and returns a `MasterySpineReference`.

Allowed input sources:

- current `Exam.topic`;
- current `Exam.question_schema[].topic`;
- current mastery ledger row topic fields when passed explicitly;
- existing `CurriculumPack`, `CurriculumChapter`, `CurriculumTopic`,
  `CurriculumConcept`, and `CurriculumLearningOutcome` records;
- existing `EducationalIdentity` resolver/service where appropriate;
- current tenant/class/subject/year context.

No LLM or AI inference is authorized.

### 3.3 Read-only curriculum/EUI lookup

The resolver may read existing curriculum and EUI identity data.

It may not:

- write curriculum records;
- alter `CurriculumPack` approval flow;
- publish graph edges;
- mutate EUI identity/context/capability/trust records;
- create database rows;
- perform backfills.

### 3.4 Resolution precedence

Implement deterministic precedence consistent with the design brief:

1. Explicit curriculum ID already attached to the input.
2. EducationalIdentity metadata with curriculum entity IDs.
3. Approved `CurriculumPack` entity lookup within tenant/class/subject/year.
4. Exact topic/concept label match within the approved pack.
5. Normalized label match within the approved pack.
6. Legacy free-text topic fallback.
7. Ambiguous/unresolved result.

Lower-precedence sources must not override higher-precedence sources.

Conflicts must be recorded as passive evidence.

### 3.5 Ambiguity handling

Ambiguity must be represented structurally.

Examples:

- duplicate topic labels across chapters;
- multiple concept matches;
- missing approved pack;
- incomplete class/subject/year context;
- unresolved historical label.

Ambiguous or unresolved results must not change existing product behavior.

### 3.6 Passive observer

Implement a default-off passive observer that can be called from a narrow
runtime seam to attempt spine resolution and record internal evidence.

Allowed runtime posture:

- no-op when disabled;
- exception isolated;
- read-only;
- low-cardinality metrics/logging only;
- no user-visible output;
- no source switch.

### 3.7 Feature flag

Add a default-off feature flag:

```text
MASTERY_SPINE_PASSIVE_ENABLED=false
```

The flag must:

- default to disabled in code;
- enable passive observation only;
- provide rollback by disabling the flag;
- not imply dual-read, dual-write, schema, or source adoption.

### 3.8 Observability

Add operational metrics and structured logs consistent with existing platform
patterns.

Suggested event/status names:

- `mastery_spine_resolve_invoked`
- `mastery_spine_resolve_completed`
- `mastery_spine_resolve_failed`
- `mastery_spine_resolve_ambiguous`
- `mastery_spine_resolve_unresolved`
- `mastery_spine_resolve_legacy_fallback`

Metrics/logs must not include student names, raw answers, or raw topic text.

### 3.9 Golden Harness readiness cases

Add deterministic Golden Harness cases covering:

- exact topic ID match;
- exact concept ID match;
- label-only legacy fallback;
- duplicate topic label ambiguity;
- missing approved pack;
- unresolved historical label;
- tenant/class/subject/year boundary preservation.

The harness must prove:

- same input produces same output;
- ambiguity does not authorize source switching;
- disabled passive mode preserves legacy behavior;
- canonical IDs are tenant-scoped.

### 3.10 Certification report

Produce:

```text
docs/product/learning-intelligence/
TOPIC_ID_MASTERY_SPINE_UNIFICATION_PHASE_A_CERTIFICATION_REPORT.md
```

The report must include:

- scope compliance;
- changed files;
- validation evidence;
- feature flag proof;
- rollback proof;
- ambiguity behavior proof;
- Golden Harness proof;
- explicit statement that no product behavior changed.

---

## 4. Authorized repository boundary

If accepted, implementation changes are limited to the following areas.

### 4.1 API source

Allowed:

```text
apps/api/app/core/config.py
apps/api/app/modules/mastery/schemas/
apps/api/app/modules/mastery/services/
apps/api/app/modules/eui/services/      # read-only integration helpers only, if necessary
apps/api/app/modules/eui/schemas/       # references only, if necessary
```

Preferred new files:

```text
apps/api/app/modules/mastery/schemas/mastery_spine.py
apps/api/app/modules/mastery/services/mastery_spine_resolver.py
apps/api/app/modules/mastery/services/mastery_spine_passive.py
```

### 4.2 Tests and Golden Harness

Allowed:

```text
apps/api/tests/test_mastery_spine_reference.py
apps/api/tests/test_mastery_spine_resolver.py
apps/api/tests/test_mastery_spine_passive.py
apps/api/tests/golden/learning_intelligence/
apps/api/tests/test_golden_evaluation_harness.py  # only if reused as the existing harness entry point
```

### 4.3 Documentation

Allowed:

```text
docs/product/learning-intelligence/
```

### 4.4 Protected areas

Not allowed without separate ARM authorization:

```text
apps/api/alembic/
apps/api/app/db/models/
apps/api/app/modules/examinations/
apps/api/app/modules/tutor/
apps/api/app/modules/parent/
apps/api/app/modules/principal/
apps/admin-web/
```

Exception:

- `apps/api/app/core/config.py` is allowed for the default-off flag only.

---

## 5. Explicit exclusions

This implementation contract does not authorize:

- database schema changes;
- Alembic migrations;
- persistence of spine references;
- mastery ledger writes using canonical IDs;
- mastery source switching;
- dual-write;
- dual-read divergence scoring;
- tutor migration;
- parent/student/principal behavior changes;
- UI changes;
- public API changes;
- API response field additions;
- AEI behavior changes;
- EUI contract changes;
- LLM inference;
- automatic historical backfill;
- source adoption;
- deletion or replacement of legacy topic fields;
- product capability claim expansion.

---

## 6. Runtime constraints

The implementation must remain:

- passive;
- read-only;
- deterministic;
- default-off;
- exception isolated;
- tenant-safe;
- product-invisible;
- reversible by flag disablement.

Legacy mastery remains the only runtime source of truth.

---

## 7. Rollback proof

Certification must prove:

- with `MASTERY_SPINE_PASSIVE_ENABLED=false`, passive resolution is not invoked;
- existing mastery compute outputs remain unchanged;
- existing mastery API behavior remains unchanged;
- no database schema or persisted records are introduced;
- disabling the flag fully removes the passive runtime path.

---

## 8. Validation requirements

Before ARM acceptance, the implementation must provide evidence for:

Backend:

- focused ruff on changed Python files;
- focused tests for model, resolver, passive observer, and Golden Harness;
- adjacent mastery regression tests:
  - `tests/test_mastery_compute.py`
  - `tests/test_mastery_handler.py`
  - `tests/test_mastery_flags.py`
  - `tests/test_mastery_api.py`
- API import:
  - `python -c "import app.main"`
- `git diff --check`.

If an adjacent test is too slow or blocked by existing external state, the
certification report must state exactly what was and was not verified.

---

## 9. Acceptance criteria

Phase A may be accepted only if all are true:

- `MasterySpineReference` exists as a strict canonical runtime model.
- Resolver is deterministic and read-only.
- Feature flag defaults off.
- Passive observer is no-op when disabled.
- Ambiguous/unresolved cases preserve legacy behavior.
- Golden Harness cases cover supported resolution scenarios and failure modes.
- Existing mastery computation remains unchanged.
- No schema/API/UI/product behavior changes are introduced.
- Certification report is complete.

---

## 10. Recommended implementation metadata

If implementation is later accepted after code review:

Suggested commit:

```text
feat(learning): add passive mastery spine resolution foundation
```

Suggested annotated tag:

```text
topic-id-mastery-spine-passive-resolution-certified
```

---

## 11. ARM review posture

ARM decision:

```text
Contract accepted.
Implementation authorized for Phase A passive mastery spine resolution only.
No later phase is authorized.
```
