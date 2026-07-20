# Showcase — StudyNexs Reference School

> **Official name:** StudyNexs Reference School  
> **General usage:** Reference School  
> **Engineering shorthand:** Showcase  
> **Purpose:** Permanent product asset — canonical demonstration of the platform

---

## What this is

The Showcase is our **permanent product asset** — the **StudyNexs Reference School** — a continuously maintained **golden tenant** for sales, training, and pre-customer validation.

It is **not** a customer tenant, **not** a throwaway demo database, and **not** any single prospect's production environment.

| Property | Value |
|----------|-------|
| **Formal name** | StudyNexs Reference School |
| **Engineering shorthand** | Showcase |
| **Golden tenant rule** | New capabilities are demonstrated here **before** customer rollout |
| **Software baseline** | `v0.1.0-batch1` |
| **Tenant slug (current)** | `naagarjuna` — Phase B target: `showcase` |
| **Roadmap** | [`SHOWCASE_ROADMAP.md`](./SHOWCASE_ROADMAP.md) — what the Reference School should eventually demonstrate |

See [`customer-journey/README.md`](../customer-journey/README.md) for how the Reference School fits in the adoption lifecycle.

---

## Product asset model

The Reference School is a **StudyNexs product asset** — maintained by StudyNexs, not owned by a customer.

```
StudyNexs
    ├── Platform ..................... software, Intelligence Layer, portals
    ├── Reference School ............. canonical demonstration environment
    ├── Documentation ................ governance, architecture, runbooks
    └── Customer Tenants ............. one per signed school (onboarding + pilot + go-live)
```

Internally the Reference School is backed by a tenant (isolation, `school_id`). In product and governance documentation, treat it as a **product asset**, not as a customer school.

### Terminology (frozen — do not introduce synonyms)

| Context | Use |
|---------|-----|
| Official name | **StudyNexs Reference School** |
| General usage | **Reference School** |
| Engineering shorthand | **Showcase** |
| **Avoid** | Demo School · Showcase School · Pilot School (ambiguous) |

---

## Documentation index

| Document | Purpose |
|----------|---------|
| [SHOWCASE_GO.md](./SHOWCASE_GO.md) | Showcase environment authorized to operate |
| [SHOWCASE_DECISION_LOG.md](./SHOWCASE_DECISION_LOG.md) | Ops decisions (Priority, Owner, Status) |
| [SHOWCASE_DEMO_SCRIPT.md](./SHOWCASE_DEMO_SCRIPT.md) | Sales walkthrough (HOD + teacher) |
| [SHOWCASE_ENVIRONMENT_VALIDATION.md](./SHOWCASE_ENVIRONMENT_VALIDATION.md) | Pre-demo stack checks |
| [SHOWCASE_READINESS_AUDIT.md](./SHOWCASE_READINESS_AUDIT.md) | Readiness audit (historical T-0) |
| [SHOWCASE_ROADMAP.md](./SHOWCASE_ROADMAP.md) | Golden tenant capability target & quality standards |
| [reference-school/](./reference-school/) | Seed scripts, Batch 1 validation evidence |

## Quick start (operator)

```powershell
cd D:\Projects\studynexs-platform\studynexs-dev
git checkout v0.1.0-batch1   # or develop at/after tag

docker compose -f infra/docker/docker-compose.dev.yml up -d

cd apps\api
python scripts/seed_pilot_naagarjuna.py          # Phase B: rename to seed_showcase
python scripts/seed_pilot_naagarjuna_curriculum.py
python scripts/smoke_pilot_readiness.py           # expect 12/12

cd ..\admin-web
# .env.local: NEXT_PUBLIC_TENANT_SLUG=naagarjuna (Phase B: showcase)
npm run dev -- -p 3006
```

Playwright: `node scripts/batch1-ui-workflow-demo.cjs` → evidence in [`product/batch1-ui-demo/`](../product/batch1-ui-demo/).

---

## Operating mode

- Enrich representative demo data (Classes 6–10, Telangana SSC, etc.) — product backlog.
- **No customer-specific information** in this tree — use [`discovery/schools/`](../discovery/schools/).
- Software changes: critical defects on `v0.1.0-batch1` baseline only (PO-approved).
