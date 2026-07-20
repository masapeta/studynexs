# StudyNexs Architecture Constitution

**Version:** 1.0  
**Status:** Active (frozen)  
**Owner:** Avinash Reddy Masapeta  
**Effective:** Product Execution Phase (2026-07-17)

> **Answers:** *What are we building?*  
> **Operational detail:** [`PLATFORM_ARCHITECTURE.md`](../PLATFORM_ARCHITECTURE.md), [`DEPLOYMENT_ARCHITECTURE.md`](../DEPLOYMENT_ARCHITECTURE.md), [`/CLAUDE.md`](../../CLAUDE.md) Parts I–VIII

---

## Vision

StudyNexs is the **AI-native operating system for schools** — India-first, subscription to schools and parents, human-in-the-loop for all authoritative output.

Schools run on trust. The platform exists so teachers, principals, parents, and students get **consistent, grounded, tenant-safe** educational capabilities — not generic SaaS with AI bolted on.

---

## Product identity

| Attribute | Definition |
|-----------|------------|
| **Product** | StudyNexs (Noustriks) |
| **Buyer** | Schools; parents where applicable |
| **Core promise** | One platform for operations + intelligence, grounded in each school's approved curriculum |
| **AI stance** | Assists; humans decide. Metered, credit-checked, gateway-routed |
| **Content stance** | Content is data — no hardcoded board/syllabus assumptions in code |

---

## Platform architecture (summary)

| Layer | Description |
|-------|-------------|
| **Modular monolith** | FastAPI (`apps/api`) — domain modules with endpoints/services/schemas/jobs |
| **Web** | Next.js 16 admin + portals (`apps/admin-web`) |
| **Data** | Postgres 16 (source of truth), Redis, Qdrant (RAG) |
| **AI platform** | Provider-agnostic gateway, RAG engine, embeddings, credits/metering |
| **Company DNA** | Per-tenant School Config + **CurriculumPack** + Knowledge Graph |

Full diagram: [`PLATFORM_ARCHITECTURE.md`](../PLATFORM_ARCHITECTURE.md)

---

## Multi-tenancy (non-negotiable)

- Every query scoped by `school_id` derived from authenticated `CurrentUser`.
- Never trust client-supplied `school_id`.
- Cross-tenant access is **Sev-1**.

---

## Domain boundaries

| Domain | Responsibility |
|--------|----------------|
| **School operations** | Fees, attendance, exams, admissions, staff |
| **Curriculum intelligence** | CurriculumPack, ingestion, RAG, knowledge graph |
| **Assessment intelligence** | Papers, evaluation, grading (grounded in curriculum) |
| **Copilots** | Teacher, parent, student — human-in-the-loop |
| **AI gateway** | All LLM calls — metered, swappable providers |

Modules live under `apps/api/app/modules/`. Do not create cross-module circular dependencies.

---

## Runtime philosophy

- **Async where it matters** — long AI jobs via Arq workers
- **API stability** — `/api/v1` additive only; breaking changes need v2 + deprecation
- **Money is exact** — `Decimal` end-to-end, idempotent, audited
- **Fail-secure** — production boot guardrails are not weakened for demos

---

## AI architecture

1. All LLM calls through **AI Gateway** (`apps/api/app/modules/ai/gateway`).
2. Retrieval grounded in **tenant-approved CurriculumPack** where applicable.
3. Authoritative outputs (papers, grades, report cards) require **human approval**.
4. Cost-aware — credit check at generation time.

---

## Security principles

- Parameterized queries only; authz on every protected route.
- No secrets in code; no PII in logs.
- DPDP compliance-first — minimize, protect, retain appropriately.
- Indian data residency where configured.

---

## Non-negotiable architectural rules

1. Tenant isolation is sacred.
2. Content is data (curriculum/board in DB, not code).
3. AI stays human-in-the-loop for authoritative output.
4. One unified ecosystem — shared contracts and design language across portals.
5. Platform changes only when implementation is **genuinely blocked** (see Product Execution Constitution).

---

## Governing references

| Document | Role |
|----------|------|
| [`../engineering/ENGINEERING_GOVERNANCE.md`](../engineering/ENGINEERING_GOVERNANCE.md) | How we build |
| [`../design/PLATFORM_DESIGN_SYSTEM_V1.md`](../design/PLATFORM_DESIGN_SYSTEM_V1.md) | How it feels |
| [`../product/PRODUCT_EXECUTION_CONSTITUTION.md`](../product/PRODUCT_EXECUTION_CONSTITUTION.md) | How effort is prioritized |
| [`../decisions/DECISION_LOG.md`](../decisions/DECISION_LOG.md) | Why decisions were made |

---

## Amendment

Changes to this document require explicit product-owner approval. Architecture changes are rare in the Product Execution Phase.
