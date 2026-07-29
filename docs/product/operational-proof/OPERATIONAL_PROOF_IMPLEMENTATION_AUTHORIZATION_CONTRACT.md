# Operational Proof Implementation Authorization Contract

- **Program:** Stabilization program
- **Gate:** Operational Proof
- **Authorization ID:** OPS-PROOF-AUTH-001
- **Classification:** Implementation authorization contract
- **Status:** Accepted
- **Implementation:** Authorized within this contract only
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./OPERATIONAL_PROOF_DESIGN_BRIEF.md`](./OPERATIONAL_PROOF_DESIGN_BRIEF.md)
- **Production Safety baseline:** [`../PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md`](../PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)
- **Execution plan baseline:** [`../PRODUCT_EXECUTION_PLAN.md`](../PRODUCT_EXECUTION_PLAN.md)
- **ARM review:** Accepted; Operational Proof implementation authorized within this contract only

---

## 1. Authorization status

This document is the accepted implementation authorization contract for
Operational Proof.

Implementation is authorized only within the scope, repository boundary,
validation requirements, rollback proof, and explicit exclusions defined here.

---

## 2. Purpose

Operational Proof should prove that StudyNexs can run in a production-like
container topology, preserve uploads, remain privately bound behind the edge
container, execute migrations and smoke checks, expose authenticated metrics,
and complete a real backup/restore drill.

The implementation must answer:

> Can StudyNexs be operated and recovered through a production-like runtime
> without changing product behavior?

This is an operational certification gate, not a product-feature gate.

---

## 3. Implementation scope

This contract authorizes only the following work.

### 3.1 Production-like Compose profile

Add a production-like Docker Compose profile that proves the approved
single-host runtime posture.

The profile must:

- run API and worker from built images;
- avoid source bind mounts for API and worker;
- support `ENVIRONMENT=production` boot posture using synthetic local proof
  secrets;
- keep API private behind Nginx/proxy;
- avoid public host ports for PostgreSQL, Redis, Qdrant, and direct API;
- mount uploads through persistent storage;
- run worker from the same image and environment posture as API;
- support health/readiness verification.

### 3.2 Persistent uploads proof

Implement a deterministic proof that a file under the configured upload mount
survives API container restart or recreate.

The proof may use a synthetic test file and must not use real student,
teacher, parent, admission, answer-sheet, or school data.

### 3.3 Private API binding proof

Add automated or scripted evidence that:

- Nginx/proxy can reach the API internally;
- the public entry point is the proxy;
- direct API host port publishing is absent from the production-like profile.

### 3.4 Backup and off-runtime copy proof

Extend or add operational scripts to create a PostgreSQL backup, compute a
checksum/manifest, and copy the artifact outside the runtime data directory.

For local certification, an off-runtime-boundary directory may stand in for a
true off-VM target. The certification report must label this as a local
certification substitute, not as proof of cloud or real off-VM retention.

No real production secrets or backup artifacts may be committed.

### 3.5 Real restore drill

Implement a real restore drill into a clean database target.

Minimum drill requirements:

- create backup from source database;
- restore into clean target database or clean restore container;
- run deterministic verification query or smoke check;
- emit evidence containing backup size, checksum, restore target, and
  verification result;
- leave no committed backup artifact.

Backup readability without restore is insufficient for this gate.

### 3.6 Migration and container smoke

Add an operational smoke path that proves:

```text
build image
        |
        v
start production-like dependencies
        |
        v
run Alembic migrations
        |
        v
start API / worker / proxy
        |
        v
verify readiness, metrics, and smoke probes
```

The smoke path must be deterministic and suitable for local and CI execution
where Docker is available.

### 3.7 Authenticated metrics proof

Update metrics scrape configuration and proof scripts so production-like
metrics are authenticated.

The implementation must prove:

- unauthenticated `/metrics` scrape fails when `METRICS_TOKEN` is configured;
- authenticated `/metrics` scrape succeeds;
- Prometheus can be configured with a token mechanism without committing the
  token;
- metrics proof avoids tenant, student, parent, teacher, and raw content
  labels.

### 3.8 CI on `develop`

Update CI so pushes to `develop` run the existing quality gates.

If a container/migration smoke job is added to CI, it must use synthetic
configuration only and must not require production secrets.

### 3.9 Documentation and certification

Produce an Operational Proof certification report documenting:

- production-like Compose proof;
- persistent uploads proof;
- private API binding proof;
- backup and off-runtime copy proof;
- real restore drill proof;
- migration/container smoke proof;
- authenticated metrics proof;
- CI on `develop`;
- rollback proof;
- phase retrospective;
- no product behavior change.

---

## 4. Authorized repository boundary

Implementation may modify only the following areas.

### 4.1 Infrastructure and observability

Permitted:

```text
infra/docker/docker-compose.prod.yml
infra/observability/prometheus.yml
infra/observability/*.yml
infra/nginx/*
```

`infra/nginx/*` may be changed only if required for private API/proxy proof.

### 4.2 API operational scripts

Permitted:

```text
apps/api/scripts/backup_postgres.py
apps/api/scripts/verify_postgres_backup.py
apps/api/scripts/production_ops_check.py
apps/api/scripts/*restore*.py
apps/api/scripts/*operational*.py
```

Any new script must be operational proof only. It must not change product data
except inside synthetic proof databases or explicitly created proof artifacts.

### 4.3 CI

Permitted:

```text
.github/workflows/ci.yml
```

### 4.4 Tests

Permitted:

```text
apps/api/tests/test_production_ops_check.py
apps/api/tests/test_operational_proof_*.py
apps/api/tests/test_*backup*.py
apps/api/tests/test_*restore*.py
apps/api/tests/test_*compose*.py
```

Tests must use synthetic data and temporary paths.

### 4.5 Documentation

Permitted:

```text
docs/product/operational-proof/
docs/runbooks/production-operations.md
docs/DEPLOYMENT_CONVENTIONS.md
docs/DEPLOYMENT_ARCHITECTURE.md
```

Deployment and runbook docs may be updated only to align with implemented
proof. They must not claim capabilities not demonstrated by the certification.

Post-publication status updates must be committed separately:

```text
docs/STATUS.md
docs/product/CURRENT_BATCH.md
docs/product/PRODUCT_EXECUTION_PLAN.md
docs/decisions/DECISION_LOG.md
```

### 4.6 Protected areas

The following must not be changed under this contract:

```text
apps/admin-web/
apps/api/app/modules/examinations/
apps/api/app/modules/eui/
apps/api/app/modules/ai/
apps/api/app/db/models/
apps/api/alembic/versions/
```

Any change to protected areas requires separate ARM authorization.

---

## 5. Runtime constraints

Operational Proof implementation must be:

- product-neutral;
- synthetic-data-only;
- secret-safe;
- tenant-safe;
- rollbackable;
- deterministic where practical;
- compatible with the existing `/api/v1` contract;
- respectful of production boot guardrails.

The implementation must not weaken production validation to make the proof
pass.

---

## 6. Explicit exclusions

This contract does not authorize:

- database schema changes;
- Alembic migrations for product behavior;
- API route changes;
- API response shape changes;
- UI changes;
- admin-web changes;
- AEI feature flag enablement;
- EUI source-of-truth switching;
- Teacher Evaluation UX-D;
- manual-review acknowledgement changes;
- Golden accuracy or teacher-marked set work;
- object storage migration;
- real production deployment;
- real school data;
- committed `.env`, key, certificate, token, or backup artifacts;
- OCR activation or Tesseract installation as a product capability;
- public product claim changes.

---

## 7. Required validation

Before ARM acceptance, implementation must provide evidence for:

| Area | Required proof |
|---|---|
| Compose syntax | `docker compose config` passes for production-like profile. |
| Image-only API/worker | Production-like profile has no API/worker source bind mount. |
| Private API | Direct API host port is absent; proxy remains public entry. |
| Persistent uploads | Synthetic upload file survives API restart/recreate. |
| Migration smoke | Alembic upgrade succeeds against proof database. |
| Container smoke | API imports, boots, and `/ready` passes. |
| Metrics auth | Unauthenticated scrape fails; authenticated scrape succeeds. |
| Prometheus auth | Scrape config has token mechanism without committed token. |
| Backup | Backup is created, non-empty, checksummed, and copied off runtime data path. |
| Restore | Backup restores into clean target and verification passes. |
| CI | `develop` is included in CI push branches. |
| Behavior safety | No product API/UI/AEI/EUI behavior changes. |

---

## 8. Recommended validation commands

The final implementation may adjust exact commands if the certification report
explains why. Expected commands include:

```powershell
git diff --check
docker compose -f infra/docker/docker-compose.prod.yml config
docker build -t studynexs-api:operational-proof apps/api
cd apps/api
python -c "import app.main; print('api import ok')"
pytest tests/test_production_ops_check.py -q
```

If Docker is unavailable in the local environment, the implementation may not
be accepted as complete unless equivalent CI/container evidence is attached.

---

## 9. Certification deliverable

Implementation must add:

```text
docs/product/operational-proof/OPERATIONAL_PROOF_CERTIFICATION_REPORT.md
```

The report must include:

- starting commit;
- changed files;
- proof commands;
- command results;
- generated evidence locations, excluding secrets and backup payloads;
- restore drill evidence;
- metrics authentication evidence;
- CI trigger evidence;
- rollback proof;
- residual risks;
- phase retrospective;
- ARM recommendation.

---

## 10. Rollback proof

Rollback proof must demonstrate:

- disabling or not using the production-like Compose profile leaves existing
  development and product flows unchanged;
- no data migration rollback is needed;
- no product feature flag rollback is needed;
- removing CI smoke additions does not change runtime behavior;
- metrics auth configuration can be reverted without weakening API-side token
  enforcement;
- backup/restore proof artifacts are outside Git and disposable.

---

## 11. Exit criteria

Operational Proof can be accepted only when all of the following are true:

1. all authorized implementation surfaces are within this contract;
2. production-like Compose proof passes;
3. persistent uploads proof passes;
4. private API binding proof passes;
5. backup and off-runtime copy proof passes;
6. real restore drill passes;
7. migration/container smoke passes;
8. authenticated metrics proof passes;
9. CI includes `develop`;
10. certification report is complete;
11. no schema/API/UI/AEI/EUI/product behavior change is introduced;
12. no real secrets, env files, certificates, or backup artifacts are committed.

---

## 12. Publication metadata

If implementation is later accepted, recommended metadata:

```text
Commit: ops: add operational proof foundation
Tag: operational-proof-certified
```

`docs/STATUS.md` should be updated only after publication as a separate
docs-only status commit.

---

## 13. ARM gate

ARM accepts this contract.

Operational Proof implementation may begin within this contract only.

Acceptance of this contract will not authorize AEI Activation/Trust,
topic-ID/mastery spine design, Teacher Evaluation UX-D, or any product-facing
behavior change.
