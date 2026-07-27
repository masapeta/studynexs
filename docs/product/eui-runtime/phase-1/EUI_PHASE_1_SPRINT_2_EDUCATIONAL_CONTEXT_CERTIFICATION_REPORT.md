# EUI Runtime Phase 1 Sprint 2 Certification Report

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 1 - Educational Identity and Context
- **Sprint:** Sprint 2 - Educational Context
- **Authorization:** EUI-PH1-SP2-AUTH-001
- **Certification type:** Passive runtime foundation
- **Date:** 2026-07-27
- **Status:** PASS
- **Implementation commit:** Pending
- **Feature flag:** `EUI_CONTEXT_PASSIVE_ENABLED=false` by default

---

## Objective

Certify that StudyNexs now has a passive Educational Context runtime capable of
deterministically resolving supported educational references to a canonical
`EducationalContext` object without changing product behavior.

The certified flow is:

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
No downstream consumer uses the result
```

---

## Scope certified

### Contracts

Status: PASS

- Added canonical `EducationalContext`, `EducationalContextReference`, and
  `EducationalContextProvenance` runtime/domain contracts.
- Added structured conflict and ambiguity contracts.
- Added internal field-source traceability so passive certification can explain
  which source resolved each context field.
- Added an in-process context cache.
- Added passive observer capture contract for verification only.

### Runtime behavior

Status: UNCHANGED

- No endpoint, workflow, evaluation path, curriculum approval path, UI, or
  downstream consumer was migrated to depend on Educational Context.
- Existing evaluation, AEI, Educational Identity, and Knowledge Graph regression
  slices passed.
- Educational Context can execute passively, but no existing product path uses
  the result as source of truth.

### Feature flags

Status: PASS

- Added `EUI_CONTEXT_PASSIVE_ENABLED`.
- Default state is `false`.
- Passive observer is a no-op when disabled.
- Rollback is achieved by keeping or returning the flag to `false`.

### Context precedence

Status: PASS

Certified precedence model:

1. trusted server-side tenant/runtime scope;
2. explicit artifact references;
3. Educational Identity / approved curriculum-derived context;
4. existing runtime metadata;
5. derived non-authoritative labels.

Lower-precedence fields do not silently override higher-precedence fields.
Conflicts are recorded as passive evidence only.

### Ambiguity behavior

Status: PASS

- Ambiguity produces a structured non-authoritative context result.
- Candidate references and ambiguity reasons are recorded when safe.
- Ambiguity does not route review, alter evaluation, update UI, or affect
  product behavior.

### Observability

Status: PASS

- Passive observer records low-cardinality operational metrics through the
  existing platform metrics registry.
- Recorded statuses include `invoked`, `completed`, `failed`, `ambiguous`,
  `not_found`, `conflict`, `cache_hit`, and `cache_miss`.
- Passive observer emits structured logs for completion, conflict, ambiguity,
  not-found, and unexpected failure cases.
- No student, parent, tenant slug, free-text answer, uploaded content, or other
  sensitive educational content is used as a metric label.

### Rollback

Status: PASS

- Feature flag defaults off.
- Disabled state produces no passive capture and no resolver execution.
- No schema, persistence, API, UI, or consumer migration exists to roll back.
- Rollback mechanism is:

```text
EUI_CONTEXT_PASSIVE_ENABLED=false
```

### AEI impact

Status: UNCHANGED

- No AEI contracts were changed.
- No AEI runtime behavior was changed.
- AEI architecture, passive integration, evaluation policy, Golden Harness,
  evaluation engine, answer-sheet evaluation, Knowledge Graph, graph-query, and
  question-concept-link regression slices passed.

### Schema

Status: UNCHANGED

- No database migrations added.
- No table, column, index, enum, or persistence change introduced.
- Educational Context exists as a runtime/domain object only.

### API

Status: UNCHANGED

- No public or internal endpoint contract was changed.
- No request or response schema used by existing consumers was changed.

### UI

Status: UNCHANGED

- No frontend or user-facing UI changed.
- No teacher, student, parent, principal, or administrator surface consumes
  Educational Context in this sprint.

---

## Tests executed

```text
cd apps/api
ruff check app/modules/eui tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_eui_golden_harness.py

python -m pytest tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_eui_golden_harness.py

python -m pytest tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_eui_golden_harness.py

python -m pytest tests/test_aei_architecture.py tests/test_aei_passive_integration.py tests/test_evaluation_policy.py tests/test_golden_evaluation_harness.py tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py tests/test_knowledge_graph.py tests/test_graph_queries.py tests/test_question_concept_links.py

python -c "import app.main; print('api import ok')"

git diff --check
```

Observed result:

```text
Focused EUI Ruff: PASS
Focused Sprint 2 tests: 17 passed
Sprint 1 Educational Identity regression: 15 passed
AEI / evaluation / KG regression slice: 57 passed
API import: PASS
git diff --check: PASS
```

Additional validation note:

```text
DB-backed pytest suites must be run sequentially in this local environment.
An earlier parallel execution attempt caused a PostgreSQL enum DDL collision
while two test engines created metadata concurrently. Sequential execution
passed and is the certification evidence.
```

---

## Golden Harness

Status: PASS

Added:

```text
apps/api/tests/golden/eui_v1/educational_context_cases.json
```

Updated:

```text
apps/api/tests/test_eui_golden_harness.py
```

Coverage includes deterministic context resolution for:

- CBSE Grade 6 Science unit-test context.
- ICSE Grade 8 Physics homework context.
- State Board Telugu-medium context.
- Same Educational Identity used in different assessment modes.
- Precedence conflict between Educational Identity and runtime metadata.
- Precedence conflict where explicit artifact reference wins over
  curriculum-derived identity metadata.
- Ambiguous grade/section candidate context.

---

## Behavior identity evidence

Sprint 2 introduces a callable passive runtime but does not attach it to any
existing product consumer.

Evidence:

- `EUI_CONTEXT_PASSIVE_ENABLED` defaults to `false`.
- Passive observer returns `None` and records no capture when disabled.
- Enabled passive mode only records internal captures/metrics.
- Existing Sprint 1, AEI, evaluation, answer-sheet, Golden Harness, Knowledge
  Graph, graph-query, and question-concept-link tests passed unchanged.
- API import succeeds.

Result:

```text
Existing product behavior remains unchanged.
```

---

## Risks

| Risk | Severity | Mitigation |
|---|---:|---|
| Context sources can conflict across identity, artifact metadata, and runtime metadata. | Medium | Precedence is deterministic; conflicts are recorded as passive evidence only. |
| Ambiguous context may appear frequently before consumer migration. | Medium | Ambiguity is non-authoritative and invisible to consumers in Sprint 2. |
| In-process cache is process-local. | Low | Explicitly scoped; distributed cache remains out of scope. |
| Field-source traceability could be mistaken for product-facing explainability. | Low | Stored only inside passive runtime objects/captures; not exposed to consumers. |
| Broader repository lint debt may still block full `ruff check .`. | Low for this sprint | Scoped EUI lint passes; unrelated lint debt is not modified under this authorization. |

---

## Conditions

| Condition | Severity | Owner | Disposition |
|---|---:|---|---|
| None | - | - | - |

---

## Phase retrospective

- **What assumptions held?** Sprint 1 patterns for strict contracts, passive
  observers, in-process cache, platform metrics, and Golden Harness data reused
  cleanly for Educational Context.
- **What surprised us?** Running multiple DB-backed pytest suites in parallel
  can collide during PostgreSQL enum creation in the local test environment.
  Sequential validation should remain the evidence path for DB-backed suites.
- **What should the next phase change?** Future phases should continue
  documenting exact repository boundaries and avoid consumer migration until
  passive context evidence is accepted.
- **What governance or tooling improvements emerged?** Field-source
  traceability is useful implementation evidence and should be considered for
  future passive foundational sprints where precedence matters. ARM review also
  surfaced one useful correction: explicit artifact references must outrank
  curriculum-derived identity metadata, and that behavior now has focused
  regression coverage.

---

## Recommendation

APPROVED FOR ARM IMPLEMENTATION REVIEW.

Sprint 2 satisfies the authorized passive runtime foundation scope. It should
not be committed until ARM reviews the implementation diff and accepts the
certification evidence.
