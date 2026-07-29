# Assessment Intelligence v1.0 Question Bank and Reuse Supported Scope Declarations

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Batch D foundation
> Authorization: ASSESSMENT-V1-BATCH-D-AUTH-001
> Runtime behavior: Unchanged
> Scope: Static question-bank and reuse declarations only

---

## 1. Purpose

This document declares the initial Assessment Intelligence v1.0 question-bank
and reuse support posture.

These declarations are static, read-only, and non-runtime. They make
school-private question reuse explicit without changing question-paper
generation, question-bank services, paper approval, answer-sheet evaluation,
exam services, AEI, EUI, API contracts, UI behavior, database schema, feature
flags, provider behavior, or LLM prompts.

---

## 2. Declaration rules

StudyNexs may claim question-bank reuse support only when all of the following
are true:

1. the reuse posture is declared in this document;
2. the declaration mode is `supported`;
3. the source item is approved;
4. the source and target are inside the same school-private scope;
5. class and subject scope match the declared support posture;
6. blueprint-slot suitability is explicit where compose is claimed;
7. teacher review and approval remain required before new paper authority;
8. academic answer evaluation still flows through AEI;
9. downstream evidence remains teacher-approved.

The product must not claim a global, cross-school, marketplace, or universal
question-bank.

---

## 3. Declared question-bank and reuse postures

### 3.1 Approved-paper ingestion

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://school-private/approved-paper-ingestion/v1` |
| Mode | `supported` |
| Reuse posture | `approved_paper_ingestion` |
| Source scope | Approved paper in the same school |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- source paper must be approved;
- source paper must belong to the school context;
- valid questions become bank items;
- blank questions do not become bank items;
- source paper provenance is required;
- answer-key/rubric context may be carried where present;
- teacher authority for new paper contexts remains required.

### 3.2 Idempotent re-approval

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://school-private/idempotent-reapproval/v1` |
| Mode | `supported` |
| Reuse posture | `idempotent_reapproval` |
| Source scope | Same source paper |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- re-approving a paper replaces prior bank rows for that source paper;
- source paper lineage remains stable;
- duplicate approval does not create duplicate source rows;
- runtime authority still requires teacher-approved paper state.

### 3.3 Same-school approved bank reuse

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://school-private/same-school-approved-reuse/v1` |
| Mode | `supported` |
| Reuse posture | `same_school_reuse` |
| Source scope | Same school, class, and subject |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- source bank item must be approved;
- source and target must belong to the same school;
- class and subject scope must match;
- source paper and source bank item provenance must be retained;
- reused question enters the target paper as reviewable draft content.

### 3.4 Blueprint-slot compose

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://school-private/blueprint-slot-compose/v1` |
| Mode | `supported` |
| Reuse posture | `blueprint_slot_compose` |
| Source scope | Same school, class, subject, marks, and question type |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- source bank item must be approved;
- marks must match the target blueprint slot;
- question type must match or be an explicitly accepted equivalent;
- selected bank item should not be reused twice in the same composed paper;
- answer-key/rubric availability must remain visible;
- composed paper remains draft until teacher approval.

### 3.5 Blueprint-slot topic overlap

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://school-private/blueprint-topic-overlap/v1` |
| Mode | `supported` |
| Reuse posture | `blueprint_slot_compose` |
| Source scope | Same school/class/subject with topic or concept overlap |
| Product claim allowed | Yes, inside this declared scope only |

Validation posture:

- topic or concept overlap may improve candidate ordering;
- overlap does not override tenant, approval, marks, or type requirements;
- missing EUI identity does not authorize a broader product claim;
- teacher review remains required.

### 3.6 Gap-fill assist

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://school-private/gap-fill-assist/v1` |
| Mode | `assist` |
| Reuse posture | `gap_fill_assist` |
| Source scope | Bank missing one or more blueprint slots |
| Product claim allowed | No |

Validation posture:

- generated gap-fill questions must be visibly non-bank;
- gap-fill provenance must be explicit;
- gap-fill questions must not be represented as approved bank reuse;
- answer-key/rubric posture must remain explicit or manual review;
- teacher approval remains required.

### 3.7 Changed-context reuse

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://school-private/changed-context-review/v1` |
| Mode | `manual_review` |
| Reuse posture | `changed_context_review` |
| Source scope | Same school but changed academic context |
| Product claim allowed | No |

Validation posture:

- changed board, curriculum, grade, chapter, paper type, language, academic
  year, or assessment purpose requires teacher review;
- previous approval remains provenance only;
- the system must not silently transfer product support claims;
- conflicts should be recorded for review where available.

### 3.8 Draft or unapproved bank item reuse

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://unsupported/draft-or-unapproved-bank-item/v1` |
| Mode | `unsupported` |
| Reuse posture | `unsupported_reuse` |
| Source scope | Draft, rejected, unknown, or unapproved bank item |
| Product claim allowed | No |

Validation posture:

- unsupported for v1.0;
- source must not be reused as approved bank content;
- teacher review or future approval workflow is required.

### 3.9 Cross-tenant reuse

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://unsupported/cross-tenant-reuse/v1` |
| Mode | `unsupported` |
| Reuse posture | `unsupported_reuse` |
| Source scope | Different school or tenant |
| Product claim allowed | No |

Validation posture:

- cross-school reuse is not a v1.0 supported claim;
- tenant isolation is mandatory;
- no marketplace or shared-bank behavior is implied.

### 3.10 Global or marketplace question bank

| Field | Value |
|---|---|
| Reuse Declaration ID | `assessment-bank-reuse://expansion/global-marketplace-bank/v1` |
| Mode | `expansion` |
| Reuse posture | `future_expansion` |
| Source scope | Future global or marketplace question bank |
| Product claim allowed | No |

Validation posture:

- future scope only;
- requires separate architecture, tenant/commercial policy, content licensing,
  teacher review, Golden Harness, and certification before support may be
  claimed.

---

## 4. Product claim posture

Allowed claims:

- approved paper ingestion into a school-private bank;
- idempotent re-approval behavior for the same source paper;
- same-school/class/subject approved-bank reuse posture;
- blueprint-slot compose when approval, marks, and type posture match;
- teacher-final authority.

Disallowed claims:

- automatic approval of reused questions in a new paper;
- autonomous paper approval;
- autonomous answer grading;
- direct marks from question-bank reuse;
- direct parent/student evidence before teacher approval;
- direct mastery update from unapproved reuse evidence;
- cross-school reuse;
- global question marketplace;
- universal question-bank support.

---

## 5. Batch D boundary

These declarations do not replace existing runtime question-bank handling.

Question-paper generation, question-bank services, paper approval, answer-sheet
evaluation, exam services, AEI, EUI, API contracts, UI behavior, feature flags,
provider behavior, LLM prompts, and database schema remain unchanged.
