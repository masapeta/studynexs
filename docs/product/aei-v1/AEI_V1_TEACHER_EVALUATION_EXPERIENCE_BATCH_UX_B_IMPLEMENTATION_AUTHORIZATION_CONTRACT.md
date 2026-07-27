# AEI v1.0 Teacher Evaluation Experience - Batch UX-B Implementation Authorization Contract

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-B - Override reason workflow
- **Classification:** Implementation authorization contract
- **Authorization ID:** AEI-TEACHER-UX-B-AUTH-001
- **Status:** Accepted
- **Implementation:** Authorized for Batch UX-B only
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **UX-A baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize, if accepted, the second narrow product-facing AEI v1.0 teacher
experience implementation batch.

Batch UX-B should replace the current generic override reason behavior with a
teacher-visible, auditable override reason workflow on the existing teacher
evaluation review page.

The guiding product question is:

> When a teacher changes AI-suggested marks, can StudyNexs capture the reason
> clearly and safely without changing marks calculation, approval authority, or
> backend contracts?

---

## 2. Current behavior

The current teacher evaluation page allows teachers to edit final marks before
approval.

When the teacher changes marks, the frontend currently submits:

```json
{
  "marks": 2,
  "reason": "Teacher adjustment"
}
```

This is technically auditable but not educationally meaningful.

UX-B should make the reason explicit and teacher-authored.

---

## 3. Implementation scope

If this contract is accepted, implementation is authorized only for:

1. adding per-question override reason state on the existing teacher evaluation
   page;
2. showing a reason input only when the teacher changes final marks from the AI
   suggested marks;
3. requiring a non-empty reason before approval when marks are changed;
4. submitting the existing approval payload shape:

   ```json
   {
     "teacher_overrides": {
       "question_no": {
         "marks": 1.5,
         "reason": "Accepted alternate method"
       }
     }
   }
   ```

5. preserving the existing approval endpoint and response shape;
6. displaying saved override reasons for approved evaluations when available;
7. preserving UX-A trust metadata display;
8. producing a Batch UX-B certification report.

This batch is a frontend workflow hardening slice.

---

## 4. Authorized repository boundary

### 4.1 Frontend source

Implementation may modify:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`

Implementation may add or modify small display-only/frontend helpers if needed:

- `apps/admin-web/src/lib/aei-evaluation-display.ts`

Any helper change must remain frontend-only and must not introduce API calls,
global state management, new routes, backend coupling, or source-of-truth
decisions.

### 4.2 Frontend tests / browser proof

Implementation may add or modify focused validation artifacts:

- `apps/admin-web/e2e-aei-teacher-evaluation-ux-b.cjs`
- existing admin-web smoke/e2e scripts only if needed for the proof harness.

### 4.3 Documentation

Implementation may add:

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md`

Post-publication status updates, if any, must be committed separately:

- `docs/STATUS.md`

### 4.4 Protected areas

The following must not be changed without separate ARM authorization:

- backend evaluation service;
- backend evaluation endpoints;
- backend schemas;
- database models;
- Alembic migrations;
- AEI/EUI runtime services;
- AEI/EUI architecture documents;
- public marketing pages;
- student/parent/principal portals;
- billing/payment code;
- RBAC/authz logic.

---

## 5. Runtime constraints

Batch UX-B must be:

- frontend-only;
- deterministic;
- tenant-safe;
- compatible with the existing approval API;
- tolerant of existing approved evaluations that have no reason;
- non-authoritative;
- rollbackable by reverting the frontend/docs commit.

The UI may guide teacher review, but it must not change who owns the final
academic decision.

---

## 6. Data and API constraints

This batch must not introduce:

- database schema changes;
- migrations;
- new API endpoints;
- breaking API changes;
- backend validation changes;
- backend feature-flag enablement;
- source-of-truth switching;
- evidence-ledger behavior changes.

The existing `EvaluationApprove.teacher_overrides` payload already supports
`reason`. UX-B should use that shape rather than changing the contract.

The page must continue to work when:

- an evaluation has no teacher overrides;
- an approved evaluation has override marks but no stored reason;
- the teacher changes marks back to the original suggestion;
- an evaluation has legacy suggestion shapes without AEI metadata;
- the evaluation is already approved.

---

## 7. Teacher-facing workflow requirements

### 7.1 Editing final marks

When the teacher changes a final mark away from `marks_suggested`, the row
should reveal a reason input.

Recommended label:

```text
Reason for change
```

Recommended placeholder:

```text
Example: Accepted alternate method
```

### 7.2 Approval validation

When a teacher attempts to approve with changed marks and a missing reason, the
UI should block approval and show a calm, specific error.

Recommended copy:

```text
Add a reason for each changed mark before approving.
```

The UI must not block approval when marks match the AI suggestion.

### 7.3 Saved override display

For approved evaluations, saved override reasons should be visible near the
final mark or feedback area where available.

If a legacy approved evaluation has an override without a reason, show neutral
fallback copy rather than alarming the teacher.

Recommended fallback:

```text
Reason not recorded.
```

### 7.4 No hidden generic reason

UX-B should stop submitting `"Teacher adjustment"` as the automatic reason for
changed marks.

If a reason is required, it should come from the teacher.

---

## 8. Explicit exclusions

Batch UX-B does not authorize:

- marks calculation changes;
- automatic review routing changes;
- approval endpoint changes;
- backend validation changes;
- evidence-ledger changes;
- database schema changes;
- API route changes;
- source switching to EUI;
- Phase 7F source adoption;
- Trust Report display;
- language/OCR assist panel expansion;
- visual/science assist panel expansion;
- student/parent/principal visibility changes;
- production feature-flag enablement;
- public product claim changes;
- new OCR/vision/LLM behavior;
- a new review-state machine;
- notification workflows.

Evidence panel expansion belongs to Batch UX-C.

Language/OCR and visual/science detailed assist panels belong to Batch UX-D.

---

## 9. Feature-flag posture

No new backend feature flag is authorized.

No AEI v1.0 feature flag may be enabled by this batch.

No frontend display flag is required by this contract. If implementation
discovers a flag is necessary, stop and request contract amendment before adding
it.

---

## 10. Observability

No new backend observability is authorized.

Frontend/browser proof should capture:

- changed mark reveals reason input;
- approval is blocked when a changed mark has no reason;
- approval remains available when marks are unchanged;
- saved override reason renders for approved evaluations when present;
- no console errors on the covered path.

No product analytics, telemetry pipeline, or tracking event is authorized.

---

## 11. Golden Harness and test requirements

Golden Harness additions are not required for UX-B unless implementation changes
AEI metadata interpretation.

Required validation should include:

- focused frontend build/type validation;
- focused helper/page validation where practical;
- browser or e2e proof for the teacher override reason path when environment is
  available;
- regression proof that legacy evaluations without override reasons still
  render;
- regression proof that approval payload shape remains unchanged;
- `git diff --check`.

If backend files are touched, implementation must stop for ARM review unless
the change is explicitly authorized by contract amendment.

---

## 12. Rollback proof

Rollback for UX-B must be simple:

```text
Revert the UX-B frontend/docs commit.
```

No data rollback is required because UX-B must not introduce:

- migrations;
- persisted schema changes;
- backend behavior changes;
- new approval API contracts;
- marks calculation changes.

---

## 13. Certification deliverable

Implementation must produce:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md
```

The report must include:

- scope implemented;
- repository files changed;
- explicit exclusions preserved;
- user-visible changes;
- approval payload behavior;
- validation commands and results;
- browser proof evidence or documented blocker;
- rollback proof;
- recommendation for ARM review.

---

## 14. Exit criteria

Batch UX-B is complete only when:

- changed marks require a teacher-authored reason before approval;
- unchanged marks do not require a reason;
- the existing approval endpoint shape is preserved;
- saved override reasons render when present;
- legacy approved evaluations without reasons still render safely;
- no backend/API/schema/marks/routing/ledger/source behavior changes were
  introduced;
- focused validation passes;
- browser proof passes or clearly documents environmental blockers;
- certification report is complete;
- implementation is accepted by ARM before commit;
- commit/tag/publication occur only after ARM acceptance.

---

## 15. Recommended commit and tag

If implementation is later accepted after code review:

```text
Commit: feat(aei): add teacher override reason workflow
Tag: aei-v1-teacher-evaluation-ux-b-override-reasons-certified
```

---

## 16. ARM review decision

**Contract status:** Accepted

Recommended decision:

```text
Accept the contract and authorize Batch UX-B implementation only.
Implementation must remain within this contract.
Implementation outside Batch UX-B is not authorized by this contract.
```
