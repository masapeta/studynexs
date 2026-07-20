# Gate 1 — Demo Ready Execution

> **Business milestone:** Demo Ready (Gate 1) — split into **1A Demo Online** and **1B Demo Reliable**.  
> **Owner:** Avinash Reddy Masapeta (ARM). **Assessment:** 2026-07-15 pilot readiness review.  
> **Rule:** Complete **Batch 29 (Infrastructure Readiness)** before Gate 1A HTTPS deploy. No Batch 30 until Gate 1 **exit criteria** met.

---

## Two sub-milestones (different goals)

```
Gate 1A — Demo Online          "Click this link."
        ↓
Gate 1B — Demo Reliable        "The demo won't embarrass me."
        ↓
Gate 1 EXIT → First principal demo → Gate 2 (Pilot Ready)
```

| Sub-gate | Goal | Enough to… |
|----------|------|------------|
| **1A — Demo Online** | HTTPS URL, login, demo data, AI works, smokes pass | **Send someone a URL** |
| **1B — Demo Reliable** | Fallbacks, UX polish, timeout handling, teacher/parent flows, backup scenarios | **Run the demo with confidence** |

Do not conflate them. **1A is the deploy milestone.** **1B is the confidence milestone.**

---

## Demo Reliability Targets (measurable)

Track these during Gate 1B validation on the **HTTPS demo environment**:

| Metric | Target | How to verify |
|--------|--------|---------------|
| **AI success rate** | ≥ 95% | Smoke + 5 manual QP generations; ≤ 1 failure without acceptable fallback |
| **Page load (FCP)** | < 2 seconds | Browser devtools on dashboard + AI Papers (demo URL) |
| **QP generation** | < 20 seconds | Timed live generation or smoke log |
| **Fallback coverage** | 100% of critical AI paths | QP, report card, copilot ask — each has fallback or pre-approved backup |
| **Critical errors** | 0 | No boot failures, auth breaks, or tenant leaks on demo stack |
| **Smoke tests** | 100% | `smoke_demo_readiness.py` + `e2e-smoke.cjs` green against demo URL |

Record evidence in the Engineering Report ([`004-validation-and-testing.md`](../engineering/004-validation-and-testing.md) §14).

---

## Hard exit criteria (Gate 1 complete)

**Gate 1 is complete when ALL of the following are true — then STOP. Do not keep polishing.**

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | **HTTPS URL available** | Shareable link documented (not localhost) |
| 2 | **Smoke tests pass** | 100% on demo URL (API + E2E) |
| 3 | **Principal demo completed successfully** | Outcome sheet in `docs/pilot/<school>/` |
| 4 | **No critical issues found** | No Critical/Important failures per validation standard |

**After exit:** Move to **Gate 2 (Pilot Ready)** or reprioritize from demo feedback — **not** "one more improvement."

**Anti-pattern to avoid:**

```
Almost finished → one more thing → another improvement → three weeks pass
```

---

## Execution order

| Step | Sub-gate | Work | Status |
|------|----------|------|--------|
| 0 | — | **Batch 29** — Infrastructure Readiness (reserved hosts, runtime tenant, Dockerfile, deploy docs) | 🟡 in progress |
| 1 | — | Housekeeping — docs sync | ✅ |
| 2 | **1A** | HTTPS demo deploy | ⬜ blocked on credentials |
| 3 | **1A** | Configure production env vars | ⬜ |
| 4 | **1A** | Verify API connectivity | ⬜ |
| 5 | **1A** | Seed demo tenant | ⬜ |
| 6 | **1A** | Execute smoke tests on demo URL | ⬜ |
| 7 | **1A** | **Demo Online complete** — URL sendable | ⬜ |
| 8 | **1B** | AI Reliability (key, QP fallback, timeout, pre-approved backup) | 🟡 partial |
| 9 | **1B** | CurriculumPack for demo (syllabus moat) | ⬜ |
| 10 | **1B** | Demo experience (runbook, labels, teacher + parent E2E) | ⬜ |
| 11 | **1B** | Hit Demo Reliability Targets | ⬜ |
| 12 | **EXIT** | First principal demo + outcome sheet | ⬜ |

**Batch 30 deferred** until Gate 1 exit or ARM explicitly reprioritizes.

---

## Gate 1A — Demo Online

**Success means:** ✅ HTTPS · ✅ Login · ✅ Demo data · ✅ AI works · ✅ Smoke tests

### Deployment checklist

**Web (Cloudflare / OpenNext)**

- [ ] Set `NEXT_PUBLIC_API_URL` to public API origin at build time
- [ ] `npm run cf:build` then `npm run cf:deploy`
- [ ] Login, dashboard, AI Papers load over HTTPS
- [ ] CORS + cookies configured for demo origin

**API (Azure Container Apps or equivalent)**

- [ ] Postgres, Redis, Qdrant reachable from API host
- [ ] Production env: JWT secret, AI keys, encryption keys, non-localhost CORS
- [ ] Migrations applied on demo database
- [ ] `seed_demo_e2e_journey.py` on demo DB (synthetic data only)

**Validation**

- [ ] `smoke_demo_readiness.py` against public API URL — 25/25
- [ ] `e2e-smoke.cjs` against demo web URL — green
- [ ] Document URL + demo logins in operator runbook (no secrets in git)
- [ ] Close BACKLOG G1-07 / DEMO-02

**References:** `apps/admin-web/wrangler.jsonc`, `package.json` (`cf:deploy`), `infra/azure/`, `TRACK_AB_EXECUTION.md` A1.

---

## Gate 1B — Demo Reliable

**Success means:** graceful fallbacks · better UX · polished flows · timeout handling · teacher/parent flows · backup scenarios · **Reliability Targets met**

### AI Reliability (one batch — not endless fallbacks)

- [ ] ARM-owned `GEMINI_API_KEY` in demo env (G1-09)
- [ ] QP fallback on LLM failure (dev/test stub ✅; production = pre-approved backup)
- [ ] Pre-approve one Class 10 Maths QP before live meetings
- [ ] Timeout messaging in UI if generation > 20s
- [ ] Verify report card stub path on demo stack

### CurriculumPack for demo

- [ ] Approved Class 10 Maths pack in demo seed
- [ ] RAG index on demo stack
- [ ] Grounded QP + copilots cite syllabus context

### Demo experience

- [ ] `DEMO_RUNBOOK.md` (from `HANDS_ON_RUNBOOK.md`)
- [ ] G1-05 one-pager (privacy, consent, "not live yet")
- [ ] G1-04 preview badges on incomplete modules
- [ ] E2E: teacher QP path, parent child + Parent Copilot
- [ ] Pre-meeting smoke within 30 minutes of demo

---

## Resume after deployment credentials (ARM)

When cloud credentials are available, resume from **Step 2 (Gate 1A)**:

1. Deploy HTTPS demo
2. Configure production environment variables
3. Verify API connectivity
4. Seed demo tenant
5. Execute smoke tests
6. Record validation evidence
7. Update Gate 1 documentation
8. Produce Engineering Report

**Do not:** start new features · start Batch 30 · create new foundational architecture docs · perform git operations without ARM approval.

---

## Freeze + commit policy (ARM 2026-07-15)

Architecture is **frozen after reality confirms it**, not before.

```
Batch 29 (code + docs draft)     ← implemented locally
        ↓
Gate 1A — HTTPS live             ← Oracle + Cloudflare + smokes
        ↓
Validate against live stack        ← demo.studynexs.com, api.studynexs.com
        ↓
Freeze all architecture docs as **v1.0 (Frozen)** — headers per [`DEPLOYMENT_CONVENTIONS.md`](../DEPLOYMENT_CONVENTIONS.md) §12 · mark Batch 29 complete
        ↓
Commit (two commits — ARM-approved order):
  1. feat(platform): implement infrastructure readiness (Batch 29)
  2. docs(platform): add deployment, platform and URL architecture
        ↓
Gate 1B → principal demo → pilot
```

**Do not commit** Batch 29 until Gate 1A validation passes and deployment doc is frozen.

Future architecture doc: `SECURITY_ARCHITECTURE.md` — **after** Gate 1, not now.

---

## Explicitly out of Gate 1

Azure Blob, async Arq workers, consent product, malware scan, real PII, Batch 30 analytics.

See [`BACKLOG.md`](../BACKLOG.md) three-gates rule.
