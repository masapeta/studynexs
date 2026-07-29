# StudyNexs Production Operations Runbook

> H7 scope: operate the existing Academic Intelligence Platform safely. This
> runbook does not authorize product features, roadmap changes, or architecture
> changes.

## 1. Operating baseline

| Area | Current expectation |
|---|---|
| Canonical branch | `develop` on `studynexs-github` |
| Canonical remote | `https://github.com/masapeta/studynexs.git` |
| Required services | API, worker, PostgreSQL, Redis, Qdrant, edge/proxy |
| Health endpoint | `GET /ready` must return `status=ready` |
| Metrics endpoint | `GET /metrics` must expose HTTP, AI, and job metrics |
| Recovery principle | Reconcile committed business state; do not replay AI work automatically |

## 2. Pre-deploy / pre-pilot operations check

From the repository root:

```powershell
cd apps/api
python scripts/production_ops_check.py
```

Expected result:

- `git_sync`: pass
- `docker_services`: pass, unless running in a non-Docker production topology
- `runtime_ready`: pass
- `platform_metrics`: pass

For a managed production deployment where Docker Compose is not the runtime:

```powershell
python scripts/production_ops_check.py --skip-docker --base-url https://<api-host>
```

For the Operational Proof production-like Compose profile, run the check
against the proxy entry point and include the metrics token:

```powershell
cd apps/api
python scripts/production_ops_check.py `
  --compose-file ../../infra/docker/docker-compose.prod.yml `
  --base-url http://localhost:8080 `
  --metrics-token <synthetic-proof-token>
```

## 3. Backup verification

Create a PostgreSQL custom-format backup to a secure location outside Git:

```powershell
cd apps/api
python scripts/backup_postgres.py --output "$env:TEMP\studynexs-prepilot.dump"
```

Verify the backup is readable:

```powershell
python scripts/verify_postgres_backup.py "$env:TEMP\studynexs-prepilot.dump"
```

Operational Proof also requires a restore drill into a clean target:

```powershell
python scripts/restore_postgres_backup.py "$env:TEMP\studynexs-prepilot.dump"
```

Pass criteria:

- backup file exists
- size is non-zero
- `pg_restore -l` succeeds
- restore listing contains schema/table entries
- restore drill succeeds against the synthetic restore target

Production note: for managed databases, use the managed backup facility, then
perform the equivalent restore-list/readability verification.

## 4. Restore and rollback decision tree

| Symptom | First action | Escalation |
|---|---|---|
| API unavailable | Check `/ready`, container/service status, logs | Roll back deployment if new code caused outage |
| Redis unavailable | Restart/recover Redis; verify `/ready` | Pause async workflows until recovered |
| PostgreSQL unavailable | Stop writes; recover DB service | Restore from verified backup if data is corrupt |
| Qdrant unavailable | Pause curriculum/RAG-dependent generation | Recover Qdrant or re-index approved packs |
| Worker backlog stale | Run dry-run recovery check | Apply recovery only after operator approval |
| Cross-tenant leakage | Stop service immediately | Sev-1 incident; preserve logs and do not continue pilot |
| Evidence-chain defect | Stop affected workflow | Certification defect; do not harden around it |

## 5. Background job recovery

Dry-run stale answer-sheet evaluation jobs first:

```powershell
cd apps/api
python scripts/recover_stale_evaluation_jobs.py --tenant-slug reference --older-than-minutes 60
```

Apply only when the dry-run classifies terminal evaluation states safely:

```powershell
python scripts/recover_stale_evaluation_jobs.py --tenant-slug reference --older-than-minutes 60 --apply
```

Post-apply checks:

```powershell
python scripts/production_ops_check.py
```

Recovery invariant:

- business records remain unchanged unless the operator intentionally runs a
  business recovery procedure;
- stale job metadata may be reconciled to match already-committed evaluation
  state;
- processing evaluations require manual review.

## 6. Alert response

| Alert | First response |
|---|---|
| `StudyNexsAPIDown` | Check deployment, service health, and ingress |
| `StudyNexsHTTP5xxHigh` | Inspect request logs by route/request ID; pause affected workflow |
| `StudyNexsJobStatusScrapeError` | Check API-to-DB connectivity and metrics logs |
| `StudyNexsFailedJobBacklog` | Inspect failed job rows; decide replay/reconcile/manual fix |
| `StudyNexsStaleJobBacklog` | Run stale job dry-run recovery; apply only if terminal-safe |
| `AI_LLM_ErrorRateHigh` | Check provider status/credentials/credits; use fallback only if approved |
| `AI_LLM_FallbackSpike` | Confirm provider degradation; monitor quality and cost |
| `AI_LLM_LatencyP95High` | Check provider latency and queue saturation |

## 7. Post-deploy verification

Run these after any deployment, rollback, or recovery:

```powershell
git status --short --branch
cd apps/api
python scripts/production_ops_check.py
python -c "import app.main; print('api import ok')"
```

Then run the currently relevant certification proof for the affected area.

## 8. Data handling and evidence

- Store backup artifacts outside Git.
- Do not copy production secrets into logs, screenshots, or tickets.
- Use tenant slug and IDs for internal triage; minimize student/parent PII.
- Preserve request IDs, job IDs, evaluation IDs, and tenant IDs in incident notes.

## 9. Go / no-go gate for guided pilot

Guided pilot operations are ready only when:

- production ops check passes;
- backup is created and verified;
- rollback owner is assigned;
- alert channels are watched during the session;
- recovery scripts are available to the operator;
- no P0/P1 certification or tenant-isolation issue is open.
