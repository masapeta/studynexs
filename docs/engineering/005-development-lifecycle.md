# Development Lifecycle

**Version:** 1.2  
**Last updated:** 2026-07-15  
**Applies to:** Cursor · Claude Code · ChatGPT-assisted reviews

> **Process document** — how engineering work flows through this repository.  
> **Not** architecture (`CLAUDE.md`, `docs/modules/`), **not** verification detail alone ([`004-validation-and-testing.md`](./004-validation-and-testing.md)), **not** git mechanics alone ([`002-git-workflow.md`](./002-git-workflow.md)).

| Doc | Answers |
|-----|---------|
| [`/CLAUDE.md`](../../CLAUDE.md) | **What** must be true — standards, architecture, prime directives |
| **This file** | **How** work is done — health check → read → verify → plan → implement → validate → document → review |
| [`004-validation-and-testing.md`](./004-validation-and-testing.md) | **What must be verified** — validation levels, batch gates, definition of done |
| [`003-engineering-dashboard.md`](./003-engineering-dashboard.md) | **What to update** when a batch completes |
| [`002-git-workflow.md`](./002-git-workflow.md) | **When** git operations are allowed |

---

## Source of truth

Documentation **summarizes** the platform. **Implementation is authoritative.**

If docs and code disagree: inspect code → run validation → update docs. Never ship or mark work complete based on docs alone.

---

## Lifecycle (every batch, feature, or fix)

```
Repository health check
    ↓
Read docs
    ↓
Verify implementation
    ↓
Plan
    ↓
Implement
    ↓
Validate (focused → batch scope)
    ↓
Update documentation
    ↓
Review
    ↓
Request Product Owner approval
    ↓
Commit
```

Each step is mandatory unless explicitly scoped out by the product owner.

---

## 0. Repository health check

Before reading documentation:

- Confirm you are in the **correct repository**
- Confirm the **current branch**
- Confirm **working tree status**
- Do **not** perform Git operations automatically
- Report any **unexpected local modifications**

This prevents working in the wrong repo, branch, or against unreviewed local changes.

---

## 1. Read docs

Orient before writing code.

| Read | Why |
|------|-----|
| [`/CLAUDE.md`](../../CLAUDE.md) | Non-negotiables, stack, quality bar |
| [`docs/PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) | Current platform state + capability matrix |
| [`docs/AGENT_HANDOVER.md`](../AGENT_HANDOVER.md) | Latest session, batch, blockers |
| [`docs/engineering/platform.json`](./platform.json) | Machine-readable status |
| [`docs/engineering/modules.json`](./modules.json) | Module deps + verification |
| [`docs/engineering/roadmap.json`](./roadmap.json) | Next milestone |
| Relevant [`docs/modules/`](../modules/) | Pillar/module you are touching |

**Goal:** Know what exists, what is verified, and what the next milestone is — without assuming docs are current.

---

## 2. Verify implementation

Confirm reality in the repo **before** planning new work.

- Does the feature already exist (fully or partially)?
- Can an existing module or service be extended?
- Run focused validation or smoke-check the area you will touch
- Check `git log` / working tree if resuming after a break

**Stop and update docs first** if you find drift between documentation and code.

See: [`004-validation-and-testing.md`](./004-validation-and-testing.md) — validation philosophy and levels.

---

## 3. Plan

Prefer the **smallest safe change** (`CLAUDE.md` — incremental over rewrite).

- Define scope: which batch, which files, which validation proves done
- Note product-owner decisions needed **before** coding (authz, money, breaking API)
- If scope is large, split into reviewable commits (logical units, not one monolith)

### Reuse check

Before creating any of the following, verify whether an equivalent already exists. **Prefer extending existing implementations.**

| Layer | Examples |
|-------|----------|
| API | service, endpoint, schema, model |
| Platform | provider, utility |
| Admin UI | React component |

Also reuse shared platform paths (gateway, RAG, existing services) — no duplicate AI or integration paths.

### Rollback thinking

For larger changes, ask before implementation:

- Can this change be **reverted cleanly**?
- Is it **isolated enough** for a focused commit?
- Will it be **easy to debug** if issues arise?

This is a design mindset, not a Git operation — but it leads to smaller, safer diffs.

Do not start implementation while blocked on an owner decision — state the blocker and a recommended default.

---

## 4. Implement

- Match surrounding conventions (naming, layers, tenant scoping)
- Security: parameterized queries, authz on every protected route, no secrets in code
- AI: gateway only, metered, HITL for authoritative output
- UI: responsive, accessible, consistent with `sn-*` design system

Keep refactors separate from features when possible.

---

## 5. Validate

Validation is not optional for significant changes. Full standard: [`004-validation-and-testing.md`](./004-validation-and-testing.md).

```text
Build → focused tests → fix → repeat during development
Batch close → broader regression + documentation validation
```

| Phase | Minimum |
|-------|---------|
| During development | Focused tests for touched modules; startup smoke where relevant |
| Batch close | Batch validation gates (Section 8 of validation standard); full suite when scope requires |
| Admin UI | Production build when frontend changed |

Record results in `docs/engineering/platform.json` (`tests.passed`, `last_run`) when closing a batch.

Never claim verification you did not run. Distinguish product regressions from environmental failures.

---

## 6. Update documentation

After **verified** implementation, run the **Documentation Impact** check ([`ONBOARDING.md`](./ONBOARDING.md) § Documentation governance):

1. **Architecture changed?** → requires ARM approval before frozen doc edits.
2. **Execution process changed?** → update living docs (below).
3. **Infrastructure changed?** → update `infra/inventory/` only.

Then update docs so the next session starts informed.

**Always (batch or significant feature):**

- [`docs/CHANGELOG.md`](../CHANGELOG.md)
- [`docs/STATUS.md`](../STATUS.md)
- [`docs/ROADMAP.md`](../ROADMAP.md)
- [`docs/AGENT_HANDOVER.md`](../AGENT_HANDOVER.md)

**Engineering dashboard:**

- [`docs/PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)
- [`docs/engineering/platform.json`](./platform.json)
- [`docs/engineering/modules.json`](./modules.json)
- [`docs/engineering/roadmap.json`](./roadmap.json)
- Affected [`docs/modules/*.md`](../modules/)

Set `verified` honestly: `tests_passing` only when tests exist and pass.

**Operating system policy:** grow module and architecture docs as the platform evolves; update the dashboard every batch; avoid changing core standards (`001`–`005`) unless real engineering work proves a gap. See [`ONBOARDING.md`](./ONBOARDING.md).

---

## 7. Review

Before asking for commit approval, self-review:

- Tenant isolation on every new query path
- No merge conflict markers, debug prints, or accidental secrets
- Diff is focused — no unrelated drive-by changes
- Docs and JSON agree with code and validation results
- HITL and metering preserved for AI features

Prepare the engineering report per [`004-validation-and-testing.md`](./004-validation-and-testing.md) Section 14.

---

## 8. Request Product Owner approval

**Prime Directive 9:** commit only when explicitly asked.

The workflow **pauses here** until approval is received. Git operations (commit, push, merge, branch switch) require owner approval. See [`002-git-workflow.md`](./002-git-workflow.md).

Provide the engineering report (scope, validation executed, results, capabilities, remaining work, next milestone).

---

## 9. Commit

After approval:

- Logical commit messages (why, not just what)
- Split unrelated work into separate commits when appropriate
- Do not push unless explicitly asked

---

## When to stop vs continue

**Continue autonomously** through steps 0–7 when progress is clear and guardrails are met.

**Stop and ask** when:

1. A product-owner decision is required
2. Credentials or secrets are missing
3. External systems are unavailable
4. Repository limitations block progress
5. A change could significantly impact business behavior

State what is done, what is blocked, why, and a recommended default.

---

## Definition of Done

A batch is complete when the criteria in [`004-validation-and-testing.md`](./004-validation-and-testing.md) Section 13 are satisfied — including verified implementation, evidence recorded, honest dashboard state, and product owner approval requested.

---

## Related

- Validation standard: [`004-validation-and-testing.md`](./004-validation-and-testing.md)
- Constitution pointer: [`001-studynexs-constitution.md`](./001-studynexs-constitution.md)
- Cursor rule (dashboard updates): [`.cursor/rules/engineering-dashboard.mdc`](../../.cursor/rules/engineering-dashboard.mdc)
- In-app view: Dashboard → Platform → Engineering
