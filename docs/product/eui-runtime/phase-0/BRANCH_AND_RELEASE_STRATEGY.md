# EUI Phase 0 Branch and Release Strategy

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 0 - Engineering Preparation
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

Define the branch, commit, tag, and release cadence for future EUI runtime phases.

This document does not create a branch and does not authorize implementation.

---

## 2. Branch strategy

Recommended future branch pattern:

```text
codex/eui-phase-<phase-number>-<short-name>
```

Examples:

```text
codex/eui-phase-0-preparation
codex/eui-phase-1-educational-identity
codex/eui-phase-2-context-engine
```

For small docs-only acceptance changes, `develop` may be used only when ARM explicitly authorizes direct publication.

---

## 3. Commit strategy

Each phase should produce isolated commits:

| Commit type | Example |
|---|---|
| Planning | `docs(eui): complete phase 0 preparation` |
| Foundation code | `feat(eui): add educational identity contracts` |
| Tests | Include with implementation unless separately useful. |
| Certification | Include certification report with the phase commit when practical. |

Runtime phases should not mix unrelated product or marketing changes.

---

## 4. Tag strategy

Recommended tag pattern:

```text
eui-runtime-phase<phase-number>-<short-name>-certified
```

Examples:

```text
eui-runtime-phase0-preparation-certified
eui-runtime-phase1-identity-certified
eui-runtime-phase2-context-certified
```

Tags should be annotated and should summarize:

- scope;
- validation;
- certification status;
- behavior impact;
- rollback posture.

---

## 5. Release cadence

Each runtime phase should follow:

```text
Authorization
  -> Implementation
  -> Focused validation
  -> Regression validation
  -> Certification report
  -> ARM acceptance
  -> Commit
  -> Annotated tag
  -> Publish
  -> Remote verification
```

No phase implies authorization for the next phase.

---

## 6. Publication requirements

Before publication:

- working tree contains only the phase scope;
- validation is complete;
- certification report is complete;
- rollback path is documented;
- ARM acceptance is recorded;
- commit is isolated;
- tag is annotated.

---

## 7. Phase 0 conclusion

The repository already has a proven commit/tag/publication cadence from AEI and EUI milestones.

No branch was created in Phase 0.
