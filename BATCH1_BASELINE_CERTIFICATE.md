# Batch 1 Baseline Certificate

> **Issued:** 2026-07-20  
> **Program:** Batch 1 Reconciliation (P3–P6)  
> **Status:** Engineering certification complete — **tag and Gate 2 GO await Product Owner approval**

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
| **Tag applied** | ❌ No — await PO approval |
| **Current git HEAD** | `45ed42a63bb57a3568646d57390adc9f340afab9` |
| **RC commit** | ⏳ Pending — Batch 1 artifacts (107 files) uncommitted at certification time |
| **Alembic head** | `f4a5b6c7d8e9` |
| **DB revision (runtime)** | `f4a5b6c7d8e9 (head)` — verified in `studynexs-api` container |

### Prepared annotated tag (do not apply until PO approves)

```
git tag -a v0.1.0-batch1 -m "Batch 1 Curriculum Intelligence — reconciled baseline

- approve_pack() orchestration with KG spine + eager RAG + audit
- ground_approved_pack() sole governance entry for QP/LP
- Learning outcomes, audit trail, curriculum UI extensions
- Smoke 12/12, Playwright 11/11 validated on studynexs-dev
- Canonical repository; academix-platform archived

Pilot: Naagarjuna Talent School · Class 10 Maths · Gate 2 ready pending PO GO."
```

**Apply only after:** (1) Batch 1 RC commit on `develop`, (2) PO approval.

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
| Working tree clean | ⚠️ **107 uncommitted files** — RC commit required before tag |

**Legacy npm package name:** `academix-platform` in `apps/admin-web/package.json` — cosmetic only; no runtime path impact.

---

## 6. Release readiness

| Gate | Status |
|------|--------|
| P3 implementation | ✅ Approved |
| P4 implementation | ✅ Approved |
| P5 operational validation | ✅ Approved |
| P6 release governance | ✅ Complete |
| Git tag `v0.1.0-batch1` | ⏳ Prepared — **not created** |
| Gate 2 GO announcement | ⏳ Await PO |
| Pilot rollout | ⏳ Await PO |

### Engineering recommendation

**Release candidate is operationally ready.** Apply tag on a clean RC commit after PO approves commit + tag. Proceed to Gate 2 pilot execution upon PO GO.

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
