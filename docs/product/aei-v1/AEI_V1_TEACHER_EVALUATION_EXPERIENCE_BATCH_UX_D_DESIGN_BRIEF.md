# AEI v1.0 Teacher Evaluation Experience - Batch UX-D Design Brief

- **Program:** Post-AEI v1.0 product-facing enablement
- **Workstream:** Teacher evaluation experience
- **Batch:** UX-D - Supported-scope assist panels
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
- **Activation / Trust baseline:** [`./AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md`](./AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

UX-A made AEI trust metadata visible in the review table.
UX-B made teacher override reasons explicit.
UX-C made draft AI suggestions and teacher-approved evidence distinguishable.

Batch UX-D should complete the supported-scope teacher inspection experience for
non-Maths assistive capability families:

- language and OCR assist metadata;
- visual and science checklist/assist metadata.

The product question is:

> Can a teacher inspect language/OCR and visual/science assist signals clearly
> enough to review them confidently, while the product remains honest that these
> signals are assistive and non-authoritative?

This document defines the design baseline only. It does not authorize code,
schema, API, UI, feature-flag, rollout, or product-claim changes.

---

## 2. Product outcome

Inside the existing teacher evaluation page, a teacher should be able to inspect
supported-scope assist evidence without mistaking it for autonomous grading.

For language/OCR cases, the teacher should see:

- answer input source when available;
- detected language;
- detected script;
- code-mixed posture;
- OCR confidence when available;
- capability mode;
- why teacher confirmation is required.

For visual/science cases, the teacher should see:

- visual/science capability mode;
- reasoning type;
- visual type or scientific type when available;
- checklist-only or assist-only posture;
- checklist observations when available;
- why autonomous marks are not certified.

The desired teacher-facing message is:

```text
This evidence can help your review, but it does not replace your decision.
```

---

## 3. Design principle

UX-D must make assistive evidence inspectable, not authoritative.

```text
AEI metadata
     |
     v
Teacher-safe assist panel
     |
     v
Teacher confirms / edits / overrides
     |
     v
Existing approval flow
```

The UI must never imply:

- universal OCR;
- reliable handwriting correction;
- automatic language grading;
- pixel-perfect visual grading;
- automatic graph/map/diagram marks;
- full chemistry structure grading;
- autonomous marks from checklist evidence.

---

## 4. Existing surfaces to reuse

### 4.1 Canonical teacher surface

Reuse the existing teaching evaluation route:

```text
apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx
```

The legacy dashboard evaluation route must remain a redirect or compatibility
surface. UX-D should not create a new evaluation page.

### 4.2 Existing frontend helper

Reuse and, if authorized later, extend the existing teacher-safe metadata helper:

```text
apps/admin-web/src/lib/aei-evaluation-display.ts
```

The helper already understands:

- language fields;
- OCR confidence;
- assist/checklist badges;
- visual/science capability mode;
- AEI metadata presence.

UX-D should deepen display structure without replacing the helper.

### 4.3 Existing backend metadata

UX-D should consume only existing response metadata produced by certified AEI
v1.0 foundations and activation/trust proof:

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
- `aei_v1_visual_science_assist`.

If metadata is absent, UX-D should render a calm absence state instead of
inventing evidence.

---

## 5. Experience design

### 5.1 Per-question assist panel

UX-D should add an inspectable assist section inside each relevant question row
or existing decision-evidence area.

The panel should appear only when a suggestion contains language/OCR or
visual/science metadata. It should not add visual noise to ordinary objective
or deterministic Maths-only questions.

Suggested section title:

```text
Assist evidence for teacher review
```

Suggested posture copy:

```text
Assistive evidence only. Teacher confirmation is required before marks are
trusted downstream.
```

### 5.2 Language/OCR assist panel

The language/OCR panel should make extraction and language uncertainty visible.

Recommended fields:

| Field | Teacher-facing wording | Notes |
|---|---|---|
| `answer_input_source` | Source | Example: manual entry, OCR image, teacher-entered text |
| `answer_language` | Detected language | Do not present as guaranteed |
| `detected_script` | Detected script | Useful for Hindi/Telugu/Sanskrit and romanized answers |
| `code_mixed` | Code-mixed answer | Use careful wording such as "code-mixed detected" |
| `language_confidence` | Language confidence | Show only when present |
| `ocr_confidence` | OCR confidence | Low confidence should be warning-toned |
| `language_ocr_capability_mode` | Capability posture | Supported wording from the capability matrix |
| `manual_review_reason` | Review reason | Explain why the teacher must confirm |

Required copy boundary:

```text
OCR/language assist does not certify marks. Confirm the answer text before
approving.
```

### 5.3 Visual/science assist panel

The visual/science panel should show observations and checklist posture without
claiming autonomous correctness.

Recommended fields:

| Field | Teacher-facing wording | Notes |
|---|---|---|
| `visual_science_capability_mode` | Capability posture | Assist/checklist/manual-review wording |
| `visual_science_reasoning_type` | Reasoning type | Example: map checklist, diagram checklist, reaction balancing |
| `visual_type` | Visual type | Diagram, graph, map, circuit, flowchart, visual |
| `scientific_type` | Scientific type | Chemistry equation, formula, symbol, structure where present |
| `checklist_only` | Checklist only | Strong teacher-review posture |
| `assist_only` | Assist only | Strong teacher-review posture |
| `visual_science_review_required` | Teacher review required | Must be obvious |
| `manual_review_reason` | Review reason | Explain capability boundary |

If nested `aei_v1_visual_science_assist` evidence includes checklist expected,
observed, present, or missing values, UX-D may display those values as
observations. It must label them as checklist evidence, not marks authority.

Required copy boundary:

```text
Checklist observations support your review. They do not automatically award
marks.
```

### 5.4 Empty and legacy states

Legacy evaluations and evaluations without Batch D/E metadata must remain calm:

```text
No language/OCR or visual/science assist evidence is available for this answer.
```

This should be shown only when an assist panel area is otherwise expected. The
table should not become cluttered with absence messages for every ordinary row.

### 5.5 Tone and visual hierarchy

The panel should be:

- compact;
- teacher-readable;
- low-jargon;
- warning-toned for assist/checklist/manual-review cases;
- visually consistent with UX-A/B/C trust badges and evidence panel;
- accessible by keyboard and screen reader when expandable/collapsible behavior
  is used.

The highest-priority information should be:

1. whether teacher confirmation is required;
2. why;
3. what evidence was observed;
4. what the capability boundary is.

---

## 6. Supported-scope wording rules

UX-D must use the certified supported-scope matrix as its wording boundary.

| Capability mode | Allowed wording | Forbidden implication |
|---|---|---|
| `assist` | Assist only - teacher confirmation required | Automatically correct |
| `checklist` | Checklist only - teacher confirmation required | Automatically graded |
| `manual_review` | Teacher review required | AI can certify marks |
| `unsupported` | Not supported for automatic evaluation | Hidden or treated as normal |
| `expansion` | Future scope | Available now |

For language/OCR:

- "OCR assist" is acceptable.
- "Fully reliable handwriting OCR" is not acceptable.
- "Teacher confirmation required" should be visible for OCR-derived or
  low-confidence cases.

For visual/science:

- "Checklist observations" is acceptable.
- "Diagram grading" or "map grading" is not acceptable unless a future
  certification explicitly authorizes it.

---

## 7. Data/API posture

UX-D should be frontend display-only.

Preferred posture:

- read existing `ai_suggestions` metadata;
- read existing evidence metadata only when already present;
- tolerate missing or legacy metadata;
- do not request new fields from the API;
- do not introduce schema migrations;
- do not change approval payloads;
- do not alter marks persistence;
- do not alter evidence-ledger generation.

If implementation discovers that the existing response shape cannot support a
safe panel, it should stop and request an implementation-contract amendment
instead of expanding backend scope implicitly.

---

## 8. Feature-flag posture

UX-D does not enable any AEI backend capability flag.

The following remain default-off in source:

```text
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
```

UX-D may display metadata when metadata is already present in the evaluation
response. It must render safely when flags are off and metadata is absent.

No new frontend display flag is required by this design. If implementation
needs one, it must be authorized in the implementation contract.

---

## 9. Explicit non-goals

UX-D is not:

- an OCR engine integration;
- a handwriting recognition project;
- a language grading project;
- a vision model integration;
- a diagram/graph/map grading engine;
- a chemistry structure evaluator;
- a Trust Report display project;
- an EUI source-adoption project;
- a mastery-spine source-switching project;
- a new evaluation workflow;
- a new approval workflow;
- a public product-claims update.

---

## 10. Explicit exclusions

Until a UX-D implementation authorization contract states otherwise, UX-D does
not authorize:

- backend changes;
- database schema changes;
- Alembic migrations;
- API contract changes;
- new public endpoints;
- OCR provider changes;
- LLM provider changes;
- vision model changes;
- marks calculation changes;
- teacher-review routing changes;
- approval endpoint changes;
- evidence-ledger generation changes;
- source-of-truth switching to EUI;
- Phase 7F source adoption;
- Topic-ID / Mastery Spine Phase B;
- parent/student/principal visibility changes;
- production feature-flag enablement;
- public product claim changes;
- product analytics or tracking events.

---

## 11. Expected implementation boundary

A later UX-D implementation authorization contract should likely permit only:

- `apps/admin-web/src/app/dashboard/teaching/exams/[examId]/evaluate/page.tsx`;
- `apps/admin-web/src/lib/aei-evaluation-display.ts`;
- focused frontend tests/helpers if already present or necessary;
- UX-D certification documentation.

Any backend file change should require explicit contract amendment.

---

## 12. Testing and certification strategy

UX-D implementation should produce evidence that:

- language/OCR metadata renders when present;
- visual/science metadata renders when present;
- assist/checklist/manual-review copy is visible and honest;
- missing metadata renders safely;
- UX-A trust badges remain intact;
- UX-B override reason workflow remains intact;
- UX-C evidence/approved-decision panel remains intact;
- no marks, approval, API, schema, backend, source-switching, or consumer
  behavior changed.

Expected validation:

- admin-web build / TypeScript validation;
- focused helper validation where practical;
- browser proof or documented environment blocker for:
  - language/OCR assist case;
  - visual/science checklist case;
  - legacy metadata absence;
  - approved-evidence panel coexistence;
- `git diff --check`;
- backend validation only if a future contract authorizes backend changes.

Certification should explicitly review teacher-facing copy against the supported
scope matrix.

---

## 13. Acceptance criteria

UX-D design is ready for implementation authorization when ARM agrees that:

- the panel scope is display-only;
- language/OCR metadata is represented as assistive evidence only;
- visual/science metadata is represented as checklist/assist evidence only;
- teacher confirmation remains visibly required;
- unsupported or low-confidence cases cannot look authoritative;
- no new AI, OCR, vision, grading, backend, schema, API, source-switching, or
  consumer migration work is implied;
- the implementation boundary can remain narrow and reviewable.

The eventual UX-D implementation is complete only when:

- relevant metadata is inspectable by teachers;
- unsupported and uncertain cases are visibly non-authoritative;
- UX-A/B/C behavior remains intact;
- browser/build validation evidence exists;
- certification is accepted by ARM before commit/tag/publication.

---

## 14. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_D_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended implementation posture:

```text
Frontend display-only assist panels.
No backend/API/schema/marks/source changes.
```

---

## 15. ARM review decision

**Design brief status:** Accepted

ARM decision:

```text
Accept the UX-D design brief.
Next artifact: Batch UX-D Implementation Authorization Contract.
Implementation remains unauthorized until a separate UX-D implementation
authorization contract is accepted.
```
