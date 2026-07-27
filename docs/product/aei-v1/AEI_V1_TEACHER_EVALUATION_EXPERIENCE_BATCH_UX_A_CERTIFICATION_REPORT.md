# AEI v1.0 Teacher Evaluation Experience - Batch UX-A Certification Report

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-A - Review-table trust metadata display
- **Authorization:** AEI-TEACHER-UX-A-AUTH-001
- **Classification:** Product-facing UX certification report
- **Status:** Accepted
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md)
- **Authorization baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **AEI v1.0 certification baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Supported scope matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Recommended commit:** `feat(aei): add teacher evaluation trust metadata display`
- **Recommended tag:** `aei-v1-teacher-evaluation-ux-a-trust-display-certified`

---

## 1. Executive decision

Batch UX-A implements a display-only teacher evaluation trust layer on the
existing answer-sheet evaluation page.

The implementation:

- adds a pure frontend display helper for AEI suggestion metadata;
- shows a compact teacher-review guidance summary;
- shows per-question confidence/capability/manual-review badges;
- shows available Maths normalization/equivalence evidence;
- remains tolerant of legacy suggestions without AEI metadata;
- preserves the existing upload, polling, suggestion, override, and approval
  flows;
- introduces no backend, API, schema, marks, routing, evidence-ledger, source
  switch, or feature-flag enablement changes.

**Certification decision:** PASS
**Runtime product behavior:** Display-only UI enhancement
**Backend behavior:** Unchanged
**Schema/API changes:** None
**Risk:** Low, bounded to teacher evaluation page rendering
**Recommendation:** Accept and publish Batch UX-A.

---

## 2. Repository changes

### 2.1 Frontend source

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`
  - adds teacher-review guidance summary above the review table;
  - adds per-suggestion AEI trust badges and evidence rows;
  - preserves existing evaluation actions and API calls.

- `apps/admin-web/src/lib/aei-evaluation-display.ts`
  - adds pure display helpers for summarizing and labeling existing
    `ai_suggestions` metadata;
  - does not call APIs;
  - does not mutate suggestions;
  - does not make source-of-truth decisions.

### 2.2 Documentation

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_DESIGN_BRIEF.md`
  - accepted as the teacher evaluation experience design baseline.

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`
  - accepted and authorized for Batch UX-A only.

- `docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_A_CERTIFICATION_REPORT.md`
  - this report.

---

## 3. Scope compliance

| Contract requirement | Result | Evidence |
|---|---:|---|
| Display existing suggestion-level metadata | PASS | Review table now renders summary, badges, and evidence rows |
| Safe fallback when AEI metadata is absent | PASS | Summary shows neutral legacy suggestion posture |
| Preserve upload/polling/suggestion/approval flows | PASS | No API call or workflow logic changed |
| Frontend-only implementation | PASS | No backend runtime files changed |
| No marks changes | PASS | No marks calculation or approval payload logic changed |
| No approval endpoint changes | PASS | Existing endpoint and payload shape unchanged |
| No schema/API changes | PASS | No backend schema/endpoint files changed |
| No source switch / Phase 7F | PASS | No EUI source-of-truth code touched |
| No Trust Report display | PASS | UI displays AEI suggestion metadata only |
| No public product claim changes | PASS | Marketing/support surfaces untouched |

---

## 4. User-visible behavior

When a teacher opens an evaluation in suggested or approved state, the page now
shows:

- a compact "Teacher review guidance" summary;
- total suggestions;
- supported/manual-review/low-confidence/assist-checklist counts when AEI
  metadata exists;
- neutral legacy guidance when metadata is absent;
- per-question badges for confidence, capability mode, method, language/OCR
  posture, visual/science posture, and teacher-review requirement when present;
- available evidence rows such as normalized answer, matched acceptable answer,
  unit/tolerance result, and manual-review reason.

The UI copy remains cautious:

```text
AI suggestions are draft only. Final marks are published after teacher approval.
```

---

## 5. Explicit exclusions preserved

Batch UX-A did not introduce:

- backend evaluation changes;
- marks calculation changes;
- teacher-review routing changes;
- approval endpoint changes;
- teacher override reason workflow changes;
- evidence-ledger changes;
- database schema changes;
- database migrations;
- API route changes;
- EUI source-of-truth switching;
- Phase 7F source adoption;
- Trust Report display;
- student/parent/principal visibility changes;
- production feature-flag enablement;
- public product claim changes;
- new OCR/vision/LLM behavior.

---

## 6. Supported-scope wording review

Teacher-facing labels align with the AEI v1.0 supported scope matrix:

| Metadata posture | UX-A display posture |
|---|---|
| `supported` | `Supported` |
| `assist` | `Assist only` |
| `checklist` | `Checklist only` |
| `manual_review` | `Manual review` / `Teacher review required` |
| `unsupported` | `Unsupported` |
| Missing AEI metadata | Neutral legacy suggestion guidance |

UX-A does not claim autonomous grading, universal OCR, universal language
grading, visual grading, or source-of-truth adoption.

---

## 7. Validation evidence

### 7.1 New helper lint

Command:

```text
npx eslint "src/lib/aei-evaluation-display.ts"
```

Result:

```text
PASS
```

### 7.2 Focused page + helper lint

Command:

```text
npx eslint "src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx" "src/lib/aei-evaluation-display.ts"
```

Result:

```text
FAILED due to pre-existing lint debt in the existing evaluation page:
- @typescript-eslint/no-explicit-any;
- react-hooks/set-state-in-effect.
```

Interpretation:

The new helper file is lint-clean. The page-level lint failure is pre-existing
debt in the touched evaluation page and is outside the display-only UX-A
authorization. UX-A does not expand scope to rewrite the page state model or
fully type the legacy page.

### 7.3 Admin-web production build

Command:

```text
npm run build
```

Result:

```text
PASS
```

Evidence:

```text
Compiled successfully
Running TypeScript ...
Finished TypeScript
Generating static pages ... 72/72
```

The build includes both:

- `/dashboard/teaching/exams/[examId]/evaluate`;
- `/dashboard/exams/[examId]/evaluate`.

### 7.4 Diff whitespace

Command:

```text
git diff --check
```

Result:

```text
PASS
```

---

## 8. Browser proof status

Dedicated browser proof was not executed in this session.

Reason:

- The existing browser harness requires a running API and production web server
  with the Reference tenant and authenticated teacher data.
- This implementation was validated through successful Next build/type-check
  and the existing route compilation.

Before a public launch/readiness claim, run a teacher evaluation page browser
proof against the Reference tenant and verify:

- suggested evaluation renders;
- trust summary renders with AEI metadata;
- legacy/no-AEI suggestions render without alarm;
- approval controls remain available;
- no disallowed console/API errors occur.

This is recorded as a validation caveat, not an expansion of UX-A scope.

---

## 9. Rollback proof

Rollback is straightforward:

```text
Revert the UX-A frontend/docs commit.
```

No data rollback is required because UX-A does not introduce:

- migrations;
- persisted state;
- API changes;
- backend behavior;
- marks calculation changes.

---

## 10. Risk assessment

| Risk | Level | Mitigation |
|---|---:|---|
| Misleading teacher-facing claim | Low | Labels use supported/assist/checklist/manual-review posture |
| Legacy evaluation rendering regression | Low | Missing AEI metadata has neutral fallback |
| Approval flow regression | Low | Approval logic and payload unchanged |
| Backend behavior regression | Low | Backend files untouched |
| Browser-only layout issue | Medium | Browser proof recommended before launch-readiness claim |

---

## 11. ARM decision

ARM decision:

```text
Accept Batch UX-A implementation with the recorded browser-proof caveat.
Approve commit and annotated certification tag.
```

Recommended commit:

```text
feat(aei): add teacher evaluation trust metadata display
```

Recommended tag:

```text
aei-v1-teacher-evaluation-ux-a-trust-display-certified
```
