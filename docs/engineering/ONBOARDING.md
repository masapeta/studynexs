# Engineering Onboarding

> **Entry point** for humans and AI assistants joining StudyNexs engineering work.

---

## Engineering Operating System

StudyNexs engineering docs form a layered **operating system** — not a loose collection of notes. Read top-down for authority; read horizontally within `docs/engineering/` for process.

```
CLAUDE.md                    → constitution (what must be true)
        ↓
001 Constitution pointer     → tooling entry to CLAUDE.md
        ↓
005 Development Lifecycle    → how work flows
        ↓
004 Validation Standard      → how work is verified
        ↓
003 Engineering Dashboard    → what status to update
        ↓
002 Git Workflow             → when git is allowed
        ↓
ONBOARDING.md                → this document
        ↓
AI Discovery Prompt          → read-only repository assessment
        ↓
AI Development Prompt        → autonomous implementation
```

Machine-readable state: `platform.json`, `modules.json`, `roadmap.json`. Human summary: [`PLATFORM_STATUS.md`](../PLATFORM_STATUS.md).

### What grows vs what stays stable

The operating system is valuable because it is **stable** — every new AI agent or engineer can rely on it without relearning the process every few weeks.

| Category | Policy |
|----------|--------|
| **Module documentation** (`docs/modules/`) | **Add and update** as StudyNexs grows — new pillars, new capabilities, verified state per module |
| **Architecture documentation** (`CLAUDE.md`, `docs/modules/`, decision logs when contracts change) | **Update when the platform evolves** — new contracts, providers, pillars, or material design shifts |
| **Engineering dashboard** (`PLATFORM_STATUS.md`, `platform.json`, `modules.json`, `roadmap.json`) | **Update every engineering batch** — reflects verified implementation |
| **Core standards** (`001`–`005`, AI prompts, this onboarding doc) | **Avoid changing** unless real engineering work proves something is missing — use 1.x clarifications only; reserve 2.0 for fundamental process change |

**Grow the map; don't rewrite the compass.**

Core standards change only when repeated sessions expose a genuine gap — not preemptively, not for stylistic preference, and not because a new agent "would do it differently."

---

## Documentation governance (ARM 2026-07-16)

### Standing instruction for every coding agent

**Before changing documentation, classify the work and update only the appropriate layer.**

1. Determine whether the change affects **Architecture**, **Execution**, or **Inventory**.
2. Update **only** the matching document(s).
3. **Do not duplicate** information across layers.
4. **Do not modify frozen architecture** without explicit ARM approval.

### Three documentation lifecycles

| Lifecycle | Documents | When it changes |
|-----------|-----------|-----------------|
| **Frozen (architecture)** | `URL_ARCHITECTURE.md`, `PLATFORM_ARCHITECTURE.md`, `DEPLOYMENT_ARCHITECTURE.md`, `DEPLOYMENT_CONVENTIONS.md` | Rarely — after Gate 1A freeze; Level 4 changes only with approval |
| **Living (execution)** | `GATE1_EXECUTION.md`, `ROADMAP.md`, `STATUS.md`, `AGENT_HANDOVER.md`, `PLATFORM_STATUS.md`, engineering dashboard JSON | Every sprint / batch |
| **Continuous (inventory)** | `infra/inventory/*` (SSH, VM, DNS, certs, backups) | Whenever infrastructure changes |

Architecture describes **design**. Execution tracks **current work**. Inventory records **what exists on which host**.

### Four change levels

| Level | Type | Examples | Action |
|-------|------|----------|--------|
| **1** | Bug | Wrong Docker command, incorrect env var, broken diagram | Fix immediately in the correct layer |
| **2** | Clarification | Better wording, missing example | Update the relevant doc only |
| **3** | Operational learning | OCI/Cloudflare/Docker discovery during Gate 1A | Update **Conventions** or **Inventory** — do not redesign architecture |
| **4** | Architecture | New tenant model, routing strategy, platform boundaries | **Explicit ARM approval** before any edit to frozen architecture docs |

Detail: [`DEPLOYMENT_CONVENTIONS.md`](../DEPLOYMENT_CONVENTIONS.md) §13 · inventory index: [`infra/inventory/README.md`](../../infra/inventory/README.md).

### Documentation Impact (every batch / PR)

Before closing work, run this three-question check:

| Question | If yes |
|----------|--------|
| **Architecture changed?** | Requires **explicit ARM approval** before editing frozen architecture docs (`URL`, `Platform`, `Deployment`, `Conventions`). |
| **Execution process changed?** | Update the relevant **living** doc (`GATE1_EXECUTION`, `ROADMAP`, `STATUS`, `HANDOVER`, `PLATFORM_STATUS`, dashboard JSON). |
| **Infrastructure changed?** | Update **`infra/inventory/`** (SSH, VM, DNS, backups, certs) — do not duplicate into architecture docs. |

If all three are **no**, update only module docs / changelog / handover as required by the batch — no architecture or inventory edits.

---

## When to use each document

| Document | Purpose |
|----------|---------|
| [`AI_DISCOVERY_PROMPT.md`](../AI_DISCOVERY_PROMPT.md) | Onboard an AI assistant and assess repository state (read-only discovery) |
| [`AI_DEVELOPMENT_PROMPT.md`](../AI_DEVELOPMENT_PROMPT.md) | Continue autonomous engineering work after discovery is approved |
| [`/CLAUDE.md`](../../CLAUDE.md) | Engineering constitution, architecture, and standards |
| [`005-development-lifecycle.md`](./005-development-lifecycle.md) | End-to-end engineering workflow |
| [`004-validation-and-testing.md`](./004-validation-and-testing.md) | Engineering Validation Standard — what must be verified |
| [`PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) | Current verified engineering status |
| [`DEPLOYMENT_CONVENTIONS.md`](../DEPLOYMENT_CONVENTIONS.md) | VM layout, change levels, doc freeze protocol |
| [`infra/inventory/README.md`](../../infra/inventory/README.md) | Operational inventory (SSH, DNS, VM — not architecture) |

### Numbered engineering standards

```
001-studynexs-constitution.md   → constitution pointer
002-git-workflow.md             → git approval gates
003-engineering-dashboard.md    → dashboard update policy
004-validation-and-testing.md   → verification standard
005-development-lifecycle.md    → end-to-end workflow
```

Supporting (unnumbered): this file, AI prompts, `platform.json`, `modules.json`, `roadmap.json`.

### Typical flow

```
AI Discovery Prompt
        │
        ▼
Repository Health Check
        │
        ▼
Read Engineering Documentation
        │
        ▼
Verify Against Implementation
        │
        ▼
Assess Engineering Readiness
        │
        ▼
Recommend Next Work
        │
        ▼
Product Owner Approval
        │
        ▼
AI Development Prompt → autonomous implementation
```

**New session:** start with **AI Discovery** (or the constitution checklist in [`001-studynexs-constitution.md`](./001-studynexs-constitution.md) for lightweight orienting).

**After discovery is approved:** switch to **AI Development** for implementation batches.

### Prompt symmetry

| Discovery | Development |
|-----------|-------------|
| Purpose | Purpose |
| Discovery Scope | Development Scope |
| Discovery Priority | Development Priority |
| Engineering Constraints | Engineering Constraints |
| Repository Health Check | Repository Health Check |
| Engineering Startup | Engineering Startup |
| Verification | Verification |
| Engineering Readiness | Engineering Readiness |
| Discovery report | Engineering report |
| Discovery Complete | Development Complete |

---

## AI prompt versioning

| Version | Meaning |
|---------|---------|
| **1.x** | Wording, clarity, or workflow improvements |
| **2.0** | Changes to the engineering process itself (e.g. code review gates, multi-team workflow, CI/CD approval stages, validation decision engine) |

Revise prompts when real sessions surface a gap — not preemptively. Validation standard versioning: [`004-validation-and-testing.md`](./004-validation-and-testing.md) Section 15.

---

## Related

- [`002-git-workflow.md`](./002-git-workflow.md) — when Git operations are allowed
- [`003-engineering-dashboard.md`](./003-engineering-dashboard.md) — what to update after a batch
- [`004-validation-and-testing.md`](./004-validation-and-testing.md) — validation levels, batch gates, definition of done
