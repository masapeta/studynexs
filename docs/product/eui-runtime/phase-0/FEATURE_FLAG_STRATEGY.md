# EUI Phase 0 Feature Flag Strategy

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 0 - Engineering Preparation
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

Define the feature flag strategy for future EUI runtime phases before implementation begins.

This document does not add flags. It documents the strategy future phases should follow.

---

## 2. Existing repository pattern

Current feature controls are environment-driven settings in `apps/api/app/core/config.py`.

Relevant existing examples:

| Flag | Default | Current purpose |
|---|---:|---|
| `AEI_PASSIVE_INTEGRATION_ENABLED` | `False` | Run AEI as a passive observer only. |
| `AEI_SHADOW_MODE_ENABLED` | `False` | Run AEI shadow comparison without changing production output. |
| `RATE_LIMIT_ENABLED` | `True` | Enable request rate limiting. |
| `OUTBOX_WORKER_ENABLED` | `True` | Enable embedded outbox worker outside tests. |
| `OTEL_ENABLED` | `False` | Enable OpenTelemetry export. |

Tests commonly override settings with monkeypatching.

---

## 3. EUI flag principles

1. EUI behavior-changing paths default to off.
2. Planning and read-only preparation do not require feature flags.
3. Passive or dual-read modes must run without changing production output.
4. Consumer switches require separate flags from foundational contract flags.
5. Flags should be low-count, explicit, and phase-scoped.
6. Flags must not expose unsupported product claims.
7. Disabling a flag must restore legacy behavior or no-op behavior.

---

## 4. Proposed future flag families

These are planning names only. They are not implemented by Phase 0.

| Future flag | Phase | Purpose | Default |
|---|---:|---|---:|
| `EUI_IDENTITY_PASSIVE_ENABLED` | 1 | Resolve Educational Identity beside existing references without changing consumers. | `False` |
| `EUI_CONTEXT_PASSIVE_ENABLED` | 2 | Resolve Educational Context beside existing context without switching consumers. | `False` |
| `EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED` | 3 | Load platform capability registry without replacing AEI registry. | `False` |
| `EUI_KAI_CANDIDATE_EXTRACTION_ENABLED` | 4 | Produce acquisition candidates without authoritative use. | `False` |
| `EUI_EKG_EXPANSION_ENABLED` | 5 | Enable new graph relationship writes or reads under explicit scope. | `False` |
| `EUI_TRUST_REPORT_ENABLED` | 6 | Produce Trust Reports alongside existing confidence fields. | `False` |
| `EUI_AEI_CONTEXT_DUAL_READ_ENABLED` | 7.1 | Compare EUI context with existing AEI context without switching. | `False` |
| `EUI_AEI_CONTEXT_SOURCE_ENABLED` | 7.1 | Allow AEI to consume EUI context as source after certification. | `False` |

---

## 5. Rollout modes

| Mode | Meaning |
|---|---|
| Off | EUI runtime path does not execute. |
| Passive | EUI executes and captures internal output only. |
| Dual read | Legacy and EUI paths both execute; legacy remains source of truth. |
| Source | EUI becomes source for the scoped consumer under explicit authorization. |
| Cleanup | Legacy path removed after accepted stable operation. |

---

## 6. Testing expectations

Each future flag requires tests proving:

- default disabled behavior;
- enabled behavior within the authorized mode;
- disabled rollback path;
- no production output change for passive or dual-read phases;
- exception isolation where EUI is not the source of truth.

---

## 7. Phase 0 conclusion

The repository already has a suitable settings-based feature flag pattern for EUI Phase 1 preparation.

No new feature flags were added in Phase 0.
