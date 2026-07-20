# StudyNexs — Deployment Conventions

> **Implementation contract** for how deployments are organized on disk and in Compose.
> Not architecture (see [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md)) — **how to lay out and operate** a host.
>
> **Owner:** Avinash Reddy Masapeta · **Status:** v1.0 draft · **Last updated:** 2026-07-16  
> **Approved in draft form** — freeze after Gate 1A (§12).

---

## 1. Purpose

One definitive reference for engineers and agents **before** creating directories, compose files,
or env files on a VM. If this doc and implementation disagree, fix implementation or update this
doc in the same change — never leave silent drift.

**Read with:**

| Document | Role |
|----------|------|
| [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) | Where services run (cloud topology) |
| [`URL_ARCHITECTURE.md`](./URL_ARCHITECTURE.md) | Hostnames and tenant routing |
| [`pilot/GATE1_EXECUTION.md`](./pilot/GATE1_EXECUTION.md) | Gate 1A execution checklist |
| [`../infra/inventory/`](../infra/inventory/) | SSH keys, future host inventory |

---

## 2. Directory layout (OCI production VM)

All StudyNexs host state lives under **`/opt/studynexs/`**. Do not scatter paths across `/home`.

```
/opt/studynexs/
│
├── repo/                       # Git clone — fully reproducible from Git
│   └── infra/                  # Source: docker/, nginx/, scripts/, observability/
│
├── runtime/                    # Active deploy metadata (not in Git)
│   └── current.json            # e.g. image tag, git sha, deployed_at
│
├── data/                       # Persistent runtime state (never in Git)
│   ├── postgres/               # If bind-mounted; else Docker named volume
│   ├── qdrant/
│   └── uploads/                # API uploads until object storage (Gate 2+)
│
├── backups/                    # Backup staging before off-VM copy
│   ├── postgres/
│   └── manifests/              # Optional: date, size, checksum log
│
├── deploy/                     # Active deployment artifacts for THIS host
│   ├── compose/                # Compose files used by docker compose
│   ├── env/                    # Secrets — chmod 600, never in Git
│   │   └── api.env
│   ├── nginx/                  # Active nginx.conf (+ includes if any)
│   ├── scripts/                # Host deploy/backup helpers (copied from repo)
│   └── ssl/                    # Origin certs if not terminated only at Cloudflare
│
└── monitoring/                 # Active observability stack (Gate 2+)
    ├── prometheus/
    ├── grafana/
    └── otel/
```

**Naming:** lowercase, no spaces. Container names use `studynexs-` prefix (matches dev compose).

**SSH / IP / DNS:** record in [`infra/inventory/`](../infra/inventory/) — not in this document.

---

## 3. Repository vs deploy (Git vs VM)

| | **`repo/`** (Git) | **`deploy/`** (VM operational) |
|--|-------------------|--------------------------------|
| **Role** | Source of truth for infrastructure definitions | What this host runs **right now** |
| **Reproducible from Git?** | Yes — clone + checkout tag/commit | No — env secrets and host paths are local |
| **Contains secrets?** | Never | Yes — `deploy/env/` only |
| **Updated how?** | `git pull` / deploy new tag | Copy or sync from `repo/infra/` + edit env |

**Sync flow (every deploy or bootstrap):**

```
repo/infra/
├── docker/          ──copy/sync──►  deploy/compose/
├── nginx/           ──copy/sync──►  deploy/nginx/
└── scripts/         ──copy/sync──►  deploy/scripts/

deploy/env/api.env   ◄── created on host only (never from Git)
```

**Rules:**

1. **Repository architecture describes the software.** Paths under `repo/` mirror the Git tree.
2. **Server layout describes operations.** Paths under `deploy/`, `data/`, `backups/`, `runtime/` are host-specific.
3. **`repo/` is fully reproducible from Git.** Delete and re-clone anytime.
4. **Runtime state never belongs in Git.** Data, backups, env, SSL private keys, `runtime/`.

Do not edit `deploy/compose/` as the canonical compose file — change `infra/docker/` in Git, then
sync to the VM.

---

## 4. Compose layering

Canonical compose files live in **Git:** `infra/docker/`. On the VM they are synced to
**`deploy/compose/`** — do not fork compose into random paths.

### 4.1 Layers (merge order)

| Layer | File (Git: `infra/docker/`) | VM: `deploy/compose/` |
|-------|----------------------------|------------------------|
| **Base stack** | `docker-compose.dev.yml` | Reference for Gate 1A |
| **Production** | `docker-compose.prod.yml` | *Add at Gate 1A hardening* — image-only API, prod env |
| **Observability** | `docker-compose.observability.yml` | Gate 2+ overlay |

**Command pattern (production):**

```bash
cd /opt/studynexs/deploy/compose
docker compose -f docker-compose.prod.yml up -d
# With observability (later):
docker compose -f docker-compose.prod.yml -f docker-compose.observability.yml up -d
```

Compose must reference:

- `env_file: ../env/api.env` (relative to compose dir) **or** absolute `/opt/studynexs/deploy/env/api.env`
- Nginx volume: `../nginx/nginx.conf:/etc/nginx/nginx.conf:ro`

### 4.2 Service rules

| Service | Production rule |
|---------|-----------------|
| **api** | Built image `studynexs-api:<tag>`. **No** source bind-mount from `repo/`. |
| **nginx** | Config from `deploy/nginx/nginx.conf` — read-only mount. |
| **postgres / redis / qdrant** | Named volumes **or** `/opt/studynexs/data/*` bind mounts — document choice in inventory. |
| **worker** | Same `deploy/env/api.env`; no public ports when split from API. |

### 4.3 Dev vs prod

| | Development (local / VM dev) | Production (demo / pilot / app) |
|--|------------------------------|-----------------------------------|
| API code mount | Allowed in dev compose | **Forbidden** — image only |
| `ENVIRONMENT` | `development` | `production` |
| Postgres password | `studynexs_dev` | Strong unique secret in `deploy/env/api.env` |
| Public ports | May expose DB ports for debug | **Only 80/443** (Nginx) to internet |

---

## 5. Environment file policy

### 5.1 Locations

| Environment | API env file | Web (Cloudflare) |
|-------------|--------------|------------------|
| Local dev | `apps/api/.env` (gitignored) | `apps/admin-web/.env.local` (gitignored) |
| OCI VM | `/opt/studynexs/deploy/env/api.env` | Cloudflare Pages — build env vars |
| CI | GitHub Actions secrets | N/A |

### 5.2 Rules

1. **Never commit** secrets, `.env`, `.pem`, or private keys.
2. **One file per runtime** on VM: `deploy/env/api.env` via compose `env_file:`.
3. **Permissions:** `chmod 600` on `api.env`; owner = deploy user.
4. **Required keys** — [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) §8. Production boot **crashes** if guardrails fail.
5. **Rotation:** update env → rolling restart → verify `/ready` → append to `runtime/current.json` (not Git).

### 5.3 Web build variables (Cloudflare Pages)

Set in Cloudflare UI — not on OCI VM: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_TENANT_BASE_DOMAIN`,
`NEXT_PUBLIC_TENANT_SLUG`. Rebuild web when these change.

---

## 6. Bind mount policy

| Path | Mount type | Production |
|------|------------|------------|
| PostgreSQL data | Named volume `pgdata` **or** `/opt/studynexs/data/postgres` | Required persistence |
| Qdrant data | Named volume **or** `/opt/studynexs/data/qdrant` | Required if RAG enabled |
| API uploads | `/opt/studynexs/data/uploads` → `/app/uploads` | Until object storage |
| Nginx config | `deploy/nginx/nginx.conf` → container `:ro` | Read-only |
| Application source | — | **Do not mount** in production |

Never mount `deploy/env/` inside the image; use compose `env_file:` only.

---

## 7. Backup policy

### 7.1 Gate 1A (demo)

| Asset | Policy |
|-------|--------|
| PostgreSQL | Daily `pg_dump` → `/opt/studynexs/backups/postgres/`; keep 7 days |
| Redis | No backup — rebuild acceptable |
| Qdrant | Re-index from CurriculumPack if lost |
| Uploads | Weekly copy of `data/uploads/` if used |
| Env secrets | Password manager — not in backup buckets |

### 7.2 Pilot+ (target)

Daily Postgres backup + off-VM copy; quarterly restore drill. See [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) §13.

### 7.3 Reference command

```bash
docker exec studynexs-postgres pg_dump -U studynexs studynexs \
  | gzip > /opt/studynexs/backups/postgres/studynexs_$(date +%Y%m%d_%H%M).sql.gz
```

---

## 8. Operational principles (frozen)

These do not change without ARM approval and a conventions doc update:

1. **Repository architecture describes the software. Server layout describes operations.**
2. **`repo/` is fully reproducible from Git. Runtime state never belongs in Git.**
3. **Run database migrations before switching traffic.**
4. **Always run smoke tests after deployment.**
5. **Frontend and API deploy independently** — update CORS when adding origins.
6. **Tenant isolation is non-negotiable** — reserved API hosts + `X-Tenant-Slug`; see [`URL_ARCHITECTURE.md`](./URL_ARCHITECTURE.md).
7. **Fail secure** — production env validation must pass before serving traffic.
8. **Immutable API in production** — image tag recorded in `runtime/current.json`.
9. **Sync `deploy/` from Git** — do not let the VM become the canonical compose editor.
10. **Host facts live in `infra/inventory/`** — SSH, IP, DNS, backups, certs (metadata). Do not duplicate in architecture docs.

---

## 9. Gate 1A VM bootstrap sequence

```
1. Create /opt/studynexs/{repo,runtime,data,backups,deploy,monitoring}
2. Create deploy/{compose,env,nginx,scripts,ssl}
3. git clone → /opt/studynexs/repo
4. Sync repo/infra/docker → deploy/compose/
5. Sync repo/infra/nginx → deploy/nginx/
6. Create deploy/env/api.env (chmod 600)
7. Install Docker + Compose
8. cd deploy/compose && docker compose build && up (healthchecks green)
9. cd repo/apps/api && alembic upgrade head && demo seed
10. Verify /health and /ready via Nginx
11. DNS api.studynexs.com → VM
12. Cloudflare Pages → demo.studynexs.com
13. HTTPS smokes green
14. Write runtime/current.json (image tag, sha, timestamp)
15. Apply document freeze protocol (§12) → commit (ARM approval)
```

---

## 10. Change control

| Change type | Update |
|-------------|--------|
| Host path convention | This file + `DEPLOYMENT_ARCHITECTURE.md` §6.0 + inventory |
| Compose layer | `infra/docker/` in Git → sync to `deploy/compose/` |
| New required env var | `DEPLOYMENT_ARCHITECTURE.md` §8 + this file §5 |
| Backup schedule | This file §7 + `infra/inventory/BACKUP_SCHEDULE.md` |

**Do not** add another foundational doc — extend this contract or `infra/inventory/`.

---

## 11. Related documents

- [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) — topology (includes §6.0 layout)
- [`URL_ARCHITECTURE.md`](./URL_ARCHITECTURE.md) — hostnames
- [`PLATFORM_ARCHITECTURE.md`](./PLATFORM_ARCHITECTURE.md) — product layers (not host paths)
- [`infra/inventory/README.md`](../infra/inventory/README.md) — operational inventory index

---

## 12. Document freeze protocol (after Gate 1A)

When HTTPS smokes pass, update **each** architecture doc header from draft to frozen:

```markdown
**Status:** v1.0 (Frozen)
**Approved:** YYYY-MM-DD
**Approved by:** Avinash Reddy Masapeta
**Breaking architectural changes require explicit ARM approval.**
```

Apply to: `URL_ARCHITECTURE.md`, `PLATFORM_ARCHITECTURE.md`, `DEPLOYMENT_ARCHITECTURE.md`, this file.

Inventory files (`infra/inventory/*`) are updated continuously — they are not frozen versions.

---

## 13. Change classification (governance)

Every proposed documentation or deployment change falls into one of four levels:

| Level | Type | Action |
|-------|------|--------|
| **1 — Bug** | Wrong command, env var, diagram | Fix immediately in the correct layer |
| **2 — Clarification** | Wording, examples | Update the relevant doc only |
| **3 — Operational learning** | Gate 1A discoveries (OCI, Cloudflare, Docker) | Update **this file** or **inventory** — no architecture redesign |
| **4 — Architecture** | Tenant model, routing, deployment strategy, platform boundaries | **Explicit ARM approval** before editing frozen architecture docs |

**Agent rule:** Classify first → run **Documentation Impact** (Architecture? Execution? Infrastructure?) → update only the matching layer → never duplicate across layers.

**Every batch / PR:** [`docs/engineering/ONBOARDING.md`](./engineering/ONBOARDING.md) § Documentation Impact.

Standing instruction: [`docs/engineering/ONBOARDING.md`](./engineering/ONBOARDING.md) § Documentation governance.
