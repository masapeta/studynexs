# AEI v1.0 Teacher Evaluation Experience - Batch UX-E Design Brief

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-E - Final teacher evaluation experience certification
- **Classification:** Product-facing design brief
- **Status:** Accepted
- **Implementation:** Not authorized by this document
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **UX-A baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md)
- **UX-B baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md)
- **UX-C baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md)
- **UX-D baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_CERTIFICATION_REPORT.md)
- **Activation / Trust baseline:** [`./AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md`](./AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

UX-A through UX-D made AEI v1.0 visible in the teacher evaluation page:

- UX-A exposed trust metadata and teacher-review guidance.
- UX-B captured teacher-authored override reasons.
- UX-C separated draft AI suggestions from teacher-approved evidence.
- UX-D surfaced supported-scope language/OCR and visual/science assist evidence.
- The follow-up lint cleanup removed the pre-existing focused page lint blocker.

Batch UX-E should now certify the end-to-end teacher evaluation experience as a
school-visible workflow inside the declared supported scope.

The product question is:

> Can a teacher complete the supported evaluation loop with clear trust signals,
> explicit human authority, approved evidence, and no unsupported capability
> claims?

UX-E is primarily a certification/proof gate. It should not invent a new
feature surface unless implementation review discovers a small product-trust
bug that blocks certification and ARM explicitly authorizes the fix.

This document defines the design baseline only. It does not authorize code,
schema, API, UI, feature-flag, rollout, or product-claim changes.

---

## 2. Product outcome

After UX-E, StudyNexs should be able to state:

```text
The teacher evaluation experience is certified for AEI v1.0 supported-scope use.
```

That means the teacher can:

1. open the existing teacher evaluation page;
2. choose a student;
3. upload an answer sheet or enter answers manually;
4. run evaluation;
5. inspect AI suggestions as draft recommendations;
6. see confidence, capability, manual-review, and method signals;
7. inspect Maths equivalence evidence when available;
8. inspect language/OCR assist evidence when available;
9. inspect visual/science assist evidence when available;
10. acknowledge manual-review uncertainty when required;
11. change marks with teacher-authored override reasons;
12. approve final marks;
13. distinguish teacher-approved evidence from draft AI output.

The final teacher-facing message should remain:

```text
AI recommends. Teacher decides. Evidence explains.
```

---

## 3. Certification principle

UX-E should certify the whole teacher trust loop, not just isolated components.

```text
Input
  |
  v
AI suggestion metadata
  |
  v
Teacher trust display
  |
  v
Manual review / override reason
  |
  v
Teacher approval
  |
  v
Approved evidence posture
```

The certification must prove that unsupported, low-confidence, assist-only, or
checklist-only signals cannot look like authoritative marks.

---

## 4. Existing surfaces to reuse

### 4.1 Canonical teacher route

Reuse the existing teacher evaluation route:

```text
apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx
```

Do not create a second teacher evaluation page.

### 4.2 Existing display helper

Reuse the teacher-safe AEI display helper:

```text
apps/admin-web/src/lib/aei-evaluation-display.ts
```

UX-E should treat this helper as the display contract for AEI suggestion
metadata unless the implementation authorization contract explicitly permits a
targeted improvement.

### 4.3 Existing backend behavior

UX-E should not require backend changes. It should certify the experience using
the already-published AEI v1.0 and Activation / Trust surfaces:

- `ai_suggestions`;
- `teacher_overrides`;
- `manual_review_acknowledgements`;
- `evidence_ledger`;
- approved-evidence metadata;
- existing evaluation approval flow.

If end-to-end proof cannot be completed because backend metadata is absent in a
supported scenario, the implementation should stop and request a separate
backend authorization rather than expanding UX-E implicitly.

---

## 5. Certification scenarios

UX-E should validate a representative supported-scope teacher workflow matrix.

### 5.1 Legacy / no AEI metadata

Purpose:

Ensure existing evaluations without AEI metadata remain usable and calmly
reviewable.

Expected behavior:

- legacy suggestion format message appears where appropriate;
- no broken panels;
- no false unsupported/certified claim;
- teacher can still review and approve through the existing flow.

### 5.2 Deterministic Maths supported case

Purpose:

Ensure Maths normalization/equivalence evidence is visible and understandable.

Expected behavior:

- confidence/method/capability badges render;
- normalized answer and matched acceptable answer render when present;
- no manual-review acknowledgement is required for a supported confident case
  unless metadata says otherwise;
- final teacher approval remains required.

### 5.3 Manual review required case

Purpose:

Ensure uncertainty is visible and must be acknowledged when Activation / Trust
requires it.

Expected behavior:

- manual-review badge is visible;
- reason is visible when present;
- acknowledgement checkbox appears for the affected question;
- approval is blocked until acknowledgement is provided when required;
- approval payload preserves the existing contract.

### 5.4 Teacher override case

Purpose:

Ensure teacher authority is explicit and auditable.

Expected behavior:

- changing marks reveals the override reason input;
- approval is blocked if a changed mark has no reason;
- saved override reason is visible after approval;
- original AI suggestion and final teacher decision remain distinguishable.

### 5.5 Approved evidence case

Purpose:

Ensure teacher-approved evidence is visually distinct from draft AI output.

Expected behavior:

- evidence and approval posture panel renders;
- teacher-approved evidence is clearly labeled;
- downstream source of truth is teacher decision when metadata supports it;
- unapproved draft AI suggestions are not presented as downstream evidence.

### 5.6 Language/OCR assist case

Purpose:

Ensure language/OCR support remains assistive and bounded.

Expected behavior:

- language/OCR assist panel renders when metadata exists;
- detected language, script, code-mixed posture, input source, and OCR
  confidence appear when present;
- teacher-confirmation copy is visible;
- no reliable-handwriting or autonomous language-grading claim appears.

### 5.7 Visual/science assist case

Purpose:

Ensure visual/science support remains checklist/assist-only unless separately
certified otherwise.

Expected behavior:

- visual/science assist panel renders when metadata exists;
- checklist or assist-only posture is visible;
- observations render as evidence, not marks authority;
- no autonomous diagram, graph, map, chemistry structure, or science grading
  claim appears.

---

## 6. Browser proof strategy

UX-E should include browser proof wherever the local or staging environment can
support it.

Recommended proof set:

| Proof | Required evidence |
|---|---|
| Page load | Teacher evaluation page renders without runtime error |
| Legacy evaluation | Safe fallback state renders |
| Maths metadata | Trust badges and equivalence evidence render |
| Manual review | Acknowledgement requirement is visible and enforced |
| Override reason | Missing reason blocks approval; provided reason persists |
| Approved evidence | Draft vs approved posture is distinguishable |
| Language/OCR assist | Assist evidence is visible and non-authoritative |
| Visual/science assist | Checklist/assist evidence is visible and non-authoritative |

If a browser proof cannot be run because the environment lacks a running API,
tenant seed, authenticated session, or deterministic fixture, the certification
report must say so explicitly and record what was verified instead.

UX-E should not silently waive browser proof.

---

## 7. Supported-scope copy review

The certification must review teacher-facing copy against the supported scope
matrix.

Allowed posture:

- "AI suggestions are draft only."
- "Teacher review required."
- "Assist only - teacher confirmation required."
- "Checklist observations support your review."
- "Teacher decision is the source of truth."

Forbidden posture:

- "AI corrected the paper."
- "Handwriting OCR is reliable."
- "Diagram grading complete."
- "Science answer certified."
- "No teacher review needed" for uncertain or assist-only cases.
- Any claim that parent/student downstream views may consume unapproved AI
  suggestions.

---

## 8. Runtime and feature-flag posture

UX-E must not enable production capability flags.

The certification should record the posture of relevant flags:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED
AEI_V1_REVIEW_POLICY_ENABLED
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED
AEI_ACTIVATION_TRUST_ENABLED
```

Expected proof:

- flag-off behavior remains safe;
- supported metadata display is additive and tolerant of absence;
- no source-of-truth switch occurs;
- rollback remains code/config revert rather than data repair.

---

## 9. Data/API posture

UX-E should certify existing behavior, not expand contracts.

Preferred posture:

- no new API fields;
- no new endpoint;
- no schema migration;
- no approval payload shape change;
- no evidence-ledger generation change;
- no parent/student/principal consumer change.

If certification discovers that a missing field blocks a trustworthy teacher
experience, the correct outcome is a finding and a later implementation
contract, not hidden expansion inside UX-E.

---

## 10. Explicit non-goals

UX-E is not:

- a new UI feature batch;
- an AEI runtime expansion batch;
- an OCR integration;
- a vision model integration;
- a graph/map/diagram grading project;
- a source-of-truth switch to EUI;
- a Topic-ID / Mastery Spine migration;
- a parent/student visibility change;
- a principal analytics change;
- a public marketing claim update.

---

## 11. Explicit exclusions

Until a UX-E implementation authorization contract states otherwise, UX-E does
not authorize:

- backend changes;
- database schema changes;
- Alembic migrations;
- API contract changes;
- new public endpoints;
- marks calculation changes;
- teacher-review routing changes;
- approval endpoint changes;
- evidence-ledger generation changes;
- parent/student/principal UI changes;
- source-of-truth switching to EUI;
- Phase 7F source adoption;
- Topic-ID / Mastery Spine Phase B;
- production feature-flag enablement;
- public product-claim changes;
- LLM/OCR/vision provider changes.

---

## 12. Expected implementation boundary

A later UX-E implementation authorization contract should likely permit:

- UX-E certification report;
- deterministic browser proof script or documented manual browser-proof steps;
- optional frontend fixture/test data if scoped to proof only;
- focused fixes only if ARM explicitly accepts them as certification blockers.

Likely files:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx
apps/admin-web/src/lib/aei-evaluation-display.ts
```

The implementation authorization contract should decide whether code changes
are allowed at all. If no blocker is found, UX-E may be docs/proof-only.

---

## 13. Testing and certification strategy

Expected validation:

- focused teacher evaluation page lint;
- AEI display helper lint;
- admin-web TypeScript validation;
- admin-web production build;
- browser proof for the teacher evaluation page, or explicit blocker evidence;
- supported-scope copy review;
- no backend/API/schema/marks/routing/source-switch diff;
- `git diff --check`.

Expected certification sections:

1. certification decision;
2. scenario matrix;
3. browser proof evidence;
4. supported-scope copy review;
5. feature-flag posture;
6. API/schema/backend boundary review;
7. known limitations;
8. rollback posture;
9. ARM recommendation.

---

## 14. Acceptance criteria

UX-E design is ready for implementation authorization when ARM agrees that:

- UX-E is a final certification/proof gate, not a new feature batch;
- UX-A/B/C/D behavior must be reviewed together;
- supported-scope copy must be reviewed against the matrix;
- browser proof is required unless explicitly blocked by environment;
- no product behavior expansion is implied;
- any discovered blocker must be escalated rather than hidden in scope.

The eventual UX-E implementation/certification is complete only when:

- teacher evaluation page lint remains clean;
- admin-web TypeScript and production build pass;
- the supported teacher trust scenarios are proven or blockers are documented;
- no unsupported product claims are present;
- AI suggestions remain draft until teacher approval;
- manual-review uncertainty cannot appear authoritative;
- teacher-approved evidence remains the downstream posture;
- ARM accepts the certification before commit/publication.

---

## 15. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended posture:

```text
Certification/proof first.
Code changes only for explicitly authorized certification blockers.
No backend/API/schema/marks/source changes.
```

---

## 16. ARM review decision

**Design brief status:** Accepted

ARM decision:

```text
Accept the UX-E design brief.
Next artifact: Batch UX-E Implementation Authorization Contract.
Implementation remains unauthorized until a separate UX-E implementation
authorization contract is accepted.
```
