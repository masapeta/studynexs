# EUI Runtime Decision Log

- **Program:** EUI Runtime Implementation Roadmap v1
- **Classification:** Planning artifact
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

The EUI Runtime Decision Log captures implementation-level decisions that do not rise to the level of an ADR.

ADRs remain for architecture changes. This log is for runtime sequencing, provider selection, migration details, feature-flag strategy, and certification decisions made during implementation.

---

## 2. When to use this log

Use this log for decisions such as:

- phase sequencing adjustments;
- compatibility adapter choices;
- feature flag naming and rollout strategy;
- provider selection within an accepted architecture;
- migration order refinements;
- rollback approach;
- certification scope;
- test fixture/golden dataset choices.

Do not use this log to change EUI or AEI architecture. Architecture changes require ADR review.

---

## 3. Entry template

```text
Decision ID:
Date:
Owner:
Phase:
Decision:
Reason:
Alternatives considered:
Impact:
Rollback:
Evidence:
Status:
```

---

## 4. Initial entries

### EUI-RD-0001 - Runtime implementation proceeds through dependency maturity

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Roadmap
- **Decision:** EUI runtime implementation order follows dependency maturity, not feature popularity.
- **Reason:** Foundational contracts such as Educational Identity, ECE, and Capability Registry must mature before consumer-facing intelligence migrates.
- **Alternatives considered:** Consumer-first implementation led by Teacher Copilot, AI Tutor, or evaluation enhancements.
- **Impact:** Reduces integration risk and prevents consumers from creating duplicate understanding logic.
- **Rollback:** Not applicable; planning decision.
- **Evidence:** EUI architecture baseline and runtime roadmap.
- **Status:** Accepted

### EUI-RD-0002 - Curriculum Packs become the delivery unit

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Roadmap
- **Decision:** EUI runtime delivery should be planned around supported curriculum scopes rather than isolated technical features.
- **Reason:** A curriculum-led unit naturally drives identity, context, graph, capabilities, evaluation, tutor, analytics, and parent-safe reporting coherently.
- **Alternatives considered:** Feature-led planning by OCR, tutor, reports, or analytics.
- **Impact:** Aligns engineering with educational outcomes and production product claims.
- **Rollback:** Revisit through ARM roadmap review if a phase requires a non-curriculum-led infrastructure prerequisite.
- **Evidence:** EUI Runtime Implementation Roadmap v1.
- **Status:** Accepted

### EUI-RD-0003 - Consumer migration requires dual-read verification

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Roadmap
- **Decision:** Consumers should migrate through preparation, compatibility layer, dual read, verification, switch, and cleanup.
- **Reason:** EUI will become a shared platform dependency; direct switching creates unnecessary runtime and trust risk.
- **Alternatives considered:** Direct consumer migration or bulk migration.
- **Impact:** Increases implementation discipline and improves rollback safety.
- **Rollback:** ARM may authorize a scoped exception with explicit risk acceptance.
- **Evidence:** EUI Consumer Migration Plan.
- **Status:** Accepted

### EUI-RD-0004 - Phase 0 Engineering Preparation precedes Phase 1

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Roadmap
- **Decision:** Add Phase 0 Engineering Preparation before Educational Identity runtime implementation.
- **Reason:** Foundational implementation needs feature flag verification, observability baseline, Golden Harness planning, dependency inventory, branch strategy, release cadence, and certification template before runtime changes begin.
- **Alternatives considered:** Start directly with Phase 1 Educational Identity.
- **Impact:** Reduces implementation risk and creates a clean readiness gate before runtime work.
- **Rollback:** Not applicable; planning decision.
- **Evidence:** EUI Runtime Implementation Roadmap v1 and Runtime Readiness Checklist.
- **Status:** Accepted
