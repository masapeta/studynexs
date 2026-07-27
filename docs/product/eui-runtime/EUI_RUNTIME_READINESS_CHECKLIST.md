# EUI Runtime Readiness Checklist

- **Program:** EUI Runtime Implementation Roadmap v1
- **Classification:** Planning artifact
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

The Runtime Readiness Checklist defines the minimum gate before any EUI runtime phase begins.

It is intentionally stricter than ordinary task planning because EUI becomes a platform dependency for multiple intelligence consumers.

---

## 2. Phase readiness gate

Before a phase starts:

| Gate | Required evidence |
|---|---|
| Contracts finalized | Input/output contracts documented for the phase. |
| Dependencies complete | Dependency matrix updated and upstream dependencies available. |
| Tests defined | Focused tests, regression tests, and certification tests planned. |
| Rollback documented | Feature flag, compatibility path, or rollback plan documented. |
| Observability defined | Metrics/logs/traces identified. |
| Feature flags defined | Any behavior-changing path has a control. |
| Golden Harness updated | Required if academic capability behavior changes. |
| Tenant boundary reviewed | Required if tenant-scoped or student-linked data is touched. |
| AEI impact assessed | Required if evaluation, evidence, confidence, or review is touched. |
| Product claims reviewed | Required if capability visibility or messaging changes. |

---

## 3. Runtime implementation checklist

During implementation:

- keep legacy behavior as source of truth until switch authorization;
- prefer read-only or passive integration first;
- add compatibility adapters rather than rewriting consumers;
- preserve tenant scoping;
- preserve `/api/v1` compatibility;
- keep AI calls through the AI Gateway;
- preserve teacher authority for consequential academic output;
- capture metrics for invocation, success, failure, duration, and fallback where relevant;
- write certification evidence before requesting acceptance.

---

## 4. Phase exit checklist

Before a phase can be accepted:

| Exit criterion | Status |
|---|---|
| Focused tests pass | Required |
| Regression tests pass | Required |
| API import/build proof passes | Required for API-touching phase |
| Runtime behavior unchanged or explicitly certified | Required |
| Observability proof exists | Required |
| Rollback proof exists | Required |
| Documentation updated | Required |
| Certification report completed | Required |
| ARM review completed | Required |

---

## 5. Consumer switch checklist

Before a consumer switches to EUI as source:

- compatibility layer exists;
- dual-read data exists;
- differences classified;
- rollback control verified;
- user-facing behavior reviewed;
- role/tenant authorization verified;
- certification report accepted;
- ARM explicitly authorizes switch.

---

## 6. Capability claim checklist

Before StudyNexs claims support for a capability:

- Platform Capability Registry entry exists;
- supported scope is clear;
- unsupported scenarios are documented;
- Trust Report behavior exists;
- manual-review behavior exists where needed;
- user-facing expectation messaging exists;
- tests/certification evidence exists;
- ARM approves production claim.

---

## 7. Platform readiness scorecard template

| Dimension | Status | Evidence |
|---|---|---|
| Architecture | Not started |  |
| Contracts | Not started |  |
| Runtime | Not started |  |
| Tests | Not started |  |
| Observability | Not started |  |
| Documentation | Not started |  |
| Rollback | Not started |  |
| Certification | Not started |  |

---

## 8. Phase 0 preparation checklist

Before Phase 1 can be authorized:

| Preparation item | Required evidence |
|---|---|
| Feature flag framework verified | Existing pattern identified or new flag strategy documented. |
| Observability baseline defined | Metrics/logs/traces listed for Phase 1. |
| Golden Harness expansion plan | Required cases identified if academic behavior later changes. |
| Dependency inventory completed | Required modules, docs, services, and tests listed. |
| Branch strategy documented | Implementation branch and publication cadence defined. |
| Certification template prepared | Phase certification report structure ready. |
| Rollback pattern defined | Phase 1 rollback approach documented. |

---

## 9. Governance status

This checklist is accepted as part of the EUI Runtime Planning Baseline.

It does not authorize runtime implementation.
