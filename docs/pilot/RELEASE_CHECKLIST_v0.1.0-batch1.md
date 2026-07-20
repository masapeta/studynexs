# Release Checklist — v0.1.0-batch1

> **Repository:** `studynexs-dev` · **Branch:** `develop` (frozen)  
> **Tag:** `v0.1.0-batch1` — **prepared, not applied** (await PO approval)  
> **Validated:** 2026-07-20 (P6)

---

## Pre-release governance

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| G-1 | P5 operational validation approved | ✅ | `P5_IMPLEMENTATION_REPORT.md` |
| G-2 | P6 authorized (release governance only) | ✅ | PO authorization 2026-07-20 |
| G-3 | No feature/schema/architecture changes in P6 | ✅ | Verification + docs only |
| G-4 | `develop` frozen for Batch 1 RC | ✅ | Policy in `CANONICAL_REPOSITORY.md` |
| G-5 | `academix-platform` marked Reference Archive | ✅ | `REFERENCE_ARCHIVE.md` |
| G-6 | Git tag **not** created (await PO) | ✅ | STOP gate honored |

---

## Repository verification

| # | Check | Result | Notes |
|---|-------|--------|-------|
| R-1 | Canonical repo is `studynexs-dev` | ✅ | |
| R-2 | No runtime bind mounts to `academix-platform` | ✅ | `studynexs-dev/apps/api → /app` |
| R-3 | Single Alembic head | ✅ | `f4a5b6c7d8e9` |
| R-4 | DB migrations at head | ✅ | Container: `f4a5b6c7d8e9 (head)` |
| R-5 | No pending migrations | ✅ | `alembic heads` shows one head |
| R-6 | Working tree clean | ⚠️ | **107 uncommitted files** — Batch 1 RC commit required before tag |

---

## Build verification

| # | Check | Command / method | Result |
|---|-------|------------------|--------|
| B-1 | API Docker image build | `docker compose build api` | ✅ Success |
| B-2 | Admin production build | `npm run build` (admin-web) | ✅ Success |
| B-3 | Docker compose stack | `docker compose ps` | ✅ All core services healthy |

---

## Runtime verification

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| V-1 | API `/health` | ✅ 200 | Smoke |
| V-2 | API `/ready` | ✅ 200 | Smoke |
| V-3 | Smoke readiness | ✅ **12 / 12** | `t0-evidence/smoke-results.json` |
| V-4 | Playwright workflow | ✅ **11 / 11** | `batch1-ui-demo/workflow-results.json` |
| V-5 | Batch 1 API tests | ✅ **37 passed** | P6 re-run |
| V-6 | Cross-tenant isolation | ✅ 403 | Smoke |
| V-7 | Approval pipeline | ✅ | Smoke + Playwright step 8 |
| V-8 | Grounding facade | ✅ | Smoke + Playwright steps 10–11 |

---

## Documentation deliverables

| # | Artifact | Status |
|---|----------|--------|
| D-1 | `RELEASE_NOTES_v0.1.0-batch1.md` | ✅ |
| D-2 | `BATCH1_BASELINE_CERTIFICATE.md` | ✅ |
| D-3 | `P6_IMPLEMENTATION_REPORT.md` | ✅ |
| D-4 | Gate 2 package (`docs/pilot/gate2/`) | ✅ |
| D-5 | T-0 evidence bundle | ✅ |

---

## Tag application (blocked — await PO)

| Step | Action | Status |
|------|--------|--------|
| T-1 | Commit Batch 1 RC artifacts (107 pending files) | ⏳ PO / eng decision |
| T-2 | PO approves tag creation | ⏳ Pending |
| T-3 | `git tag -a v0.1.0-batch1 -m "..."` on RC commit | ⏳ **Do not execute** |
| T-4 | Announce Gate 2 GO | ⏳ Pending |
| T-5 | Begin pilot rollout | ⏳ Pending |

---

## Sign-off

| Role | Decision | Date |
|------|----------|------|
| Engineering (P6) | Release candidate **prepared** — tag blocked on clean RC commit + PO approval | 2026-07-20 |
| Product Owner | | Pending |
