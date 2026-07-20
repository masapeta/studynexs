# Naagarjuna Talent School — Pilot Tenant

> **Tenant slug:** `naagarjuna`  
> **Pilot wedge:** Class 10 · Mathematics · Telangana SSC  
> **Baseline:** `studynexs-dev` branch `develop`

---

## Seed scripts

| Script | Purpose |
|--------|---------|
| [`apps/api/scripts/seed_pilot_naagarjuna.py`](../../../apps/api/scripts/seed_pilot_naagarjuna.py) | Idempotent tenant + accounts |
| [`apps/api/scripts/seed_pilot_naagarjuna_curriculum.py`](../../../apps/api/scripts/seed_pilot_naagarjuna_curriculum.py) | Curriculum pack via `approve_pack()` pipeline |

Run from `apps/api`:

```powershell
python scripts/seed_pilot_naagarjuna.py
python scripts/seed_pilot_naagarjuna_curriculum.py
```

---

## Validation

| Suite | Command | Target |
|-------|---------|--------|
| Smoke (12 checks) | `python scripts/smoke_pilot_readiness.py` | 12/12 |
| Playwright (11 steps) | `node scripts/batch1-ui-workflow-demo.cjs` | 11/11 |

Playwright requires admin-web on `:3006` with `.env.local` pointing to `http://localhost:8000`.

---

## Evidence

| Artifact | Location |
|----------|----------|
| T-0 checklist | [`t0-evidence/t0-checklist.md`](./t0-evidence/t0-checklist.md) |
| Smoke results | [`t0-evidence/smoke-results.json`](./t0-evidence/smoke-results.json) |
| Playwright results | [`t0-evidence/workflow-results.json`](./t0-evidence/workflow-results.json) |
| Screenshots | [`../../product/batch1-ui-demo/`](../../product/batch1-ui-demo/) |
| P5 report | [`../../P5_IMPLEMENTATION_REPORT.md`](../../P5_IMPLEMENTATION_REPORT.md) |
| Gate 2 package | [`../gate2/`](../gate2/) |
