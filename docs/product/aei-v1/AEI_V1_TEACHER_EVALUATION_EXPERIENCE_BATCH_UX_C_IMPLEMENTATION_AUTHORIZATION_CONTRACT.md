# AEI v1.0 Teacher Evaluation Experience - Batch UX-C Implementation Authorization Contract

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-C - Evidence and approved-decision panel
- **Classification:** Implementation authorization contract
- **Authorization ID:** AEI-TEACHER-UX-C-AUTH-001
- **Status:** Accepted
- **Implementation:** Authorized for Batch UX-C only
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **UX-A baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md)
- **UX-B baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize the third narrow product-facing AEI v1.0 teacher evaluation
experience implementation batch.

Batch UX-C should make the existing evidence chain and approved-decision posture
understandable to teachers without changing evidence persistence, approval
behavior, marks, routing, APIs, or downstream consumers.

The guiding product question is:

> Can a teacher clearly see the difference between an unapproved AI suggestion
> and teacher-approved evidence that is safe for downstream learning
> intelligence?

---

## 2. Implementation scope

Implementation is authorized only for:

1. improving the existing evidence strip/panel on the teacher evaluation page;
2. displaying draft-vs-approved evidence posture;
3. displaying original AI suggestion versus final teacher decision where
   existing response data already contains it;
4. displaying approved-evidence status after teacher approval where existing
   `evidence_ledger` metadata is present;
5. making grounded/citation status clearer;
6. preserving UX-A trust metadata display;
7. preserving UX-B override reason workflow;
8. producing a Batch UX-C certification report.

This batch is a frontend display and explanation slice.

---

## 3. Authorized repository boundary

### 3.1 Frontend source

Implementation may modify:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`

Implementation may add or modify small display-only/frontend helpers if needed:

- `apps/admin-web/src/lib/aei-evaluation-display.ts`

Any helper change must remain frontend-only and must not introduce API calls,
global state management, new routes, backend coupling, source-of-truth
decisions, or product analytics.

### 3.2 Documentation

Implementation may add:

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md`

Post-publication status updates, if any, must be committed separately:

- `docs/STATUS.md`

### 3.3 Protected areas

The following must not be changed without separate ARM authorization:

- backend evaluation service;
- backend evaluation endpoints;
- backend schemas;
- database models;
- Alembic migrations;
- AEI/EUI runtime services;
- evidence-ledger generation logic;
- public marketing pages;
- student/parent/principal portals;
- billing/payment code;
- RBAC/authz logic.

---

## 4. Runtime constraints

Batch UX-C must be:

- frontend-only;
- deterministic;
- tenant-safe;
- read-only against existing response metadata;
- tolerant of missing `evidence_ledger` metadata;
- tolerant of evaluations created before AEI v1.0 evidence metadata existed;
- non-authoritative;
- rollbackable by reverting the frontend/docs commit.

The UI may explain evidence posture, but it must not promote an unapproved AI
suggestion into approved evidence.

---

## 5. Data and API constraints

This batch must not introduce:

- database schema changes;
- migrations;
- new API endpoints;
- breaking API changes;
- backend validation changes;
- backend feature-flag enablement;
- evidence-ledger persistence changes;
- source-of-truth switching;
- downstream consumer migration.

UX-C must consume only fields already returned by the existing evaluation
response, including:

- `status`;
- `approved_by`;
- `approved_at`;
- `ai_suggestions`;
- `teacher_overrides`;
- `evidence_ledger`;
- `curriculum_pack_id`;
- `question_paper_id`;
- `citation_ids`;
- `evaluation_grounded`.

---

## 6. Teacher-facing workflow requirements

### 6.1 Evidence posture

Suggested evaluations should communicate:

```text
Draft AI suggestions - not approved for downstream use yet.
```

Approved evaluations should communicate:

```text
Teacher-approved evidence - safe for downstream learning intelligence.
```

### 6.2 Evidence chain clarity

The UI should make these existing facts easier to inspect:

- CurriculumPack reference;
- question paper reference;
- grounded / needs citation review posture;
- citation count;
- whether the downstream source of truth is `teacher_decision`.

### 6.3 Approved-decision comparison

Where existing metadata is available, the UI should show:

- original AI-suggested marks;
- final teacher-approved marks;
- whether an override was applied;
- override reason where available;
- manual-review requirement where available.

The comparison is explanatory only and must not change marks.

---

## 7. Explicit exclusions

Batch UX-C does not authorize:

- marks calculation changes;
- automatic review routing changes;
- approval endpoint changes;
- backend validation changes;
- evidence-ledger generation changes;
- evidence-ledger schema changes;
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
- notification workflows;
- analytics dashboards.

Language/OCR and visual/science detailed assist panels belong to Batch UX-D.

---

## 8. Feature-flag posture

No new backend feature flag is authorized.

No AEI v1.0 feature flag may be enabled by this batch.

No frontend display flag is required by this contract. If implementation
discovers a flag is necessary, stop and request contract amendment before adding
it.

---

## 9. Observability

No new backend observability is authorized.

Frontend/browser proof should capture:

- evidence panel renders for suggested evaluations;
- evidence panel renders for approved evaluations;
- approved-evidence status is visibly distinct from draft AI suggestions;
- original suggestion versus final teacher decision renders when present;
- legacy/missing evidence metadata renders safely;
- no console errors on the covered path.

No product analytics, telemetry pipeline, or tracking event is authorized.

---

## 10. Golden Harness and test requirements

Golden Harness additions are not required for UX-C unless implementation changes
AEI metadata interpretation.

Required validation should include:

- focused frontend build/type validation;
- focused helper/page validation where practical;
- browser or e2e proof for the teacher evidence panel path when environment is
  available;
- regression proof that legacy evaluations without evidence metadata still
  render;
- `git diff --check`.

If backend files are touched, implementation must stop for ARM review unless
the change is explicitly authorized by contract amendment.

---

## 11. Rollback proof

Rollback for UX-C must be simple:

```text
Revert the UX-C frontend/docs commit.
```

No data rollback is required because UX-C must not introduce migrations, schema
changes, endpoint changes, evidence-ledger generation changes, source switches,
marks calculation changes, or downstream consumer migrations.

---

## 12. Certification deliverable

Implementation must produce:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md
```

The report must include:

- scope implemented;
- repository files changed;
- explicit exclusions preserved;
- user-visible changes;
- evidence metadata read behavior;
- validation commands and results;
- browser proof evidence or documented blocker;
- rollback proof;
- recommendation for ARM review.

---

## 13. Exit criteria

Batch UX-C is complete only when:

- draft AI suggestions are visibly distinct from approved evidence;
- approved evaluations communicate teacher-approved downstream posture;
- existing evidence chain metadata is clearer to teachers;
- original AI suggestion versus final teacher decision renders when existing
  metadata is present;
- legacy/missing evidence metadata renders safely;
- UX-A trust metadata display remains intact;
- UX-B override reason workflow remains intact;
- no backend/API/schema/marks/routing/ledger/source behavior changes were
  introduced;
- focused validation passes;
- browser proof passes or clearly documents environmental blockers;
- certification report is complete;
- implementation is accepted by ARM before commit;
- commit/tag/publication occur only after explicit ARM approval.

---

## 14. Recommended commit and tag

If implementation is later accepted after code review:

```text
Commit: feat(aei): add teacher evidence decision panel
Tag: aei-v1-teacher-evaluation-ux-c-evidence-decision-certified
```

---

## 15. ARM review decision

**Contract status:** Accepted

ARM decision:

```text
Accept the contract and authorize Batch UX-C implementation only.
Implementation must remain within this contract.
Implementation outside Batch UX-C is not authorized by this contract.
```
