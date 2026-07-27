# AEI Wave 2 Shadow Mode Certification Report

**Subsystem:** Academic Evaluation Intelligence (AEI)
**Phase:** Controlled Runtime Integration
**Wave:** Wave 2 - Shadow Mode
**Certification type:** Shadow Comparison Certification
**Date:** 2026-07-27
**Status:** PASS

---

## Objective

Certify that AEI can compare its passive output against the existing production
evaluation result without changing production behavior.

Wave 2 introduces internal shadow comparison only. The existing evaluation result
remains the single source of truth.

---

## Scope Certified

### Shadow Mode Feature Flag

Status: PASS

- `AEI_SHADOW_MODE_ENABLED` exists.
- Default value is `False`.
- Shadow Mode can enable AEI observer execution without enabling the Wave 1
  passive flag.
- Shadow Mode remains user-invisible.

### Shadow Comparison

Status: PASS

- Shadow comparison is attached to the existing bounded in-memory passive capture.
- No database schema or persistence was introduced.
- Per-question comparison captures:
  - production method;
  - production confidence;
  - production review signal;
  - production suggested marks;
  - production max marks;
  - AEI policy decision;
  - AEI manual-review requirement;
  - AEI supported-capability signal;
  - difference categories.
- Per-evaluation summary captures:
  - question count;
  - agreement count;
  - difference count;
  - unsupported-capability count;
  - manual-review delta count.

### Difference Classification

Status: PASS

Initial deterministic difference categories exist:

- `capability_unsupported`
- `manual_review_signal_delta`
- `production_heuristic_fallback`
- `production_low_confidence`

The classifier treats low-confidence production output as a difference only when
AEI does not align with the review signal. It does not mark agreed uncertainty as
a disagreement.

### Metrics

Status: PASS

- Shadow Mode emits bounded operational metrics through the existing platform
  metrics registry using task `aei_shadow_mode`.
- Recorded statuses include:
  - `invoked`
  - `completed`
  - `difference`
  - `failed`

### Runtime Behavior

Status: UNCHANGED

- Shadow comparison does not affect `row.ai_suggestions`.
- Shadow comparison does not affect `row.correction_summary`.
- Shadow comparison does not affect `row.status`.
- Shadow comparison does not affect AI credit recording.
- Shadow comparison does not affect teacher approval.
- Shadow comparison does not affect gradebook or mastery.

### Schema

Status: UNCHANGED

- No database schema changes.
- No Alembic migration.

### UI

Status: UNCHANGED

- No frontend changes.
- No browser-facing behavior changes.

---

## Tests Executed

```text
python -m ruff check app/core/config.py app/modules/examinations/services/aei_passive_integration.py app/modules/examinations/services/answer_sheet_eval_service.py tests/test_aei_passive_integration.py

python -m pytest tests/test_aei_passive_integration.py -q

python -m pytest tests/test_teacher_review_decision.py tests/test_teacher_review.py tests/test_policy_decision.py tests/test_evaluation_policy.py tests/test_academic_reasoning_result.py tests/test_academic_reasoning_engine.py tests/test_academic_understanding_engine.py tests/test_academic_answer.py tests/test_subject_capability_registry.py tests/test_golden_evaluation_harness.py tests/test_aei_architecture.py -q

python -m pytest tests/test_answer_sheet_eval.py::test_grade_objective_mcq tests/test_answer_sheet_eval.py::test_grade_objective_wrong -q

python -c "import app.main"

git diff --check
```

Observed result:

```text
Wave 2 shadow mode tests: PASS
Batch 0-5 AEI regression tests: PASS
Existing evaluation regression slice: PASS
API import: PASS
Ruff: PASS
git diff --check: PASS
```

---

## Behavior Identity Evidence

Wave 2 includes a deterministic integration test proving:

```text
Existing evaluation output with AEI disabled
    ==
Existing evaluation output with AEI Shadow Mode enabled
```

Compared fields:

- evaluation status;
- AI suggestions;
- correction summary;
- error message.

The test forces the existing subjective path into its certified deterministic
fallback so the comparison measures Shadow Mode integration rather than live LLM
variation.

---

## Risks

Risk level: LOW

Known risks:

- Shadow comparison is in-process and bounded; it is not durable analytics.
- Shadow comparison is currently a workflow-signal comparison, not an AEI marks
  comparison, because AEI still does not assign marks.
- Subject aliases such as "Maths" may produce unsupported-capability differences
  until the Subject Capability Registry gains explicit alias handling in a future
  authorized batch.

Mitigation:

- Wave 3 should not become teacher-visible until shadow differences are reviewed.
- Alias calibration should remain a capability-registry concern and should not be
  patched ad hoc in the runtime hook.

---

## Recommendation

Shadow Comparison Certification result: PASS

Recommendation: APPROVED FOR WAVE 2 ACCEPTANCE

Wave 2 satisfies its success criterion:

```text
AEI Shadow Mode compared production evaluation outputs against AEI outputs while
production results remained identical.
```

Next authorized phase should be Wave 3 - Pilot Mode only, after ARM acceptance
and publication of Wave 2.
