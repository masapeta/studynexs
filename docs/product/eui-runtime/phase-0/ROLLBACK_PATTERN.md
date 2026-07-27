# EUI Phase 0 Rollback Pattern

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 0 - Engineering Preparation
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

Define the rollback pattern future EUI runtime phases must follow.

This document does not perform rollback and does not change runtime behavior.

---

## 2. Rollback principle

Legacy behavior remains the source of truth until a phase is explicitly switched and certified.

For early EUI phases, rollback should usually mean:

```text
Disable EUI flag
  -> Legacy path remains active
  -> Verify metrics/logs
  -> Verify regression slice
```

---

## 3. Phase rollback coverage

| Phase | Rollback pattern |
|---|---|
| Phase 1 - Educational Identity | Disable identity passive flag; continue using legacy curriculum/KG references. |
| Phase 2 - ECE | Disable context passive or dual-read flag; continue existing context construction. |
| Phase 3 - Capability Registry | Disable platform registry flag; AEI registry remains source for evaluation capability. |
| Phase 4 - KAI | Disable candidate extraction flag; uploaded artifacts remain in existing flows only. |
| Phase 5 - EKG Expansion | Disable new graph reads/writes; existing KG spine remains active. |
| Phase 6 - Trust Framework | Disable Trust Report generation; existing confidence fields remain active. |
| Phase 7 - Consumer Migration | Disable consumer-specific source flag; legacy consumer path resumes as source of truth. |

---

## 4. Rollback proof requirements

Each phase certification must prove:

- flag-off behavior;
- flag-on behavior;
- rollback to flag-off behavior;
- no data loss;
- no tenant isolation regression;
- metrics/logs show rollback state;
- production behavior matches expected legacy behavior where applicable.

---

## 5. Data rollback posture

Early phases should avoid irreversible writes.

If a future phase introduces schema or persisted data:

- migration must be additive where possible;
- old paths must continue reading legacy data;
- destructive migrations require separate ARM approval;
- rollback must state whether data rollback is required or only behavior rollback is required.

---

## 6. Emergency stop posture

Any phase that affects consequential academic output must support immediate disablement.

For AEI-affecting phases:

- AEI remains protected;
- teacher-approved evidence remains source of truth;
- downstream consumers must not receive unapproved EUI outputs;
- rollback must preserve gradebook, mastery, and evidence integrity.

---

## 7. Phase 0 conclusion

Rollback strategy coverage is defined for all planned runtime phases.

No rollback execution occurred in Phase 0 because no runtime changes were made.
