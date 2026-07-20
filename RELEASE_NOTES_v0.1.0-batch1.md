# Release Notes — v0.1.0-batch1

> **Product:** StudyNexs — Batch 1 Curriculum Intelligence  
> **Repository:** `studynexs-dev` · **Branch:** `develop`  
> **Tag status:** Prepared — **not applied** (await Product Owner approval)  
> **Date:** 2026-07-20

---

## Summary

Batch 1 delivers **Curriculum Intelligence** for the Naagarjuna Talent School pilot (Class 10 Mathematics, Telangana SSC). This release reconciles the frozen Batch 1 capability set onto the canonical `studynexs-dev` repository while preserving Knowledge Graph, Hybrid RAG, and Teacher Copilot infrastructure from parallel development (Batches 17–28).

---

## Reconciliation summary

| Phase | Scope | Outcome |
|-------|-------|---------|
| P3 | Schema + services (LO, audit, approve pipeline, grounding facade) | ✅ Complete |
| P4 | UI + facade wiring (QP/LP provenance, curriculum UI extensions) | ✅ Complete |
| P5 | Operational validation (smoke 12/12, Playwright 11/11) | ✅ Complete |
| P6 | Release governance (canonical repo, archive, tag preparation) | ✅ Complete |

**Source archive:** `academix-platform` @ historical `513c3a3` — now **Reference Archive**.  
**Canonical baseline:** `studynexs-dev` `develop` with validated working tree.

---

## Architecture summary (frozen)

| Component | Role |
|-----------|------|
| `approve_pack()` | Orchestration entry — KG spine + eager RAG index + audit events |
| `ground_approved_pack()` | **Only** curriculum-governance entry for question papers and lesson plans |
| Hybrid RAG | Retrieval engine (tenant-scoped, self-healing index) |
| Knowledge Graph | Concept graph spine from approved packs |
| Teacher Copilot | Optional — template lesson plan is default workflow |
| Human-in-the-loop | Required for authoritative QP/LP output |

No architecture changes are authorized during Batch 1 pilot unless PO-approved critical defects.

---

## Major capabilities

### Curriculum pack lifecycle
- Draft pack CRUD (chapters, topics, concepts)
- Learning outcomes per topic/chapter
- HOD approval → immutable approved pack
- Append-only pack audit trail

### Grounding & generation
- Grounded question paper generation with provenance badge
- Template lesson plans with curriculum grounding (Copilot optional)
- Shared `ground_approved_pack()` facade over Hybrid RAG

### Integration
- Knowledge Graph spine on approve
- Hybrid RAG eager indexing on approve
- Tenant-scoped retrieval and cross-tenant isolation (403)

### Pilot operations
- Seed scripts: `seed_pilot_naagarjuna.py`, `seed_pilot_naagarjuna_curriculum.py`
- Smoke readiness: 12 automated checks
- Playwright: 11-step UI workflow with screenshot evidence
- Gate 2 operational documentation package

### Admin UI
- Curriculum builder with LO editor, audit panel, grounding preview
- `CurriculumGroundingBadge` on AI Papers and Lesson Plans pages

---

## Database migrations (Batch 1 additions)

| Revision | Description |
|----------|-------------|
| `d2e3f4a5b6c7` | Pack RAG index status |
| `e3f4a5b6c7d8` | Learning outcomes |
| `f4a5b6c7d8e9` | Pack audit events |

**Alembic head:** `f4a5b6c7d8e9` (single head, verified at DB)

---

## Known limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Minimal seed pack has 0 KG concepts | Smoke shows `concepts=0` | HOD imports full syllabus during pilot |
| QP generation latency (~60–70s) | Teacher wait time | Set expectations; backup QP prepared |
| Login page hydration warning | Console noise only | Non-blocking; monitor during pilot |
| Windows `127.0.0.1:8000` ghost listener | Browser API failures | Use `localhost:8000` exclusively |
| Eval assist scope | Objective/short answers only | Document in demo script |
| Copilot LLM lesson plans | Available but not default | Template + grounding is pilot default |
| Working tree uncommitted | Tag cannot apply to HEAD yet | Commit Batch 1 RC before tag |

---

## Operational notes

### Pilot tenant
- **Slug:** `naagarjuna`
- **Admin env:** `NEXT_PUBLIC_TENANT_SLUG=naagarjuna`, `NEXT_PUBLIC_API_URL=http://localhost:8000`
- **Dev port:** `:3006` (with `.env.local`)

### Pre-session validation
```powershell
cd apps\api
python scripts\smoke_pilot_readiness.py   # expect 12/12

cd ..\admin-web
$env:E2E_BASE_URL="http://localhost:3006"
node scripts\batch1-ui-workflow-demo.cjs  # expect 11/11
```

### Smoke checks (12)
Stack health · Auth · Learning outcomes · Audit trail · Knowledge graph · Hybrid RAG · Grounding facade · Approval pipeline · Question papers · Lesson plans · Cross-tenant isolation · Copilot routing

---

## Deployment prerequisites

| Requirement | Notes |
|-------------|-------|
| Docker Desktop | `infra/docker/docker-compose.dev.yml` |
| PostgreSQL 16 | Via compose |
| Redis 7 | Via compose |
| Qdrant | Via compose; `[rag]` extras installed in API image |
| Node.js 20+ | Admin web build/dev |
| Python 3.11 | API scripts and tests |
| LLM API keys | In `apps/api/.env` (OPENAI or configured provider) |
| Migrations | `alembic upgrade head` (at `f4a5b6c7d8e9`) |

---

## Validation evidence

| Suite | Result | Location |
|-------|--------|----------|
| Smoke | 12 / 12 | `docs/pilot/naagarjuna-talent-school/t0-evidence/smoke-results.json` |
| Playwright | 11 / 11 | `docs/product/batch1-ui-demo/workflow-results.json` |
| API tests | 37 passed | Batch 1 test modules |
| Admin build | Success | P6 verification |
| API Docker build | Success | P6 verification |

---

## Upgrade / migration

From pre-reconciliation `academix-platform` deployments:

1. Switch to `studynexs-dev` repository
2. Apply migrations through `f4a5b6c7d8e9`
3. Re-seed pilot tenant if needed (scripts are idempotent)
4. Re-run smoke + Playwright before Gate 2 sessions

---

*Prepared by P6 release governance. Tag application requires Product Owner approval.*
