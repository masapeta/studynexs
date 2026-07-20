# Batch 1 Baseline Certificate

> **Historical note (2026-07-20):** Terminology predates Showcase / Customer Pilot documentation split. Software baseline remains valid for Reference School and customer deployments.  
> **Issued:** 2026-07-20  
> **Program:** Batch 1 Reconciliation (P3–P6)  
> **Status:** ✅ **Certified and released**

---

## 1. Canonical repository

| Field | Value |
|-------|-------|
| **Repository** | `studynexs-dev` |
| **Path** | `D:\Projects\studynexs-platform\studynexs-dev` |
| **Branch** | `develop` (frozen for Batch 1 RC) |
| **Archive superseded** | `academix-platform` → Reference Archive |

---

## 2. Version information

| Field | Value |
|-------|-------|
| **Prepared tag** | `v0.1.0-batch1` |
| **Tag applied** | ✅ Yes — 2026-07-20 |
| **Release commit (RC SHA)** | `649967a83cc5aceacaf7dee02c4d37d73fc71f27` |
| **Branch** | `develop` |
| **Validation date** | 2026-07-20 |
| **Alembic head** | `f4a5b6c7d8e9` |
| **DB revision (runtime)** | `f4a5b6c7d8e9 (head)` — verified in `studynexs-api` container |

### Applied tag

```
v0.1.0-batch1 → 649967a83cc5aceacaf7dee02c4d37d73fc71f27
```

Tag object SHA: `96c3fbc90a9293537b3ee47a2976f3349305b5d8`

---

## 3. Architecture freeze (certified)

The following architecture is **frozen** for Batch 1 pilot and must not be revisited without explicit PO authorization:

| Decision | Entry point / component |
|----------|-------------------------|
| Approval orchestration | `approve_pack()` |
| Curriculum governance | `ground_approved_pack()` — **only** approved entry |
| Retrieval | Hybrid RAG |
| Concept graph | Knowledge Graph |
| Lesson plan default | Template mode |
| Copilot | Optional |

Certified validated capabilities:

- Approval pipeline
- Curriculum grounding facade
- Knowledge Graph integration
- Hybrid RAG integration
- Learning Outcomes
- Audit Trail
- Question Papers
- Lesson Plans
- Curriculum UI extensions
- Playwright workflow (11/11)
- Smoke validation (12/12)
- Operational documentation

---

## 4. Validation evidence

### Automated (P6 re-verification — 2026-07-20)

| Suite | Result | Timestamp / artifact |
|-------|--------|----------------------|
| Smoke readiness | **12 / 12** ALL GREEN | `docs/pilot/naagarjuna-talent-school/t0-evidence/smoke-results.json` |
| Playwright workflow | **11 / 11** ALL GREEN | `docs/product/batch1-ui-demo/workflow-results.json` |
| API tests (Batch 1) | **37 passed** | `tests/test_batch1_*.py`, `test_knowledge_graph.py`, `test_curriculum_pack.py` |
| Admin build | Success | `npm run build` |
| API Docker build | Success | `docker compose build api` |

### Infrastructure

| Service | Status |
|---------|--------|
| PostgreSQL | healthy |
| Redis | healthy |
| Qdrant | up |
| API (`studynexs-api`) | healthy |
| Docker bind mount | `studynexs-dev/apps/api → /app` ✅ |

### Screenshots

11 workflow screenshots under `docs/product/batch1-ui-demo/` (`01-login.png` … `11-question-paper-grounded.png`).

---

## 5. Repository verification

| Check | Result |
|-------|--------|
| Canonical repo is `studynexs-dev` | ✅ |
| No runtime references to `academix-platform` paths | ✅ |
| Docker bind mounts point to `studynexs-dev` only | ✅ |
| Single Alembic head | ✅ `f4a5b6c7d8e9` |
| No pending migrations | ✅ |
| Working tree clean | ✅ At release commit |

**Legacy npm package name:** `academix-platform` in `apps/admin-web/package.json` — cosmetic only; no runtime path impact.

---

## 6. Release readiness

| Gate | Status |
|------|--------|
| P3 implementation | ✅ Approved |
| P4 implementation | ✅ Approved |
| P5 operational validation | ✅ Approved |
| P6 release governance | ✅ Complete |
| Git tag `v0.1.0-batch1` | ✅ Applied on RC commit |
| Gate 2 GO announcement | ✅ [`docs/pilot/GATE2_GO.md`](docs/pilot/GATE2_GO.md) |
| Pilot rollout | ✅ **Authorized** — Naagarjuna Talent School |

### Engineering recommendation

**Batch 1 is feature complete.** Gate 2 pilot is **GO**. Apply tag `v0.1.0-batch1` on commit `649967a`.

---

## 7. Certification

This certificate attests that Engineering has completed Batch 1 baseline finalization per P6 scope on the canonical `studynexs-dev` repository, with all automated validation green and governance artifacts produced.

**No further feature work** is authorized under the Batch 1 reconciliation program.

| Role | Signature | Date |
|------|-----------|------|
| Engineering (P6) | Certified | 2026-07-20 |
| Product Owner | Pending | |

---

## Related documents

- [`RELEASE_NOTES_v0.1.0-batch1.md`](./RELEASE_NOTES_v0.1.0-batch1.md)
- [`P6_IMPLEMENTATION_REPORT.md`](./P6_IMPLEMENTATION_REPORT.md)
- [`docs/pilot/RELEASE_CHECKLIST_v0.1.0-batch1.md`](./docs/pilot/RELEASE_CHECKLIST_v0.1.0-batch1.md)
- [`CANONICAL_REPOSITORY.md`](./CANONICAL_REPOSITORY.md)
- [`REFERENCE_ARCHIVE.md`](../../academix-platform/REFERENCE_ARCHIVE.md)
