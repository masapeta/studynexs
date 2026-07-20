# Release Engineering Review — Gate 2 Pilot Readiness

> **Review date:** 2026-07-20  
> **Reviewer role:** Release engineer (read-only; no code changes)  
> **Baseline:** Git tag `v0.1.0-batch1` on branch `integration/studynexs`  
> **Scope:** Deployment, operations, documentation, monitoring, backups, pilot assumptions

---

## Executive summary

1. **Batch 1 is pilot-capable for a controlled, engineer-supervised Gate 2 demo** — curriculum RAG, grounded QP/lesson plans, smoke scripts, and the Gate 2 doc package are in place; the API Dockerfile correctly installs `[ai,rag,observability]`.
2. **There is no continuous deployment path** — CI tests and builds images only; no deploy to Azure Container Apps, no migration job, no Cloudflare admin-web automation.
3. **The documented pilot stack is dev-oriented Docker Compose**, not production-grade: bind-mounted API with `--reload`, no Arq worker service, no uploads volume, unpinned `qdrant/qdrant:latest`.
4. **CI has a critical gap vs runtime:** it installs `.[dev,ai,observability]` but **not `[rag]`**, and does not run on `integration/studynexs` — green CI does not guarantee RAG works.
5. **Backups, DR, and production monitoring are largely undocumented/unimplemented** — Gate 2 rollback requires manual T-0 snapshots; observability exists locally but is not wired for pilot/production alerting.

**Overall verdict:** **Conditional go** for Gate 2 as an engineer-supervised local/staging pilot using manual checklists — **not go** for unattended or cloud production until P0 backups, worker/RAG verification, env documentation, and P1 CD/observability/DR items are addressed.

---

## 1. Deployment risks

### Critical

| Finding | Severity | Evidence |
|---------|----------|----------|
| **No CD pipeline** — image build in CI only; no deploy, migration job, or admin-web deploy | Critical | `.github/workflows/ci.yml`; `docs/STATUS.md`; `docs/AGENT_HANDOVER.md` |
| **Pilot stack = dev compose** — API bind-mount + `--reload`; unsuitable unattended | Critical | `infra/docker/docker-compose.dev.yml` |
| **Arq background worker not in compose** — async eval/jobs may require separate worker process | Critical | No worker in compose; `apps/api/app/core/jobs/worker.py` |

### High

| Finding | Severity | Evidence |
|---------|----------|----------|
| **CI omits `[rag]`** — Dockerfile has it; CI does not | High | `.github/workflows/ci.yml` L57–58; `apps/api/Dockerfile` |
| **CI does not run on pilot branch** — triggers `phase-0-foundation`, `main` only | High | `.github/workflows/ci.yml` L10–11 |
| **No `.env.example` committed** — env contract missing from repo | High | `.gitignore` references; file absent |
| **Uploads on ephemeral container FS** — restarts may lose files | High | `apps/api/Dockerfile`; no uploads volume in compose |
| **Qdrant not in `/ready` probe** — API ready while RAG fails | High | `apps/api/app/main.py` (DB + Redis only) |
| **Unpinned container images** — `qdrant/qdrant:latest` | High | `infra/docker/docker-compose.dev.yml` |

### Medium

| Finding | Severity | Evidence |
|---------|----------|----------|
| **No AI kill-switch env flags** — rollback = stop API or revoke keys | Medium | `GATE2_ROLLBACK_PLAN.md` §3 |
| **Migration path ambiguous** — `alembic upgrade head` OR `apply_batch1_schema.sql` | Medium | Gate 2 env validation; `apps/api/scripts/apply_batch1_schema.sql` |
| **Tesseract not in Docker image** — admission OCR fails in container | Medium | `pyproject.toml`; `Dockerfile` |
| **Smoke uses `127.0.0.1:8000`** — docs warn ghost listener on Windows | Medium | `smoke_pilot_readiness.py`; Gate 2 env validation |
| **Lint non-blocking in CI** | Medium | `.github/workflows/ci.yml` |
| **No admin-web container deploy doc** — Cloudflare scripts exist, pilot path unclear | Medium | `apps/admin-web/package.json`, `wrangler.jsonc` |

### Low

| Finding | Severity | Evidence |
|---------|----------|----------|
| Dev compose exposes DB/Redis/Qdrant on host ports | Low | `docker-compose.dev.yml` |
| Default dev DB password in compose | Low | `docker-compose.dev.yml` |
| Seed/smoke scripts excluded from Docker image | Low | `apps/api/.dockerignore` |

---

## 2. Documentation gaps

### Critical / high

| Gap | Severity | Notes |
|-----|----------|-------|
| **No production deployment runbook** (API → ACR → Container Apps, web → Cloudflare) | Critical | `README.md` implies CD; `infra/azure/` is WAF-only |
| **No committed environment template** | High | Vars scattered in AGENT_HANDOVER, observability README |
| **Canonical docs stale vs Batch 1** — STATUS, ROADMAP, AGENT_HANDOVER | High | Pre-Batch-1 snapshots |
| **Root README outdated** — omits `[rag]`, Qdrant, pilot tenant | High | `README.md` |
| **DPDP/consent not implemented** — no templates/runbook | High | Mentioned as blocker; no artifacts |

### Medium

| Gap | Severity | Notes |
|-----|----------|-------|
| Admin-web pilot deploy (CORS, tenant slug, HTTPS cookies) | Medium | Port 3003 vs naagarjuna README port 3000 |
| Arq worker ops not documented | Medium | Code exists; no runbook |
| Azure IaC incomplete beyond WAF Bicep | Medium | `infra/azure/` |

### Strengths

- Complete Gate 2 package: [`docs/pilot/gate2/`](./README.md)
- [`BATCH_1_PILOT_READINESS.md`](../product/BATCH_1_PILOT_READINESS.md)
- Environment validation, rollback, risk register

---

## 3. Operational risks during school pilot

| Risk | Severity | Mitigation status |
|------|----------|-------------------|
| Engineer-present local/docker pilot — school Wi‑Fi, no HA | High | Hotspot fallback documented; not automated |
| LLM quota/timeout during live QP (~90s) | High | Backup QP in backlog; not enforced in smoke |
| Handwriting OCR on real sheets | High | HITL + eval limits doc |
| Shared demo password in docs | Medium | Rotate post-pilot — not scripted |
| Single-engineer bus factor | Medium | On-call in preflight |
| Real student PII without DPDP tooling | High | Consent/retention not built |
| File loss on container restart | Medium | No persistent uploads volume |
| School expectation mismatch (LLM lessons, eval accuracy) | High | Demo script + CLASS_10_MATHS doc |

---

## 4. Missing runbooks

| Runbook | Status | Partial coverage |
|---------|--------|------------------|
| Production / pilot deploy | **Missing** | Gate 2 env validation |
| Backup & restore (Postgres, Qdrant, uploads) | **Missing** | Rollback plan §4 (manual T-0 only) |
| Database migration (CI/CD job) | **Missing** | Alembic dev; schema SQL fallback |
| Incident response / on-call | Partial | Gate 2 rollback, risk register |
| Arq worker lifecycle | **Missing** | Worker code only |
| AI provider failover / kill switch | **Missing** | Rollback acknowledges gap |
| Secrets rotation | **Missing** | — |
| School onboarding (tenant + seed) | Partial | `seed_pilot_naagarjuna*.py` |

**Existing:** `docs/runbooks/rate-limits-and-waf.md`, `audit-retention.md`, `6-hour-soak-test.md`

---

## 5. Monitoring and observability

| Finding | Severity | Evidence |
|---------|----------|----------|
| Observability stack dev-local only — not default pilot compose | High | `infra/docker/docker-compose.observability.yml` |
| OTEL disabled by default | Medium | `apps/api/app/core/config.py` |
| No Alertmanager / PagerDuty / Slack wiring | High | `prometheus-alerts.yml` rules only |
| Grafana default creds in compose | Medium | `docker-compose.observability.yml` |
| No pilot SLOs (login, QP latency, RAG index) | Medium | Product criteria only in success doc |
| No centralized log aggregation documented | Medium | structlog in-app |

**Strengths:** OTEL instrumentation, Prometheus AI alerts, Grafana dashboard JSON, WAF runbook.

---

## 6. Backups and disaster recovery

| Asset | Strategy today | DR readiness |
|-------|----------------|--------------|
| PostgreSQL | Manual `pg_dump` in rollback plan | No schedule, no restore drill, no RPO/RTO |
| Qdrant vectors | Volume snapshot or re-index | No automation |
| Uploads (`/app/uploads`) | None | Ephemeral in compose |
| Secrets | Checklist only | No vault integration |
| Approved QP exports | Manual | Not automated |

Gap acknowledged in [`GATE2_ROLLBACK_PLAN.md`](./GATE2_ROLLBACK_PLAN.md) §4.

---

## 7. Assumptions that could fail during pilot

| Assumption | Likelihood | Impact |
|------------|------------|--------|
| Operator runs full Gate 2 preflight manually | High | High |
| Dev compose sufficient for pilot hosting | Medium | High |
| `alembic upgrade head` on fresh DB | Medium | High |
| Qdrant + embeddings available at pack approve | Medium | Critical |
| `localhost:8000` works (not `127.0.0.1` ghost) | Medium | High |
| Teachers select approved pack for grounded AI | Medium | Medium |
| Arq jobs not needed for pilot wedge | Medium | Medium |
| School provides syllabus on time | Medium | Medium |
| CI green = deploy safe | High | High |
| Cross-origin Cloudflare web + Azure API CORS/cookies | Medium | High |

---

## 8. Recommendations (no code changes in this review)

### P0 — Before pilot day

1. Execute [GATE2_PREFLIGHT_CHECKLIST.md](./GATE2_PREFLIGHT_CHECKLIST.md) and [GATE2_ENVIRONMENT_VALIDATION.md](./GATE2_ENVIRONMENT_VALIDATION.md); file signed copy under `docs/pilot/naagarjuna-talent-school/`.
2. Take verified **T-0 backups:** Postgres `pg_dump`, Qdrant volume snapshot; document restore steps (even if manual).
3. **Verify RAG in running API container** — `qdrant_client` import + pack approve; do not rely on CI alone.
4. **Run Arq worker alongside API** if async eval is in scope; document start/stop in operator notes.
5. **Align API URL** — use `localhost:8000` everywhere (admin-web, smoke, CORS).
6. **Pre-approve backup QP** and confirm LLM credits before each session.
7. **Publish pilot env matrix** (`.env.example` or Gate 2 appendix) listing required vars without secrets.
8. **Add Qdrant (+ embedding key) to daily health checklist** — `/ready` will not catch failures.

### P1 — Before production / extended pilot

1. Add CD workflow: build → push image → deploy → `alembic upgrade head` job.
2. Fix CI: install `.[dev,ai,rag,observability]`; trigger on `integration/studynexs`; optional RAG import smoke.
3. Production compose: no bind-mount/reload, pinned digests, uploads volumes, worker service.
4. Deploy observability with alerting; set `METRICS_TOKEN`, `OTEL_ENABLED=true`.
5. Author runbooks: deploy, backup/restore, migration, incident, Arq worker.
6. Implement backup automation with quarterly restore drill.
7. Refresh STATUS, ROADMAP, AGENT_HANDOVER, README to Batch 1 baseline.
8. Define AI kill-switches per rollback plan.
9. Document admin-web Cloudflare deploy with CORS/cookie matrix.
10. DPDP minimum: consent record template + retention policy before real PII.

### P2 — Post-pilot hardening

1. Pin base images by digest; container scanning in CI.
2. Flip lint to blocking after backlog cleared.
3. Extend Azure IaC (Container Apps, managed Postgres, Redis, Qdrant).
4. Azure Blob for uploads.
5. Extend `/ready` to include Qdrant and optional LLM probe.
6. Run 6-hour soak test before scale.
7. Rotate pilot demo passwords; remove from public channels.
8. Frontend deploy to CI (Cloudflare preview on PR).

---

## 9. Prioritized action list

| Priority | Action | Owner | Effort |
|----------|--------|-------|--------|
| **P0** | Complete Gate 2 preflight + env validation with sign-off | Ops/Eng | 4–8 h |
| **P0** | T-0 Postgres + Qdrant backup with restore notes | Eng | 2–4 h |
| **P0** | Verify `[rag]` in live API; daily smoke import check | Eng | 1 h |
| **P0** | Arq worker if eval jobs needed | Eng | 1–2 h |
| **P0** | Publish pilot env matrix | Eng | 2 h |
| **P0** | Backup QP + LLM credit monitoring | Eng/PO | 1 h |
| **P1** | CI: add `[rag]`, trigger on pilot branch | Eng | 1 h |
| **P1** | Production compose + deploy runbook | Eng | 1–2 d |
| **P1** | CD pipeline + migration job | Eng | 2–3 d |
| **P1** | Backup automation + restore drill | Eng | 1–2 d |
| **P1** | Observability with alerting on pilot host | Eng | 1 d |
| **P1** | Refresh canonical docs to Batch 1 | Eng | 4 h |
| **P1** | DPDP consent/retention templates | PO/Legal | 2–3 d |
| **P2** | Image digest pinning + scanning | Eng | 4 h |
| **P2** | Full Azure IaC beyond WAF | Eng | 1–2 w |
| **P2** | Azure Blob + persistent uploads | Eng | 3–5 d |

---

## 10. Baseline verification

| Item | Status |
|------|--------|
| Tag `v0.1.0-batch1` | Present |
| Branch `integration/studynexs` at tag | Yes |
| Dockerfile includes `[rag]` | Yes |
| CI includes `[rag]` | **No** |
| Gate 2 doc package (10 deliverables) | Complete |
| Alembic head | `z6a7b8c9d0e1` (per pilot docs) |

---

## Related documents

- [Gate 2 Pilot Package index](./README.md)
- [Batch 1 Pilot Readiness](../product/BATCH_1_PILOT_READINESS.md)
- [Pilot Feedback Log](../product/PILOT_FEEDBACK_LOG.md)
