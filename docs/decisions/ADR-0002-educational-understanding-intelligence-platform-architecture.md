# ADR-0002: Educational Understanding Intelligence Platform Architecture

- **Status:** Accepted
- **Date:** 2026-07-27
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Subsystem:** Educational Understanding Intelligence (EUI)
- **Related ADR:** [`ADR-0001-academic-evaluation-intelligence-architecture-freeze.md`](./ADR-0001-academic-evaluation-intelligence-architecture-freeze.md)

---

## Context

StudyNexs has completed a protected Academic Evaluation Intelligence (AEI) architecture and controlled runtime integration foundation.

AEI answers:

> How does StudyNexs evaluate answers safely, explainably, and under teacher authority?

The broader platform question is:

> How does StudyNexs understand education?

Evaluation is only one consumer of educational understanding. Curriculum intelligence, lesson planning, tutoring, question generation, parent communication, principal analytics, institutional memory, and school intelligence all require a shared educational understanding layer.

Without EUI, future capability expansion risks creating parallel understanding systems in each consumer.

---

## Decision

Establish Educational Understanding Intelligence (EUI) v1 as the platform capability for educational understanding.

First principle:

> Educational understanding is the platform capability. Evaluation is one application of that capability.

EUI v1 defines:

- Educational Knowledge Graph (EKG)
- Educational Identity
- Knowledge Acquisition Intelligence (KAI)
- Educational Context Engine (ECE)
- Institutional Memory
- Platform Capability Registry
- Trust Framework
- Learning Loop Governance
- EUI Consumer Contracts
- Production Scope and Versioning

AEI remains a protected subsystem and one consumer of EUI. No evaluation behavior may bypass AEI.

---

## Architecture

```text
Educational Knowledge Graph
        |
        v
Educational Understanding Intelligence
        |
        +-- Knowledge Acquisition Intelligence
        +-- Educational Context Engine
        +-- Institutional Memory
        +-- Platform Capability Registry
        +-- Trust Framework
        |
        v
Subject Intelligence
        |
        v
Academic Evaluation Intelligence
        |
        +-- Learning Intelligence
        +-- Teacher Intelligence
        +-- Parent Intelligence
        +-- Student Intelligence
        +-- Principal Intelligence
        +-- School Intelligence
```

---

## Architecture rules

1. EUI is platform-level educational understanding.
2. AEI is evaluation-level academic governance.
3. Educational knowledge is governed data, not prompt text.
4. Educational Identity provides stable references for artifacts, questions, lessons, assessments, interventions, and evidence.
5. Provenance and trust are separate architecture concepts.
6. Educational context is resolved through ECE.
7. Institutional Memory is explicit, tenant-scoped, versioned, and auditable.
8. Platform capability claims come from the Platform Capability Registry.
9. Trust is multi-dimensional and explainable.
10. Teacher corrections create governed improvement evidence, not live behavior drift.
11. Consumers must use EUI contracts and must not reimplement educational understanding.
12. Platform capabilities should be extended through providers, registry entries, graph relationships, or consumer contracts.
13. EUI architecture changes require explicit ARM approval and an ADR.

---

## Consequences

### Positive

- Positions StudyNexs as an AI-first School Operating System, not an AI grading tool.
- Prevents duplicated understanding logic across consumers.
- Makes educational context and institutional memory first-class platform concepts.
- Establishes the EKG as the educational backbone.
- Gives product claims one registry-backed source of truth.
- Creates a safer learning loop for product improvement.

### Tradeoffs

- Requires discipline to avoid overbuilding EUI before consumers need runtime behavior.
- Requires clear boundaries so EUI does not absorb AEI responsibilities.
- Requires capability claims to remain honest and versioned.

---

## Scope of this ADR

This ADR is architecture-only.

It does not authorize:

- production code changes;
- database schema changes;
- runtime behavior changes;
- UI changes;
- new external providers;
- changes to AEI certified contracts.

---

## Governance

EUI is architecture-frozen as the v1 platform educational understanding baseline.

Future EUI changes require:

1. ADR update or new ADR;
2. architecture review;
3. compatibility assessment;
4. versioning decision.

AEI remains feature-frozen except for authorized controlled integration waves.
