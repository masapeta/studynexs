# Operational Proof Design Brief

- **Program:** Stabilization program
- **Gate:** Operational Proof
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)
- **Execution plan baseline:** [`../PRODUCT_EXECUTION_PLAN.md`](../PRODUCT_EXECUTION_PLAN.md)
- **Current batch baseline:** [`../CURRENT_BATCH.md`](../CURRENT_BATCH.md)
- **Production Safety baseline:** [`../PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md`](../PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md)
- **Deployment conventions baseline:** [`../../DEPLOYMENT_CONVENTIONS.md`](../../DEPLOYMENT_CONVENTIONS.md)
- **Deployment architecture baseline:** [`../../DEPLOYMENT_ARCHITECTURE.md`](../../DEPLOYMENT_ARCHITECTURE.md)
- **Operations runbook baseline:** [`../../runbooks/production-operations.md`](../../runbooks/production-operations.md)
- **ARM review:** Accepted; implementation remains separately gated

---

## 1. Purpose

Operational Proof answers one question:

> Can StudyNexs be run, observed, backed up, restored, and smoke-tested through
> a production-like runtime without changing product behavior?

Production Safety closed direct correctness defects. Operational Proof is the
next gate because the product now needs executed operational evidence, not more
architectural intent.

This design brief does not authorize implementation.

---

## 2. Core principle

Operational claims require executed proof.

StudyNexs should not claim production readiness because a runbook exists or a
compose file is planned. It should claim operational readiness only when the
runtime can be started, inspected, backed up, restored, smoke-tested, and
rolled back with recorded evidence.

Operational Proof must remain product-neutral:

```text
Production-like runtime
        |
        v
Health, readiness, migrations, uploads, backups, metrics, restore proof
        |
        v
Certification evidence
        |
        v
No teacher/student/parent/admin behavior change
```

---

## 3. Why this gate is needed now

The accepted remediation order requires Operational Proof before AEI
Activation/Trust and before any further teacher-evaluation UX expansion.

Production Safety explicitly deferred these items:

- production Compose topology;
- persistent upload mount;
- private API binding;
- off-VM backup posture;
- real restore drill;
- CI on `develop`;
- migration/container smoke;
- authenticated metrics scraping.

Without this gate, later AEI activation would be testing academic trust on top
of an unproven runtime. That would blur product risk and operational risk.

---

## 4. Product outcome

After Operational Proof is certified, the engineering team should be able to
truthfully state:

1. the API can run from an image-only production-like Compose profile;
2. runtime uploads survive container restart/recreate through a persistent
   mount;
3. the API container is private behind the edge/proxy container;
4. PostgreSQL backups can be created, copied off the runtime host boundary, and
   restored into a clean database;
5. migrations can run safely before smoke verification;
6. `/ready` and `/metrics` can be verified under production-like settings;
7. production metrics scraping is authenticated;
8. CI runs on `develop` and validates the core container/migration smoke path;
9. rollback can be proven without product behavior changes.

---

## 5. Responsibilities

Operational Proof is responsible for proving:

- production-like container topology;
- persistent upload storage posture;
- private service binding posture;
- backup creation and off-VM copy posture;
- clean restore drill posture;
- migration and container smoke posture;
- authenticated metrics posture;
- CI trigger coverage for `develop`;
- operational evidence collection;
- rollback and recovery evidence.

Operational Proof is not responsible for:

- enabling AEI feature flags;
- changing academic evaluation behavior;
- introducing Teacher Evaluation UX-D;
- switching EUI or AEI source-of-truth behavior;
- adding object storage as the permanent upload backend;
- changing database schema for product features;
- changing public API contracts;
- changing UI behavior;
- expanding product capability claims;
- deploying to a real production VM with real school data.

---

## 6. Existing foundations to reuse

The implementation should reuse existing operational assets before creating new
ones:

| Existing asset | Expected role |
|---|---|
| `apps/api/Dockerfile` | Production API image baseline. |
| `infra/docker/docker-compose.dev.yml` | Development reference, not production runtime. |
| `infra/docker/docker-compose.observability.yml` | Observability overlay baseline. |
| `infra/nginx/nginx.conf` | Edge/proxy baseline. |
| `infra/observability/prometheus.yml` | Metrics scrape baseline. |
| `apps/api/scripts/backup_postgres.py` | Backup helper baseline. |
| `apps/api/scripts/verify_postgres_backup.py` | Backup readability helper baseline. |
| `apps/api/scripts/production_ops_check.py` | Existing operational smoke helper. |
| `.github/workflows/ci.yml` | CI baseline to extend for `develop`. |
| `docs/runbooks/production-operations.md` | Runbook baseline. |
| `docs/DEPLOYMENT_CONVENTIONS.md` | Host-layout and Compose convention baseline. |

New artifacts should be introduced only where these foundations cannot produce
the required proof.

---

## 7. Design scope

### 7.1 Production Compose proof

Operational Proof should define and later implement a production-like Compose
profile that differs from development in safety-critical ways:

- API and worker run from built image, not source bind mount;
- `ENVIRONMENT=production` posture is representable with a safe test env;
- API is not directly published to the host when behind Nginx;
- Postgres, Redis, and Qdrant are not public services in the production-like
  topology;
- uploads are mounted from a persistent host/volume path;
- worker uses the same image and runtime env as API;
- health and readiness can be checked after startup.

This gate may use synthetic secrets and local proof paths. It must not commit
real secrets.

### 7.2 Persistent uploads proof

Operational Proof should prove that upload data survives the operational action
that previously created risk:

```text
write upload/test file
        |
        v
restart or recreate API container
        |
        v
verify file still exists through mounted persistent storage
```

This does not require object storage in this gate. Local persistent storage is
acceptable for the approved single-host topology if it is mounted, backed up,
and documented honestly.

### 7.3 Private API binding proof

The API should be reachable internally by Nginx/proxy and not exposed as a
public host port in the production-like Compose profile.

The proof should distinguish:

- internal container reachability;
- public edge/proxy reachability;
- absence of direct public API port publication.

### 7.4 Off-VM backup posture

Operational Proof should not merely create a local backup file. It should define
and prove an off-runtime-boundary copy posture.

For local certification, this may use a separate host directory or artifact
folder representing off-VM retention. For real deployment, the implementation
contract should name the target mechanism or explicitly document the local
substitute used for certification.

The design goal is:

```text
database backup
        |
        v
checksum / manifest
        |
        v
copy outside runtime data directory
        |
        v
verify readability
```

### 7.5 Real restore drill

Operational Proof must include a real restore drill into a clean database or
clean restore target.

Backup readability alone is not enough.

Minimum proof:

- create backup from source database;
- restore into a clean target database/container;
- run a deterministic verification query or smoke check;
- record backup size, checksum, restore target, and verification result;
- prove restore procedure does not require production secrets in Git.

### 7.6 CI on `develop`

CI must run on the active `develop` branch.

The current workflow runs on `phase-0-foundation`, `main`, and pull requests.
Operational Proof should update the design expectation so `develop` pushes are
covered by CI before future activation work.

### 7.7 Migration and container smoke

Operational Proof should validate the deployment order:

```text
build image
        |
        v
start production-like dependencies
        |
        v
run migrations
        |
        v
start API/worker/proxy
        |
        v
verify /ready and smoke checks
```

Smoke proof should cover container import/boot, database migration state,
readiness, metrics, and one tenant-safe application probe where feasible.

### 7.8 Authenticated metrics

Production metrics must not rely on an unauthenticated scrape.

Operational Proof should prove:

- API requires a metrics token under production-like settings;
- unauthenticated scrape fails;
- authenticated scrape succeeds;
- Prometheus scrape configuration supplies the required token through a
  secret/env/file mechanism without committing the token.

---

## 8. Runtime constraints

Operational Proof must preserve these constraints:

- no product behavior changes;
- no teacher, student, parent, principal, or admin workflow changes;
- no real school data;
- no committed secrets;
- no weakening production boot guardrails;
- no public database, Redis, Qdrant, or direct API exposure in production-like
  Compose;
- no source bind mount for API/worker in production-like Compose;
- no AEI/EUI capability activation;
- no product claim expansion.

---

## 9. Expected repository surfaces for a future implementation contract

A future implementation authorization contract may permit changes in these
areas, subject to ARM review:

| Area | Possible files |
|---|---|
| Production-like Compose | `infra/docker/docker-compose.prod.yml` |
| Observability auth | `infra/observability/prometheus.yml`, related examples/templates |
| Nginx/proxy proof | `infra/nginx/*` if required |
| Ops smoke | `apps/api/scripts/production_ops_check.py` or new scoped ops proof scripts |
| Backup/restore proof | `apps/api/scripts/*backup*`, `apps/api/scripts/*restore*` |
| CI trigger/smoke | `.github/workflows/ci.yml` |
| Certification docs | `docs/product/operational-proof/*` |
| Runbook alignment | `docs/runbooks/production-operations.md`, deployment docs if implementation proves drift |

The implementation contract should whitelist exact files before code changes
begin.

---

## 10. Explicit exclusions

Operational Proof design does not authorize:

- any schema migration for product behavior;
- API response or endpoint changes;
- UI changes;
- AEI feature flag enablement;
- manual-review acknowledgement changes;
- Golden accuracy claims for AEI;
- browser proof for Teacher Evaluation UX A-C;
- OCR engine activation or Tesseract installation as a product capability;
- object storage migration;
- deployment to a live customer environment;
- production secrets, certificates, keys, or environment files in Git.

---

## 11. Validation strategy

The future implementation should produce evidence for:

| Proof area | Expected evidence |
|---|---|
| Compose config | `docker compose config` succeeds for production-like profile. |
| Image-only runtime | API/worker have no source bind mount in production-like profile. |
| Private binding | Direct API host port is not published; edge/proxy remains the public entry. |
| Persistent uploads | File survives API container restart/recreate. |
| Migration smoke | Alembic upgrade runs before readiness smoke. |
| Container smoke | API imports, boots, and `/ready` passes. |
| Metrics auth | Unauthenticated scrape fails; authenticated scrape succeeds. |
| Prometheus auth | Scrape config includes token mechanism without committed secret. |
| Backup | Backup artifact exists, has checksum, and is copied off runtime data path. |
| Restore | Backup restores into clean target and verification query passes. |
| CI | `develop` push triggers CI and runs the authorized smoke coverage. |
| Product behavior | No API/UI/AEI/EUI product behavior changes. |

---

## 12. Certification criteria

Operational Proof can be accepted only when the certification report truthfully
states:

1. production-like Compose starts successfully;
2. API and worker run from images without source bind mounts;
3. API direct host publishing is absent in production-like topology;
4. uploads survive container restart/recreate through persistent storage;
5. PostgreSQL backup is created, checksummed, copied off runtime data path, and
   verified;
6. backup is restored into a clean target and verification passes;
7. migration/container smoke passes;
8. authenticated metrics scrape is proven;
9. CI runs on `develop`;
10. no product behavior, schema, public API, UI, AEI activation, EUI source
    selection, or product claim changes occurred.

---

## 13. Rollback expectations

Rollback for Operational Proof should be operational, not product-facing.

Expected rollback posture:

- disable or remove the production-like Compose profile without changing
  application behavior;
- revert CI smoke additions without data rollback;
- revert Prometheus auth configuration changes while preserving API token
  guardrails;
- leave backup artifacts outside Git;
- no database rollback should be required because this gate should not change
  product schema.

---

## 14. Relationship to later gates

Operational Proof is the prerequisite for the next ordered gates:

1. **AEI Activation/Trust** can begin only after runtime operations are proven.
2. **Topic-ID/mastery spine unification design** remains a separate design gate.
3. **Teacher Evaluation UX-D** remains deferred until supported capabilities
   execute under a proven runtime profile with evidence.

Operational Proof does not authorize any of these later gates.

---

## 15. ARM gate

ARM accepts this design brief as the Operational Proof design baseline.

This acceptance does not authorize implementation.

The next artifact is:

```text
docs/product/operational-proof/OPERATIONAL_PROOF_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

That contract should define exact repository boundaries, permitted files,
validation commands, certification evidence, rollback proof, and explicit
exclusions before any implementation begins.
