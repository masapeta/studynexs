# EUI Runtime Certification Report Template

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 0 - Engineering Preparation
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## Template

Use this template for future EUI runtime phase certification reports.

```markdown
# EUI Runtime Phase <N> Certification Report

- **Program:** EUI Runtime Implementation
- **Phase:** Phase <N> - <Name>
- **Certification type:** <Foundation | Passive | Dual-read | Runtime | Consumer migration>
- **Date:** <YYYY-MM-DD>
- **Status:** <PASS | PASS WITH CONDITIONS | FAIL>
- **Implementation commit:** <commit or pending>
- **Feature flags:** <flags>

---

## Objective

State what this phase was intended to prove.

---

## Scope certified

### Contracts

Status: <PASS | UNCHANGED | NOT APPLICABLE>

- <contract evidence>

### Runtime behavior

Status: <UNCHANGED | CHANGED AND CERTIFIED>

- <behavior evidence>

### Feature flags

Status: <PASS | NOT APPLICABLE>

- default state;
- enabled state;
- rollback state.

### Observability

Status: <PASS | NOT APPLICABLE>

- metrics;
- logs;
- traces if applicable.

### Rollback

Status: <PASS | NOT APPLICABLE>

- rollback mechanism;
- rollback proof.

### AEI impact

Status: <UNCHANGED | CHANGED AND CERTIFIED | NOT APPLICABLE>

- <impact evidence>

### Schema

Status: <UNCHANGED | CHANGED AND CERTIFIED>

- <schema evidence>

### UI

Status: <UNCHANGED | CHANGED AND CERTIFIED>

- <UI evidence>

---

## Tests executed

```text
<commands>
```

Observed result:

```text
<summary>
```

---

## Behavior identity evidence

If runtime behavior is expected to remain unchanged, prove disabled vs enabled output identity.

---

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| <risk> | <severity> | <mitigation> |

---

## Conditions

| Condition | Severity | Owner | Disposition |
|---|---|---|---|
| <condition> | <severity> | <owner> | <disposition> |

---

## Recommendation

<APPROVED | APPROVED WITH CONDITIONS | NOT APPROVED>
```

---

## Phase 0 conclusion

The certification template is ready for future runtime phases.

No certification report for runtime implementation was produced in Phase 0 because no runtime implementation occurred.

---

## Phase retrospective addendum

Future runtime phases should add a short retrospective after certification:

```markdown
## Phase retrospective

- What assumptions held?
- What surprised us?
- What should the next phase change?
- What governance or tooling improvements emerged?
```

This section is not an ADR and does not replace certification evidence.
