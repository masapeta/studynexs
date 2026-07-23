# StudyNexs Current Batch

> Single operational execution artifact for the active implementation batch.

**Last updated:** 2026-07-23

---

## Current Batch

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

---

## Mission

Build the curriculum-first onboarding experience that teaches StudyNexs a school's curriculum and culminates in **Academic Intelligence Ready**.

The onboarding loop must prove that the newly approved `CurriculumPack` is actually used by downstream AI:

```text
Curriculum source
↓
AI draft CurriculumPack
↓
Human review
↓
Approval
↓
KG + RAG indexing
↓
Academic Intelligence Ready
↓
Lesson Plan
↓
Question Paper
↓
Grounding Verified
```

---

## Acceptance Criteria

- Academic Onboarding has a clear first-run entry point for a paid school.
- Supported curriculum sources are named honestly in the UI.
- Uploaded or pasted curriculum source creates a draft `CurriculumPack` through existing extraction services.
- Teacher draft ownership and class-incharge/admin approval remain enforced.
- Approval triggers the existing KG + RAG pipeline.
- **Academic Intelligence Ready** appears only after approval, KG success, RAG success, and retrievable topics/vectors.
- Lesson-plan generation cites the newly onboarded approved pack.
- Question-paper generation cites the newly onboarded approved pack.
- Grounding verification proves both outputs use the same approved `CurriculumPack`.
- Tenant isolation is verified for all Batch 2 routes.
- Runtime evidence is recorded at Batch 2 completion.

---

## Out of Scope

- Full textbook warehousing.
- A second curriculum engine.
- Parallel ingestion services.
- Complete OCR automation across arbitrary book layouts.
- Advanced report cards.
- Rich student practice engine.
- Batch 3 / Assessment Intelligence expansion.

---

## Known Risks

- Real-world curriculum sources vary widely in quality and structure.
- PDF/OCR behavior must be described honestly until full textbook automation is authorized.
- Long-running KG/RAG processing needs clear progress and retry behavior.
- Downstream grounding must fail clearly if the approved pack is not ready.

---

## Definition of Done

- Build passes.
- Focused API tests pass.
- Web build and type check pass.
- Runtime smoke proves source → draft pack → review → approval → ready.
- Downstream lesson-plan and question-paper generation cite the same newly approved pack.
- Browser walkthrough validates the paid-school onboarding journey as far as the local environment allows.
- Batch 2 completion documentation is produced only after implementation is complete.

---

## Current Progress

Authorized. Implementation not yet started.
