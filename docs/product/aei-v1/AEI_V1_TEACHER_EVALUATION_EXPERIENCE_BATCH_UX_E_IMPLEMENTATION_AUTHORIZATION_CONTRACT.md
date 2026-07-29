# AEI v1.0 Teacher Evaluation Experience - Batch UX-E Implementation Authorization Contract

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-E - Final teacher evaluation experience certification
- **Classification:** Implementation authorization contract
- **Authorization ID:** AEI-TEACHER-UX-E-AUTH-001
- **Status:** Accepted
- **Implementation:** Authorized for Batch UX-E only
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_DESIGN_BRIEF.md)
- **Teacher evaluation experience baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **UX-A baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md)
- **UX-B baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_B_CERTIFICATION_REPORT.md)
- **UX-C baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_C_CERTIFICATION_REPORT.md)
- **UX-D baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_CERTIFICATION_REPORT.md)
- **Activation / Trust baseline:** [`./AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md`](./AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize, if accepted by ARM, a narrow UX-E certification/proof slice that
validates the complete teacher evaluation experience assembled across UX-A,
UX-B, UX-C, UX-D, AEI Activation / Trust, and the teacher evaluation page lint
cleanup.

The goal is not to add another feature. The goal is to prove:

```text
The teacher evaluation experience is production-ready for AEI v1.0
supported-scope use.
```

UX-E should answer:

> Can a teacher complete the supported evaluation loop with clear trust signals,
> teacher authority, approved evidence posture, and no unsupported capability
> claims?

---

## 2. Authorization posture

This contract is accepted by ARM.

It authorizes only:

- certification evidence;
- deterministic validation;
- browser proof or documented browser-proof blockers;
- supported-scope copy review;
- a UX-E certification report;
- small frontend fixes only if they are required to pass the accepted UX-E
  certification scenarios and remain within this contract.

This contract does not authorize a new product feature batch.

---

## 3. Implementation scope if accepted

Implementation is authorized only for:

1. reviewing UX-A/B/C/D behavior together on the existing teacher evaluation
   page;
2. validating the teacher trust scenario matrix from the UX-E design brief;
3. producing browser proof where the local or staging environment supports it;
4. documenting any browser-proof blockers explicitly when proof cannot be run;
5. reviewing teacher-facing copy against the supported scope matrix;
6. verifying feature-flag posture and rollback posture;
7. validating focused frontend lint, TypeScript, and production build;
8. producing the UX-E certification report;
9. making small frontend-only certification-blocker fixes if and only if they:
   - are discovered during UX-E validation;
   - are necessary for teacher-trust correctness;
   - do not expand product scope;
   - do not change backend, API, schema, marks, routing, ledger, or source
     behavior.

If validation discovers a blocker that requires backend, API, schema, evidence
ledger, source-of-truth, AEI runtime, or product capability changes, the
implementation must stop and request a separate ARM authorization.

---

## 4. Authorized repository boundary

### 4.1 Documentation and certification

Implementation may add:

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md`

Implementation may update, if needed for final accepted status:

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_DESIGN_BRIEF.md`
- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`

Post-publication status updates must be committed separately:

- `docs/STATUS.md`

### 4.2 Frontend source

Frontend source changes are not expected.

Small certification-blocker fixes may modify only:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`
- `apps/admin-web/src/lib/aei-evaluation-display.ts`

Any such change must remain:

- frontend-only;
- display or validation behavior only;
- deterministic;
- teacher-trust preserving;
- tolerant of legacy or absent metadata;
- compatible with UX-A/B/C/D behavior;
- free of new API calls.

### 4.3 Browser proof / validation scripts

Implementation may add a lightweight proof script or notes only if it uses
existing project tooling and does not introduce a new framework or dependency.

Permitted locations, if needed:

- `apps/admin-web/e2e-smoke.cjs` only for additive, compatible smoke coverage;
- `docs/product/aei-v1/` for manual browser-proof notes or fixture
  descriptions.

Do not introduce a new browser-testing framework in UX-E.

### 4.4 Protected areas

The following must not be changed:

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
- notification workflows;
- production deployment configuration;
- feature-flag defaults.

---

## 5. Required scenario matrix

UX-E certification must review the following scenarios:

| Scenario | Required proof |
|---|---|
| Legacy / no AEI metadata | Existing evaluation remains usable; no false claims or broken panels |
| Deterministic Maths supported case | Trust badges and equivalence evidence render when metadata exists |
| Manual review required case | Review reason is visible; acknowledgement is enforced when required |
| Teacher override case | Changed marks require teacher-authored reason before approval |
| Approved evidence case | Draft AI output and teacher-approved evidence remain distinct |
| Language/OCR assist case | Assist evidence is visible and clearly non-authoritative |
| Visual/science assist case | Checklist/assist evidence is visible and clearly non-authoritative |

The scenario matrix may be proven through:

- browser proof against a running environment;
- deterministic local/manual fixture proof documented in the certification
  report;
- source inspection and focused validation when browser proof is blocked.

Any unproven scenario must be recorded as a finding, not silently passed.

---

## 6. Browser proof requirements

UX-E must attempt browser proof for the teacher evaluation page.

The proof should cover:

- page load without runtime error;
- existing evaluation review page state;
- AI suggestion trust metadata display;
- manual-review acknowledgement posture;
- override reason validation posture;
- evidence/approved-decision panel coexistence;
- language/OCR assist panel when metadata exists;
- visual/science assist panel when metadata exists.

If browser proof cannot run, the certification report must document:

- exact blocker;
- environment requirement that was missing;
- what validation was run instead;
- whether the blocker affects product readiness or only local proof.

Acceptable blockers include:

- no running API;
- no seeded Reference tenant;
- no authenticated teacher session;
- no deterministic fixture route;
- unavailable browser automation environment.

Browser proof must not be replaced by silence.

---

## 7. Supported-scope copy review

Implementation must review teacher-facing copy against:

- [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)

Allowed posture:

- AI suggestions are draft only.
- Teacher review required.
- Assist only - teacher confirmation required.
- Checklist observations support teacher review.
- Teacher decision is the downstream source of truth.

Forbidden posture:

- AI corrected the paper.
- Handwriting OCR is reliable.
- Diagram grading is complete.
- Science answer is certified by AI.
- No teacher review is needed for uncertain/assist/checklist cases.
- Parent/student consumers can use unapproved AI suggestions.

Any forbidden or ambiguous copy found during implementation must be fixed if it
is inside the authorized frontend boundary. If it is outside the boundary, the
implementation must record it as a finding.

---

## 8. Feature-flag posture

UX-E must not enable or change feature-flag defaults.

Certification must record the posture of:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED
AEI_V1_REVIEW_POLICY_ENABLED
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED
AEI_ACTIVATION_TRUST_ENABLED
```

Expected proof:

- metadata display remains additive and tolerant of absence;
- flag-off behavior remains safe;
- no source-of-truth switch occurs;
- rollback does not require data repair.

---

## 9. Runtime and product constraints

UX-E must preserve:

- existing marks calculation;
- existing approval endpoint behavior;
- existing teacher override payload shape;
- existing evidence ledger generation;
- existing parent/student downstream posture;
- teacher-approved evidence as the downstream authority;
- AEI/EUI architecture boundaries;
- EUI Phase 7F deferred status.

UX-E must not introduce:

- new OCR inference;
- new LLM inference;
- new vision inference;
- autonomous grading;
- automatic visual/science marks;
- product analytics;
- notifications;
- public claims.

---

## 10. Validation requirements

Before ARM acceptance, UX-E must provide evidence for:

```powershell
git diff --check
```

Frontend validation:

```powershell
npm run lint -- src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx
npm run lint -- src/lib/aei-evaluation-display.ts
npx tsc --noEmit
npm run build
```

Working directory for frontend commands:

```text
apps/admin-web
```

Additional validation:

- browser proof or documented blocker;
- supported-scope copy review;
- repository boundary review;
- no backend/API/schema diff review.

Backend validation is required only if a future contract amendment authorizes
backend changes. This contract does not authorize backend changes.

---

## 11. Certification report requirements

Implementation must add:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md
```

Required sections:

1. certification decision;
2. scope implemented;
3. repository files changed;
4. explicit exclusions preserved;
5. teacher trust scenario matrix;
6. browser proof evidence or blocker;
7. supported-scope copy review;
8. feature-flag posture;
9. runtime/API/schema/backend boundary review;
10. validation evidence;
11. known limitations;
12. rollback posture;
13. ARM recommendation.

If code changes are made, the report must explain why they were certification
blockers and confirm they stayed within this contract.

---

## 12. Rollback posture

UX-E should be rollback-simple.

Expected rollback:

- revert any UX-E code changes, if any;
- leave UX-A/B/C/D certified artifacts intact;
- leave AEI/EUI runtime foundations intact;
- do not require data repair;
- do not require migrations;
- do not alter feature flags.

If UX-E is docs/proof-only, rollback is simply reverting the UX-E certification
artifacts.

---

## 13. Explicit exclusions

This contract does not authorize:

- backend changes;
- database schema changes;
- Alembic migrations;
- API contract changes;
- new public endpoints;
- marks calculation changes;
- teacher-review routing changes;
- approval endpoint changes;
- approval payload shape changes;
- evidence-ledger generation changes;
- evidence-ledger schema changes;
- parent/student/principal UI changes;
- source-of-truth switching to EUI;
- EUI Phase 7F source adoption;
- Topic-ID / Mastery Spine Phase B;
- production feature-flag enablement;
- public product-claim changes;
- LLM provider changes;
- OCR provider changes;
- vision provider changes;
- new test framework or dependency;
- product analytics or tracking events.

---

## 14. Exit criteria

UX-E may be considered complete only when:

- the required scenario matrix is reviewed;
- browser proof is captured or blockers are explicitly documented;
- teacher-facing copy is reviewed against the supported scope matrix;
- focused page lint passes;
- AEI display helper lint passes;
- TypeScript validation passes;
- admin-web production build passes;
- `git diff --check` passes;
- repository diff stays within the authorized boundary;
- no backend/API/schema/marks/routing/ledger/source-switch changes are present;
- UX-E certification report is complete;
- ARM accepts the certification before commit/publication.

---

## 15. Recommended implementation metadata

If UX-E is accepted after implementation review, recommended commit message:

```text
docs(aei): certify teacher evaluation experience
```

If UX-E includes an accepted certification-blocker code fix, recommended commit
message should be adjusted to:

```text
feat(aei): certify teacher evaluation experience
```

Recommended annotated tag:

```text
aei-v1-teacher-evaluation-experience-certified
```

`docs/STATUS.md` must be updated separately after publication.

---

## 16. ARM review decision

**Contract status:** Accepted

ARM decision:

```text
Accept the UX-E implementation authorization contract.
Implementation is authorized for Batch UX-E only, within this proof-first
contract.
```
