# Topic-ID / Mastery Spine Unification Phase A Certification Report

- **Program:** Product-facing learning intelligence readiness
- **Gate:** Topic-ID / mastery spine unification
- **Implementation slice:** Phase A — Passive mastery spine resolution
- **Status:** Accepted for commit
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./TOPIC_ID_MASTERY_SPINE_UNIFICATION_DESIGN_BRIEF.md`](./TOPIC_ID_MASTERY_SPINE_UNIFICATION_DESIGN_BRIEF.md)
- **Authorization contract:** [`./TOPIC_ID_MASTERY_SPINE_UNIFICATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./TOPIC_ID_MASTERY_SPINE_UNIFICATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)

---

## 1. Certification decision

Recommendation: Accepted for commit after ARM implementation review.

The implementation stays within the accepted Phase A contract. It adds a
strict internal `MasterySpineReference` contract, deterministic read-only
resolver, default-off passive observer, Golden Harness readiness cases, focused
tests, and validation evidence.

ARM review hardening added one tenant-scope validation: a passive
`MasterySpineResolutionReference` may not provide a `tenant_id` different from
its `school_id`.

No product behavior changes were introduced.

---

## 2. Implemented scope

Implemented:

- `MASTERY_SPINE_PASSIVE_ENABLED = False` default-off feature flag.
- Internal `MasterySpineReference` model.
- Internal `MasterySpineResolutionReference` input model.
- Structured provenance and ambiguity contracts.
- Deterministic read-only resolver:
  - explicit curriculum ID resolution;
  - EducationalIdentity metadata resolution;
  - approved CurriculumPack label matching;
  - normalized label matching;
  - legacy fallback;
  - unresolved/ambiguous evidence.
- Default-off passive observer:
  - no-op when disabled;
  - exception isolated;
  - low-cardinality metrics/logging only.
- Golden Harness cases for passive mastery spine resolution.
- Focused tests and adjacent mastery regression validation.

---

## 3. Explicit exclusions verified

Not introduced:

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
- deletion or replacement of legacy topic fields;
- product capability claim expansion.

---

## 4. Behavior posture

Default behavior remains unchanged:

- `MASTERY_SPINE_PASSIVE_ENABLED` defaults to `False`.
- No runtime consumer is migrated.
- No existing mastery computation path depends on `MasterySpineReference`.
- Existing topic-label mastery remains the source of truth.
- Passive resolution can be disabled by keeping the flag off.

Rollback:

- Keep or set `MASTERY_SPINE_PASSIVE_ENABLED=false`.
- No persisted data or schema changes need rollback.
- Existing mastery compute, flags, APIs, tutor, parent, and principal surfaces
  continue using existing behavior.

---

## 5. Golden Harness evidence

Added:

```text
apps/api/tests/golden/learning_intelligence/mastery_spine_resolution_cases.json
```

Coverage:

- explicit topic ID resolution;
- exact concept-label resolution inside an approved pack;
- legacy fallback without pack context;
- duplicate topic-label ambiguity;
- unresolved empty reference.

Certification assertion:

- Golden Harness proves deterministic same-input/same-output resolution;
- ambiguous cases remain non-authoritative;
- source switching remains false;
- canonical resolution uses tenant-scoped curriculum IDs.

---

## 6. Validation results

Focused ruff:

```text
python -m ruff check app/core/config.py app/modules/mastery/schemas/mastery_spine.py app/modules/mastery/services/mastery_spine_resolver.py app/modules/mastery/services/mastery_spine_passive.py tests/test_mastery_spine_reference.py tests/test_mastery_spine_resolver.py tests/test_mastery_spine_passive.py tests/test_mastery_spine_golden_harness.py
All checks passed!
```

Focused Phase A tests:

```text
python -m pytest tests/test_mastery_spine_reference.py tests/test_mastery_spine_resolver.py tests/test_mastery_spine_passive.py tests/test_mastery_spine_golden_harness.py -q
10 passed in 82.62s (0:01:22)
```

Adjacent mastery regression slice:

```text
python -m pytest tests/test_mastery_compute.py tests/test_mastery_handler.py tests/test_mastery_flags.py tests/test_mastery_api.py -q
41 passed in 162.56s (0:02:42)
```

API import:

```text
python -c "import app.main; print('API_IMPORT_PASS')"
API_IMPORT_PASS
```

Diff hygiene:

```text
git diff --check
PASS
```

---

## 7. Files changed

Implementation:

- `apps/api/app/core/config.py`
- `apps/api/app/modules/mastery/schemas/mastery_spine.py`
- `apps/api/app/modules/mastery/services/mastery_spine_resolver.py`
- `apps/api/app/modules/mastery/services/mastery_spine_passive.py`

Tests / Golden Harness:

- `apps/api/tests/test_mastery_spine_reference.py`
- `apps/api/tests/test_mastery_spine_resolver.py`
- `apps/api/tests/test_mastery_spine_passive.py`
- `apps/api/tests/test_mastery_spine_golden_harness.py`
- `apps/api/tests/golden/learning_intelligence/mastery_spine_resolution_cases.json`

Governance / certification:

- `docs/product/learning-intelligence/TOPIC_ID_MASTERY_SPINE_UNIFICATION_DESIGN_BRIEF.md`
- `docs/product/learning-intelligence/TOPIC_ID_MASTERY_SPINE_UNIFICATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`
- `docs/product/learning-intelligence/TOPIC_ID_MASTERY_SPINE_UNIFICATION_PHASE_A_CERTIFICATION_REPORT.md`

---

## 8. Risk assessment

Risk: Low.

Why:

- default-off flag;
- no runtime wire-up into mastery recompute;
- no schema changes;
- no API/UI changes;
- no source switch;
- existing mastery regression slice passed;
- implementation is read-only and internal.

Main future risk:

- Source adoption must not happen until passive and later dual-read evidence
  proves low divergence across real curriculum data.

---

## 9. Recommended commit metadata

Suggested commit:

```text
feat(learning): add passive mastery spine resolution foundation
```

Suggested annotated tag:

```text
topic-id-mastery-spine-passive-resolution-certified
```

---

## 10. ARM review recommendation

Accept the implementation for commit if ARM agrees that Phase A correctly
establishes passive internal spine resolution without changing any product
behavior.

Recommended next gate after publication:

```text
Teacher Evaluation UX-D design
```

or, if ARM wants deeper learning-intelligence plumbing first:

```text
Topic-ID / mastery spine Phase B additive schema readiness design
```

No later phase is authorized by this certification.
