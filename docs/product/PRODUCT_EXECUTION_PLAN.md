# StudyNexs Product Execution Plan

> **Living document** — update this file when product execution batches are accepted or re-prioritized.
> **Constitutional priority:** [`PRODUCT_EXECUTION_CONSTITUTION.md`](./PRODUCT_EXECUTION_CONSTITUTION.md)

**Last updated:** 2026-07-23
**Current governance state:** Batch 1, Batch 2, and Batch 3 are accepted and frozen; no implementation batch is currently authorized.

---

## Release train

| Release | Batch | Capability | Status | Evidence |
|---|---:|---|---|---|
| **Release 0.1** | **Batch 1** | Curriculum Intelligence | **Accepted / Frozen** | [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md) |
| **Release 0.2** | **Batch 2** | Academic Onboarding | **Accepted / Frozen** | [`BATCH_02_COMPLETION_REPORT.md`](./BATCH_02_COMPLETION_REPORT.md) |
| **Release 0.3** | **Batch 3** | School Pilot Experience | **Accepted / Frozen** | [`BATCH_03_COMPLETION_REPORT.md`](./BATCH_03_COMPLETION_REPORT.md) |
| **Release 0.4** | Batch 4 | Student + Parent Pilot Experience | Deferred | Not authorized |
| **Release 0.5** | Batch 5 | Pilot Operations / Assessment Reliability | Future | Not authorized |
| **Release 1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future | Not authorized |

Batch 1, Batch 2, and Batch 3 are immutable except for production defects, security fixes, or critical regressions.

---

## Batch Authorization

Only one batch may have status **AUTHORIZED** at any time.

| Field | Value |
|---|---|
| **Release** | None |
| **Batch** | None |
| **Title** | No current authorized batch |
| **Status** | **NO ACTIVE BATCH** |
| **Authorized by** | ARM approval required before Release 0.4 |
| **Authorization date** | Not applicable |
| **Previous batch** | Release 0.3 / Batch 3 — School Pilot Experience (**Frozen**) |
| **Next batch** | Release 0.4 — Not Authorized |

All other batches must be one of: Planned, Frozen, Deferred, or Completed.

---

## Current phase

**No active implementation batch**

### Status

**Release 0.3 / Batch 3 — School Pilot Experience is Accepted / Frozen. Release 0.4 is not authorized.**

### Objective completed

Batch 3 validated the smallest pilot-success slice: the existing Principal and Teacher journeys complete successfully without engineering assistance during the walkthrough.

### Product story

```text
Principal login
↓
Dashboard + curriculum readiness
↓
Academic Intelligence Ready
↓
Teacher login
↓
Assigned class/subject scope
↓
Approved CurriculumPack
↓
Grounded lesson plan
↓
Grounded question paper
↓
Principal + Teacher walkthrough PASS
```

### Primary personas

- School Principal
- Subject Teacher

### Architecture reuse requirements

Batch 3 reused the existing platform foundation:

- tenant resolution and `X-Tenant-Slug`;
- auth and RBAC;
- `CurriculumPack`;
- Knowledge Graph readiness;
- RAG retrieval and grounding;
- LLM gateway and AI credits;
- lesson-plan generation;
- question-paper generation;
- existing browser/API validation harness patterns.

### Hard constraints

Do **not** modify frozen releases except for:

- production defects;
- security fixes;
- critical regressions.

Do **not** start Release 0.4 until ARM explicitly authorizes it.

---

## Accepted batches

**Batch 3 — School Pilot Experience**

### Status

**Accepted / Frozen**

### Delivered capability

StudyNexs now has a validated Principal + Teacher pilot experience:

- Principal runtime proof;
- Teacher runtime proof;
- Principal browser walkthrough;
- Teacher browser walkthrough;
- tenant isolation verification;
- same-pack grounding verification for teacher lesson plan and question paper;
- focused Batch 3 validation harnesses.

### Acceptance evidence

See [`BATCH_03_COMPLETION_REPORT.md`](./BATCH_03_COMPLETION_REPORT.md).

### Commit

`649d835` — `feat(pilot): complete Batch 3 principal teacher proof`

### Freeze rule

Do not modify Batch 3 architecture or implementation except for:

- production defects;
- security fixes;
- critical regressions.

---

**Batch 2 — Academic Onboarding**

### Status

**Accepted / Frozen**

### Delivered capability

StudyNexs now has a curriculum-first onboarding loop:

- uploaded curriculum source intake;
- AI extraction into draft `CurriculumPack`;
- teacher/HOD human review;
- class-incharge/admin approval governance;
- KG + RAG readiness;
- deterministic same-pack evidence ledger;
- downstream proof across lesson plans, learning materials, question papers, assessment evaluation, mastery, student tutor/copilot, and parent copilot.

### Acceptance evidence

See [`BATCH_02_COMPLETION_REPORT.md`](./BATCH_02_COMPLETION_REPORT.md).

### Commit

`469c0f8` — `feat(onboarding): complete Batch 2 academic onboarding proof`

### Freeze rule

Do not modify Batch 2 architecture or implementation except for:

- production defects;
- security fixes;
- critical regressions.

---

**Batch 1 — Curriculum Intelligence**

### Status

**Accepted / Frozen**

### Delivered capability

StudyNexs now has an institutional curriculum memory foundation:

- teacher-owned curriculum drafts;
- class-incharge/admin approval governance;
- tenant-scoped `CurriculumPack` lifecycle;
- KG + RAG indexing on approval;
- same-pack grounding across lesson plans, question papers, tutor, and parent evidence paths.

### Acceptance evidence

See [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md).

### Commit

`63a5584` — `feat(curriculum): complete Batch 1 intelligence closure`

### Freeze rule

Do not modify Batch 1 architecture or implementation except for:

- production defects;
- security fixes;
- critical regressions.

---

## Deferred backlog

- Release 0.4 — Student + Parent Pilot Experience.
- Production async answer-sheet evaluation worker hardening.
- Pilot operations and deployment readiness.
- Full textbook PDF warehousing.
- Full textbook-to-`CurriculumPack` automation across arbitrary book layouts.
- Advanced report cards.
- Rich student practice engine.
- Public/prospect full learner loop.
