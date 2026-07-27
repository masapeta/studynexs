# AEI Wave 1 Passive Integration Certification Report

**Subsystem:** Academic Evaluation Intelligence (AEI)
**Phase:** Controlled Runtime Integration
**Wave:** Wave 1 - Passive Integration
**Certification type:** Passive Runtime Integration Certification
**Date:** 2026-07-27
**Status:** PASS

---

## Objective

Certify that AEI can execute safely and deterministically beside the existing
answer-sheet evaluation path without changing production behavior.

Wave 1 introduces AEI as an observer only. The existing evaluation result remains
the single source of truth.

---

## Scope Certified

### Passive Integration Hook

Status: PASS

- `AnswerSheetEvalService.execute_evaluation(...)` invokes AEI only through a
  passive observer hook.
- The hook runs after existing suggestions are produced.
- The hook receives copies of student answers and suggestions.
- The production result does not consume AEI output.
- Existing marks, summary, status, gradebook, mastery, and approval behavior are
  unchanged.

### Feature Flag

Status: PASS

- `AEI_PASSIVE_INTEGRATION_ENABLED` exists.
- Default value is `False`.
- When disabled, the observer does not execute and captures nothing.
- When enabled, the observer executes passively.

### Passive Capture

Status: PASS

- Passive capture is bounded and in-memory only.
- No database schema or persistence was introduced.
- Captured output includes the complete AEI contract stack per question:
  - `AcademicAnswer`
  - `AcademicReasoningResult`
  - `PolicyDecision`
  - `TeacherReviewDecision`
- Structured logs record passive completion/failure summaries without changing
  user-visible behavior.

### Exception Isolation

Status: PASS

- AEI exceptions are caught inside the passive observer.
- Failed AEI execution returns `None`.
- Existing evaluation continues.
- Marks and suggestions remain controlled by the legacy evaluation path.

### Metrics

Status: PASS

- Passive integration emits bounded operational metrics through the existing
  platform metrics registry using task `aei_passive_integration`.
- Recorded statuses include:
  - `invoked`
  - `completed`
  - `failed`
- Completion/failure duration is recorded.

### Runtime Behavior

Status: UNCHANGED

- AEI does not affect `row.ai_suggestions`.
- AEI does not affect `row.correction_summary`.
- AEI does not affect `row.status`.
- AEI does not affect AI credit recording.
- AEI does not affect teacher approval.
- AEI does not affect gradebook or mastery.

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
Wave 1 passive integration tests: PASS
Batch 0-5 AEI regression tests: PASS
Existing evaluation regression slice: PASS
API import: PASS
Ruff: PASS
git diff --check: PASS
```

---

## Behavior Identity Evidence

Wave 1 includes a deterministic integration test proving:

```text
Existing evaluation output with AEI disabled
    ==
Existing evaluation output with AEI enabled
```

Compared fields:

- evaluation status;
- AI suggestions;
- correction summary;
- error message.

The test forces the existing subjective path into its certified deterministic
fallback so the comparison measures AEI integration rather than live LLM
variation.

---

## Risks

Risk level: LOW

Known risks:

- Passive capture is in-process and bounded; it is not durable evidence.
- Subject aliases such as "Maths" may resolve as unsupported until the Subject
  Capability Registry gains explicit alias handling in a future authorized batch.
- Passive capture is intended for Wave 1 validation, not operational analytics.

Mitigation:

- Wave 2 should introduce explicit comparison/shadow analysis if authorized.
- Alias calibration should remain a capability-registry concern, not a Wave 1
  runtime integration change.

---

## Recommendation

Passive Runtime Integration Certification result: PASS

Recommendation: APPROVED FOR WAVE 1 ACCEPTANCE

Wave 1 satisfies its success criterion:

```text
AEI executed against production evaluation requests while production results
remained identical.
```

Next authorized phase should be Wave 2 - Shadow Mode only, after ARM acceptance
and publication of Wave 1.
