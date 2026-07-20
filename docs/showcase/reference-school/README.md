# Reference School — Demonstration Tenant

> **Formal name:** StudyNexs Reference School  
> **Display name:** **ARM International School**  
> **Purpose:** Permanent full working model — prospects log in and experience the platform  
> **Not a customer production environment**

---

## Tenant

| Field | Value |
|-------|-------|
| **Slug** | `reference` |
| **Display name** | ARM International School |
| **Config** | `apps/api/scripts/reference_school_config.py` |

**Seed (one command):**

```powershell
cd apps\api
python scripts/seed_reference_school.py
python scripts/smoke_reference_school.py
```

**Login card:** [`../REFERENCE_SCHOOL_LOGIN_CARD.md`](../REFERENCE_SCHOOL_LOGIN_CARD.md)

---

## Legacy (not Reference School)

| Item | Notes |
|------|-------|
| `seed_pilot_naagarjuna*.py` | Prospect tooling only |
| `smoke_pilot_readiness.py` | Batch 1 wedge validation — superseded for showcase |
| Tenant `test` | Old dev slug — replaced by `reference` |

---

## Validation evidence (Batch 1 baseline)

| Artifact | Location |
|----------|----------|
| Smoke results (historical) | [`t0-evidence/smoke-results.json`](./t0-evidence/smoke-results.json) |
| T-0 checklist | [`t0-evidence/t0-checklist.md`](./t0-evidence/t0-checklist.md) |

Re-run showcase validation with `smoke_reference_school.py` after seeding `reference`.

---

## Prospect note

**Naagarjuna Talent School** is a commercial prospect record: [`discovery/schools/naagarjuna/`](../../discovery/schools/naagarjuna/) — not the Reference School.
