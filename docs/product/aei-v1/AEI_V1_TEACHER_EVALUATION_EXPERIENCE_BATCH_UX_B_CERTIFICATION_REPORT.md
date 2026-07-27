# AEI v1.0 Teacher Evaluation Experience - Batch UX-B Certification Report

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-B - Override reason workflow
- **Status:** Certified for ARM review
- **Date:** 2026-07-28
- **Authorization:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **Recommended commit:** `feat(aei): add teacher override reason workflow`
- **Recommended tag:** `aei-v1-teacher-evaluation-ux-b-override-reasons-certified`

---

## 1. Certification decision

**Result:** PASS

Batch UX-B implements teacher-authored override reason capture on the existing
teacher evaluation page without changing backend contracts, marks calculation,
approval authority, routing, persistence schema, evidence-ledger behavior, or
AEI/EUI source-of-truth posture.

The implementation is suitable for commit, tag, and publication after ARM
acceptance.

---

## 2. Scope implemented

Implemented:

- per-question override reason state on the existing teacher evaluation page;
- reason input displayed only when final marks differ from AI-suggested marks;
- approval blocked when changed marks have no teacher-authored reason;
- approval payload continues to use the existing `teacher_overrides` shape;
- saved override reasons displayed for approved evaluations;
- safe fallback for legacy approved overrides without stored reasons;
- removal of automatic `"Teacher adjustment"` submission from runtime code;
- UX-A trust metadata display preserved.

---

## 3. Repository files changed

Implementation:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`

Governance / certification:

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`
- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md`

No backend, schema, API, migration, AEI/EUI runtime, evidence-ledger, or product
claim files were changed.

---

## 4. Explicit exclusions preserved

Verified preserved:

- no marks calculation changes;
- no automatic review-routing changes;
- no approval endpoint changes;
- no backend validation changes;
- no evidence-ledger changes;
- no database schema changes;
- no API route changes;
- no source switching to EUI;
- no Trust Report display;
- no language/OCR assist panel expansion;
- no visual/science assist panel expansion;
- no student/parent/principal visibility changes;
- no new OCR, vision, or LLM behavior;
- no new review-state machine;
- no notification workflow.

---

## 5. User-visible behavior

For suggested evaluations:

1. the teacher can continue editing final marks;
2. when a final mark changes from the AI suggestion, the row displays
   **Reason for change**;
3. approval is blocked until every changed mark has a non-empty reason;
4. unchanged marks require no reason.

For approved evaluations:

1. stored override reasons render near final marks;
2. legacy overrides without reasons render neutral fallback copy:
   `Reason not recorded.`

---

## 6. Approval payload behavior

Payload shape remains unchanged:

```json
{
  "teacher_overrides": {
    "1": {
      "marks": 1.5,
      "reason": "Accepted alternate method"
    }
  }
}
```

Runtime no longer submits the generic automatic reason:

```text
Teacher adjustment
```

Changed marks must use teacher-authored reason text.

---

## 7. Validation evidence

Commands run:

```powershell
git diff --check
```

Result: PASS

```powershell
npm run build
```

Working directory: `apps/admin-web`

Result: PASS

The admin-web production build completed successfully, including TypeScript.

```powershell
npx eslint "src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx"
```

Working directory: `apps/admin-web`

Result: FAIL due to pre-existing page lint debt:

- existing `@typescript-eslint/no-explicit-any` usage in the page;
- existing `react-hooks/set-state-in-effect` finding.

UX-B initially introduced helper-level `any` usage during implementation; those
new helper lint findings were removed. The remaining focused lint failures are
pre-existing page-level debt and are not introduced by this batch.

---

## 8. Browser proof

Automated browser proof was not executed in this environment.

Covered through deterministic frontend validation:

- build/type validation;
- focused source inspection;
- approval payload shape review;
- state/render logic review for changed marks, missing reasons, saved reasons,
  unchanged marks, and legacy no-reason overrides.

Recommended manual browser proof before broad staff enablement:

1. open an exam evaluation with suggested marks;
2. change Q1 final marks;
3. verify reason input appears;
4. attempt approval with missing reason and verify blocking error;
5. add reason and approve;
6. reload approved evaluation and verify saved reason renders;
7. verify unchanged marks approve without reason.

---

## 9. Rollback proof

Rollback is simple:

```text
Revert the UX-B frontend/docs commit.
```

No data rollback is required because the batch introduces no migrations, schema
changes, endpoint changes, source switches, marks calculation changes, or
evidence-ledger behavior changes.

---

## 10. Risks and follow-ups

Known non-blocking risk:

- the touched page still has existing lint debt unrelated to UX-B. A future
  focused cleanup should replace broad `any` usage and address the existing
  effect lint finding as a separate refactor.

Future UX batches:

- Batch UX-C should expand evidence / approved-decision panel surfaces.
- Batch UX-D should handle language/OCR and visual/science assist panels within
  supported scope.

---

## 11. ARM recommendation

**Recommendation:** ACCEPT

Batch UX-B satisfies the accepted authorization contract and may proceed to:

1. commit;
2. annotated certification tag;
3. publication;
4. separate post-publication `docs/STATUS.md` update.
