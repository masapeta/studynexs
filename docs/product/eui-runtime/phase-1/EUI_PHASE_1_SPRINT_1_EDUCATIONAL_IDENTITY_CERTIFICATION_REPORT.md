# EUI Runtime Phase 1 Sprint 1 Certification Report

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 1 - Educational Identity
- **Sprint:** Sprint 1 - Passive Runtime Foundation
- **Authorization:** EUI-PH1-AUTH-001
- **Certification type:** Passive runtime foundation
- **Date:** 2026-07-27
- **Status:** PASS
- **Implementation commit:** Pending
- **Feature flag:** `EUI_IDENTITY_PASSIVE_ENABLED=false` by default

---

## Objective

Certify that StudyNexs now has a passive Educational Identity runtime capable of
deterministically resolving supported curriculum artifacts to a canonical
`EducationalIdentity` object without changing product behavior.

The certified flow is:

```text
Existing Curriculum / Artifact
        |
        v
Educational Identity Resolver
        |
        v
Canonical EducationalIdentity
        |
        v
Metrics / Logs / Golden Harness
        |
        v
Captured for verification only
        |
        v
No downstream consumer uses the result
```

---

## Scope certified

### Contracts

Status: PASS

- Added canonical `EducationalIdentity`, `EducationalIdentityReference`, and
  `EducationalIdentityProvenance` runtime/domain contracts.
- Added deterministic stable ID generation using the `ei://` namespace.
- Added a read-only in-memory `EducationalIdentityRegistry`.
- Added an in-process resolver cache.
- Added a passive observer capture contract for verification only.

### Runtime behavior

Status: UNCHANGED

- No existing endpoint, workflow, evaluation path, curriculum approval path, UI,
  or downstream consumer was migrated to depend on Educational Identity.
- The resolver reads existing `CurriculumPack`, chapter, topic, learning outcome,
  and Knowledge Graph concept data.
- The resolver does not write to the database.
- Existing AEI/evaluation/KG regression slices passed.

### Feature flags

Status: PASS

- Added `EUI_IDENTITY_PASSIVE_ENABLED`.
- Default state is `false`.
- Passive observer is a no-op when disabled.
- Rollback is achieved by keeping or returning the flag to `false`.

### Observability

Status: PASS

- Passive observer records low-cardinality operational metrics through the
  existing platform metrics registry.
- Recorded statuses include `invoked`, `completed`, `failed`, `ambiguous`,
  `not_found`, `cache_hit`, and `cache_miss`.
- Passive observer emits structured logs for completion, ambiguity, not-found,
  and unexpected failure cases.
- No student, parent, tenant slug, or free-text answer content is used as a
  metric label.

### Rollback

Status: PASS

- Feature flag defaults off.
- Disabled state produces no passive capture and no resolver execution.
- No schema, persistence, API, UI, or consumer migration exists to roll back.

### AEI impact

Status: UNCHANGED

- No AEI contracts were changed.
- No AEI runtime behavior was changed.
- AEI architecture, passive integration, evaluation policy, and golden harness
  regression slices passed.

### Schema

Status: UNCHANGED

- No database migrations added.
- No table, column, index, enum, or persistence change introduced.
- Educational Identity IDs are generated at runtime only.

### API

Status: UNCHANGED

- No public or internal endpoint contract was changed.
- No request or response schema used by existing consumers was changed.

### UI

Status: UNCHANGED

- No frontend or user-facing UI changed.
- No teacher, student, parent, principal, or administrator surface consumes
  Educational Identity in this sprint.

---

## Tests executed

```text
ruff check app/modules/eui tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_eui_golden_harness.py

python -m pytest tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_eui_golden_harness.py

python -m pytest tests/test_aei_architecture.py tests/test_aei_passive_integration.py tests/test_evaluation_policy.py tests/test_golden_evaluation_harness.py tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py tests/test_knowledge_graph.py tests/test_graph_queries.py tests/test_question_concept_links.py

python -c "import app.main; print('api import ok')"
```

Observed result:

```text
Focused EUI Ruff: PASS
Focused EUI tests: 14 passed
AEI / evaluation / KG regression slice: 57 passed
API import: PASS
```

Additional validation note:

```text
ruff check .
ruff check app ...
```

Both broader Ruff invocations remain blocked by pre-existing unrelated lint debt
in older migrations, application modules, and tests. The sprint-specific files
and the affected regression neighborhood are Ruff-clean.

---

## Behavior identity evidence

Phase 1 Sprint 1 introduces a callable passive runtime but does not attach it to
any existing product consumer.

Evidence:

- `EUI_IDENTITY_PASSIVE_ENABLED` defaults to `false`.
- Passive observer returns `None` and records no capture when disabled.
- Existing AEI, evaluation, answer-sheet, Golden Harness, Knowledge Graph, graph
  query, and question-concept-link tests passed unchanged.
- API import succeeds.

Result:

```text
Existing product behavior remains unchanged.
```

---

## Golden Harness

Status: PASS

Added:

```text
apps/api/tests/golden/eui_v1/educational_identity_cases.json
apps/api/tests/test_eui_golden_harness.py
```

Coverage includes deterministic stable ID generation for:

- CBSE Grade 6 Science concept identity.
- ICSE Grade 8 Physics learning objective identity.
- State Board Telugu chapter identity.
- CBSE Grade 10 Mathematics topic identity.
- Same chapter name with different subject producing a distinct identity.
- Missing chapter number falling back to a chapter slug.

---

## Risks

| Risk | Severity | Mitigation |
|---|---:|---|
| Raw-label references may be ambiguous across packs, subjects, or boards. | Medium | Resolver raises `EducationalIdentityAmbiguous`; passive observer records `ambiguous`; no consumer uses the result yet. |
| Runtime IDs are generated, not persisted. | Low | Explicitly authorized for Phase 1 Sprint 1; persistence requires later authorization. |
| In-process cache is process-local. | Low | Explicitly scoped; distributed cache is out of scope. |
| Broader repository lint debt prevents full `ruff check .` certification. | Low for this sprint | Scoped EUI lint passes; unrelated debt is documented and not modified under this authorization. |

---

## Conditions

| Condition | Severity | Owner | Disposition |
|---|---:|---|---|
| Full-repository Ruff remains blocked by unrelated pre-existing lint debt. | Low | Engineering | Documented; not a Phase 1 Sprint 1 blocker because scoped files are clean and regression slices pass. |

---

## Phase retrospective

- **What assumptions held?** Existing CurriculumPack, CurriculumChapter,
  CurriculumTopic, CurriculumLearningOutcome, and CurriculumConcept data were
  sufficient to build a read-only identity resolver without schema changes.
- **What surprised us?** Topic-level learning outcomes needed explicit registry
  inclusion so registry coverage matched resolver coverage.
- **What should the next phase change?** No consumer should migrate until a later
  authorization defines dual-read verification and source-of-truth boundaries.
- **Governance/tooling improvement:** Sprint-specific scoped Ruff remains useful
  while broader legacy lint debt exists; certification should continue to
  distinguish sprint-owned evidence from repository-wide historical debt.

---

## Recommendation

APPROVED FOR ARM REVIEW.

Phase 1 Sprint 1 satisfies the authorized scope:

- canonical Educational Identity model implemented;
- deterministic resolver implemented;
- read-only registry operational;
- stable runtime IDs generated consistently;
- in-process cache functioning;
- feature flag default-off;
- passive execution only;
- observability present;
- Golden Harness added and passing;
- no schema, API, UI, consumer migration, AEI behavior, or product behavior
  change introduced.
