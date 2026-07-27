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

### EUI-RD-0005 - EUI feature flags follow the existing settings pattern

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Phase 0
- **Decision:** Future EUI runtime flags should follow the existing settings-based pattern used by AEI passive and shadow integration.
- **Reason:** The repository already has default-off AEI runtime flags, environment configurability, and tests that override settings safely.
- **Alternatives considered:** Introduce a new feature flag service before Phase 1.
- **Impact:** Keeps Phase 1 lightweight and consistent with certified AEI integration patterns.
- **Rollback:** Disable the relevant EUI flag and legacy behavior remains source of truth.
- **Evidence:** `phase-0/FEATURE_FLAG_STRATEGY.md`
- **Status:** Accepted

### EUI-RD-0006 - EUI observability starts with platform metrics and structured logs

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Phase 0
- **Decision:** Future EUI runtime phases should initially use the existing platform metrics task/status/duration pattern and structured logs.
- **Reason:** AEI passive and shadow integration already use this pattern successfully without user-visible behavior changes.
- **Alternatives considered:** Add a new observability subsystem before Phase 1.
- **Impact:** Reduces runtime preparation risk and avoids premature observability architecture.
- **Rollback:** Disable EUI runtime flag; metrics should show no further EUI task activity.
- **Evidence:** `phase-0/OBSERVABILITY_BASELINE.md`
- **Status:** Accepted

### EUI-RD-0007 - EUI Golden Harness expansion starts with identity and context cases

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Phase 0
- **Decision:** Future EUI Golden Harness expansion should begin with Educational Identity and Educational Context cases before consumer behavior tests.
- **Reason:** Identity and context are foundational dependencies for every later EUI runtime phase.
- **Alternatives considered:** Begin Golden Harness expansion with consumer-facing tutor or evaluation cases.
- **Impact:** Keeps runtime validation dependency-led and prevents consumer tests from inventing private EUI assumptions.
- **Rollback:** Not applicable; planning decision.
- **Evidence:** `phase-0/GOLDEN_HARNESS_EXPANSION_PLAN.md`
- **Status:** Accepted

### EUI-RD-0008 - EUI rollback pattern keeps legacy behavior as source of truth

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Phase 0
- **Decision:** Future EUI runtime phases should preserve legacy behavior as source of truth until a certified switch is separately authorized.
- **Reason:** EUI will become a platform dependency; behavior rollback must be simple, observable, and fast.
- **Alternatives considered:** Direct switch to EUI implementations during each phase.
- **Impact:** Requires compatibility layers and dual-read validation, but reduces production and trust risk.
- **Rollback:** Disable EUI phase or consumer flag and verify legacy behavior.
- **Evidence:** `phase-0/ROLLBACK_PATTERN.md`
- **Status:** Accepted

### EUI-RD-0009 - Future phases include lightweight retrospectives

- **Date:** 2026-07-27
- **Owner:** ARM
- **Phase:** Phase 0
- **Decision:** Future EUI runtime implementation phases should include a lightweight retrospective after certification.
- **Reason:** Certification answers whether requirements were met; retrospectives capture operational learning, surprises, and improvements for the next phase without changing architecture records.
- **Alternatives considered:** Put lessons learned into ADRs or certification reports only.
- **Impact:** Keeps ADRs focused on architecture and certification focused on evidence while preserving implementation learning.
- **Rollback:** Not applicable; process decision.
- **Evidence:** `phase-0/PHASE_0_COMPLETION_REPORT.md`
- **Status:** Accepted
