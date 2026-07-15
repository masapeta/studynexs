# Engineering Validation Standard

**Version:** 1.3  
**Last updated:** 2026-07-15  
**Applies to:** All engineering work — human and AI-assisted

**Document versioning:** **1.x** — minor clarifications (wording, typos, links, cross-references; no new sections). **2.0** — fundamental process change only (see Section 16).

> **Verification document** — how engineering work is proven ready before it is considered complete.  
> **Not** architecture ([`/CLAUDE.md`](../../CLAUDE.md)), **not** workflow alone ([`005-development-lifecycle.md`](./005-development-lifecycle.md)), **not** git mechanics ([`002-git-workflow.md`](./002-git-workflow.md)), **not** dashboard fields ([`003-engineering-dashboard.md`](./003-engineering-dashboard.md)), **not** coding standards ([`/CLAUDE.md`](../../CLAUDE.md)).

| Doc | Answers |
|-----|---------|
| **This file** | **What must be verified** — validation scope, decision matrix, levels, evidence, batch gates, definition of done |
| [`005-development-lifecycle.md`](./005-development-lifecycle.md) | **How work flows** — read → verify → plan → implement → validate → document → review → approve |
| [`003-engineering-dashboard.md`](./003-engineering-dashboard.md) | **What to update** in status docs and JSON after verified work |
| [`002-git-workflow.md`](./002-git-workflow.md) | **When** git operations are allowed |

---

## 1. Purpose

**Testing** asks: *Did the code work?*

**Validation** asks: *Is this engineering work ready?*

Validation is broader than tests. It confirms we built the right thing, did not break what already worked, can describe release readiness honestly, and that the engineering dashboard matches verified reality.

| Testing | Validation |
|---------|------------|
| Asserts behavior of a unit, module, or route | Asserts readiness of an engineering change or batch |
| Produces pass/fail for specific cases | Produces evidence for documentation, review, and release judgment |
| Can be automated | Combines automated checks, manual verification, and documentation alignment |
| Answers “does this work?” | Answers “did we build the right thing?”, “did we break anything?”, “can we safely release?”, “does the dashboard match reality?” |

No engineering batch is complete on tests alone. Validation is the full gate.

---

## 2. Validation Philosophy

1. **Implementation is the source of truth.** Code, runtime behavior, and executed checks override documentation.
2. **Documentation must reflect verified implementation.** Update status docs only after checks have actually run.
3. **Never claim verification that has not been executed.** Do not record `tests_passing`, `build_passing`, or similar unless the corresponding check succeeded in the current session or a clearly cited run.
4. **Honest partial verification is acceptable.** Report what was run, what passed, what was skipped, and why — especially when environment limits apply.
5. **Validation serves release judgment.** The goal is safe, incremental delivery — not maximum test count.
6. **Validation is evidence-based.** Summarize what was observed — not merely that checks “succeeded.”

If documentation and implementation disagree: inspect code → run focused validation → update docs. Never mark work complete from docs alone.

---

## 3. Verification Principles

Validation should proceed from the **smallest scope to the largest**. Fail fast — do not perform expensive validation when earlier stages have already identified blocking failures.

**Typical order:**

1. **Static verification** — imports resolve, types check, obvious syntax or lint blockers
2. **Focused tests** — module or feature tests for the area changed
3. **Integration tests** — routes, services, persistence, auth, tenant scoping together
4. **Application startup** — API (and worker if applicable) boots without errors
5. **UI build** — production build when frontend changed
6. **Full regression suite** — when engineering scope requires it (see Section 4)
7. **Documentation validation** — dashboard and docs match verified implementation

Stop at the first **Critical** or **Important** failure. Fix or classify before advancing to the next stage.

This order saves engineering time: focused validation during iteration; broader regression only at batch boundaries or when scope demands it.

---

## 4. Validation Scope

Choose validation depth by **engineering scope** — how much of the platform the change touches. This complements validation **levels** (Section 5), which describe *what kind* of check to run.

| Scope | Examples | Minimum validation |
|-------|----------|-------------------|
| **Minor fix** | Typo, copy, isolated bug in one module, docs-only correction with no behavior change | Static verification + focused tests for affected module |
| **Medium feature** | New endpoint, new UI panel, single-module service change | Focused tests + integration tests + startup; UI build if frontend touched |
| **Large batch** | Multi-module feature, new copilot surface, cross-portal work | Focused + integration + regression in batch domain + UI build + documentation validation; full suite when batch is cross-cutting |
| **Platform change** | Auth, middleware, shared models, database migrations, core dependencies | **Platform Change Validation** — startup, targeted integration, full regression suite, security review for affected surfaces, documentation validation |

When scope is unclear, validate at the **higher** scope until evidence shows the lower scope is sufficient.

### Validation Decision Matrix

Use this table to choose validation by **change type**. When a change spans multiple rows, apply the **union** of all required validation. Follow **Verification Principles** (Section 3) — smallest scope first, fail fast.

| Change | Required validation |
|--------|---------------------|
| **Documentation only** | Documentation validation |
| **API endpoint** | Focused tests + integration validation |
| **Shared service** | Integration validation + regression validation |
| **Middleware** | Platform Change Validation |
| **Database migration** | Platform Change Validation + full regression suite |
| **AI prompt / pipeline** | AI validation + focused tests |
| **RAG** | AI validation + integration validation |
| **UI only** | UI build + UI validation |

**Platform Change Validation** is the named validation tier for platform-scope changes (see scope table above): startup, integration, security review for affected surfaces, full suite when applicable, documentation validation.

> **Future (2.0): Validation Decision Engine** — A structured if/then flow (change type → required checks → commands) for autonomous agents. Not required in 1.x; this matrix is the manual decision standard until then.

---

## 5. Validation Levels

Each level addresses a different risk. Apply the levels relevant to the change — not every level on every edit. Match depth to **scope** (Section 4) and **verification order** (Section 3).

| Level | What it verifies | When required |
|-------|------------------|---------------|
| **Unit validation** | Isolated logic, schemas, pure functions, service methods with mocked dependencies | Any new or changed business logic |
| **Integration validation** | Modules working together — database, auth, tenant scoping, service orchestration | New or changed API routes, services touching persistence or cross-module calls |
| **End-to-end validation** | Critical user flows across UI and API | Portal features, multi-step workflows, auth boundaries |
| **Regression validation** | Existing behavior still works | Batch close, refactors, shared infrastructure changes |
| **Performance validation** | Latency, load, or resource use within acceptable bounds | Hot paths, bulk operations, new background jobs, UI lists at scale |
| **Security validation** | Authn/authz, input handling, tenant isolation, secrets hygiene | Every protected route, PII/financial/AI surface |
| **AI validation** | Grounding, metering, HITL, prompt safety, hallucination controls | Any LLM-backed feature or change to AI pipeline |
| **UI validation** | Build, layout, responsiveness, accessibility, empty/error/loading states | Any user-facing UI change |
| **Documentation validation** | Dashboard, module docs, changelog, and JSON agree with verified implementation | Every engineering batch and any significant feature |
| **Platform Change Validation** | Startup, integration, security review, full regression suite, documentation — for auth, middleware, shared models, migrations, core dependencies | Platform-scope changes (Section 4); middleware and database migrations (Decision Matrix) |

**Minimum during development:** unit + integration (as applicable) for the area touched.

**Minimum at batch close:** regression scope for the batch domain, UI build when frontend changed, documentation validation, dashboard updates.

---

## 6. Validation Evidence

Engineering validation should be **evidence-based**. Reports and handovers must summarize observable evidence — not merely assert that validation succeeded.

**Examples of evidence:**

| Evidence type | What to capture |
|---------------|-----------------|
| **Test output** | Command run, pass/fail/skip/error counts, test file or suite name |
| **Build logs** | Build command, success or failure, relevant error excerpt if failed |
| **Application startup logs** | Import/boot confirmation or failure message |
| **API responses** | Status code, key fields verified (not full PII payloads) |
| **Screenshots** | UI states when automation does not cover the flow |
| **Performance metrics** | Latency or resource numbers when performance validation applies |

**Do not write “verified” without stating what was run and what the outcome was.**

Example (acceptable):

> Ran `pytest tests/test_parent_copilot.py -q` — 3 passed in 20s.  
> Ran `npm run build` in `apps/admin-web` — exit 0.

Example (not acceptable):

> All tests pass. Build verified.

---

## 7. Revalidation

Validation is **point-in-time**. If implementation changes after validation has completed, previous results are **stale**.

**Rule:** Rerun validation appropriate to the **affected scope** before considering the batch complete or requesting commit approval.

| Change after validation | Revalidation required |
|-------------------------|----------------------|
| Bug fix in same module | Focused tests for that module (minimum) |
| Change to shared service, model, or middleware | Integration tests + regression scope for dependents |
| Fix prompted by full-suite failure | Re-run the failing test(s); expand scope if fix touched shared code |
| Documentation-only edit | Documentation validation only — if docs claim test results, those results must still be current |

Typical failure mode to avoid:

```
Tests pass → developer fixes one bug → does not rerun tests → commits
```

Treat stale validation as **incomplete validation**.

---

## 8. Batch Validation

An **engineering batch** is complete only when all applicable items below are verified.

### Required verification

| Gate | Requirement |
|------|-------------|
| **Relevant tests** | Focused tests for touched modules pass; full suite at batch close when scope is large batch or Platform Change Validation |
| **Application startup** | API (and worker if applicable) starts without import or boot errors |
| **API verification** | New or changed endpoints behave as specified; authz and tenant scoping confirmed |
| **UI build** | Frontend production build passes when admin-web or portal UI changed |
| **Regression checks** | No new failures in adjacent modules; existing tests for shared paths still pass |
| **Documentation updated** | `CHANGELOG.md`, `STATUS.md`, `ROADMAP.md`, `AGENT_HANDOVER.md`, `PLATFORM_STATUS.md`, `platform.json`, `modules.json`, `roadmap.json`, affected `docs/modules/*.md` — per [`003-engineering-dashboard.md`](./003-engineering-dashboard.md) |

### Batch close checklist (summary)

```
Verification principles (smallest → largest; fail fast)
    ↓
Scope-appropriate validation
    ↓
Evidence recorded
    ↓
Documentation + dashboard aligned with evidence
    ↓
Engineering report prepared
    ↓
Product Owner approval requested
    ↓
Commit (only after explicit approval)
```

Detailed workflow: [`005-development-lifecycle.md`](./005-development-lifecycle.md).

---

## 9. Test Strategy

Tests are one validation tool — not the whole standard. This section complements **Verification Principles** (Section 3): same philosophy, applied to automated tests specifically.

### Focused tests (default during development)

Run tests scoped to what you changed:

- Module or feature test file(s)
- Related integration tests for the same API surface
- Fast feedback loop after each meaningful change

**Use focused tests** after most edits, while iterating, and when fixing a specific failure.

### Full test suite (batch close and high-risk changes)

Run the complete automated suite when:

- Closing an engineering batch at **large batch** or **Platform Change Validation** scope
- Touching shared infrastructure (database models, auth, middleware, core dependencies)
- Changing behavior used by many modules
- Preparing commit approval for cross-cutting work

**Do not** run the entire suite after every small change. Reserve it for boundaries where regression risk is real.

### Progression (not “always full suite”)

```
Focused
    ↓
Batch-scope integration + regression
    ↓
Full suite (when scope requires)
```

Record commands, counts, and outcomes as **evidence** (Section 6) in the engineering report.

---

## 10. Environmental Failures

Not every red test is a product regression. Classify the failure before fixing or blocking a batch.

### Product regression

- Reproducible failure in a **single, clean** test run
- Caused by a change in application code, configuration, or intentional contract change
- **Response:** fix the product or update tests if the contract change was approved

### Infrastructure failure

- Database, cache, message broker, or external service unavailable or misconfigured
- **Response:** restore infrastructure or document blocker; do not mark batch complete

### Test environment issue

Examples:

- Shared database contention from concurrent test runners
- Schema or enum creation races when multiple processes initialize the same test database
- Stale or partial test database state after interrupted runs
- Missing local services required by integration tests

**Response:** re-run in isolation; reset or isolate test environment; report as environmental if reproducible only under contention. **Do not** treat flaky environment failures as product regressions without a clean repro.

### External service outage

- Third-party API, embedding provider, or LLM unavailable in dev/test
- **Response:** use stubs/mocks where the suite supports them; document outage; defer full AI validation if blocked

When reporting results, state whether failures are **product**, **infrastructure**, or **environmental**.

---

## 11. Failure Classification

Use consistent severity so review and release decisions are clear.

| Class | Meaning | Engineering response |
|-------|---------|----------------------|
| **Critical** | Blocks release or violates prime directives — tenant leak, auth bypass, data loss, financial incorrectness, secrets exposure, boot failure, broken protected route | Stop batch close; fix before approval; no commit |
| **Important** | Incorrect behavior, missing authz on non-critical path, failing tests in batch scope, UI build failure, dashboard/doc mismatch with implementation | Fix before batch complete; may defer only with explicit owner acceptance |
| **Informational** | Style, non-blocking lint, minor UX polish, deferred performance tuning, environmental flake without clean repro | Track in backlog; do not block batch if scope is otherwise verified |

**Critical** failures override all other progress. **Important** failures block “complete” status until resolved or explicitly waived by the product owner. **Informational** items are recorded but do not falsify verification claims.

---

## 12. AI Feature Validation

AI features require validation beyond ordinary API tests.

| Requirement | Verify |
|-------------|--------|
| **AI responses** | Output shape, error handling, and fallback when provider fails |
| **Hallucination protection** | No authoritative claims without grounding source; safe refusal when context insufficient |
| **Grounding** | Responses cite or derive from approved curriculum, mastery, graph, or retrieved context — not model parametric knowledge alone |
| **Human-in-the-loop** | Authoritative outputs (papers, grades, report cards, promoted content) require explicit human approval |
| **Credit metering** | Every generation path charges credits through the gateway; no bypass |
| **Security** | Authz on routes; tenant scoping; no PII in logs; prompts minimize sensitive data |
| **Prompt safety** | Injection-resistant patterns; user input bounded; no instruction leakage to end users |

Mock or stub LLM providers in automated tests where possible. Record when live-provider validation was or was not performed.

Policy detail: [`/CLAUDE.md`](../../CLAUDE.md) — AI prime directives.

---

## 13. Definition of Done

An engineering batch is **done** when all of the following are true:

1. **Scope** — Implementation matches the approved batch scope (no silent scope creep without note).
2. **Validation** — Scope-appropriate checks (Sections 3–5) executed; **evidence** recorded (Section 6).
3. **Revalidation** — No stale validation after post-check code changes (Section 7).
4. **Regressions** — No unresolved **Critical** or **Important** product failures in batch scope.
5. **Startup & build** — Application starts; UI build passes if frontend changed.
6. **Documentation** — Changelog, handover, module docs, and engineering JSON updated per dashboard policy.
7. **Dashboard truth** — `verified` fields and test counts match what was actually run.
8. **Review** — Self-review complete (tenant isolation, secrets, HITL, focused diff).
9. **Approval** — Engineering report delivered (Section 14); product owner approval requested for commit.
10. **Commit** — Only after explicit approval ([`002-git-workflow.md`](./002-git-workflow.md)).

“Done” is not “code written.” Done is **verified, evidenced, and documented readiness**.

---

## 14. Engineering Report

Before requesting commit approval, provide a structured handover. Summarize **evidence** — do not merely claim success.

| Item | Content |
|------|---------|
| **Batch / scope** | Batch number or change summary; validation scope tier (Section 4) |
| **Files changed** | Key paths (not necessarily every file) |
| **Validation executed** | Which stages ran, in order (Section 3) — static, focused, integration, startup, build, full suite |
| **Evidence** | Commands, pass/fail counts, build exit codes, startup confirmation — concrete outputs |
| **Results** | Summary judgment; environmental vs product failures called out |
| **New capabilities** | What is now verified working |
| **Known limitations** | What was not tested, environment constraints, flaky or skipped checks |
| **Deferred work** | Explicitly out of scope for this batch; backlog items |
| **Risk assessment** | Residual risk for release (e.g. cross-cutting change without full suite, external provider not exercised) |
| **Documentation updated** | `CHANGELOG.md`, `STATUS.md`, `ROADMAP.md`, `AGENT_HANDOVER.md`, `PLATFORM_STATUS.md`, `platform.json`, `modules.json`, `roadmap.json`, affected `docs/modules/*.md` |
| **Recommended next milestone** | From roadmap or reasoned proposal |
| **Commit recommendation** | Suggested split (e.g. API batch vs UI batch) if multiple logical units |

Wait for product owner approval before any git commit, push, or branch operation.

Handover detail may also live in [`docs/AGENT_HANDOVER.md`](../AGENT_HANDOVER.md).

---

## 15. Document Versioning

This document follows semantic versioning aligned with [`ONBOARDING.md`](./ONBOARDING.md) AI prompt versioning.

| Version | When to bump |
|---------|--------------|
| **1.x** | Minor clarifications only — wording, typos, broken links, cross-references. **No new sections.** |
| **2.0** | Fundamental process change only — for example: distributed validation, autonomous engineering, AI orchestration, validation decision engine, multiple repositories, release orchestration. |

Current version: **1.3**.

---

## 16. Related Documents

| Document | Role |
|----------|------|
| [`/CLAUDE.md`](../../CLAUDE.md) | Engineering constitution — standards, prime directives, stack |
| [`005-development-lifecycle.md`](./005-development-lifecycle.md) | End-to-end workflow — when validation fits in the engineering loop |
| [`docs/PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) | Master engineering dashboard summary |
| [`003-engineering-dashboard.md`](./003-engineering-dashboard.md) | What to update in dashboard and JSON after verified work |
| [`002-git-workflow.md`](./002-git-workflow.md) | Git approval gates |
| [`001-studynexs-constitution.md`](./001-studynexs-constitution.md) | Thin pointer to constitution for tooling |
| [`ONBOARDING.md`](./ONBOARDING.md) | Entry point and document map |
| [`docs/engineering/platform.json`](./platform.json) | Machine-readable test counts and capability matrix |

---

## Engineering folder map (numbered standards)

```
001-studynexs-constitution.md   → constitution pointer
002-git-workflow.md             → git approval gates
003-engineering-dashboard.md    → dashboard update policy
004-validation-and-testing.md   → this document — verification standard
005-development-lifecycle.md    → end-to-end workflow
```

Supporting (unnumbered): `ONBOARDING.md`, AI prompts, `platform.json`, `modules.json`, `roadmap.json`.
