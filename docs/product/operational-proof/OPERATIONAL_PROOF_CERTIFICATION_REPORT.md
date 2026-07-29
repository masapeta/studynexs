# Operational Proof Certification Report

**Date:** 2026-07-29

**Gate:** Operational Proof

**Status:** Accepted by ARM; commit, certification tag, and publication authorized

**Implementation contract:** [`OPERATIONAL_PROOF_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./OPERATIONAL_PROOF_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)

## 1. Recommendation

**ARM recommendation: PASS for the authorized implementation scope.**

Operational Proof establishes a production-like runtime profile and proves
image-only API/worker runtime, private API binding behind Nginx, persistent
uploads, migration/container smoke, authenticated metrics, backup creation,
off-runtime copy, and a real restore drill.

No product behavior, schema, public API, UI, AEI activation, EUI source
selection, or product capability claim changes are included.

## 2. Changed scope

| Area | Files |
|---|---|
| Production-like Compose | `infra/docker/docker-compose.prod.yml` |
| Authenticated Prometheus config | `infra/observability/prometheus.prod.yml` |
| Proxy metrics path | `infra/nginx/nginx.conf` |
| Backup/off-runtime manifest | `apps/api/scripts/backup_postgres.py` |
| Restore drill | `apps/api/scripts/restore_postgres_backup.py` |
| Metrics auth preflight | `apps/api/scripts/production_ops_check.py` |
| CI branch coverage | `.github/workflows/ci.yml` |
| Focused tests | `apps/api/tests/test_operational_proof_*.py`, `apps/api/tests/test_production_ops_check.py` |
| Runbook alignment | `docs/runbooks/production-operations.md`, `docs/DEPLOYMENT_CONVENTIONS.md` |
| Governance/certification | `docs/product/operational-proof/*` |

## 3. Scope certification

| Requirement | Result | Evidence |
|---|---:|---|
| Production-like Compose | PASS | `docker-compose.prod.yml` resolves with `docker compose config`; API/worker use the built image. |
| No source bind mount | PASS | Production-like profile mounts only `/app/uploads` for API/worker; no source tree bind mount. |
| Private API binding | PASS | `docker compose ps --format json` showed API `Ports=""`; only Nginx published `127.0.0.1:8080->80/tcp`. |
| Persistent uploads | PASS | Synthetic file under `/app/uploads` survived API container recreate. |
| Migration smoke | PASS | `docker compose run --rm api alembic upgrade head` completed all migrations. |
| Container smoke | PASS | API imported locally and ran in the production-proof stack; `/ready` returned database and Redis `ok`. |
| Metrics auth | PASS | Unauthenticated `/metrics` returned `401`; authenticated scrape returned `200`. |
| Prometheus auth | PASS | Prometheus started with `prometheus.prod.yml` and token-file config; `studynexs-api` target health was `up`. |
| Backup | PASS | Custom-format dump created, checksummed, manifested, and copied to off-runtime substitute folder. |
| Restore | PASS | Dump restored into clean `studynexs_restore_drill`; verification query returned `58`; drill database was dropped. |
| CI on `develop` | PASS | `.github/workflows/ci.yml` push branches now include `develop`. |
| Product behavior safety | PASS | No app modules, DB models, migrations, API schemas/routes, frontend files, AEI/EUI modules, or feature flags changed. |

## 4. Validation evidence

### Static and focused tests

| Check | Result |
|---|---:|
| `git diff --check` | PASS; existing CRLF normalization warning on `docs/DEPLOYMENT_CONVENTIONS.md` only |
| Ruff on changed scripts/tests | PASS |
| Focused Operational Proof tests | PASS - 11 passed |
| API import | PASS - `api import ok` |

Focused test command:

```powershell
cd apps/api
python -m pytest tests/test_production_ops_check.py tests/test_operational_proof_backup_restore.py tests/test_operational_proof_compose.py -q
```

Result:

```text
11 passed in 1.13s
```

### Compose and image proof

Commands:

```powershell
docker compose -f infra/docker/docker-compose.prod.yml config
docker compose -f infra/docker/docker-compose.prod.yml --profile observability config
docker build -t studynexs-api:operational-proof apps/api
```

Results:

- production-like Compose config: PASS;
- production-like Compose with observability profile: PASS;
- API image build: PASS.

### Migration and runtime proof

Commands:

```powershell
docker compose -f infra/docker/docker-compose.prod.yml up -d postgres redis qdrant
docker compose -f infra/docker/docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f infra/docker/docker-compose.prod.yml up -d api worker nginx
```

Results:

- dependencies started: PASS;
- Alembic upgrade to head: PASS;
- API, worker, and Nginx started: PASS.

Operational preflight command:

```powershell
cd apps/api
python scripts/production_ops_check.py `
  --skip-git `
  --compose-file <absolute path to infra/docker/docker-compose.prod.yml> `
  --base-url http://localhost:8080 `
  --metrics-token studynexs-local-operational-proof-token `
  --json
```

Result:

```json
{
  "status": "pass",
  "checks": [
    {"name": "docker_services", "status": "pass"},
    {"name": "runtime_ready", "status": "pass"},
    {"name": "platform_metrics_auth", "status": "pass"}
  ]
}
```

### Persistent uploads proof

Proof steps:

```powershell
Set-Content ops-artifacts/operational-proof/uploads/persistence-proof.txt `
  "before-container-recreate"
docker exec studynexs-prod-api sh -c "cat /app/uploads/persistence-proof.txt"
docker compose -f infra/docker/docker-compose.prod.yml up -d --force-recreate api
docker exec studynexs-prod-api sh -c "cat /app/uploads/persistence-proof.txt"
```

Result:

```text
before-container-recreate
before-container-recreate
```

### Metrics authentication and Prometheus proof

Results:

- unauthenticated `/metrics`: `401`;
- authenticated `/metrics`: `200`;
- Prometheus readiness endpoint: `Prometheus Server is Ready.`;
- Prometheus `studynexs-api` target: `health="up"`, `lastError=""`.

### Backup and restore proof

Backup command:

```powershell
cd apps/api
python scripts/backup_postgres.py `
  --compose-file <absolute path to infra/docker/docker-compose.prod.yml> `
  --output ../../ops-artifacts/operational-proof/backups/studynexs-operational-proof.dump `
  --copy-to ../../ops-artifacts/operational-proof/off-runtime-copy `
  --manifest ../../ops-artifacts/operational-proof/backups/studynexs-operational-proof.manifest.json
```

Result:

```json
{
  "status": "pass",
  "size_bytes": 196073,
  "sha256": "75534b6f33e4b16a6bdf0ade2ced16ee443d6a0e6d5da3daa76ea39167bd6d0c",
  "copied_sha256": "75534b6f33e4b16a6bdf0ade2ced16ee443d6a0e6d5da3daa76ea39167bd6d0c",
  "off_runtime_copy_substitute": true
}
```

Backup readability command:

```powershell
python scripts/verify_postgres_backup.py `
  ../../ops-artifacts/operational-proof/backups/studynexs-operational-proof.dump `
  --compose-file <absolute path to infra/docker/docker-compose.prod.yml>
```

Result:

```json
{
  "status": "pass",
  "restore_list_entries": 471,
  "contains_schema_entries": true
}
```

Restore drill command:

```powershell
python scripts/restore_postgres_backup.py `
  ../../ops-artifacts/operational-proof/backups/studynexs-operational-proof.dump `
  --compose-file <absolute path to infra/docker/docker-compose.prod.yml>
```

Result:

```json
{
  "status": "pass",
  "target_database": "studynexs_restore_drill",
  "verify_result": "58",
  "cleanup_status": "dropped"
}
```

## 5. Behavior and contract posture

- No `/api/v1` contract changed.
- No database schema or Alembic migration was added.
- No frontend files changed.
- No AEI or EUI runtime modules changed.
- No AEI/EUI feature flags were enabled.
- No teacher, student, parent, principal, or admin workflow changed.
- No real school data was used.
- No secrets, environment files, certificates, or backup artifacts were added
  to Git.

## 6. Residual risks and boundaries

| Risk / boundary | Disposition |
|---|---|
| Off-runtime copy is local certification substitute, not real cloud/off-VM retention | Recorded explicitly. Real off-VM retention still requires deployment-specific storage credentials and procedure. |
| Object storage for uploads | Not authorized; local persistent upload mount is proven for approved single-host posture only. |
| Full repository pytest | Not rerun in this gate; focused operational tests and runtime proof passed. |
| AEI activation/trust | Not authorized by this gate; remains next ordered gate after Operational Proof acceptance/publication. |
| Teacher UX-D | Still deferred until supported capabilities run with runtime evidence. |

## 7. Rollback posture

- Production-like Compose proof can be removed or not used without product data
  rollback.
- CI branch trigger change can be reverted without runtime impact.
- Prometheus production scrape config is additive; API-side token enforcement
  remains unchanged.
- Restore drill uses the synthetic `studynexs_restore_drill` database and drops
  it after verification.
- Proof artifacts live under `ops-artifacts/`, which is gitignored and
  disposable.

## 8. Phase retrospective

What held:

- The Production Safety PDF/container hardening made the API image build fast
  and repeatable.
- Existing backup/readability scripts were a good foundation and only needed
  checksum, copy, and restore-drill extensions.
- API-side metrics token enforcement already existed and only needed proxy and
  Prometheus proof.

What surfaced:

- Nginx did not proxy `/metrics`, so authenticated scrape proof through the
  public entry initially failed. Adding a `/metrics` proxy location fixed the
  operational path while preserving API-side auth.
- The restore-drill script initially imported correctly as a module but not as
  a direct script. The import now supports both execution modes.
- Relative compose paths from nested script directories are easy to get wrong
  in PowerShell; certification used absolute paths for runtime proof.

## 9. ARM gate

ARM decision: **Operational Proof accepted; commit, annotated certification tag,
and publication authorized.**

Recommended commit, if accepted:

```text
ops: add operational proof foundation
```

Recommended annotated tag, if accepted and committed:

```text
operational-proof-certified
```

After publication, update `docs/STATUS.md`, `docs/product/CURRENT_BATCH.md`,
`docs/product/PRODUCT_EXECUTION_PLAN.md`, and
`docs/decisions/DECISION_LOG.md` as a separate docs-only status/governance
commit.
