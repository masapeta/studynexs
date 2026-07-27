# AEI v1.0 Teacher Evaluation Experience - Batch UX-A Implementation Authorization Contract

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-A - Review-table trust metadata display
- **Authorization ID:** AEI-TEACHER-UX-A-AUTH-001
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized for Batch UX-A only
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize, if accepted, the first narrow product-facing AEI v1.0 teacher
experience implementation batch.

Batch UX-A should make existing certified AEI metadata easier for teachers to
see and understand inside the existing answer-sheet evaluation review table.

The batch must not change evaluation behavior, marks, approval rules, evidence
ledger semantics, source-of-truth posture, or product claims.

The guiding product question is:

> Can a teacher understand which AI suggestions are supported, uncertain, or
> review-required without changing how marks are calculated or approved?

---

## 2. Implementation scope

If this contract is accepted, implementation is authorized only for:

1. displaying existing suggestion-level trust metadata in the teacher evaluation
   review table;
2. showing safe badges/labels for:
   - confidence;
   - method;
   - capability mode;
   - manual-review requirement;
   - manual-review reason;
   - Maths normalization/equivalence metadata when present;
3. adding a compact trust summary above the review table derived only from the
   already-returned evaluation payload;
4. using safe fallback text when AEI metadata is absent;
5. preserving the existing upload, polling, suggestion, override, and approval
   flows;
6. adding focused frontend/browser validation for the display behavior;
7. producing a Batch UX-A certification report.

This batch is presentation-only.

---

## 3. Authorized repository boundary

### 3.1 Frontend source

Implementation may modify:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`

Implementation may add small display-only helpers/components if the evaluation
page becomes too large:

- `apps/admin-web/src/components/teaching/AeiEvaluationTrustSummary.tsx`
- `apps/admin-web/src/components/teaching/AeiSuggestionTrustBadges.tsx`
- `apps/admin-web/src/lib/aei-evaluation-display.ts`

Helpers/components must remain display-only and must not introduce API calls,
global state management, new routes, or source-of-truth decisions.

### 3.2 Frontend tests / browser proof

Implementation may add or modify focused validation artifacts:

- `apps/admin-web/e2e-aei-teacher-evaluation-ux-a.cjs`
- existing admin-web smoke/e2e scripts only if needed for the proof harness.

### 3.3 Documentation

Implementation may add:

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md`

Post-publication status updates, if any, must be committed separately:

- `docs/STATUS.md`

### 3.4 Protected areas

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

## 4. Runtime constraints

Batch UX-A must be:

- display-only;
- deterministic;
- tenant-safe;
- tolerant of missing metadata;
- compatible with existing API responses;
- non-authoritative;
- rollbackable by reverting the frontend/docs commit.

The UI must not infer correctness from unsupported metadata. It may only display
what the evaluation payload already contains.

---

## 5. Data and API constraints

This batch must not introduce:

- database schema changes;
- migrations;
- new API endpoints;
- breaking API changes;
- response-shape requirements that older evaluations cannot satisfy;
- backend feature-flag enablement;
- source-of-truth switching;
- evidence-ledger behavior changes.

The page must continue to work when:

- AEI metadata is absent;
- all AEI v1.0 flags are disabled;
- an evaluation has legacy suggestion shapes;
- an evaluation is already approved;
- citation/evidence metadata is absent.

---

## 6. Teacher-facing display requirements

### 6.1 Trust summary

The review page should show a compact summary derived from `ai_suggestions`.

Candidate summary fields:

- number of questions with confidence;
- number of questions requiring teacher review;
- number of low-confidence suggestions;
- number of assist/checklist/manual-review capability suggestions;
- number of deterministic/supported suggestions where metadata indicates that.

The summary must avoid claiming evaluation quality when metadata is absent.

### 6.2 Per-question badges

Each suggestion row may show badges such as:

- `Confidence 92%`;
- `Supported`;
- `Assist only`;
- `Checklist only`;
- `Teacher review required`;
- `Low confidence`;
- `Maths equivalence`;
- `OCR needs confirmation`.

Badges must use cautious language aligned to the supported scope matrix.

### 6.3 Manual-review explanation

When `manual_review_required` or `manual_review_reason` exists, the row should
make that visible to the teacher.

Teacher-facing wording should be calm and direct:

```text
Teacher review required: OCR confidence is low.
```

Avoid:

```text
AI failed.
```

### 6.4 Maths evidence display

When present, Maths metadata may display:

- normalized answer;
- matched acceptable answer;
- interpreted/matched value;
- unit/tolerance result.

The UI must not invent Maths evidence from raw answers.

### 6.5 Missing metadata fallback

If AEI metadata is absent, show either nothing or a neutral legacy-state label.

Do not show warnings solely because older evaluations do not contain AEI
metadata.

---

## 7. Explicit exclusions

Batch UX-A does not authorize:

- marks calculation changes;
- automatic review routing changes;
- approval endpoint changes;
- teacher override reason workflow changes;
- evidence-ledger changes;
- backend code changes;
- schema/API/UI route changes beyond the existing evaluation page display;
- source switching to EUI;
- Phase 7F source adoption;
- Trust Report display;
- language/OCR assist panel expansion beyond existing metadata badges;
- visual/science assist panel expansion beyond existing metadata badges;
- student/parent/principal visibility changes;
- production feature-flag enablement;
- public product claim changes;
- new OCR/vision/LLM behavior.

Override reason capture belongs to Batch UX-B, not UX-A.

Evidence panel expansion belongs to Batch UX-C.

Language/OCR and visual/science detailed assist panels belong to Batch UX-D.

---

## 8. Feature-flag posture

No new backend feature flag is authorized.

No AEI v1.0 feature flag may be enabled by this batch.

The frontend must behave safely regardless of whether the backend environment
has AEI metadata enabled.

If implementation discovers that a frontend display flag is necessary, stop and
request contract amendment before adding it.

---

## 9. Observability

No new backend observability is authorized.

Frontend/browser proof should capture:

- page loads;
- suggested evaluation renders;
- trust summary renders when metadata exists;
- page remains usable when metadata is absent;
- approval flow remains available;
- no console errors on the covered path.

No product analytics, telemetry pipeline, or tracking event is authorized.

---

## 10. Golden Harness and test requirements

Golden Harness additions are optional for UX-A unless implementation changes the
interpretation of AEI metadata.

Required validation should include:

- focused UI/helper tests if helper functions are added;
- browser or e2e proof for the teacher evaluation page;
- admin-web build validation where practical;
- regression proof that legacy evaluations without AEI metadata still render;
- regression proof that approved evaluations still render;
- `git diff --check`.

If backend files are touched despite the intended frontend-only scope, the
implementation must stop for ARM review unless the change is strictly docs/test
and still within this contract.

---

## 11. Rollback proof

Rollback for UX-A must be simple:

```text
Revert the frontend/docs commit.
```

Because UX-A must not change backend behavior, database schema, API contracts,
or marks persistence, rollback must not require data migration.

The certification report must explicitly confirm this.

---

## 12. Certification deliverable

Implementation must produce:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md
```

The report must include:

- scope implemented;
- repository files changed;
- explicit exclusions preserved;
- user-visible changes;
- supported-scope wording review;
- validation commands and results;
- browser proof evidence;
- rollback proof;
- recommendation for ARM review.

---

## 13. Exit criteria

Batch UX-A is complete only when:

- existing teacher evaluation page displays trust metadata when present;
- missing AEI metadata does not break or alarm the UI;
- no marks, approval, routing, ledger, API, schema, or source behavior changes
  were introduced;
- teacher-facing language aligns with the supported scope matrix;
- focused validation passes;
- browser proof passes or clearly documents environmental blockers;
- certification report is complete;
- implementation is accepted by ARM before commit;
- commit/tag/publication occur only after ARM acceptance.

---

## 14. Recommended commit and tag

If implementation is later accepted after code review:

```text
Commit: feat(aei): add teacher evaluation trust metadata display
Tag: aei-v1-teacher-evaluation-ux-a-trust-display-certified
```

---

## 15. ARM review decision

**Contract status:** Accepted

ARM decision:

```text
Accept the contract and authorize Batch UX-A implementation only.
Implementation must remain within this contract.
```

Implementation outside Batch UX-A is not authorized by this contract.
