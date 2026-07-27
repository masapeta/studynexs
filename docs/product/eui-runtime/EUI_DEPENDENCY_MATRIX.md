# EUI Dependency Matrix

- **Program:** EUI Runtime Implementation Roadmap v1
- **Classification:** Planning artifact
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

The EUI Dependency Matrix defines implementation dependencies, consumers, runtime risk, migration order, breaking risk, and rollback posture for every EUI subsystem.

It exists to prevent circular dependencies, consumer-driven shortcuts, and feature-first implementation.

---

## 2. Matrix

| Component | Depends On | Used By | Runtime Risk | Migration Order | Breaking Risk | Rollback |
|---|---|---|---|---:|---|---|
| Phase 0 Engineering Preparation | EUI architecture baseline, AEI certification history, existing feature flag/observability patterns | Every runtime phase | Low | 0 | Low | Planning-only; no runtime rollback needed |
| Educational Identity | CurriculumPack, existing Knowledge Graph concepts, tenant scope | ECE, EKG, AEI, AI Tutor, Teacher Copilot, Lesson Planner, Question Generator, Analytics | Low if read-only | 1 | Medium if identity shape changes after consumers adopt it | Keep legacy references as source of truth until dual-read validates identity |
| Educational Context Engine | Educational Identity, CurriculumPack, School Config, Institutional Memory later | AEI, AI Tutor, Question Generator, Lesson Planner, Parent Assistant, Principal Dashboard | Medium because context drives behavior once switched | 2 | High if consumers depend on incomplete context | Start as adapter over existing context; feature-flag consumer use |
| Platform Capability Registry | AEI Subject Capability Registry, EUI architecture modes, production scope docs | AEI, UI badges, Trust Framework, docs, tests, support | Medium | 3 | Medium if modes differ from AEI semantics | Keep AEI registry active; map platform registry to AEI subset before switch |
| Knowledge Acquisition Intelligence | AI Gateway, OCR providers, file intake, Educational Identity, Trust Framework | EKG, Institutional Memory, AEI, Teacher Copilot, Question Generator | High when external extraction is involved | 4 | Medium if artifacts are treated as trusted too early | Store as candidates; disable consumer use independently |
| Educational Knowledge Graph Expansion | Existing KG, Educational Identity, CurriculumPack, KAI, provenance | AEI, AI Tutor, Lesson Planner, Principal Dashboard, Analytics | Medium to High depending on evidence edges | 5 | High for student-linked evidence relationships | Add edges incrementally; keep existing KG queries unchanged |
| Trust Framework | KAI, AEI, Capability Registry, Teacher Review, provenance references | Every intelligence UI and consumer | Medium | 6 | Medium if existing confidence consumers break | Run trust alongside confidence; preserve legacy confidence fields |
| Institutional Memory | School Config, ECE, teacher decisions, governance approvals | ECE, AEI, Teacher Copilot, Parent Assistant, communications | Medium | 6 or later | High if unreviewed memory affects authority | Read-only/manual-entry first; no automatic behavior mutation |
| Learning Loop Governance | AEI evidence, Trust Framework, Institutional Memory, certification process | Engineering review, capability expansion, release planning | Low runtime / High governance | 6 or later | Low if kept as evidence only | Keep learning loops out of live behavior until certified release |
| AEI Consumer Migration | AEI v1, Educational Identity, ECE, Capability Registry, Trust Framework | Evaluation flow, evidence ledger, downstream learning intelligence | High because evaluation is consequential | 7.1 | High | Feature flags, shadow comparison, legacy evaluation source of truth |
| Teacher Copilot Migration | ECE, EKG, Trust Framework, Institutional Memory | Teacher workflows | Medium | 7.2 | Medium | Dual-read recommendations; legacy prompt/context path remains fallback |
| AI Tutor Migration | ECE, EKG, Educational Identity, Trust Framework, language capabilities | Student learning experience | Medium | 7.3 | Medium | Feature-flag EUI-grounded tutor context; fallback to certified tutor path |
| Question Generator Migration | EKG, Educational Identity, ECE, Capability Registry | Assessment Intelligence | Medium | 7.4 | High if paper generation changes unexpectedly | Generate comparison outputs before switch |
| Lesson Planner Migration | EKG, ECE, Institutional Memory | Teacher planning | Medium | 7.5 | Medium | Dual-read lesson context; retain legacy plan generation |
| Principal Dashboard Migration | EKG, Trust Framework, approved evidence | Principal intelligence | Medium | 7.6 | Medium to High if analytics interpretation changes | Shadow analytics metrics before surfacing |
| Parent Assistant Migration | Approved evidence, ECE, Trust Framework, Institutional Memory | Parent communication | High trust risk | 7.7 | High | Parent surfaces remain on approved evidence only; feature flag explanations |
| School Analytics Migration | EKG, approved evidence, ECE | Management and leadership insights | Medium | 7.8 | Medium | Run parallel aggregate jobs and compare |

---

## 3. Dependency chain

```text
Educational Identity
        |
        v
Educational Context Engine
        |
        v
Platform Capability Registry
        |
        v
Knowledge Acquisition Intelligence
        |
        v
Educational Knowledge Graph Expansion
        |
        v
Trust Framework + Institutional Memory + Learning Loop Governance
        |
        v
Consumer Migration
```

---

## 4. Highest-risk transitions

| Transition | Why risky | Mitigation |
|---|---|---|
| ECE consumed by AEI | Context affects evaluation interpretation | Dual read and passive comparison first |
| Platform registry replacing AEI registry | Capability modes affect claims and routing | Keep AEI registry active until compatibility proven |
| KAI feeding EKG | Extracted artifacts may be low confidence | Candidate state and review gate |
| EKG evidence edges | Student evidence is sensitive and consequential | Tenant isolation tests and provenance checks |
| Trust replacing confidence | UI and workflows may interpret trust incorrectly | Run trust alongside confidence first |
| Parent Assistant migration | Parent trust is fragile | Approved evidence only and parent-safe copy review |

---

## 5. Matrix maintenance rule

Before any EUI runtime phase begins, update this matrix with:

- actual dependencies found in implementation;
- feature flags;
- rollback mechanism;
- certification evidence path;
- owner and date.
