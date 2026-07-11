# Development Lifecycle

> **Process document** — how engineering work flows through this repository.  
> **Not** architecture (`CLAUDE.md`, `docs/modules/`) and **not** git mechanics alone ([`002-git-workflow.md`](./002-git-workflow.md)).

| Doc | Answers |
|-----|---------|
| [`/CLAUDE.md`](../../CLAUDE.md) | **What** must be true — standards, architecture, prime directives |
| **This file** | **How** work is done — read → verify → plan → ship → document → review |
| [`003-engineering-dashboard.md`](./003-engineering-dashboard.md) | **What to update** when a batch completes |
| [`002-git-workflow.md`](./002-git-workflow.md) | **When** git operations are allowed |

---

## Source of truth

Documentation **summarizes** the platform. **Implementation is authoritative.**

If docs and code disagree: inspect code → run tests → update docs. Never ship or mark work complete based on docs alone.

---

## Lifecycle (every batch, feature, or fix)

```
Read docs
    ↓
Verify implementation
    ↓
Plan
    ↓
Implement
    ↓
Run tests
    ↓
Update documentation
    ↓
Review
    ↓
Wait for approval
    ↓
Commit
```

Each step is mandatory unless explicitly scoped out by the product owner.

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
- Run focused tests or `import app.main` for the area you will touch
- Check `git log` / working tree if resuming after a break

**Stop and update docs first** if you find drift between documentation and code.

See also: [`testing-guidelines.md`](./testing-guidelines.md).

---

## 3. Plan

Prefer the **smallest safe change** (`CLAUDE.md` — incremental over rewrite).

- Define scope: which batch, which files, which tests prove done
- Identify reuse: gateway, RAG, existing services — no duplicate AI paths
- Note product-owner decisions needed **before** coding (authz, money, breaking API)
- If scope is large, split into reviewable commits (logical units, not one monolith)

Do not start implementation while blocked on an owner decision — state the blocker and a recommended default.

---

## 4. Implement

- Match surrounding conventions (naming, layers, tenant scoping)
- Security: parameterized queries, authz on every protected route, no secrets in code
- AI: gateway only, metered, HITL for authoritative output
- UI: responsive, accessible, consistent with `sn-*` design system

Keep refactors separate from features when possible.

---

## 5. Run tests

Validation is not optional for significant changes.

```text
Build → Lint → Test → fix → repeat until clean
```

| Scope | Minimum |
|-------|---------|
| API logic | Focused `pytest` for touched modules |
| Cross-cutting / batch close | `pytest tests/` (full suite) |
| Admin UI | `npm run build` / lint on touched app |

Record results in `docs/engineering/platform.json` (`tests.passed`, `last_run`) when closing a batch.

Never claim verification you did not run.

---

## 6. Update documentation

After **verified** implementation, update docs so the next session starts informed.

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

---

## 7. Review

Before asking for commit approval, self-review:

- Tenant isolation on every new query path
- No merge conflict markers, debug prints, or accidental secrets
- Diff is focused — no unrelated drive-by changes
- Docs and JSON agree with code and test results
- HITL and metering preserved for AI features

Use [`testing-guidelines.md`](./testing-guidelines.md) closing checklist for the handover summary.

---

## 8. Wait for approval

**Prime Directive 9:** commit only when explicitly asked.

Git operations (commit, push, merge, branch switch) require owner approval. See [`002-git-workflow.md`](./002-git-workflow.md).

Provide in the handover:

- Files changed
- Tests executed and results
- New capabilities vs remaining work
- Recommended next milestone

---

## 9. Commit

After approval:

- Logical commit messages (why, not just what)
- Split unrelated work into separate commits when appropriate
- Do not push unless explicitly asked

---

## When to stop vs continue

**Continue autonomously** through steps 1–7 when progress is clear and guardrails are met.

**Stop and ask** when:

1. A product-owner decision is required
2. Credentials or secrets are missing
3. External systems are unavailable
4. Repository limitations block progress
5. A change could significantly impact business behavior

State what is done, what is blocked, why, and a recommended default.

---

## Related

- Constitution pointer: [`001-studynexs-constitution.md`](./001-studynexs-constitution.md)
- Cursor rule (dashboard updates): [`.cursor/rules/engineering-dashboard.mdc`](../../.cursor/rules/engineering-dashboard.mdc)
- In-app view: Dashboard → Platform → Engineering
