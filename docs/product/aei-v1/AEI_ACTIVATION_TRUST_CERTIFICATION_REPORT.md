# AEI Activation / Trust Certification Report

Status: Ready for ARM review  
Date: 2026-07-29  
Scope: AEI Activation / Trust implementation under the accepted implementation authorization contract

## 1. Certification decision

Recommendation: Accept for commit after ARM review.

The implementation stays within the accepted AEI Activation / Trust contract. It adds controlled activation evidence, an optional manual-review acknowledgement gate, teacher-marked Golden Harness cases, and UX A-C runtime proof surfaces without changing marks, routing, database schema, public API endpoints, evidence-ledger source of truth, or student/parent/principal behavior.

## 2. Implemented scope

Implemented:

- Default-off activation/trust flag:
  - `AEI_V1_MANUAL_REVIEW_ACK_REQUIRED = False`
- AEI Activation / Trust service:
  - activation profile detection
  - manual-review-required question detection
  - manual-review acknowledgement validation
  - additive activation evidence metadata
  - low-cardinality operational metrics/logging
  - exception-isolated passive observation
- Approval payload extension:
  - additive `manual_review_acknowledgements`
  - no breaking change to existing approval requests
- Teacher evaluation UX A-C proof:
  - trust evidence chip
  - review-required count
  - manual-review acknowledgement checkbox when required
  - approved acknowledgement display
- Golden Harness expansion:
  - teacher-marked activation/trust cases for mathematics, language assist, visual/science assist, and low-confidence/manual-review behavior
- Focused backend and API tests.

## 3. Explicit exclusions verified

Not introduced:

- UX-D.
- Production rollout.
- EUI source-of-truth switch.
- Autonomous grading.
- OCR provider integration.
- LLM/provider integration.
- Database schema changes.
- Database migrations.
- New public API endpoints.
- Mark calculation changes.
- Teacher-review routing changes beyond the optional acknowledgement gate.
- Evidence ledger source replacement.
- Student/parent/principal UI changes.

## 4. Behavior posture

Default behavior remains unchanged:

- `AEI_V1_MANUAL_REVIEW_ACK_REQUIRED` defaults to `False`.
- When the flag is off, existing approval behavior is preserved.
- The approval payload remains backward compatible because `manual_review_acknowledgements` defaults to `{}`.
- Activation/trust evidence is additive metadata when an AEI v1 trust profile is enabled.
- Manual-review acknowledgement enforcement only applies when explicitly enabled.

Rollback:

- Disable `AEI_V1_MANUAL_REVIEW_ACK_REQUIRED` to remove the acknowledgement gate.
- Disable AEI v1 activation flags to remove activation/trust evidence from the runtime profile.
- Existing evaluation/approval behavior remains the fallback path.

## 5. Golden Harness evidence

Added:

- `apps/api/tests/golden/aei_v1/activation_trust_teacher_marked_cases.json`

Coverage:

- supported deterministic mathematics case with no review requirement
- language/OCR assist case with teacher acknowledgement
- visual/science assist case with teacher-adjusted marks and acknowledgement
- low-confidence/manual-review case without acknowledgement

Certification assertion:

- Golden Harness validates deterministic activation/trust evidence, manual-review counts, acknowledgement counts, capability counts, no autonomous grading, and teacher-decision evidence source.

## 6. Runtime proof evidence

Backend/API:

- Approval without required acknowledgement is rejected when the manual-review acknowledgement gate is enabled.
- Approval with acknowledgement succeeds and records acknowledgement metadata under teacher overrides.
- Approval behavior remains unchanged when the acknowledgement gate is disabled.
- Activation/trust observer is no-op when disabled.
- Activation/trust observer is exception isolated.

Frontend:

- Teacher evaluation page builds successfully.
- Manual-review acknowledgement checkbox appears for backend-equivalent review signals:
  - `manual_review_required`
  - `teacher_correction_required`
  - `requires_language_teacher_review`
  - `visual_science_review_required`
  - `assist_only`
  - `checklist_only`
  - `capability_mode` values: `assist`, `checklist`, `manual_review`, `unsupported`, `expansion`
- Approved evaluations can display saved manual-review acknowledgement evidence.

Browser proof:

- Production web build generated the affected dynamic routes successfully:
  - `/dashboard/exams/[examId]/evaluate`
  - `/dashboard/teaching/exams/[examId]/evaluate`

No live-browser interaction proof was run in this certification pass.

## 7. Validation results

Backend lint:

```text
python -m ruff check app/core/config.py app/modules/examinations/schemas/evaluation.py app/modules/examinations/endpoints/evaluation.py app/modules/examinations/services/answer_sheet_eval_service.py app/modules/examinations/services/aei_activation_trust.py tests/test_aei_activation_trust.py tests/test_golden_evaluation_harness.py
All checks passed!
```

Focused activation/trust tests:

```text
python -m pytest tests/test_aei_activation_trust.py tests/test_golden_evaluation_harness.py -q
15 passed in 22.53s
```

AEI regression slice:

```text
python -m pytest tests/test_answer_sheet_eval.py tests/test_aei_v1_review_policy.py tests/test_aei_v1_evidence_ledger.py tests/test_aei_v1_language_ocr_assist.py tests/test_aei_v1_visual_science_assist.py -q
51 passed in 172.30s (0:02:52)
```

API import:

```text
python -c "import app.main; print('API_IMPORT_PASS')"
API_IMPORT_PASS
```

Admin web build:

```text
npm run build
Compiled successfully.
Generated 72 routes.
```

Admin web lint caveat:

```text
npm run lint
FAILED
```

Reason: the repository lint command scans generated `.open-next` output and fails on generated build artifacts. A focused lint against the edited page also still fails on pre-existing page debt (`any` state types and `react-hooks/set-state-in-effect`). The new `Object.entries(...): [string, any]` lint issue introduced during implementation was removed. No new focused lint error remains from the Activation / Trust additions.

Diff hygiene:

```text
git diff --check
PASS
```

Note: Git emitted a line-ending warning for `apps/api/tests/test_golden_evaluation_harness.py`; the command exited successfully.

## 8. Files changed

Implementation:

- `apps/api/app/core/config.py`
- `apps/api/app/modules/examinations/services/aei_activation_trust.py`
- `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py`
- `apps/api/app/modules/examinations/schemas/evaluation.py`
- `apps/api/app/modules/examinations/endpoints/evaluation.py`
- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`

Tests / Golden Harness:

- `apps/api/tests/test_aei_activation_trust.py`
- `apps/api/tests/test_golden_evaluation_harness.py`
- `apps/api/tests/golden/aei_v1/activation_trust_teacher_marked_cases.json`

Governance:

- `docs/product/aei-v1/AEI_ACTIVATION_TRUST_DESIGN_BRIEF.md`
- `docs/product/aei-v1/AEI_ACTIVATION_TRUST_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`
- `docs/product/aei-v1/AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md`

## 9. Risk assessment

Risk: Low to medium.

Why:

- Default-off flag protects existing behavior.
- Manual-review acknowledgement enforcement is explicit and reversible.
- Approval payload change is additive.
- No database schema changes, public endpoint additions, or UI route changes.
- The approval request payload extension is additive and backward compatible.
- No source switch or autonomous grading.
- Regression slice passed.

Remaining caveat:

- Admin web lint still has pre-existing debt in generated `.open-next` artifacts and legacy teacher evaluation page typing/effect patterns. This should be addressed separately, not inside this Activation / Trust implementation batch.

## 10. Recommended commit metadata

Suggested commit:

```text
feat(aei): add activation trust runtime proof foundation
```

Suggested annotated tag:

```text
aei-activation-trust-certified
```

## 11. ARM review recommendation

Accept the implementation for commit if ARM agrees that the lint caveat is non-blocking because:

- backend checks pass,
- focused activation/trust tests pass,
- AEI regression slice passes,
- API imports successfully,
- admin-web production build passes,
- product behavior remains feature-flag controlled and unchanged by default,
- the only lint failures are pre-existing/generated-output issues outside the authorized trust implementation.
