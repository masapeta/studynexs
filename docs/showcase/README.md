# Showcase — StudyNexs Reference School

> **Formal name:** StudyNexs Reference School  
> **Engineering shorthand:** Showcase  
> **Purpose:** Permanent internal demonstration environment — **not** a customer tenant

---

## What this is

The Showcase is our **permanent sales and training environment** containing representative educational data. It demonstrates the complete StudyNexs platform to prospective schools.

| Property | Value |
|----------|-------|
| **Not** | A customer tenant · Naagarjuna's production environment · A live school pilot |
| **Is** | Internal demo · Sample data · Reusable across all sales demonstrations |
| **Software baseline** | `v0.1.0-batch1` (tag on `studynexs-dev`) |
| **Tenant slug (current)** | `naagarjuna` — **Phase B target:** `showcase` |
| **Display name (Phase B)** | StudyNexs Reference School |

See [`customer-journey/README.md`](../customer-journey/README.md) for how Showcase fits in the adoption lifecycle.

---

## Documentation index

| Document | Purpose |
|----------|---------|
| [SHOWCASE_GO.md](./SHOWCASE_GO.md) | Showcase environment authorized to operate |
| [SHOWCASE_DECISION_LOG.md](./SHOWCASE_DECISION_LOG.md) | Ops decisions (Priority, Owner, Status) |
| [SHOWCASE_DEMO_SCRIPT.md](./SHOWCASE_DEMO_SCRIPT.md) | Sales walkthrough (HOD + teacher) |
| [SHOWCASE_ENVIRONMENT_VALIDATION.md](./SHOWCASE_ENVIRONMENT_VALIDATION.md) | Pre-demo stack checks |
| [SHOWCASE_READINESS_AUDIT.md](./SHOWCASE_READINESS_AUDIT.md) | Readiness audit (historical T-0) |
| [reference-school/](./reference-school/) | Seed scripts, validation evidence |

---

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
