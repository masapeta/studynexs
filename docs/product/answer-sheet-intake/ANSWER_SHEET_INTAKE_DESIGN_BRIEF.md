# Answer Sheet Intake / Capture Assistant Design Brief

- **Program:** Product execution
- **Gate:** Answer Sheet Intake (Capture Assistant)
- **Classification:** Design brief
- **Status:** Draft — awaiting ARM review
- **Implementation:** Not authorized
- **Date:** 2026-08-19
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)
- **Execution plan baseline:** [`../PRODUCT_EXECUTION_PLAN.md`](../PRODUCT_EXECUTION_PLAN.md)
- **Current batch baseline:** [`../CURRENT_BATCH.md`](../CURRENT_BATCH.md)
- **Product execution constitution:** [`../PRODUCT_EXECUTION_CONSTITUTION.md`](../PRODUCT_EXECUTION_CONSTITUTION.md)
- **AEI architecture baseline (frozen):** [`../../decisions/ADR-0001-academic-evaluation-intelligence-architecture-freeze.md`](../../decisions/ADR-0001-academic-evaluation-intelligence-architecture-freeze.md)
- **AEI v1.0 certification baseline:** [`../ASSESSMENT_EVALUATION_INTELLIGENCE_COMPLETION_REPORT.md`](../ASSESSMENT_EVALUATION_INTELLIGENCE_COMPLETION_REPORT.md)
- **AEI activation baseline:** [`../../runbooks/aei-pilot-activation.md`](../../runbooks/aei-pilot-activation.md)

---

## 1. Purpose

Answer Sheet Intake answers one question:

> Can a school move a messy pile of physical answer sheets into organized,
> evaluation-ready digital submissions without spending teacher time?

AEI v1.0 evaluation and handwriting OCR are certified and published. The
capability exists. The paper cannot enter the system cleanly.

This design brief does not authorize implementation.

---

## 2. Core principle

Do not ask AI to solve chaos. Organize the paper flow first.

```text
Paper arrives
      |
      v
Intake organizes it            <- this gate
      |
      v
OCR reads it                   <- certified
      |
      v
AEI assists evaluation         <- certified, staged activation
      |
      v
Teacher reviews exceptions and approves
      |
      v
Parent/student see approved evidence
```

OCR is *read text from image*. Intake is *turn a messy pile of school papers
into organized evaluation-ready submissions*. The second is the product problem.

---

## 3. Why this gate is needed now

The current evaluation contract supports exactly one student and one file:

- [`answer_sheet_evaluation.py`](../../../apps/api/app/db/models/answer_sheet_evaluation.py)
  carries `exam_id`, `student_id`, and a single nullable `file_id`, with
  `UniqueConstraint("exam_id", "student_id")`.
- [`evaluation.py`](../../../apps/api/app/modules/examinations/endpoints/evaluation.py)
  accepts one `student_id` and one `file_id` per request.

The schema therefore cannot express: bundle upload, multiple pages per student,
page ordering, unmatched pages, late pages, missing pages, image-quality
exceptions, manual page assignment, or a non-teacher capture operator.

The operational consequence is the adoption risk. A teacher asked to upload
40 students one at a time concludes:

```text
Manual correction is easier.
```

That conclusion is reached before any certified intelligence becomes visible.

### Sequencing decision

The current single-student path is retained as an **internal technical smoke
path only**. It is not the teacher-facing product workflow and must not be
presented as one during a teacher acceptance test. Observation of the current
friction may proceed internally or with a friendly teacher; broad teacher
acceptance testing resumes after Batch C.

---

## 4. Product law — student identity resolution

This is a durable StudyNexs rule, not an implementation detail. It is proposed
for the Decision Log on acceptance of this brief.

> **Student identity resolution requires explicit evidence. If identity
> confidence is low or absent, the page remains unmatched and cannot proceed to
> final evaluation until a human assigns it.**

Permitted identity evidence:

| Evidence | Authority |
|---|---|
| QR / barcode encoding `exam_id` + `student_id` + page | Authoritative |
| Admission number | Authoritative when it resolves to exactly one student in scope |
| Roll number + class + exam context | Authoritative when it resolves to exactly one student in scope |
| Student name + class/exam context | Candidate; human confirmation required |
| Anchor-page sequence | Candidate; human confirmation of the whole group required |
| Manual assignment by a human | Authoritative |

Never permitted as authority, at any confidence:

```text
"This handwriting looks like this student's."
```

Handwriting similarity may exist later only as a labelled, non-authoritative
hint that pre-selects a control a human must still confirm. Mis-assigning a page
changes a student's marks, so this boundary is a trust boundary and is treated
with the same severity as tenant isolation.

### Deterministic precedence rule

Page-count reconciliation is arithmetic; anchor detection is probabilistic.
When they conflict, **the deterministic count wins and the affected group is
forced to human confirmation.** A missed anchor must never silently merge two
students' papers, because that failure produces a plausible wrong result rather
than a visible error.

---

## 5. Capability delivered

| Field | Value |
|---|---|
| **Primary persona** | Capture operator (school office / exam cell), then teacher |
| **Secondary persona** | Principal — sees intake completeness before marking starts |
| **Problem being solved** | Physical answer sheets cannot enter the system without consuming teacher time |
| **Educational capability** | A class's answer sheets become evaluation-ready submissions in one operator pass, with exceptions isolated for human decision |
| **What a school can do that it could not yesterday** | Hand a stack of answer sheets to the office and receive an evaluation-ready, reconciled set — with missing and unclear pages named before a teacher opens the app |

### Teacher-time protection

Intake is deliberately assigned away from the teacher. The teacher's first
contact with an exam remains review and approval, not data entry.

---

## 6. Roles and authority

The existing `UserRole` enum already contains `OPERATIONS`
([`user.py`](../../../apps/api/app/db/models/user.py)). **No new role is
introduced.** "Capture operator" is a capability, not a role, and maps to
existing roles through a new permission flag.

| Capability | admin / super_admin | operations | class_incharge | teacher |
|---|:-:|:-:|:-:|:-:|
| Upload bundle | yes | yes | yes | yes |
| Confirm detected groups | yes | yes | yes | yes |
| Assign unmatched pages | yes | yes | yes | yes |
| Flag page for recapture | yes | yes | yes | yes |
| Approve marks | yes | **no** | scope | scope |
| Publish results / parent evidence | yes | **no** | scope | scope |

`operations` gains intake capability and gains **no academic authority**. This
is the mechanism that allows assisted rollout — including a StudyNexs rollout
associate operating as `operations` — without granting marking authority.

Permission flags are added backend-first and surfaced via
`GET /api/v1/users/me/permissions`, per the RBAC convention.

---

## 7. Data model (additive)

Four new tenant-scoped entities. Every table carries a non-null indexed
`school_id`. Pages and groups are real tables, not JSONB, because the exception
queue *is* a filtered query over page and group status.

```text
AnswerSheetBundle
    school_id, exam_id, class_id
    uploaded_by, upload_source        (web_bulk | scanner | mobile)
    expected_students, expected_pages_per_student
    status                            (uploading | analyzing | needs_review | confirmed | failed)

AnswerSheetPage
    school_id, bundle_id, page_index, file_id
    image_quality_status              (ok | unclear | unreadable)
    detected_anchor                   (bool)
    detected_student_candidate_id     (nullable)
    detected_evidence                 (jsonb — what was seen, never a verdict)
    status                            (matched | unmatched | unclear | duplicate | recapture)

AnswerSheetGroup
    school_id, bundle_id, exam_id
    student_id                        (nullable until resolved)
    match_source                      (qr | admission_no | roll_no | name | anchor_group | manual | none)
    match_confidence                  (nullable)
    status                            (candidate | confirmed | rejected | incomplete)
    confirmed_by, confirmed_at        (nullable)

AnswerSheetGroupPage
    school_id, group_id, page_id, order_index
```

Existing evaluation evolves additively only:

```text
AnswerSheetEvaluation.page_group_id  (nullable FK)
```

`match_source` is the audit trail for *why* a page belongs to a student. It is
what allows the UI to honestly distinguish "matched by QR" from "you assigned
this," and it is required on every group.

**Migration posture:** additive, reversible, expand-then-contract. The existing
single-`file_id` path continues to work unchanged. No `/api/v1` contract is
broken; new endpoints are added alongside.

---

## 8. Two identity paths

### Recommended path — QR

StudyNexs already generates question papers through the PDF renderer. Intake
extends that to generate a per-student answer-sheet cover (or label sheet)
carrying `QR(exam_id, student_id, page_no | booklet_id)`.

QR simultaneously dissolves shuffled bundles, late pages, mixed ordering, and
manual assignment. It is the reliable long-term standard.

It requires the school to print StudyNexs-generated sheets, which some schools
will resist initially. It is therefore **recommended, not required.**

### Fallback path — anchor grouping

Real school answer sheets reliably carry student details on the first page only.

```text
Anchor page detected (header fields or QR present)
      |
      v
Following pages join the latest anchor's group
      |
      v
Until the next anchor page, or the expected page count is reached
      |
      v
Deterministic reconciliation flags shortfalls and overruns
      |
      v
Human confirms all groups before evaluation
```

Blind bundle-order mapping — assigning by sequence alone with no anchor and no
count check — is **excluded**. It can mis-assign at scale with no detectable
signal.

### Late and orphan pages

A page with no identity evidence, uploaded outside an active ordered bundle,
becomes `unmatched` and requires human assignment. Deterministic evidence may
be shown as a suggestion:

```text
Avanthika is missing 1 of 3 expected pages.
This page contains Q9-Q10; her existing pages end at Q8.
Suggested: Avanthika. Confirm?
```

Suggestion, never auto-commit.

---

## 9. Scope

### In scope (v1)

```text
Bundle upload (multi-page)
AnswerSheetBundle / Page / Group / GroupPage entities
Page status and group status
Expected page-count reconciliation (deterministic)
Anchor-page detection and grouping
QR detection on cover/label pages
QR answer-sheet template generation
Grouped-preview confirmation screen
Unmatched / unclear / recapture exception queue
Manual page assignment
Operations-role intake capability (no academic authority)
match_source audit on every group
Link confirmed group to AnswerSheetEvaluation
Intake completeness summary before evaluation
```

### Explicitly out of scope (v1)

```text
Handwritten roll-number auto-commit          (assist-only in a later batch)
Handwriting-based identity matching          (never authoritative)
Fully automatic shuffled-page recovery       (QR path solves this instead)
Advanced computer-vision grouping
Student-app upload flow
Parent-visible intake status
Automatic final marks
Scanner hardware integration
Offline capture, auto-crop, auto-rotate
```

Roll-number OCR is excluded from v1 deliberately: a handwritten roll number in
a photographed header box is the hardest OCR in the pipeline, and a *wrong*
match is worse than no match. Confirming ~30 pre-formed groups is already far
faster than assigning ~90 loose pages, so grouping delivers most of the time
saving without that risk.

---

## 10. Known platform constraints to resolve in implementation

Verified against the current codebase. Each must be addressed by the
implementation contract.

| # | Constraint | Evidence | Implication |
|---|---|---|---|
| 1 | `ANSWER_SHEET` accepts images only — **not PDF** | [`file_validation.py`](../../../apps/api/app/modules/files/services/file_validation.py) `ALLOWED_MIMES_BY_CATEGORY` | Multi-page PDF intake needs an explicit decision: extend the allowlist, or add a dedicated category with its own size cap and validation |
| 2 | `ANSWER_SHEET` cap is 5 MB per file; nginx `client_max_body_size` is 12 MB | `file_validation.py`, [`nginx.conf`](../../../infra/nginx/nginx.conf) | A 90-page bundle cannot be one request. Intake must upload per page or in chunks, with a bundle assembled server-side |
| 3 | File upload has no per-role category allowlist | [`file.py`](../../../apps/api/app/modules/files/endpoints/file.py) | Intake introduces operator uploads; category-vs-role enforcement should land with it |
| 4 | `UploadedFile` has no student linkage | [`file.py`](../../../apps/api/app/db/models/file.py) | Page→student authorization must be expressed through the group, or via a file→student link |
| 5 | OCR/image parsing runs synchronously in the request path | [`document_ocr.py`](../../../apps/api/app/modules/files/services/document_ocr.py) | Bundle analysis must run as an Arq job with progress, not inline |
| 6 | Handwriting OCR is flag-gated and default-off | `AEI_HANDWRITING_OCR_PHASE1_ENABLED` | Intake must function fully with OCR disabled — grouping and reconciliation are independent of OCR |

---

## 11. Implementation batches

Each batch requires its own ARM authorization. No batch inherits authorization
from an earlier one.

| Batch | Scope | Exit condition |
|---|---|---|
| **A** | Schema + models + reversible migration; bundle upload; per-page storage; Arq analysis job skeleton; permission flags | Bundle of N pages uploads, persists tenant-scoped, and is retrievable. No grouping yet. Tenant-isolation and RBAC tests pass |
| **B** | Anchor detection; QR detection; deterministic page-count reconciliation; grouping; grouped-preview confirmation UI; exception queue; manual assignment | An operator uploads a class bundle and confirms correct groups; missing/extra/unclear pages are named; nothing proceeds unconfirmed |
| **C** | Link confirmed groups to `AnswerSheetEvaluation`; QR template generation; intake completeness summary | A confirmed group flows into the existing certified evaluation path without changing evaluation behavior |

Teacher acceptance testing resumes after Batch C.

---

## 12. Validation posture

- Focused build, lint, and tests for every changed surface.
- Tenant isolation explicitly tested for bundles, pages, and groups.
- RBAC tested per role, including that `operations` cannot approve marks.
- Identity-law tests: a page with no evidence **cannot** reach evaluation.
- Deterministic-precedence test: a missed anchor plus a page-count conflict
  forces confirmation rather than silently merging groups.
- Additive `/api/v1` compatibility; the existing single-file path unchanged.
- Migration `upgrade` and `downgrade` both exercised.
- No weakening of boot, security, tenant, or human-authority guardrails.

---

## 13. Hard constraints

- Releases 0.1–0.3 and the frozen AEI/EUI architecture are not modified except
  for verified production defects, security fixes, or critical regressions.
- No parallel evaluation, OCR, or grouping engine. Intake feeds the existing
  certified AEI path; it does not reimplement it.
- No product-claim expansion. Intake organizes paper; it does not improve
  marking accuracy and must not be described as doing so.
- No AEI/EUI flag is enabled by this gate.
- Teacher authority is unchanged. Intake never assigns a mark.

---

## 14. Risks

| Risk | Disposition |
|---|---|
| Anchor detection misses a header and merges two students | Deterministic count precedence plus mandatory group confirmation; both required, neither sufficient alone |
| Schools decline to print QR sheets | Anchor fallback is fully supported; QR is recommended, never required |
| Operator confirms groups carelessly at volume | Confirmation screen shows page thumbnails and count reconciliation together; overrun/shortfall groups cannot be bulk-confirmed |
| Bundle upload volume exceeds gateway limits | Per-page or chunked upload; server-side assembly (constraint 2) |
| Intake becomes a second document-ingestion stack | Reuse Document Intelligence, the files module, and Arq; no new pipeline |
| Late orphan pages accumulate unresolved | Exception queue is surfaced in the intake summary and blocks completeness, not evaluation of already-confirmed groups |

---

## 15. What this brief does not do

This brief does not authorize implementation, enable any feature flag, change
any `/api/v1` contract, modify any frozen release, or expand any certified
product claim. It defines a proposed gate for ARM review.
