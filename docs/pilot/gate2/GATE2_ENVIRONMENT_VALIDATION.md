# Gate 2 Environment Validation Checklist

> **Baseline:** `studynexs-dev` branch `develop` (Batch 1 reconciliation — frozen architecture)  
> **Run:** T-1 (full) and T-0 (smoke subset) before every pilot session week  
> **Reference validation:** [batch1-ui-demo](../../product/batch1-ui-demo/) · [P5_IMPLEMENTATION_REPORT.md](../../P5_IMPLEMENTATION_REPORT.md)

---

## Sign-off

| Run date | Environment (local/staging/prod) | Engineer | Result |
|----------|----------------------------------|----------|--------|
| | | | ☐ Pass ☐ Fail |

---

## 1. Source baseline

```powershell
git fetch origin
git checkout develop
git branch --show-current
```

| Check | Expected | Pass |
|-------|----------|------|
| Branch | `develop` (reconciled Batch 1 baseline) | ☐ |
| P5 validation report present | `P5_IMPLEMENTATION_REPORT.md` at repo root | ☐ |

---

## 2. Docker stack

From repo root:

```powershell
docker compose -f infra/docker/docker-compose.dev.yml up -d --build
docker compose -f infra/docker/docker-compose.dev.yml ps
```

| Service | Container | Port | Health | Pass |
|---------|-----------|------|--------|------|
| PostgreSQL | studynexs-postgres | 5432 | healthy | ☐ |
| Redis | studynexs-redis | 6379 | healthy | ☐ |
| Qdrant | studynexs-qdrant | 6333 | up | ☐ |
| API | studynexs-api | 8000 | responds | ☐ |

**API mount:** Confirm `studynexs-api` bind-mounts **`studynexs-dev/apps/api`** (canonical). Expected: `D:\Projects\studynexs-platform\studynexs-dev\apps\api → /app`.

---

## 3. RAG dependency (`[rag]`)

```powershell
docker exec studynexs-api python -c "import qdrant_client; from qdrant_client import QdrantClient; c=QdrantClient(host='qdrant', port=6333); print('ok', [x.name for x in c.get_collections().collections])"
```

| Check | Pass |
|-------|------|
| No `ModuleNotFoundError: qdrant_client` | ☐ |
| Qdrant collections list returns | ☐ |

**Dockerfile expectation** (`apps/api/Dockerfile`):

```dockerfile
RUN pip install --no-cache-dir -e ".[ai,rag,observability]"
```

If import fails:

```powershell
docker exec studynexs-api pip install "qdrant-client>=1.12.0"
docker restart studynexs-api
```

---

## 4. Database schema (Batch 1)

```powershell
cd apps\api
alembic current
# Or idempotent dev patch if migrations lag:
# psql / run apply_batch1_schema.sql per BATCH_1_PILOT_READINESS.md
```

| Check | Pass |
|-------|------|
| Migrations at head OR `apply_batch1_schema.sql` applied | ☐ |
| Curriculum tables exist (`curriculum_packs`, etc.) | ☐ |

---

## 5. API connectivity (critical: localhost vs 127.0.0.1)

**Known issue:** A ghost listener on `127.0.0.1:8000` may return HTTP 500. Use **`localhost:8000`**.

```powershell
curl -s -o NUL -w "%{http_code}" http://localhost:8000/health
curl -s -o NUL -w "%{http_code}" http://127.0.0.1:8000/health
```

| URL | Expected | Pass |
|-----|----------|------|
| `http://localhost:8000/health` | 200 | ☐ |
| `http://127.0.0.1:8000/health` | 200 (if fails, document — use localhost only) | ☐ |

---

## 6. Pilot tenant seed

```powershell
cd apps\api
python scripts\seed_pilot_naagarjuna.py
python scripts\seed_pilot_naagarjuna_curriculum.py
```

| Check | Pass |
|-------|------|
| Seed scripts complete without error | ☐ |
| Tenant slug `naagarjuna` exists | ☐ |
| Class 10 + Maths subject present | ☐ |

---

## 7. Smoke test (API)

```powershell
cd apps\api
python scripts\smoke_pilot_readiness.py
echo Exit code: $LASTEXITCODE
```

| Check | Pass |
|-------|------|
| Exit code `0` | ☐ |
| Login as `principal` OK | ☐ |
| Curriculum packs endpoint OK | ☐ |
| AI question-papers + usage OK | ☐ |

---

## 8. Admin web

```powershell
cd apps\admin-web
$env:NEXT_PUBLIC_TENANT_SLUG="naagarjuna"
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev -- -p 3003
```

| Variable | Value | Pass |
|----------|-------|------|
| `NEXT_PUBLIC_TENANT_SLUG` | `naagarjuna` | ☐ |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | ☐ |
| Dev port | `3003` (CORS allowlist) | ☐ |

| Check | Pass |
|-------|------|
| http://localhost:3003/login loads | ☐ |
| Login `principal` / `Demo@1234` succeeds | ☐ |
| Curriculum page loads without runtime error | ☐ |

---

## 9. LLM gateway

| Check | Pass |
|-------|------|
| API keys set in env (not in repo) | ☐ |
| Test generation: lesson plan OR QP completes | ☐ |
| Usage/credits endpoint shows quota | ☐ |
| Pre-approved backup QP available if keys fail | ☐ |

---

## 10. Optional — full UI workflow (T-1 only)

```powershell
cd apps\admin-web
node scripts/batch1-ui-workflow-demo.cjs
```

| Check | Pass |
|-------|------|
| 11/11 steps pass | ☐ |
| Artifacts in `docs/product/batch1-ui-demo/` | ☐ |

---

## 11. T-0 smoke subset (daily during pilot)

Minimum daily checks:

1. `docker compose ps` — all critical services up
2. `python scripts/smoke_pilot_readiness.py` — exit 0
3. Manual login `maths_teacher` on admin-web
4. LLM credit spot-check if generation used previous day

---

## Failure log

| Timestamp | Check ID | Symptom | Root cause | Fix | Retest |
|-----------|----------|---------|------------|-----|--------|
| | | | | | |

Log failures also in [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md).
