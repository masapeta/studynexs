# StudyNexs — Decision Log

> **Canonical location:** `docs/decisions/DECISION_LOG.md`  
> Owner: Avinash Reddy Masapeta (ARM) · **Living record** — never delete entries.

This file is the **authoritative Decision Log** in the governance hierarchy.  
See [`../README.md`](../README.md) for document precedence.

---

## 2026-07-23 — Batch 1 Curriculum Intelligence accepted and frozen

**Decision:** Accept **Batch 1 — Curriculum Intelligence** as Release 0.1 and freeze its architecture and implementation.

**Reason:** Batch 1 now has curriculum ownership, approval governance, tenant-scoped `CurriculumPack`, KG/RAG grounding, same-pack grounding across multiple AI capabilities, teacher-owned workflow, runtime validation, explicit limitations, and a fixed completion artifact.

**Acceptance evidence:**

- [`../product/BATCH_01_COMPLETION_REPORT.md`](../product/BATCH_01_COMPLETION_REPORT.md)
- commit `63a5584` — `feat(curriculum): complete Batch 1 intelligence closure`

**Freeze rule:** Do not modify Batch 1 except for production defects, security fixes, or critical regressions.

**Status:** Active

---

## 2026-07-23 — Batch 2 renamed to Academic Onboarding

**Decision:** Rename the next product execution batch to **Batch 2 — Academic Onboarding**.

**Reason:** The next capability is not merely textbook ingestion. It is the first curriculum-first experience a school has with StudyNexs: create/select school context, provide syllabus/TOC/curriculum source, AI extracts structure, human reviews, approval triggers KG/RAG, and the product reaches **Academic Intelligence Ready**.

**Architecture constraints:** Batch 2 must reuse `CurriculumPack`, Document Intelligence, `CurriculumExtractionService`, the existing approval workflow, `PackService.approve_pack()`, KG, RAG, the LLM gateway, and downstream AI grounding. It must not create a parallel curriculum engine or ingestion stack.

**Out of scope:** Full textbook warehousing, complete OCR automation, advanced report cards, rich student practice engine, and Batch 3 assessment automation.

**Status:** Superseded by Batch 2 authorization entry below.

**References:** [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md) · [`../product/RELEASE_HISTORY.md`](../product/RELEASE_HISTORY.md)

---

## 2026-07-23 — Batch 2 Academic Onboarding authorized

**Decision:** Authorize **Release 0.2 / Batch 2 — Academic Onboarding** to begin implementation.

**Scope:** Build the curriculum-first onboarding experience that lets a school provide a syllabus / TOC / curriculum source, creates a draft `CurriculumPack`, supports human review, approves through the existing governance workflow, triggers KG/RAG indexing, reaches **Academic Intelligence Ready**, and proves downstream lesson-plan and question-paper generation ground on the same newly approved pack.

**Constraints:** Reuse `CurriculumPack`, Document Intelligence, `CurriculumExtractionService`, the existing approval workflow, `PackService.approve_pack()`, KG, RAG, the LLM gateway, AI credits, RBAC, and downstream grounding. Do not build a second curriculum engine, parallel ingestion service, full textbook warehousing, complete OCR automation, advanced report cards, rich student practice engine, or Batch 3 assessment expansion.

**Operational rule:** During Batch 2, do not create intermediate planning/governance documents. Update governance only when Batch 2 is complete or when ARM explicitly requests it.

**Status:** Active

**References:** [`../product/CURRENT_BATCH.md`](../product/CURRENT_BATCH.md) · [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md)

---

## 2026-07-22 — Stage 2A: Production Academic Onboarding Core (authorized)

**Decision:** Ship **Academic Onboarding** for permanent paid-school tenants first — admin/HOD supplies board/class/subject/textbook metadata plus permitted curriculum inputs (TOC, syllabus, chapter list); AI proposes a draft CurriculumPack; HOD/principal reviews/edits and approves; approval triggers existing KG spine + RAG indexing via `PackService.approve_pack`; UI shows **Academic Intelligence Ready** only after both KG and RAG audit events succeed.

**Reason:** Schools must teach StudyNexs their curriculum once before lesson plans, question papers, and tutor surfaces can be grounded and trustworthy. Stage 1 localhost validation is accepted; Gate 1A HTTPS remains a separate deployment gate. This slice reuses the existing platform — no parallel curriculum, graph, RAG, or AI stacks.

**Alternatives:** (1) Manual-only pack builder (Slice 1) — rejected for paid onboarding scale; (2) Full textbook warehousing — rejected (copyright + constitution §39.1); (3) Public self-guided demo tenants in same slice — deferred to later stage.

**Out of scope (Stage 2A):** Public signup, tenant cloning, TTL cleanup, digital student assessment, parent automation.

**Implementation seams (reuse, do not duplicate):**
- `CurriculumExtractionService` → LLM gateway + credits (`curriculum_extraction`, 3 credits)
- `PackService.populate_draft_structure` / `approve_pack` → KG + RAG side effects
- `GET /packs/{id}/intelligence-status` → readiness gate for UI banner
- Admin UI: `/dashboard/teaching/curriculum/onboarding` wizard + `AcademicIntelligenceBanner` on curriculum, lesson-plans, ai-papers

**Status:** ✅ Active (Stage 2A shipped — ARM accepted 2026-07-22)

**References:** [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md) · [`../showcase/DEMO_EXPERIENCE_GAP_ANALYSIS.md`](../showcase/DEMO_EXPERIENCE_GAP_ANALYSIS.md)

---

## 2026-07-17 — Product Execution Phase begins

**Decision:** Close Platform Foundation Phase; adopt Product Execution Constitution v1.0 and governance hierarchy.

**Reason:** Platform, governance, and Design System v1 are complete. Engineering priority shifts to educational capabilities (Batch 1: Curriculum Intelligence).

**Alternatives:** Continue platform polish (Phase 3B UI); parallel batch work — rejected per scope discipline.

**Status:** ✅ Active

**References:**

- [`../product/PRODUCT_EXECUTION_CONSTITUTION.md`](../product/PRODUCT_EXECUTION_CONSTITUTION.md)
- [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md)
- [`../design/PLATFORM_DESIGN_SYSTEM_V1.md`](../design/PLATFORM_DESIGN_SYSTEM_V1.md)

---

## Prior decisions

Historical decisions from the Platform Foundation Phase and earlier product work are preserved in the archive:

**[`../DECISION_LOG_ARCHIVE.md`](../DECISION_LOG_ARCHIVE.md)**

(New entries from 2026-07-17 onward are appended to this file.)

---

## Entry template

```
## YYYY-MM-DD — Title

**Decision:**

**Reason:**

**Alternatives:**

**Status:** Active | Superseded | Deferred
```
