# StudyNexs Product Execution Plan

> **Living document** — update this file as batch progress changes.  
> **Constitutional priority:** [`PRODUCT_EXECUTION_CONSTITUTION.md`](./PRODUCT_EXECUTION_CONSTITUTION.md)

**Last updated:** 2026-07-22 (Stage 2A — Academic Onboarding Core shipped, uncommitted)

---

## Current slice (in progress)

| Slice | Scope | Status |
|-------|--------|--------|
| **1** | Admin draft pack builder — create pack, add chapters/topics, view structure, approve | ✅ Shipped |
| **2A** | **Academic Onboarding** — AI draft from syllabus/TOC, HOD review, approve → KG+RAG, intelligence-ready banner | ✅ Shipped (ARM review) |
| **2B** | Public self-guided + sales-demo tenants (clone, TTL) | ⬜ Deferred |
| **3** | Learning outcomes per topic (schema + API) | 🟡 Partial (onboarding populates LOs) |
| **4** | Audit trail display + formal log on approve | 🟡 Partial (audit events + UI labels) |

**Stage 2A entry points:**
- API: `POST /api/v1/curriculum/onboarding/propose`, `GET …/intelligence-status`, `POST …/retry-rag-index`, `PUT …/topics/{id}`
- UI: `/dashboard/teaching/curriculum/onboarding`, `AcademicIntelligenceBanner` on curriculum / lesson-plans / ai-papers
- Tests: `apps/api/tests/test_academic_onboarding.py` (15); `e2e-onboarding-review.cjs`

**Slice 1 files:** `apps/admin-web/src/app/dashboard/teaching/curriculum/page.tsx` (wires existing pack APIs; no backend changes)

## Current release

Targeting **Batch 1 completion** — institutional curriculum memory as shared grounding for all AI capabilities.

---

## Current batch

**Batch 1 — Curriculum Intelligence**

### Mission

Create the institutional memory of the school's curriculum.

### Primary persona

**Teacher / academic coordinator** (with principal oversight for pack approval)

### Problem being solved

Curriculum knowledge is scattered across PDFs, WhatsApp forwards, and teacher memory. AI features cannot be consistent or trustworthy without a single approved academic source per school.

### Educational capability delivered

A school uploads curriculum once; every AI capability retrieves curriculum knowledge consistently from the shared **CurriculumPack**.

---

## Objectives

1. Ingest and structure curriculum content (subject → grade → chapter → topic → outcomes).
2. Index curriculum for retrieval (RAG) with tenant + pack isolation.
3. Expose search and AI retrieval APIs scoped by `school_id`.
4. Provide administration UI for pack lifecycle (draft → review → approve).
5. Prove end-to-end: **teacher uploads once → QP / tutor / copilot cite the same pack**.

---

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| 1 | CurriculumPack ingestion | 🟡 Partial | API ingest endpoints exist; document upload path |
| 2 | Subject hierarchy | 🟡 Partial | Pack/chapter/topic model in API |
| 3 | Grade hierarchy | 🟡 Partial | Class/subject linkage in packs |
| 4 | Learning outcomes | ⬜ | Structured outcomes per topic |
| 5 | Chapter mapping | 🟡 Partial | Admin UI: add chapter + topic on draft packs |
| 6 | Topic mapping | 🟡 Partial | Concepts on chapter add; RAG unit unchanged |
| 7 | Metadata extraction | 🟡 Partial | Ingest pipeline; expand coverage |
| 8 | Curriculum RAG indexing | 🟡 Partial | Qdrant indexing via `RagService` |
| 9 | Search APIs | 🟡 Partial | RAG retrieval endpoints |
| 10 | AI Retrieval APIs | 🟡 Partial | Gateway-grounded retrieval; wire all consumers |
| 11 | Curriculum Administration UI | 🟡 Partial | Create draft, chapter editor, approve — Slice 1 ✅ |

**Legend:** ✅ Done · 🟡 Partial · ⬜ Not started

---

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| M1 — Pack CRUD + approval workflow API complete | Batch 1 | 🟡 |
| M2 — RAG index + retrieval APIs tenant-scoped | Batch 1 | 🟡 |
| M3 — Admin UI: upload, review, approve | Batch 1 | 🟡 Slice 1: draft create + chapter add ✅ |
| M4 — Assessment QP consumes approved pack (proof) | Batch 1 | 🟡 Exists for QP; generalize |
| M5 — Capability acceptance evidence + demo scenario | Batch 1 | ⬜ |

---

## Progress

**Overall:** In progress — substantial API foundation; batch not yet acceptance-complete.

Do not start Batch 2 until Batch 1 acceptance criteria are met and documented.

---

## Dependencies

- Postgres + Qdrant (docker compose dev stack)
- AI Gateway (metered LLM calls)
- Tenant isolation via `school_id` on all curriculum queries
- Platform Design System v1 for admin UI (no redesign)

---

## Known risks

| Risk | Mitigation |
|------|------------|
| Ingest quality varies by board/format | Human review step before approve |
| RAG drift across features | Single CurriculumPack contract; refuse ungrounded generation |
| Scope creep into Assessment batch | Finish curriculum memory first |

---

## Blocked items

| Item | Blocker |
|------|---------|
| Phase 3B.1 Parent portal parity | Separate implementation plan — not Batch 1 |
| Phase 3B.2 Parent experience strategy | UX exploration only |

---

## Success criteria (batch acceptance)

- [ ] A teacher uploads curriculum once through the admin UI. _(Slice 1: manual chapter entry ✅; document ingest path separate)_
- [ ] Pack reaches **approved** state with audit trail.
- [ ] RAG index reflects approved content (tenant-scoped).
- [ ] At least two AI capabilities (e.g. QP generation + one retrieval API) cite the **same** CurriculumPack consistently.
- [ ] Capability acceptance document completed per Constitution.

---

## Release checklist

- [ ] API tests pass for curriculum module
- [ ] Tenant isolation verified on all curriculum routes
- [ ] Admin UI uses Design System v1 (no new platform layers)
- [ ] Demo scenario recorded
- [ ] Decision Log entry for batch completion
- [ ] `STATUS.md` updated

---

## Acceptance criteria (capability evidence template)

_To complete when Batch 1 ships:_

| Field | Value |
|-------|-------|
| Capability Delivered | |
| Problem Solved | |
| Primary Persona | |
| Business Outcome | |
| Time Saved | |
| Manual Work Eliminated | |
| AI Capability Enabled | |
| Future Capabilities Unlocked | |
| Evidence | |
| Demonstration Scenario | |
| Release Recommendation | |

---

## Next batch preview

**Batch 2 — Assessment Intelligence** (not started)

Assessment generation, evaluation, and grading loops grounded in Batch 1 curriculum memory.

**Do not implement Batch 2 until Batch 1 is accepted.**
