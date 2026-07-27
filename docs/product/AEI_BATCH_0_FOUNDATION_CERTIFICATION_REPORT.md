# AEI Batch 0 Foundation Certification Report

**Subsystem:** Academic Evaluation Intelligence (AEI)
**Batch:** Batch 0 — Golden Harness + Subject Capability Registry
**Certification type:** Foundation Certification
**Date:** 2026-07-27
**Status:** PASS

---

## Objective

Certify that AEI Batch 0 establishes the architectural and regression-test foundation for Academic Evaluation Intelligence without changing runtime evaluation behavior.

Batch 0 is not a runtime certification batch. It does not certify teacher-facing evaluation behavior, browser workflows, or end-to-end academic evaluation output. Those certifications begin when later AEI batches modify runtime behavior.

---

## Scope Certified

### Architecture

Status: PASS

- `ADR-0001` exists.
- `docs/architecture/AEI.md` exists.
- The frozen AEI pipeline is documented.
- The protected subsystem rule is documented: no academic evaluation logic may bypass AEI.
- Provider, reasoning, policy, registry, and Golden Harness expectations are documented.

### Subject Capability Registry

Status: PASS

- Registry exists at `apps/api/app/modules/examinations/data/subject_capability_registry.v1.json`.
- Registry is versioned as `aei-subject-capabilities-v1`.
- Loader uses centralized `DEFAULT_REGISTRY_VERSION`.
- Registry loads successfully.
- Registry is read-only and dependency-light.
- Unknown subjects/capabilities fail closed to `unsupported`.
- Assist, checklist, partial, manual-review, and unsupported modes require teacher review.

### Golden Harness

Status: PASS

- Golden Harness starter exists at `apps/api/tests/golden/aei_v1/pilot_trust_cases.json`.
- Cases include stable IDs.
- Cases include subject, capability, input, rubric, expected result, and notes.
- Cases cover pilot trust families:
  - mathematics equivalence;
  - units;
  - scientific notation;
  - chemistry reaction balancing;
  - biology diagrams;
  - geography maps;
  - Hindi handwriting OCR;
  - Telugu handwriting OCR;
  - Sanskrit handwriting OCR.
- Golden cases are validated against the Subject Capability Registry.

### Foundation Integrity

Status: PASS

- Focused Ruff checks pass.
- Focused pytest checks pass.
- API import passes.
- Existing objective-evaluation regression slice passes.
- `git diff --check` passes.

---

## Runtime Behavior

Status: UNCHANGED

Batch 0 does not integrate the Subject Capability Registry or Golden Harness into the runtime evaluation path.

No teacher-facing evaluation behavior changed.

---

## Schema

Status: UNCHANGED

Batch 0 introduces no database schema changes and no Alembic migration.

---

## UI

Status: UNCHANGED

Batch 0 introduces no frontend or browser-facing changes.

---

## Tests Executed

```text
python -m ruff check app\modules\examinations\services\subject_capability_registry.py tests\test_subject_capability_registry.py tests\test_golden_evaluation_harness.py tests\test_aei_architecture.py

python -m pytest tests\test_subject_capability_registry.py tests\test_golden_evaluation_harness.py tests\test_aei_architecture.py -q

python -c "from app.modules.examinations.services.subject_capability_registry import SubjectCapabilityRegistry; r=SubjectCapabilityRegistry.load_default(); print(r.version, len(r.subjects()))"

python -c "import app.main"

python -m pytest tests\test_answer_sheet_eval.py::test_grade_objective_mcq tests\test_answer_sheet_eval.py::test_grade_objective_wrong -q

git diff --check
```

Observed result:

```text
Focused AEI tests: 14 passed
Existing evaluation regression slice: 2 passed
API import: PASS
Ruff: PASS
git diff --check: PASS
```

---

## Risks

Risk level: LOW

Known risk:

- Batch 0 is foundation-only. It does not yet prove runtime AEI behavior because no runtime AEI behavior has been integrated.

Mitigation:

- Runtime certification begins with later batches once AcademicAnswer, providers, reasoning, policy, and Evaluation Service integration are implemented.

---

## Recommendation

Foundation Certification result: PASS

Recommendation: APPROVED FOR BATCH 0 ACCEPTANCE

Next authorized batch should be Batch 1 — AcademicAnswer canonical model only. Batch 1 should not introduce normalization, reasoning, policy, UI, or runtime evaluation behavior changes beyond the canonical model foundation.
