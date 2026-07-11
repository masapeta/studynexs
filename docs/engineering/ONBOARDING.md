# Engineering Onboarding

> **Entry point** for humans and AI assistants joining StudyNexs engineering work.

---

## When to use each document

| Document | Purpose |
|----------|---------|
| [`AI_DISCOVERY_PROMPT.md`](../AI_DISCOVERY_PROMPT.md) | Onboard an AI assistant and assess repository state (read-only discovery) |
| [`AI_DEVELOPMENT_PROMPT.md`](../AI_DEVELOPMENT_PROMPT.md) | Continue autonomous engineering work after discovery is approved |
| [`/CLAUDE.md`](../../CLAUDE.md) | Engineering constitution, architecture, and standards |
| [`DEVELOPMENT_LIFECYCLE.md`](./DEVELOPMENT_LIFECYCLE.md) | End-to-end engineering workflow |
| [`PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) | Current verified engineering status |

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
| **2.0** | Changes to the engineering process itself (e.g. code review gates, multi-team workflow, CI/CD approval stages) |

Revise prompts when real sessions surface a gap — not preemptively.

---

## Related

- [`002-git-workflow.md`](./002-git-workflow.md) — when Git operations are allowed
- [`003-engineering-dashboard.md`](./003-engineering-dashboard.md) — what to update after a batch
- [`testing-guidelines.md`](./testing-guidelines.md) — validation expectations
