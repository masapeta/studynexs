# T-0 Validation Checklist — Naagarjuna Pilot

> **Run date:** 2026-07-20  
> **Baseline:** `studynexs-dev` branch `develop` (Batch 1 reconciliation — P4 approved, P5 validation)  
> **Engineer:** Pilot Operations  
> **Result:** Engineering validation **PASS** — awaiting Product Owner Gate 2 authorization

---

## Stack services

| Service | Endpoint / Container | Status | Pass |
|---------|----------------------|--------|------|
| PostgreSQL | `studynexs-postgres:5432` | healthy | ✅ |
| Redis | `studynexs-redis:6379` | healthy | ✅ |
| Qdrant | `studynexs-qdrant:6333` | up | ✅ |
| API | `studynexs-api:8000` | healthy | ✅ |
| Nginx | `studynexs-nginx:80` | up | ✅ |

---

## API connectivity

| Check | URL | Expected | Actual | Pass |
|-------|-----|----------|--------|------|
| Health | `http://localhost:8000/health` | 200 | 200 | ✅ |
| Ready | `http://localhost:8000/ready` | 200 | 200 | ✅ |
| Qdrant collections | `http://localhost:6333/collections` | 200 | 200 | ✅ |

**Note:** Avoid `127.0.0.1:8000` on this Windows host (ghost listener returns 500). Use **`localhost:8000`** for browser and smoke.

---

## Frozen architecture verification

| Component | Entry point | Verified | Pass |
|-----------|-------------|----------|------|
| Approval orchestration | `approve_pack()` | Smoke + Playwright step 8 | ✅ |
| Curriculum governance | `ground_approved_pack()` only | Smoke grounding facade + LP/QP | ✅ |
| Hybrid RAG | retrieval engine | Smoke hybrid RAG | ✅ |
| Knowledge Graph | concept graph | Smoke KG endpoint | ✅ |
| Teacher Copilot | optional | Smoke copilot routing | ✅ |
| Lesson plans | template default | Smoke + Playwright step 10 | ✅ |

---

## Seed scripts

| Script | Result | Pass |
|--------|--------|------|
| `seed_pilot_naagarjuna.py` | Idempotent — tenant exists | ✅ |
| `seed_pilot_naagarjuna_curriculum.py` | Uses `approve_pack()` pipeline | ✅ |

---

## Automated validation

| Suite | Target | Result | Pass |
|-------|--------|--------|------|
| Smoke | 12/12 checks | ALL GREEN | ✅ |
| Playwright | 11/11 steps | ALL GREEN | ✅ |
| Admin build | `npm run build` | Success | ✅ |
| API tests | 37 tests (Batch 1 + curriculum) | All passed | ✅ |

---

## Evidence artifacts

| Artifact | Location |
|----------|----------|
| Smoke results | [`smoke-results.json`](./smoke-results.json) |
| Playwright results | [`workflow-results.json`](./workflow-results.json) |
| Screenshots | [`../../product/batch1-ui-demo/`](../../product/batch1-ui-demo/) |
| Gate 2 package | [`../../gate2/`](../../gate2/) |
| P5 report | [`../../../P5_IMPLEMENTATION_REPORT.md`](../../../P5_IMPLEMENTATION_REPORT.md) |

---

## Sign-off

| Role | Name | Date | Decision |
|------|------|------|----------|
| Engineering | Pilot Ops | 2026-07-20 | Validation complete — **STOP** (no tagging/release) |
| Product Owner | — | — | **Pending** |
