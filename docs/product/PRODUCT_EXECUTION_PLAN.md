# StudyNexs Product Execution Plan

> **Living document** — update this file when product execution batches are accepted or re-prioritized.
> **Constitutional priority:** [`PRODUCT_EXECUTION_CONSTITUTION.md`](./PRODUCT_EXECUTION_CONSTITUTION.md)

**Last updated:** 2026-07-23
**Current governance state:** Batch 1 and Batch 2 accepted and frozen; no implementation batch is currently authorized.

---

## Release train

| Release | Batch | Capability | Status | Evidence |
|---|---:|---|---|---|
| **Release 0.1** | **Batch 1** | Curriculum Intelligence | **Accepted / Frozen** | [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md) |
| **Release 0.2** | **Batch 2** | Academic Onboarding | **Accepted / Frozen** | [`BATCH_02_COMPLETION_REPORT.md`](./BATCH_02_COMPLETION_REPORT.md) |
| **Release 0.3** | Batch 3 | Assessment Intelligence | Deferred | Not authorized |
| **Release 1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future | Not authorized |

Batch 1 and Batch 2 are immutable except for production defects, security fixes, or critical regressions.

---

## Batch Authorization

Only one batch may have status **AUTHORIZED** at any time.

| Field | Value |
|---|---|
| **Release** | None |
| **Batch** | None |
| **Title** | No current authorized batch |
| **Status** | **NO ACTIVE BATCH** |
| **Authorized by** | ARM approval required before Batch 3 |
| **Authorization date** | Not applicable |
| **Previous batch** | Release 0.2 / Batch 2 — Academic Onboarding (**Frozen**) |
| **Next batch** | Release 0.3 / Batch 3 — Not Authorized |

All other batches must be one of: Planned, Frozen, Deferred, or Completed.

---

## Current phase

**No active implementation batch**

### Status

**Release 0.2 / Batch 2 — Academic Onboarding is Accepted / Frozen. Batch 3 is not authorized.**

### Objective

Batch 2 delivered the curriculum-first Academic Onboarding experience that teaches StudyNexs a school's curriculum and culminates in **Academic Intelligence Ready**, then proved downstream AI grounding through the same approved `CurriculumPack`.

### Product story

```text
Create School
↓
Upload Syllabus / TOC / Curriculum Source
↓
AI extracts structure
↓
Human review
↓
Approve CurriculumPack
↓
KG + RAG indexing
↓
Academic Intelligence Ready
↓
Generate Lesson Plan
↓
Generate Question Paper
↓
Grounding Verified
↓
Downstream AI capabilities use the same approved CurriculumPack
```

### Primary persona

School principal / academic coordinator, with teacher participation for subject-level curriculum ownership.

### Architecture reuse requirements

Batch 2 must reuse the existing Batch 1 foundation:

- `CurriculumPack`
- `CurriculumExtractionService`
- `DocumentIntelligenceService`
- existing approval workflow
- `PackService.approve_pack()`
- Knowledge Graph spine
- RAG indexing and retrieval
- LLM gateway + AI credits
- existing role/RBAC model

### Hard constraints

Do **not** build:

- a second curriculum engine;
- a parallel ingestion service;
- full textbook warehousing;
- complete OCR automation for all textbook formats;
- advanced report-card workflows;
- rich student practice engine;
- Batch 3 / Assessment Intelligence work.

### Batch 2 deliverable

A principal or academic coordinator can start with a real curriculum source and reach an approved, indexed, ready curriculum pack:

1. Create/select school context.
2. Select class, subject, academic year, board, and source metadata.
3. Upload or provide a syllabus / TOC / curriculum source.
4. AI extracts chapter/topic/outcome structure into a draft `CurriculumPack`.
5. Teacher/academic coordinator reviews and edits.
6. Class incharge/admin approves.
7. KG + RAG indexing completes.
8. UI shows **Academic Intelligence Ready**.
9. Generate a lesson plan from the newly approved pack.
10. Generate a question paper from the newly approved pack.
11. Verify grounding/citations point back to the same approved pack.
12. Tutor and parent surfaces continue to ground on the same approved pack where their current flows support it.

### Batch 2 acceptance criteria

- [x] Academic Onboarding has a clear first-run entry point for a paid school.
- [x] Supported curriculum sources are named honestly in the UI.
- [x] Uploaded/pasted curriculum source creates a draft `CurriculumPack` through the existing extraction service.
- [x] Teacher draft ownership and class-incharge/admin approval remain enforced.
- [x] Approval triggers the existing KG + RAG pipeline.
- [x] **Academic Intelligence Ready** is shown only after approval, KG success, RAG success, and retrievable topics/vectors.
- [x] Lesson-plan generation cites the newly onboarded approved pack.
- [x] Question-paper generation cites the newly onboarded approved pack.
- [x] Grounding verification proves both outputs use the same approved `CurriculumPack`.
- [x] Tenant isolation is verified for all Batch 2 routes.
- [x] Runtime evidence is recorded in a Batch 2 completion report.

### Recommended implementation slices

| Slice | Scope | Acceptance |
|---|---|---|
| **2.1** | Source intake UX and API contract | UI and API describe supported sources without promising full textbook warehousing |
| **2.2** | Uploaded source → extraction handoff | Reuse Document Intelligence / extraction services; no parallel stack |
| **2.3** | Review/edit refinement | Draft structure can be reviewed and corrected before approval |
| **2.4** | Ready-state orchestration | Existing KG/RAG readiness drives the UI banner |
| **2.5** | End-to-end validation | Fresh school/source reaches ready pack and downstream citations |

---

## Accepted batches

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

### Batch 1 acceptance criteria

| Criterion | Status |
|---|---:|
| Teacher creates curriculum through admin UI/onboarding path | ✅ Accepted |
| Pack reaches approved state with audit trail | ✅ Accepted |
| RAG index reflects approved content, tenant-scoped | ✅ Accepted |
| At least two AI capabilities cite the same `CurriculumPack` | ✅ Accepted |
| Capability acceptance document completed | ✅ Accepted |

### Freeze rule

Do not modify Batch 1 architecture or implementation except for:

- production defects;
- security fixes;
- critical regressions.

---

## Deferred backlog

- Full textbook PDF warehousing.
- Full textbook-to-`CurriculumPack` automation across arbitrary book layouts.
- Production async answer-sheet evaluation worker hardening.
- Advanced report cards.
- Rich student practice engine.
- Public/prospect full learner loop.
- Batch 3 — Assessment Intelligence.
