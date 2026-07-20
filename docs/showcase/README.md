# Showcase — StudyNexs Reference School

> **Official name:** StudyNexs Reference School  
> **Showcase display name:** ARM International School  
> **Engineering shorthand:** Showcase  
> **Purpose:** Permanent product asset — full end-to-end working model for prospects

---

## What this is

The Reference School is a **real tenant** where principals, teachers, parents, and students can log in and experience the complete StudyNexs platform.

Prospects explore here. When a real school signs, they get **their own tenant** — data import, pilot, go-live — never this one.

| Property | Value |
|----------|-------|
| **Formal name** | StudyNexs Reference School |
| **Display name in product** | **ARM International School** |
| **Tenant slug** | `reference` |
| **Config source** | `apps/api/scripts/reference_school_config.py` |
| **Seed (one command)** | `python scripts/seed_reference_school.py` |
| **Login card** | [`REFERENCE_SCHOOL_LOGIN_CARD.md`](./REFERENCE_SCHOOL_LOGIN_CARD.md) |
| **Capability audit** | [`REFERENCE_SCHOOL_CAPABILITY_AUDIT.md`](./REFERENCE_SCHOOL_CAPABILITY_AUDIT.md) |

See [`customer-journey/README.md`](../customer-journey/README.md) for the adoption lifecycle.

---

## Quick start (operator)

```powershell
cd D:\Projects\studynexs-platform\studynexs-dev

docker compose -f infra/docker/docker-compose.dev.yml up -d

cd apps\api
python scripts/seed_reference_school.py
python scripts/smoke_reference_school.py    # API on :8000

cd ..\admin-web
# .env.local: NEXT_PUBLIC_TENANT_SLUG=reference
npm run dev -- -p 3006
```

**Prospect logins** (password `Demo@1234`): `principal`, `teacher6`, `parent_demo`, `student_demo`

---

## Documentation index

| Document | Purpose |
|----------|---------|
| [DEMO_V1_SCRIPT.md](./DEMO_V1_SCRIPT.md) | **Primary** — 45–60 min day-in-the-life demo (Journeys 0–5) |
| [DEMO_V1_JOURNEY_CHECKLIST.md](./DEMO_V1_JOURNEY_CHECKLIST.md) | Pre-demo pass/fail checklist |
| [REFERENCE_SCHOOL_CAPABILITY_AUDIT.md](./REFERENCE_SCHOOL_CAPABILITY_AUDIT.md) | What exists vs demo-ready (code audit) |
| [REFERENCE_SCHOOL_LOGIN_CARD.md](./REFERENCE_SCHOOL_LOGIN_CARD.md) | Prospect login card |
| [SHOWCASE_DEMO_SCRIPT.md](./SHOWCASE_DEMO_SCRIPT.md) | Legacy Batch 1 script (superseded by DEMO_V1_SCRIPT) |
| [SHOWCASE_ROADMAP.md](./SHOWCASE_ROADMAP.md) | Demo v1 journey targets |
| [reference-school/](./reference-school/) | Validation evidence |

---

## Not Reference School

| Item | Location |
|------|----------|
| Naagarjuna Talent School (prospect) | [`discovery/schools/naagarjuna/`](../discovery/schools/naagarjuna/) |
| Legacy thin pilot seeds | `seed_pilot_naagarjuna*.py` — deprecated for showcase |
| Customer pilot execution | [`customer-pilot/`](../customer-pilot/) |

---

## Customer lifecycle

```
Prospect → Reference School (ARM International School) → signs → new tenant → import data → pilot
```

Reference School stays maintained as the canonical product demonstration.
