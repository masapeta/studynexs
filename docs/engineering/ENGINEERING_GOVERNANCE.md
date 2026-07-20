# StudyNexs Engineering Governance

**Version:** 1.0  
**Status:** Active (frozen)  
**Owner:** Avinash Reddy Masapeta  
**Effective:** Product Execution Phase (2026-07-17)

> **Answers:** *How do we engineer it?*  
> **Full operational charter:** [`/CLAUDE.md`](../../CLAUDE.md) — remains the binding engineering handbook; this document is the **governance index** for the Product Execution Phase.

---

## Scope

Engineering Governance defines **how** software is built, reviewed, tested, and shipped. It does not define *what* batch is active (see Product Execution Plan) or *what* the system is (see Architecture Constitution).

---

## Prime directives (summary)

From [`/CLAUDE.md`](../../CLAUDE.md) — non-negotiable:

1. **Tenant isolation is sacred** — scope by `school_id` from `CurrentUser`.
2. **`/api/v1` is stable** — additive only.
3. **Security is not optional** — authz everywhere, no secrets in code.
4. **Money is exact** — `Decimal`, idempotent, audited.
5. **AI is human-in-the-loop** and **cost-aware** via gateway.
6. **Content is data** — no hardcoded curriculum/board assumptions.
7. **Preserve product, branding, UX** — Design System v1 is frozen.
8. **Incremental over rewrite** — smallest safe change.
9. **Validate** — build, lint, test before marking work done.

---

## Repository rules

| Area | Convention |
|------|------------|
| API | `apps/api` — modules: `endpoints/`, `services/`, `schemas/`, `jobs/` |
| Web | `apps/admin-web` — App Router, single `api()` client, `sn-*` design system |
| Infra | `infra/docker` — compose for local dev |
| Docs | Constitutional stack under `docs/` — see [`../README.md`](../README.md) |

Do not reorganize the repository without architectural justification.

---

## Git workflow

- Commit only when explicitly requested by ARM.
- Feature work follows active batch in Product Execution Plan.
- Decision Log entry for durable architectural/product decisions.

---

## Testing & quality gates

| Gate | Requirement |
|------|-------------|
| **Build** | No TS/Python build failures |
| **Lint** | Clean on touched files |
| **Tests** | Meaningful tests for logic changes; API tests for routes |
| **Tenant isolation** | Every new query scoped by `school_id` |
| **Review** | Per [`../reviews/REVIEW_STANDARDS.md`](../reviews/REVIEW_STANDARDS.md) |

Detailed playbooks: [`004-validation-and-testing.md`](./004-validation-and-testing.md), [`005-development-lifecycle.md`](./005-development-lifecycle.md)

---

## Documentation rules (Product Execution Phase)

**Update only what the governance model requires:**

| Change type | Update |
|-------------|--------|
| Batch progress | `PRODUCT_EXECUTION_PLAN.md` |
| Important decision | `decisions/DECISION_LOG.md` |
| Build/status truth | `STATUS.md`, `AGENT_HANDOVER.md` |
| Platform limitation discovered | Decision Log + Architecture amendment (rare) |
| UI capability (uses existing DS) | Feature docs only; **not** Design System expansion |

Do not expand governance documents without explicit approval.

---

## Review process

All significant work passes through review standards:

- **Code review** — correctness, tenant scope, security
- **Capability review** — batch acceptance criteria at completion
- **Visual review** — only when UI changes; use Design System v1 + review package standard for platform work

See [`../reviews/REVIEW_STANDARDS.md`](../reviews/REVIEW_STANDARDS.md).

---

## ADR process

Architectural decisions → [`../decisions/DECISION_LOG.md`](../decisions/DECISION_LOG.md) with date, decision, reason, alternatives, status.

---

## Versioning

- API: `/api/v1` stable; v2 only with ≥90-day deprecation.
- Product batches: sequential capability delivery, not semver on platform layers.

---

## Onboarding

New engineers read in order:

1. [`../README.md`](../README.md) — governance hierarchy
2. [`../architecture/ARCHITECTURE_CONSTITUTION.md`](../architecture/ARCHITECTURE_CONSTITUTION.md)
3. This document
4. [`../design/PLATFORM_DESIGN_SYSTEM_V1.md`](../design/PLATFORM_DESIGN_SYSTEM_V1.md)
5. [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md)
6. [`ONBOARDING.md`](./ONBOARDING.md)

---

## Governing references

| Document | Role |
|----------|------|
| [`/CLAUDE.md`](../../CLAUDE.md) | Full engineering constitution (operational superset) |
| [`../architecture/ARCHITECTURE_CONSTITUTION.md`](../architecture/ARCHITECTURE_CONSTITUTION.md) | What we build |
| [`../product/PRODUCT_EXECUTION_CONSTITUTION.md`](../product/PRODUCT_EXECUTION_CONSTITUTION.md) | Prioritization |
| [`../reviews/REVIEW_STANDARDS.md`](../reviews/REVIEW_STANDARDS.md) | Quality evaluation |
