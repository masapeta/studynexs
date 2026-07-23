# StudyNexs Product Execution Plan

> **Living document** — update this file when product execution batches are accepted or re-prioritized.
> **Constitutional priority:** [`PRODUCT_EXECUTION_CONSTITUTION.md`](./PRODUCT_EXECUTION_CONSTITUTION.md)

**Last updated:** 2026-07-23
**Current governance state:** Batch 1 accepted and frozen; Batch 2 authorized, implementation active.

---

## Release train

| Release | Batch | Capability | Status | Evidence |
|---|---:|---|---|---|
| **Release 0.1** | **Batch 1** | Curriculum Intelligence | **Accepted / Frozen** | [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md) |
| **Release 0.2** | **Batch 2** | Academic Onboarding | **AUTHORIZED** | [`CURRENT_BATCH.md`](./CURRENT_BATCH.md) |
| **Release 0.3** | Batch 3 | Assessment Intelligence | Deferred | Not authorized |
| **Release 1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future | Not authorized |

Batch 1 is immutable except for production defects, security fixes, or critical regressions.

---

## Batch Authorization

Only one batch may have status **AUTHORIZED** at any time.

| Field | Value |
|---|---|
| **Release** | 0.2 |
| **Batch** | 2 |
| **Title** | Academic Onboarding |
| **Status** | **AUTHORIZED** |
| **Authorized by** | ARM |
| **Authorization date** | 2026-07-23 |
| **Previous batch** | Release 0.1 / Batch 1 — Curriculum Intelligence (**Frozen**) |
| **Next batch** | Not Authorized |

All other batches must be one of: Planned, Frozen, Deferred, or Completed.

---

## Current phase

**Batch 2 — Academic Onboarding**

### Status

**AUTHORIZED. Implement Batch 2 only within the Academic Onboarding scope below.**

### Objective

Build the curriculum-first Academic Onboarding experience that teaches StudyNexs a school's curriculum and culminates in **Academic Intelligence Ready**.

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

- [ ] Academic Onboarding has a clear first-run entry point for a paid school.
- [ ] Supported curriculum sources are named honestly in the UI.
- [ ] Uploaded/pasted curriculum source creates a draft `CurriculumPack` through the existing extraction service.
- [ ] Teacher draft ownership and class-incharge/admin approval remain enforced.
- [ ] Approval triggers the existing KG + RAG pipeline.
- [ ] **Academic Intelligence Ready** is shown only after approval, KG success, RAG success, and retrievable topics/vectors.
- [ ] Lesson-plan generation cites the newly onboarded approved pack.
- [ ] Question-paper generation cites the newly onboarded approved pack.
- [ ] Grounding verification proves both outputs use the same approved `CurriculumPack`.
- [ ] Tenant isolation is verified for all Batch 2 routes.
- [ ] Runtime evidence is recorded in a Batch 2 completion report.

### Recommended implementation slices

| Slice | Scope | Acceptance |
|---|---|---|
| **2.1** | Source intake UX and API contract | UI and API describe supported sources without promising full textbook warehousing |
| **2.2** | Uploaded source → extraction handoff | Reuse Document Intelligence / extraction services; no parallel stack |
| **2.3** | Review/edit refinement | Draft structure can be reviewed and corrected before approval |
| **2.4** | Ready-state orchestration | Existing KG/RAG readiness drives the UI banner |
| **2.5** | End-to-end validation | Fresh school/source reaches ready pack and downstream citations |

---

## Accepted batch

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
- Full live answer-sheet OCR/evaluation automation.
- Advanced report cards.
- Rich student practice engine.
- Public/prospect full learner loop.
- Batch 3 — Assessment Intelligence.
