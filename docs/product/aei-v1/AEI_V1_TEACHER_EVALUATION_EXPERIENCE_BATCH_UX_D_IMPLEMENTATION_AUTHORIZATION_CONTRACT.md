# AEI v1.0 Teacher Evaluation Experience - Batch UX-D Implementation Authorization Contract

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-D - Supported-scope assist panels
- **Classification:** Implementation authorization contract
- **Authorization ID:** AEI-TEACHER-UX-D-AUTH-001
- **Status:** Accepted
- **Implementation:** Authorized for Batch UX-D only
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_DESIGN_BRIEF.md)
- **Teacher evaluation experience baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **UX-A baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md)
- **UX-B baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md)
- **UX-C baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize a narrow, product-facing UX-D implementation slice that makes
language/OCR and visual/science assist metadata inspectable on the existing
teacher evaluation page.

The guiding product question is:

> Can a teacher inspect supported-scope assist evidence clearly while the
> product remains honest that teacher confirmation is required?

This batch is intended to complete the teacher-visible assist/checklist
inspection layer started by UX-A, UX-B, and UX-C.

---

## 2. Implementation scope

Implementation is authorized only for:

1. adding display-only language/OCR assist evidence panels to the existing
   teacher evaluation page;
2. adding display-only visual/science assist evidence panels to the existing
   teacher evaluation page;
3. extending the existing frontend display helper to parse teacher-safe assist
   metadata;
4. rendering teacher-confirmation-required posture for assist, checklist,
   manual-review, unsupported, or expansion cases;
5. rendering safe missing/legacy metadata states;
6. preserving UX-A trust badges and summary;
7. preserving UX-B override reason workflow;
8. preserving UX-C evidence and approved-decision panel;
9. producing a Batch UX-D certification report.

This batch is frontend display-only. It may consume existing metadata already
present in evaluation responses. It may not create or infer new academic
evidence.

---

## 3. Authorized repository boundary

### 3.1 Frontend source

Implementation may modify:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`
- `apps/admin-web/src/lib/aei-evaluation-display.ts`

Implementation may add small frontend-only helper functions inside the existing
helper file if needed.

Any helper change must remain:

- display-only;
- deterministic;
- API-call free;
- tenant-safe;
- tolerant of missing metadata;
- independent of global state management.

### 3.2 Tests / frontend validation helpers

Implementation may add or modify focused frontend tests or lightweight helper
tests only if existing project structure supports them without adding a new
test framework.

If no suitable frontend test harness exists for this surface, certification may
rely on build/type validation, source inspection, and browser proof or a
documented browser-proof blocker.

### 3.3 Documentation

Implementation must add:

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_CERTIFICATION_REPORT.md`

Post-publication status updates, if any, must be committed separately:

- `docs/STATUS.md`

### 3.4 Protected areas

The following must not be changed without separate ARM authorization:

- backend evaluation services;
- backend evaluation endpoints;
- backend schemas;
- database models;
- Alembic migrations;
- AEI runtime services;
- EUI runtime services;
- evidence-ledger generation logic;
- source-readiness/source-adoption services;
- mastery spine services;
- student/parent/principal portals;
- public marketing pages;
- billing/payment code;
- RBAC/authz logic;
- notification workflows.

---

## 4. Data and metadata constraints

UX-D may read only existing teacher-safe response metadata, including:

- `ai_suggestions`;
- `answer_language`;
- `detected_script`;
- `code_mixed`;
- `language_confidence`;
- `ocr_confidence`;
- `answer_input_source`;
- `language_ocr_capability_mode`;
- `visual_science_capability_mode`;
- `visual_science_review_required`;
- `visual_science_reasoning_type`;
- `visual_type`;
- `scientific_type`;
- `assist_only`;
- `checklist_only`;
- `manual_review_required`;
- `manual_review_reason`;
- `aei_v1_language_ocr_assist`;
- `aei_v1_visual_science_assist`;
- existing `evidence_ledger` metadata already consumed by UX-C.

UX-D may display nested checklist evidence from
`aei_v1_visual_science_assist` only as observations for teacher review.

UX-D must not:

- request new API fields;
- change request payloads;
- change response contracts;
- change approval payload shape;
- alter marks persistence;
- alter evidence-ledger persistence;
- treat assist/checklist evidence as authoritative.

---

## 5. Teacher-facing workflow requirements

### 5.1 Assist panel visibility

The assist panel should render only when relevant metadata exists.

Relevant metadata includes:

- language/OCR assist metadata;
- visual/science assist metadata;
- assist-only or checklist-only posture;
- visual/science review-required posture;
- language/OCR capability mode.

Ordinary deterministic Maths-only or legacy objective rows should not become
cluttered with empty assist panels.

### 5.2 Language/OCR assist display

The UI should show, when present:

- source;
- detected language;
- detected script;
- code-mixed posture;
- language confidence;
- OCR confidence;
- capability posture;
- review reason.

Required teacher-facing boundary:

```text
OCR/language assist does not certify marks. Confirm the answer text before
approving.
```

### 5.3 Visual/science assist display

The UI should show, when present:

- capability posture;
- reasoning type;
- visual type;
- scientific type;
- assist-only / checklist-only posture;
- teacher-review-required posture;
- checklist observations;
- review reason.

Required teacher-facing boundary:

```text
Checklist observations support your review. They do not automatically award
marks.
```

### 5.4 Legacy and missing metadata behavior

Missing or legacy metadata must be treated as absence, not failure.

UX-D must not invent evidence, infer language, infer visual type, or create
capability claims in the frontend.

---

## 6. Feature-flag posture

No new backend feature flag is authorized.

No AEI v1.0 feature flag may be enabled by this batch.

These source defaults remain unchanged:

```text
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
```

UX-D may display metadata only when metadata is already present in the response.

No frontend display flag is authorized by this contract. If implementation
discovers a display flag is necessary, stop and request contract amendment
before adding it.

---

## 7. Runtime constraints

Batch UX-D must be:

- frontend-only;
- display-only;
- deterministic;
- read-only against existing response metadata;
- tolerant of missing/legacy metadata;
- accessible and keyboard-safe for any expandable/collapsible UI;
- non-authoritative;
- source-switch free;
- rollbackable by reverting the UX-D frontend/docs commit.

The UI may explain assist evidence, but it must not convert assist/checklist
signals into mark authority.

---

## 8. Explicit exclusions

Batch UX-D does not authorize:

- backend changes;
- database schema changes;
- Alembic migrations;
- API contract changes;
- new public endpoints;
- OCR provider integration;
- handwriting OCR implementation;
- LLM provider changes;
- vision model changes;
- automatic language grading;
- automatic visual/science grading;
- chemistry structure grading;
- graph/map/diagram automatic marks;
- marks calculation changes;
- teacher-review routing changes;
- approval endpoint changes;
- evidence-ledger generation changes;
- evidence-ledger schema changes;
- Trust Report display;
- source-of-truth switching to EUI;
- Phase 7F source adoption;
- Topic-ID / Mastery Spine Phase B;
- parent/student/principal visibility changes;
- production feature-flag enablement;
- public product claim changes;
- product analytics or tracking events;
- notification workflows.

---

## 9. Supported-scope copy review

All teacher-facing copy must align with:

- [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)

Allowed copy examples:

- "Assist only - teacher confirmation required"
- "Checklist only - teacher confirmation required"
- "OCR confidence"
- "Detected language"
- "Teacher review required"
- "Checklist observations"

Forbidden copy examples:

- "Automatically graded diagram"
- "Handwriting reliably corrected"
- "Language answer certified by AI"
- "Map marks awarded by AI"
- "Chemistry structure graded"
- "No teacher review needed" for assist/checklist/manual-review cases

---

## 10. Observability

No backend observability is authorized.

No product analytics or tracking events are authorized.

Browser/manual proof should record:

- language/OCR assist panel renders when metadata exists;
- visual/science assist panel renders when metadata exists;
- missing metadata does not break the page;
- teacher-confirmation-required copy is visible;
- UX-A/B/C surfaces remain intact;
- no console errors on the covered path.

---

## 11. Golden Harness and test requirements

No Golden Harness changes are required unless implementation changes metadata
interpretation rules.

Required validation:

- `npm run build` in `apps/admin-web`;
- focused lint/helper validation where practical;
- browser or e2e proof for the teacher evaluation page when environment is
  available;
- source review proving no backend/API/schema files changed;
- `git diff --check`.

If backend files are touched, implementation must stop for ARM review unless
this contract is amended.

---

## 12. Rollback proof

Rollback is simple:

```text
Revert the UX-D frontend/docs commit.
```

No data rollback is required because UX-D must not introduce migrations,
schema changes, endpoint changes, evidence-ledger generation changes, source
switches, marks calculation changes, or downstream consumer migrations.

---

## 13. Certification deliverable

Implementation must produce:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_CERTIFICATION_REPORT.md
```

The report must include:

- scope implemented;
- repository files changed;
- explicit exclusions preserved;
- user-visible changes;
- supported-scope copy review;
- language/OCR metadata read behavior;
- visual/science metadata read behavior;
- validation commands and results;
- browser proof evidence or documented blocker;
- rollback proof;
- recommendation for ARM review.

---

## 14. Exit criteria

Batch UX-D is complete only when:

- language/OCR assist metadata is inspectable when present;
- visual/science assist metadata is inspectable when present;
- assist/checklist/manual-review posture is visibly non-authoritative;
- teacher confirmation remains clearly required;
- missing or legacy metadata renders safely;
- UX-A trust metadata display remains intact;
- UX-B override reason workflow remains intact;
- UX-C evidence and approved-decision panel remains intact;
- no backend/API/schema/marks/routing/ledger/source behavior changes were
  introduced;
- focused validation passes;
- browser proof passes or clearly documents environmental blockers;
- certification report is complete;
- implementation is accepted by ARM before commit;
- commit/tag/publication occur only after explicit ARM approval.

---

## 15. Recommended commit and tag

If implementation is later accepted after code review:

```text
Commit: feat(aei): add teacher assist evidence panels
Tag: aei-v1-teacher-evaluation-ux-d-assist-panels-certified
```

---

## 16. ARM review decision

**Contract status:** Accepted

ARM decision:

```text
Accept the UX-D implementation authorization contract.
Authorize Batch UX-D implementation only.
Implementation must remain within this contract.
Implementation outside Batch UX-D is not authorized by this contract.
```
