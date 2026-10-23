# Staging Integration & Operational Verification Checklist

Gating checklist for the GA decision on the Phase 9–11 assistant work (MCP Apps adapter, async
Question Paper generation, atomic job claim, stuck-job sweep + alerts). **Code is verified at
HEAD `32ddcc2`; this checklist gathers the integration and production-operational evidence that
code and unit tests cannot provide.**

Related runbooks: [production-operations.md](./production-operations.md) ·
[oracle-vm-production-deployment.md](./oracle-vm-production-deployment.md) ·
[rate-limits-and-waf.md](./rate-limits-and-waf.md)

## How to use this document

- Run each item **in staging** unless it explicitly requires production.
- Do **not** expose a public endpoint, deploy to production, change billing, or send external
  notifications without explicit written authorization (record the approver + ticket).
- Mark each item **VERIFIED / FAILED / BLOCKED** with: environment, config, exact command/procedure,
  observed result, timestamp, and where the evidence is stored.
- **Do not simulate** a missing capability. A simulation is not evidence — mark it BLOCKED.
- If an item reveals a genuine defect, stop, fix it in a focused commit, rerun the relevant
  regression tests, then resume from the failed item.

## Current status (local pre-work, 2026-10-23, HEAD `32ddcc2`)

| Item | Local status | What remains for staging |
|---|---|---|
| 1 MCP real-host | BLOCKED | needs a live MCP Apps host + reachable staging endpoint |
| 2 Worker/handler/cron | VERIFIED locally (real arq startup; handler+cron registered) | confirm in staging deployment |
| 3 Prometheus→Alertmanager | PARTIAL (source gauge + label match verified locally) | needs live Prometheus + Alertmanager |
| 4 Multi-process concurrency/recovery | VERIFIED locally (8-way real-Postgres race) | needs ≥2 deployed worker processes |
| 5 Deterministic + live-AI suites | deterministic green vs baseline; live-AI BLOCKED (OpenAI spend limit, edge-tts) | raise limit in a controlled live-integration run |

---

## 1. Real MCP Apps host smoke test

**Required environment:** staging API reachable by a compatible MCP Apps host (Claude / Claude
Desktop / VS Code Copilot / MCPJam). A short-lived tunnel to staging **or** a staging host already
on an allowed network. Never a production endpoint.

**Access & approvals:** authorization to expose the staging `/api/v1/mcp` endpoint to the chosen
host; a staging staff account (roles: teacher / class_incharge / admin / super_admin) with a known
school + a class that has attendance marked today; sign-off from the security owner before any
endpoint is made reachable.

**Execution procedure:**
1. Deploy HEAD `32ddcc2` to staging; confirm `/api/v1/mcp` requires auth (a tokenless
   `tools/list` returns 401).
2. Register staging as a custom connector in the host using the staging staff bearer token +
   `X-Tenant-Slug`.
3. In the host: confirm the connector consent prompt appears and is accepted by the user.
4. Trigger the tool so the host runs `tools/list` → `tools/call school_class_attendance_today`
   `{class_label:"<real class>"}` → `resources/read ui://studynexs/class-attendance.html`.
5. Confirm the MCP App renders (loading → metrics), click **Refresh**, confirm a fresh
   authenticated `tools/call` round-trip updates the view.
6. Negative paths: (a) call with another school's class → `not_found`, no cross-tenant data;
   (b) a non-staff account cannot reach the tool; (c) place a spoofed `school_id` in the tool
   arguments → result is still scoped to the authenticated user.
7. Fallback: in a host **without** MCP Apps support, confirm the tool still returns readable
   `content[].text`.

**Expected result:** consent enforced; identity server-derived; tenant/role scoping holds;
UI lifecycle + refresh work; spoofed identity ignored; text fallback usable.

**Evidence to capture:** host + version, staging commit SHA, timestamps, screen recording of the
UI lifecycle + refresh, raw JSON-RPC request/response for each call, the three negative-path
responses, server logs showing `mcp_tool_call` with the authenticated user/school.

**Rollback / cleanup:** remove the connector from the host; tear down the tunnel; revoke the
staging token; confirm `/api/v1/mcp` is no longer externally reachable.

## 2. Arq worker, Question Paper handler, and stuck-job cron verification

**Required environment:** staging with the API, an Arq worker process, Redis, and a migrated
Postgres (`alembic upgrade head`).

**Access & approvals:** staging shell/log access; permission to enqueue a staging QP job.

**Execution procedure:**
1. Start/confirm the worker: `arq app.core.jobs.worker.WorkerSettings`. Capture the startup line
   listing `run_job, sweep_expired_prospect_tenants, sweep_stuck_jobs` + the two crons, and the
   `job_handlers_registered handlers=[... 'question_paper_generate' ...]` line.
2. Enqueue a real QP generation from the assistant in staging; confirm the turn returns a
   `queued` workflow block with a `job_id`, and the worker drives the `Job` row
   `QUEUED → RUNNING → DONE` with `result.paper_id` set.
3. Confirm the generated paper exists as a `DRAFT` (approval lifecycle unchanged — do **not**
   approve/publish as part of this check).
4. Stuck-cron: confirm `cron:sweep_stuck_jobs` is scheduled (startup log) and that a seeded
   backdated QUEUED/RUNNING staging job is reported by a sweep run (`job_stuck` log +
   `studynexs_job_status_oldest_age_seconds` sample).

**Expected result:** handler registered; a real job completes end-to-end; the paper lands DRAFT;
the stuck cron is scheduled and flags backdated jobs.

**Evidence to capture:** worker startup log, the `Job` row lifecycle (id + status transitions +
timestamps), the `question_paper_generated` log, the DRAFT paper id, the `job_stuck` log line.

**Rollback / cleanup:** delete the test QP draft + its `Job` row; delete the seeded stuck job.
No approval/publish occurred, so no academic record changes.

## 3. Prometheus scrape, alert evaluation, Alertmanager routing, test-notification receipt

**Required environment:** staging Prometheus (loading `infra/observability/prometheus-alerts.yml`)
scraping the staging API `/metrics`, plus a staging Alertmanager routing to a **test** channel.

**Access & approvals:** observability-stack access; a **non-production, test-only** notification
destination; explicit approval before any notification is sent (no external/customer channels).

**Execution procedure:**
1. `promtool check rules infra/observability/prometheus-alerts.yml` → passes.
2. Confirm Prometheus loaded the rules (Status → Rules shows `StudyNexsQPJobStuckQueued` and
   `StudyNexsQPJobStuckRunning`).
3. Confirm the staging API `/metrics` is an UP scrape target and exposes
   `studynexs_job_status_oldest_age_seconds`.
4. Seed a staging QP `Job` backdated past the running threshold (>900s). Wait for the rule's
   `for:` window; confirm the alert goes `pending → firing` in Prometheus.
5. Confirm Alertmanager received it and **delivered a test notification** to the test channel.

**Expected result:** rules loaded; target UP; alert fires on the real gauge; notification received.

**Evidence to capture:** `promtool` output, Prometheus Rules + Targets screenshots, the firing
alert with labels, the Alertmanager notification log, the received test message (redacted).

**Rollback / cleanup:** delete the seeded stuck `Job`; confirm the alert resolves; remove the
test routing if it was added only for this check.

## 4. Multi-process concurrency, worker restart, recovery, single-charge invariant

**Required environment:** staging with **≥2 Arq worker processes** against the same Redis +
Postgres (this is what the local 8-coroutine race cannot prove).

**Access & approvals:** staging shell to run multiple workers + a controlled kill; a staging school
with AI credits.

**Execution procedure:**
1. Start two workers. Enqueue one QP job. Confirm exactly **one** worker claims it (atomic
   `QUEUED → RUNNING`); confirm exactly **one** `QuestionPaper` row and **one** AI-credit charge.
2. Duplicate-delivery: force re-delivery of the same job id (or submit twice concurrently from the
   assistant); confirm still **one** paper and **one** charge (`job_claim_skipped` on the losers).
3. Worker restart / recovery: kill the owning worker mid-generation; confirm the row does **not**
   stay RUNNING forever (stuck sweep flags it) and that recovery does **not** create a second paper
   or a second charge. Record whether a crashed-mid-run job requires manual requeue (document the
   operational expectation).
4. Single-charge audit: for every test job, assert one `ai_usage`/credit reservation per completed
   paper.

**Expected result:** one paper + one charge per logical request under concurrency, duplicate
delivery, and worker restart.

**Evidence to capture:** both worker logs (claim winner + `job_claim_skipped` losers), the `Job`
rows, the `QuestionPaper` count, the AI-credit ledger rows, the kill timestamp + post-restart state.

**Rollback / cleanup:** delete test papers + jobs; reverse any test credit reservations per the
credit-ledger procedure; stop the extra worker.

## 5. Deterministic regression suite + separate controlled live-integration suite

**Required environment:** CI/staging runner with migrated test DB + Redis.

**Access & approvals:** for the live-AI portion only — authorization to raise/lift the OpenAI
project spend limit for a bounded window, and a reachable edge-tts path; both run as a **separate,
controlled** suite, never mixed into the deterministic gate.

**Execution procedure:**
1. Deterministic: `pytest -q` with live-AI tests deselected → expect **0 failures** (the baseline's
   11 failures are exactly the live-AI set; deselecting them must yield green).
2. Frontend: `node --test apps/admin-web/tests/*.test.mjs` → green.
3. Live-integration (separate, authorized window): raise the OpenAI limit, run only the 10
   spend-limit-blocked tests + the edge-tts test; record pass/fail; restore the limit afterward.

**Expected result:** deterministic suite fully green; live-AI suite green within the authorized
window (or its failures attributed to a specific provider/env cause).

**Evidence to capture:** both suite summaries with counts, the exact deselect expression, the
authorized-window ticket for the live-AI run, before/after spend-limit state.

**Rollback / cleanup:** restore the OpenAI spend limit to its prior value; confirm no test data
persisted to shared stores.

---

## GA gate

GA remains **BLOCKED** until items 1, 3, 4 (staging), and the live-AI portion of 5 are **VERIFIED**
with the evidence above, and item 2 is re-confirmed in the staging deployment. No item may be
marked VERIFIED from a simulation or from code/unit-test evidence alone.
