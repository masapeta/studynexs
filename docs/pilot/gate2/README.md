# Gate 2 Pilot Package — Naagarjuna Talent School

> **Baseline:** `studynexs-dev` branch `develop` (Batch 1 reconciliation — P4 approved, P5 validated)  
> **Batch 1 status:** Frozen architecture — maintenance-only during pilot  
> **Pilot wedge:** Class 10 · Mathematics · Telangana SSC  
> **Tenant slug:** `naagarjuna`  
> **Primary success metric:** Gate 2 pilot completes with teacher confidence, stability, and actionable feedback

---

## Package index

| # | Document | Purpose |
|---|----------|---------|
| 1 | [GATE2_PREFLIGHT_CHECKLIST.md](./GATE2_PREFLIGHT_CHECKLIST.md) | Go/no-go checks before pilot day 1 |
| 2 | [GATE2_PILOT_EXECUTION_PLAN.md](./GATE2_PILOT_EXECUTION_PLAN.md) | Timeline, roles, cadence, scope boundaries |
| 3 | [GATE2_DEMO_SCRIPT.md](./GATE2_DEMO_SCRIPT.md) | HOD + Teacher live workflows (scripted) |
| 4 | [GATE2_ENVIRONMENT_VALIDATION.md](./GATE2_ENVIRONMENT_VALIDATION.md) | Infra, services, smoke tests, env vars |
| 5 | [GATE2_SUCCESS_CRITERIA.md](./GATE2_SUCCESS_CRITERIA.md) | Measurable exit conditions for Gate 2 |
| 6 | [GATE2_RISK_REGISTER.md](./GATE2_RISK_REGISTER.md) | Known risks, owners, mitigations |
| 7 | [GATE2_ROLLBACK_PLAN.md](./GATE2_ROLLBACK_PLAN.md) | How to stop safely and recover |
| 8 | [GATE2_DAILY_PILOT_LOG_TEMPLATE.md](./GATE2_DAILY_PILOT_LOG_TEMPLATE.md) | Daily operator log (copy per day) |
| 9 | [GATE2_FEEDBACK_COLLECTION_TEMPLATE.md](./GATE2_FEEDBACK_COLLECTION_TEMPLATE.md) | Structured feedback from HOD, teachers, ops |
| 10 | [GATE2_EXIT_REVIEW_TEMPLATE.md](./GATE2_EXIT_REVIEW_TEMPLATE.md) | End-of-pilot decision record |
| — | [PILOT_DECISIONS.md](./PILOT_DECISIONS.md) | Decision log (roadmap-shaping; not raw feedback) |
| — | [RELEASE_ENGINEERING_REVIEW.md](./RELEASE_ENGINEERING_REVIEW.md) | Release engineer review (recommendations only) |
| — | [GATE2_READINESS_AUDIT.md](./GATE2_READINESS_AUDIT.md) | Pre-pilot readiness audit |
| — | [GATE2_PILOT_SESSION_REPORT_TEMPLATE.md](./GATE2_PILOT_SESSION_REPORT_TEMPLATE.md) | After each live session |
| — | [GATE2_FINAL_REPORT.md](./GATE2_FINAL_REPORT.md) | Fill at pilot exit only |

---

## Reconciled architecture (frozen — do not change during pilot)

- `approve_pack()` — orchestration entry (KG spine + eager RAG + audit)
- `ground_approved_pack()` — **only** curriculum-governance entry for QP/LP
- Hybrid RAG — retrieval engine
- Knowledge Graph — concept graph
- Teacher Copilot — optional; template lesson plan is default

---

## P5 validation status (2026-07-20)

Engineering completed operational validation on `develop`. **Product Owner approval pending** — no tagging or release activities authorized.

| Criterion | Result |
|-----------|--------|
| Smoke 12/12 | ✅ |
| Playwright 11/11 | ✅ |
| Admin build | ✅ |
| API tests (37) | ✅ |
| Evidence bundle | ✅ |

See [`P5_IMPLEMENTATION_REPORT.md`](../../P5_IMPLEMENTATION_REPORT.md) and [`naagarjuna-talent-school/t0-evidence/`](../naagarjuna-talent-school/t0-evidence/).

---

## Quick start (operator)

```powershell
# 1. Canonical repo + branch
cd D:\Projects\studynexs-platform\studynexs-dev
git checkout develop

# 2. Start stack
docker compose -f infra/docker/docker-compose.dev.yml up -d

# 3. Seed tenant + curriculum (approve_pack pipeline)
cd apps\api
python scripts\seed_pilot_naagarjuna.py
python scripts\seed_pilot_naagarjuna_curriculum.py

# 4. Smoke (12 checks) — run from host for correct evidence paths
python scripts\smoke_pilot_readiness.py

# 5. Admin web (pilot tenant) — use .env.local
cd ..\admin-web
# NEXT_PUBLIC_TENANT_SLUG=naagarjuna
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev -- -p 3006

# 6. Playwright 11-step workflow
$env:E2E_BASE_URL="http://localhost:3006"
node scripts/batch1-ui-workflow-demo.cjs
```

**Evidence:** [`naagarjuna-talent-school/t0-evidence/`](../naagarjuna-talent-school/t0-evidence/) · [`batch1-ui-demo`](../../product/batch1-ui-demo/)

---

## Operating policy (Gate 2)

- **No Batch 2 implementation** during active pilot unless explicitly authorized.
- Fixes allowed: defects, deploy/env, docs, CI, tests, pilot UX bugs — **evidence before code**.
- P5 validation complete; **await PO approval** before Gate 2 GO declaration or release tagging.
