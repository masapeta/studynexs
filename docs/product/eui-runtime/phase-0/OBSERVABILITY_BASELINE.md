# EUI Phase 0 Observability Baseline

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 0 - Engineering Preparation
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

Define the observability baseline required before future EUI runtime implementation.

This document does not add metrics or logs. It defines the measurement pattern future phases should follow.

---

## 2. Existing repository pattern

Current observability foundations:

| Component | Current role |
|---|---|
| `PlatformMetricsRegistry` | In-process counters and histograms for HTTP and background job events. |
| `/metrics` | Prometheus text exposition for platform, job, and AI metrics. |
| `MetricsMiddleware` | HTTP request count and duration metrics. |
| `AI telemetry` | LLM usage, fallback, and provider telemetry. |
| `OTEL_ENABLED` | Optional OpenTelemetry export control. |
| AEI passive/shadow metrics | Existing task/status/duration pattern for internal integration phases. |

Existing AEI task names:

- `aei_passive_integration`
- `aei_shadow_mode`

Existing AEI statuses:

- `invoked`
- `completed`
- `failed`
- `difference`

---

## 3. EUI observability principles

1. Use low-cardinality labels only.
2. Do not include student, teacher, school, or tenant identifiers in metric labels.
3. Use structured logs for traceability and metrics for aggregate operation.
4. Record duration for future runtime phases.
5. Record fallback and rollback-relevant states.
6. Preserve exception isolation in passive and dual-read phases.
7. Avoid product analytics in Phase 1; start with operational readiness metrics.

---

## 4. Proposed future task names

These are planning names only. They are not implemented in Phase 0.

| Future metric task | Phase | Suggested statuses |
|---|---:|---|
| `eui_identity_resolver` | 1 | `invoked`, `completed`, `failed`, `fallback` |
| `eui_context_engine` | 2 | `invoked`, `completed`, `ambiguous`, `failed`, `fallback` |
| `eui_capability_registry` | 3 | `loaded`, `validated`, `failed`, `fallback` |
| `eui_kai_candidate_extraction` | 4 | `invoked`, `completed`, `low_confidence`, `failed` |
| `eui_ekg_expansion` | 5 | `invoked`, `completed`, `skipped`, `failed` |
| `eui_trust_report` | 6 | `invoked`, `completed`, `manual_review`, `failed` |
| `eui_consumer_migration` | 7 | `dual_read`, `matched`, `difference`, `switched`, `rollback` |

---

## 5. Phase-level observability coverage

| Phase | Baseline observability requirement |
|---|---|
| Phase 1 - Educational Identity | Resolver invocation, completion, failure, fallback, duration. |
| Phase 2 - ECE | Context resolution status, ambiguity count, fallback, duration. |
| Phase 3 - Capability Registry | Registry load/validation status and fallback. |
| Phase 4 - KAI | Acquisition candidate status, low-confidence count, failure, duration. |
| Phase 5 - EKG Expansion | Graph relationship operation status and tenant-safe failure reporting. |
| Phase 6 - Trust Framework | Trust Report generation status and manual-review signal count. |
| Phase 7 - Consumer Migration | Dual-read match/difference counts, switch status, rollback status. |

---

## 6. Structured log expectations

Future logs should include:

- event name;
- phase;
- operation;
- status;
- duration;
- feature flag state where relevant;
- sanitized correlation/request identifier where available;
- exception summary for failures.

Future logs should not include:

- raw student answers;
- parent/student PII;
- tenant identifiers as public labels;
- secrets;
- raw OCR text unless explicitly safe and scoped.

---

## 7. Phase 0 conclusion

The repository already has sufficient observability foundations for Phase 1 planning:

- platform metrics;
- `/metrics`;
- structured AEI integration metrics;
- optional OpenTelemetry;
- existing tests around metrics behavior.

No observability code was changed in Phase 0.
