# Batch 1 Reconciliation Plan — academix-platform → studynexs-dev

> **Status:** ✅ **Complete** — Batch 1 reconciled on `studynexs-dev` (P3–P6 approved)  
> **Date:** 2026-07-20  
> **Source baseline (archived):** `v0.1.0-batch1` @ `513c3a3` in `D:\Projects\academix-platform` — now Reference Archive  
> **Destination repository:** `D:\Projects\studynexs-platform\studynexs-dev` (`develop`)  
> **Release tag (pending PO):** `v0.1.0-batch1` on RC commit

---

## 1. Purpose

Development is **paused**. This document compares every verified Batch 1 capability from the frozen `v0.1.0-batch1` baseline against the current canonical `studynexs-dev` tree, classifies gaps and conflicts, and proposes a **reconciliation strategy only**.

**Explicit non-goals (until plan approval):**

- No git merge, cherry-pick, or rebase
- No automatic file overwrite
- No changes to Knowledge Graph, Hybrid RAG, or Copilot implementations already on `develop`
- No claim that Gate 2 / T-0 authorization applies to `studynexs-dev` (those were validated on `academix-platform`)

**Implementation may begin only after this plan is approved.**

---

## 2. Repository divergence

Both repositories share a common ancestor:

| Item | Value |
|------|-------|
| **Merge-base** | `5f76c00` (`integration/studynexs`) |
| **academix-platform path** | +1 commit → `513c3a3` (`v0.1.0-batch1`) |
| **studynexs-dev path** | +38 commits → `45ed42a` (Batches 17–28 + Engineering OS docs) |

The two lines **diverged in parallel** from the same parent. Batch 1 was frozen in `academix-platform`; KG, ConceptCard, Content Review, Hybrid RAG, and Copilots landed on `studynexs-dev` `develop`.

```
5f76c00 (integration/studynexs)
    ├── academix-platform → 513c3a3 [v0.1.0-batch1]  (Batch 1 frozen)
    └── studynexs-dev/develop → 45ed42a              (Batches 17–28)
```

| Property | academix-platform | studynexs-dev |
|----------|-------------------|---------------|
| Batch 1 tag | ✅ `v0.1.0-batch1` | ❌ None |
| Gate 2 ops package | ✅ `docs/pilot/gate2/*` | ❌ None |
| T-0 evidence | ✅ `docs/pilot/naagarjuna-talent-school/t0-evidence/` | ❌ None |
| Batches 17–28 | ❌ Not on `integration/studynexs` | ✅ On `develop` |
| Remote | GitHub `masapeta/academix-platform` | `origin` → local path to academix |

---

## 3. Classification legend

| Status | Meaning |
|--------|---------|
| **Already exists** | Capability present on `studynexs-dev` `develop` (committed); meets or overlaps Batch 1 intent |
| **Better implementation already exists** | `studynexs-dev` has a superset or improved design; port Batch 1 only where it adds governance/pilot parity |
| **Missing** | Not present on `studynexs-dev`; must be reconciled from source |
| **Conflict — product decision required** | Both sides implement the capability differently; reconciling without a decision risks regressions or overwriting protected work |

---

## 4. Capability reconciliation matrix

Source: 13 capabilities in [`BATCH_1_PILOT_READINESS.md`](../../academix-platform/docs/product/BATCH_1_PILOT_READINESS.md).

| # | Batch 1 capability | Status | studynexs-dev evidence | Source (v0.1.0-batch1) | Reconciliation notes |
|---|-------------------|--------|------------------------|------------------------|----------------------|
| 1 | **CurriculumPack CRUD (draft)** | **Already exists** | `curriculum/endpoints/pack.py`, admin UI `teaching/curriculum/page.tsx` | Same endpoints + simpler UI | Extend UI for LO/audit; do not replace KG/concept-card panels |
| 2 | **Chapter / topic structure** | **Already exists** | Pack builder with chapters + topics + `concepts[]` on topics | Chapters + topics (no concepts field) | studynexs adds **concepts per topic** (Batch 17+). Keep concepts; add LO as sibling field |
| 3 | **Learning outcomes per topic/chapter** | **Missing** | No `CurriculumLearningOutcome` model, API, UI, or RAG LO vectors | `x4f5a6b7c8d9_learning_outcomes.py`, pack CRUD LO endpoints, UI step 5 | **Port schema + API + UI + RAG LO indexing** (see §6.1) |
| 4 | **HOD approval → immutable pack** | **Already exists** | `pack_service.approve_pack`, `POST .../approve` | Same | Behavior diverges on post-approve side effects (see #5) |
| 5 | **RAG publish on approve** | **Conflict — product decision** | Approve → `KnowledgeGraphService.build_spine_from_pack` only; RAG index is **lazy** on first `ground_for_pack` call | Approve → `RagService.index_pack` + `rag_indexed_at` / audit events | **Decision:** run KG spine **and** eager RAG index on approve, or keep lazy index? (§7.1) |
| 6 | **Curriculum audit trail** | **Missing** | No `pack_audit.py`, no `GET .../audit`, no admin audit panel | `y5a6b7c8d9e0_pack_audit_events.py`, `PackAuditService`, UI step 9 | Port append-only audit API + UI panel |
| 7 | **Grounded question paper generation** | **Better implementation already exists** | `assessment_grounding.py` + **Hybrid RAG** (`hybrid.py`), self-healing index, eval grounding; QP UI has grounding toggle | Batch 1 uses `ground_approved_pack()` wrapper + simpler RAG | Add **facade** (`curriculum_grounding.py`) calling hybrid path; wire QP through facade for pack validation + provenance parity (§6.2) |
| 8 | **Grounded lesson plan (provenance)** | **Conflict — product decision** | Schema columns exist (`w3d4e5f6a7b8_lesson_plan_grounding`); **Teacher Copilot** LLM path when `pack_id` set; `lesson_plan_service.py` is template-only without grounding | Batch 1 template + `ground_approved_pack()` + `CurriculumGroundingBadge` | **Decision:** pilot demo uses template+provenance (Batch 1) or Copilot LLM (Batch 23+)? Can support both behind flag (§7.2) |
| 9 | **Shared grounding layer (`ground_approved_pack`)** | **Missing** (partial substitute) | Direct `ground_for_pack()` + Copilot services; no shared pack-validation facade | `curriculum_grounding.py` | **Port as thin facade** over existing Hybrid RAG — do not replace `assessment_grounding` internals (§6.2) |
| 10 | **Tenant-scoped retrieval** | **Already exists** | `test_rag.py::test_retrieval_is_tenant_scoped`, `test_vectorstore.py`, `test_curriculum_pack.py` cross-tenant | Same + Batch 1 LO vector tests | Add LO-scoped vector tests when #3 lands |
| 11 | **Pilot seed scripts** | **Missing** | No `seed_pilot_naagarjuna*.py` | `apps/api/scripts/seed_pilot_naagarjuna.py`, `seed_pilot_naagarjuna_curriculum.py` | Port scripts; adapt if LO + KG coexist |
| 12 | **Smoke readiness script** | **Missing** | No `smoke_pilot_readiness.py` | 12-check script (validated 12/12 at T-0) | Port script; extend checks for KG/Copilot if needed |
| 13 | **End-to-end UI workflow (11/11)** | **Missing** | No `batch1-ui-workflow-demo.cjs`; curriculum UI is KG/concept-card oriented | Playwright 11/11 + screenshot artifacts | Port demo script; update selectors for merged UI; re-run on studynexs-dev post-reconciliation |

### 4.1 Supporting infrastructure (not numbered in readiness doc)

| Item | Status | Notes |
|------|--------|-------|
| Docker `[rag]` dependency | **Already exists** | Both Dockerfiles install `.[ai,rag,observability]` |
| Batch 1 Alembic chain (`w3`–`z6` Batch 1 semantics) | **Conflict — product decision** | Revision ID collisions (§7.3) |
| Batch 1 product docs (`BATCH_1_*`) | **Missing** | Copy from academix; update for merged architecture |
| Gate 2 pilot ops package | **Missing** | Copy from academix; re-validate on studynexs-dev before GO |
| T-0 evidence artifacts | **Missing** | Historical record from academix; **new T-0 required** on canonical repo |
| Git tag `v0.1.0-batch1` | **Missing** | Apply **after** reconciliation + re-validation, not before |
| `apply_batch1_schema.sql` dev patch | **Missing** | Optional; prefer proper new migrations on studynexs-dev |

---

## 5. Protected assets — do not overwrite

These exist only on `studynexs-dev` `develop` and must survive reconciliation:

| Area | Key paths | Batch |
|------|-----------|-------|
| **Knowledge Graph** | `app/modules/knowledge_graph/**`, `y5f6a7b8c9d0_knowledge_graph_spine.py`, graph endpoints | 17 |
| **Hybrid RAG** | `app/modules/ai/rag/hybrid.py`, curriculum RAG endpoints | 19+ |
| **ConceptCard** | `concept_card_service.py`, `z6a7b8c9d0e1_concept_cards.py` | 18 |
| **Content Review** | `content_review_service.py`, `b9c0d1e2f3a4_content_review_queue.py` | 20 |
| **Document ingest** | `x4e5f6a7b8c9_document_ingestions.py`, ingest UI | 19 |
| **Teacher Copilot** | `teacher_copilot_service.py`, `test_teacher_copilot.py` | 23 |
| **Student Copilot** | tutor endpoints + UI (Batch 25–26) | 25–26 |
| **Parent Copilot** | parent API + UI (Batch 27–28) | 27–28 |
| **Question–concept links** | `question_concept_link_service.py`, weak-concept migrations | 22+ |

**Reconciliation principle:** Batch 1 capabilities are **additive** — they must compose with KG/Copilot/Hybrid RAG, not replace them.

---

## 6. Proposed reconciliation approach (post-approval)

### 6.1 Learning outcomes (capability #3)

**Port from source:**

- Model: `CurriculumLearningOutcome` (+ indexes)
- Migrations: **new revision IDs** (never reuse `x4f5a6b7c8d9` — see §7.3)
- API: LO CRUD on pack endpoints (`add_topic_learning_outcome`, etc.)
- RAG: LO vector indexing in `RagService.index_pack` (Batch 1 indexes topics **and** LOs)
- UI: LO fields in curriculum builder (preserve concept-card / KG panels)

**Compose with KG:** LOs feed RAG; concepts feed KG spine — both can attach to the same topic.

### 6.2 Shared grounding facade (capabilities #7, #9)

**Do not revert** `assessment_grounding.py` to Batch 1 pre-hybrid version.

Instead:

1. Add `curriculum_grounding.py` on studynexs-dev where `ground_approved_pack()`:
   - Validates pack is APPROVED and tenant/class/subject match (Batch 1 contract)
   - Delegates retrieval to existing `ground_for_pack()` (Hybrid RAG + self-heal index)
   - Returns `CurriculumGrounding` with pack provenance metadata
2. Update `question_paper_service.py` to call `ground_approved_pack()` instead of raw `ground_for_pack()` (preserves hybrid retrieval underneath)
3. Add `GET /packs/{id}/grounding` preview endpoint (Batch 1)

### 6.3 Approve side effects (capability #5)

**Recommended default (pending §7.1 approval):**

```text
approve_pack():
  1. Set status APPROVED (existing)
  2. build_spine_from_pack()     ← keep (KG)
  3. index_pack() + audit event  ← add (Batch 1 RAG-on-approve)
  4. Record rag_index_* columns  ← add (Batch 1 observability)
```

Lazy self-heal in `ground_for_pack` remains as safety net.

### 6.4 Audit trail (capability #6)

Port `pack_audit.py` + `GET /packs/{id}/audit` + admin UI panel. Events: create, edit, approve, rag_index success/failure. **Separate** from global `audit_logs` (Batch 1 design).

### 6.5 Lesson plan grounding (capability #8)

**Recommended default (pending §7.2 approval):**

- **Pilot / Batch 1 parity path:** template plan + `ground_approved_pack()` provenance (matches validated 11-step demo)
- **Teacher Copilot path:** retain `generate_grounded_lesson_plan()` when copilot flag/body field set
- UI: port `CurriculumGroundingBadge` for provenance display on both paths

### 6.6 Pilot ops & validation (capabilities #11–13)

1. Port seed + smoke scripts
2. Port `batch1-ui-workflow-demo.cjs` (+ Gate 2 T-0 script if needed)
3. Copy Gate 2 docs as **reference**, then re-run T-0 on studynexs-dev
4. Tag `v0.1.0-batch1` on studynexs-dev only after smoke 12/12 + UI 11/11 + product sign-off

---

## 7. Conflicts requiring product decision

### 7.1 RAG indexing timing (capability #5)

| Option | Pros | Cons |
|--------|------|------|
| **A — Eager on approve (Batch 1)** | Predictable latency at demo; audit trail on index; matches frozen tests | Duplicate work if lazy index also runs; slightly longer approve |
| **B — Lazy on first grounding (studynexs today)** | Faster approve; hybrid self-heal | First QP/LP slower; no `rag_indexed_at` governance; Batch 1 tests fail |
| **C — Both (recommended)** | Batch 1 governance + lazy safety net | Two index calls (idempotent) |

**Decision needed:** A, B, or C?

### 7.2 Lesson plan generation mode (capability #8)

| Option | Pros | Cons |
|--------|------|------|
| **A — Batch 1 template + provenance only** | Matches validated 11/11 demo; no LLM cost | Less impressive prose |
| **B — Teacher Copilot LLM only** | Richer plans | Different from frozen Batch 1 acceptance |
| **C — Both with explicit UI toggle (recommended)** | Pilot uses A; production can use B | Two code paths to maintain |

**Decision needed:** A, B, or C?

### 7.3 Alembic revision ID collisions

The repos reused the same revision IDs for **different** migrations after `v2c3d4e5f6a7`:

| Revision ID | academix (`v0.1.0-batch1`) | studynexs-dev (`develop`) |
|-------------|---------------------------|---------------------------|
| `w3d4e5f6a7b8` | `pack_rag_index_status` (rag_index columns on packs) | `lesson_plan_grounding` (pack_id on lesson_plans) |
| `z6a7b8c9d0e1` | `lesson_plan_grounding` | `concept_cards` table |

Additional Batch 1 migrations with **no collision** (safe to port with original IDs if chained correctly):

- `x4f5a6b7c8d9` — learning outcomes (studynexs uses `x4e5f6a7b8c9` for document ingest — different ID ✅)
- `y5a6b7c8d9e0` — pack audit events (studynexs uses `y5f6a7b8c9d0` for KG — different ID ✅)

**Decision needed:** Approve **new migration chain** on studynexs-dev with fresh revision IDs for:

1. `curriculum_learning_outcomes` table
2. `curriculum_pack_audit_events` table
3. `rag_index_*` columns on `curriculum_packs`
4. Any LO-related RAG metadata columns

**Do not** rename or replace existing `w3d4e5f6a7b8` / `z6a7b8c9d0e1` files on studynexs-dev.

### 7.4 Gate 2 authorization scope

T-0 GO was issued against **academix-platform** runtime. studynexs-dev has **not** been validated.

**Decision needed:** Confirm that Gate 2 authorization **transfers** after reconciliation + new T-0 on studynexs-dev, or requires **fresh Gate 2 sign-off**.

### 7.5 Canonical repository going forward

**Decision needed:** Confirm `studynexs-dev` replaces `academix-platform` as the sole development target and that `academix-platform` becomes archive/read-only after reconciliation.

---

## 8. File-level inventory

### 8.1 Missing on studynexs-dev — port candidates

| Path (relative to repo root) | Capability |
|------------------------------|------------|
| `apps/api/app/modules/curriculum/services/curriculum_grounding.py` | #8, #9 |
| `apps/api/app/modules/curriculum/services/pack_audit.py` | #6 |
| `apps/api/app/modules/curriculum/schemas/grounding.py` | #9 |
| `apps/api/scripts/seed_pilot_naagarjuna.py` | #11 |
| `apps/api/scripts/seed_pilot_naagarjuna_curriculum.py` | #11 |
| `apps/api/scripts/smoke_pilot_readiness.py` | #12 |
| `apps/api/scripts/apply_batch1_schema.sql` | infra (optional) |
| `apps/api/tests/test_shared_curriculum_grounding.py` | #9 |
| `apps/api/tests/test_pack_rag_on_approve.py` | #5 |
| `apps/api/tests/test_learning_outcomes.py` | #3 |
| `apps/api/tests/test_curriculum_pack_audit.py` | #6 |
| `apps/admin-web/scripts/batch1-ui-workflow-demo.cjs` | #13 |
| `apps/admin-web/src/components/curriculum/CurriculumGroundingBadge.tsx` | #8 |
| `docs/product/BATCH_1_*.md` + `batch1-ui-demo/**` | docs |
| `docs/pilot/gate2/**` | ops |
| `docs/pilot/naagarjuna-talent-school/**` | pilot |

### 8.2 Already on studynexs-dev — modify carefully (not replace)

| Path | Action |
|------|--------|
| `apps/api/app/modules/curriculum/services/pack_service.py` | Add LO methods, audit hooks, optional eager RAG index — **keep KG spine call** |
| `apps/api/app/modules/curriculum/endpoints/pack.py` | Add LO + audit + grounding preview routes |
| `apps/api/app/modules/ai/rag/service.py` | Add LO vector indexing — **keep hybrid integration** |
| `apps/api/app/modules/ai/services/assessment_grounding.py` | **No downgrade** — facade calls into this |
| `apps/api/app/modules/ai/services/question_paper_service.py` | Switch to `ground_approved_pack()` entry |
| `apps/api/app/modules/curriculum/services/lesson_plan_service.py` | Add Batch 1 grounded template path |
| `apps/api/app/db/models/curriculum_pack.py` | Add LO model + rag_index columns + audit model |
| `apps/admin-web/src/app/dashboard/teaching/curriculum/page.tsx` | Add LO + audit UI sections |
| `apps/admin-web/src/app/dashboard/teaching/ai-papers/page.tsx` | Add `CurriculumGroundingBadge` |
| `apps/admin-web/src/app/dashboard/teaching/lesson-plans/page.tsx` | Add badge + mode toggle if §7.2 = C |

### 8.3 studynexs-dev only — do not touch

All paths listed in §5.

### 8.4 academix-only post-Batch-1 (reference, not Batch 1 scope)

These exist on academix **after** `v0.1.0-batch1` and are **out of Batch 1 reconciliation scope** unless explicitly requested:

- `docs/pilot/gate2/GATE2_READINESS_AUDIT.md` (T-0 GO record)
- `infra/docker/docker-compose.dev.yml` `env_file` fix
- `apps/admin-web/scripts/gate2-t0-ui-workflows.cjs`
- T-0 evidence under `docs/pilot/naagarjuna-talent-school/t0-evidence/`

Port these during **Gate 2 re-validation phase**, not during Batch 1 capability port.

---

## 9. Recommended implementation phases (after approval)

| Phase | Scope | Exit criteria |
|-------|-------|---------------|
| **P0 — Decisions** | Resolve §7.1–§7.5 | Written PO sign-off on options |
| **P1 — Schema** | New migrations (LO, audit, rag_index columns) | `alembic upgrade head` clean on empty DB |
| **P2 — API core** | LO CRUD, audit service, `curriculum_grounding` facade | Batch 1 API tests pass |
| **P3 — Approve pipeline** | Eager RAG index + audit events + keep KG spine | `test_pack_rag_on_approve` pass |
| **P4 — AI grounding** | QP/LP through facade; badge component | `test_shared_curriculum_grounding` pass |
| **P5 — Admin UI** | LO builder, audit panel, grounding badges | Playwright 11/11 |
| **P6 — Pilot ops** | Seeds, smoke, Gate 2 docs copy | Smoke 12/12 |
| **P7 — T-0 re-run** | Full stack on studynexs-dev | New evidence bundle; GO/NO-GO |
| **P8 — Tag** | `v0.1.0-batch1` on studynexs-dev | Tag matches validated commit |

**Estimated touch surface:** ~25 files modified, ~20 files added, 0 files deleted from protected modules.

---

## 10. Post-reconciliation validation checklist

Before removing development pause:

- [ ] `alembic upgrade head` on fresh Postgres
- [ ] `pytest` — all Batch 1 tests + existing KG/Copilot/Hybrid RAG tests green
- [ ] `npm run build` (admin-web) clean
- [ ] API Docker image: `import qdrant_client` succeeds
- [ ] `python scripts/smoke_pilot_readiness.py` → 12/12
- [ ] `node apps/admin-web/scripts/batch1-ui-workflow-demo.cjs` → 11/11
- [ ] Approve pack → KG spine **and** RAG index (per §7.1 decision)
- [ ] Cross-tenant isolation tests still pass
- [ ] Teacher/Parent/Student Copilot smoke tests still pass
- [ ] Gate 2 preflight re-executed on studynexs-dev stack
- [ ] Product owner signs Gate 2 GO on **canonical repo**

---

## 11. Risk register (reconciliation-specific)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration ID collision causes bad upgrade | High if ignored | Sev-1 data | New revision IDs only (§7.3) |
| Overwriting Hybrid RAG with Batch 1 RAG | Medium | Regression | Facade pattern (§6.2) |
| Removing KG spine on approve | Medium | Batch 17+ broken | Additive approve hook (§6.3) |
| Playwright demo fails on merged UI | High | Pilot blocked | Update selectors in P5 |
| Docker mount points at wrong repo | Medium | False validation | Verify compose bind-mount path at T-0 |
| pytest blocked (Windows App Control) | Known | CI gap | Run in Docker/Linux CI |
| Stale `docs/product/PRODUCT_EXECUTION_PLAN.md` on disk | High | Planning confusion | Replace with reconciled plan after approval |

---

## 12. Approval gate

| Role | Decision | Date | Signature |
|------|----------|------|-----------|
| Product owner | Approve reconciliation plan | 2026-07-20 | ✅ Approved |
| Product owner | §7.1 RAG indexing: **C** (KG + eager RAG + lazy fallback) | 2026-07-20 | ✅ Approved |
| Product owner | §7.2 Lesson plan mode: **C** (template default; Copilot optional) | 2026-07-20 | ✅ Approved |
| Product owner | §7.3 New migration chain (no ID reuse) | 2026-07-20 | ✅ Approved |
| Product owner | §7.4 Gate 2 does **not** transfer — new T-0 + GO required | 2026-07-20 | ✅ Approved |
| Product owner | §7.5 Canonical repo: `studynexs-dev`; academix reference only | 2026-07-20 | ✅ Approved |
| Engineering | P1 Schema implementation | 2026-07-20 | ✅ Complete |
| Engineering | P2 Core Services | 2026-07-20 | ✅ Complete |
| Engineering | P3 Pipeline Integration | 2026-07-20 | ✅ Complete — awaiting review |
| Engineering | P4 UI | | ⏸ Not started |

**Phased execution:** P1 → review → P2 → review → P3 → review → P4 → review → P5 → review. No automatic Batch 1 file merge.

---

## 13. Related documents

| Document | Location |
|----------|----------|
| Batch 1 pilot readiness (source) | `academix-platform/docs/product/BATCH_1_PILOT_READINESS.md` |
| Batch 1 capability acceptance (source) | `academix-platform/docs/product/BATCH_1_CAPABILITY_ACCEPTANCE.md` |
| Repository state audit (destination) | `studynexs-dev/REPOSITORY_STATE_AUDIT.md` |
| Gate 2 package (source) | `academix-platform/docs/pilot/gate2/README.md` |
| T-0 evidence (source, historical) | `academix-platform/docs/pilot/naagarjuna-talent-school/t0-evidence/` |

---

## 14. Phase execution log

### P1 — Schema ✅ (2026-07-20) — **awaiting review**

**Alembic head:** `f4a5b6c7d8e9` (single head confirmed via `alembic heads`)

| Revision | File | Change |
|----------|------|--------|
| `d2e3f4a5b6c7` | `d2e3f4a5b6c7_batch1_pack_rag_index_status.py` | `rag_indexed_at`, `rag_index_topic_count`, `rag_index_error` on `curriculum_packs` |
| `e3f4a5b6c7d8` | `e3f4a5b6c7d8_batch1_learning_outcomes.py` | `curriculum_learning_outcomes` table + XOR check constraint |
| `f4a5b6c7d8e9` | `f4a5b6c7d8e9_batch1_pack_audit_events.py` | `curriculum_pack_audit_events` table |

**Model updates:** `curriculum_pack.py` — RAG index columns, `CurriculumLearningOutcome`, `CurriculumPackAuditEvent`; exported in `models/__init__.py`.

**Not touched:** KG, Hybrid RAG, Copilot, ConceptCard, Content Review modules.

**Runtime note:** Running `studynexs-api` container may still bind-mount `academix-platform`; apply `alembic upgrade head` against studynexs-dev mount before DB validation.

**P2 scope (next, after approval):** `pack_audit.py`, `curriculum_grounding.py` facade, LO CRUD in `pack_service.py` / schemas / endpoints.

### P2 — Core Services ✅ (2026-07-20) — **awaiting review**

**Runtime verified:**

| Check | Result |
|-------|--------|
| Compose launched from `studynexs-dev/infra/docker` | ✅ |
| API bind-mount | `D:\Projects\studynexs-platform\studynexs-dev\apps\api` → `/app` |
| `alembic heads` | `f4a5b6c7d8e9` (single head) |
| `alembic current` | `f4a5b6c7d8e9` |

**Services added (additive):**

| File | Role |
|------|------|
| `services/pack_audit.py` | Append-only audit events (no update/delete) |
| `services/curriculum_grounding.py` | Facade → validates approval/tenant → `ground_for_pack()` (Hybrid RAG) |
| `schemas/grounding.py` | Grounding preview response schema |

**Services extended:**

| File | Changes |
|------|---------|
| `services/pack_service.py` | LO CRUD, audit hooks, `list_pack_audit`; KG spine on approve **unchanged**; **no eager RAG** (P3) |
| `schemas/pack.py` | LO schemas, audit out, optional `learning_outcomes` on chapter/topic in/out |
| `endpoints/pack.py` | Additive routes: `/topics/{id}/learning-outcomes`, `/chapters/{id}/learning-outcomes`, `/learning-outcomes/{id}`, `/packs/{id}/audit`, `/packs/{id}/grounding` |

**Tests (22 passed):**

- `test_batch1_learning_outcomes.py` — LO CRUD, HTTP, cross-tenant, approval immutability
- `test_batch1_pack_audit.py` — lifecycle events, HTTP audit, cross-tenant
- `test_batch1_curriculum_grounding.py` — facade provenance, tenant scope, draft rejection, preview endpoint
- Regression: `test_curriculum_pack.py`, `test_knowledge_graph.py`

**P3 scope (next, after approval):** Eager RAG index on approve + audit events for index success/failure; wire QP/LP through facade.

### P3 — Pipeline Integration ✅ (2026-07-20) — **awaiting review**

See **[P3_IMPLEMENTATION_REPORT.md](./P3_IMPLEMENTATION_REPORT.md)** for full detail.

**Summary:** `approve_pack()` now runs validate → approve → KG spine (isolated) → eager RAG index (isolated) → audit + `rag_index_*` metadata. Lazy Hybrid RAG fallback unchanged. **34 tests passed.**

**P4 scope (next, after approval):** UI (LO builder, audit panel, grounding badges), wire QP/LP through facade — no P4 work started.
