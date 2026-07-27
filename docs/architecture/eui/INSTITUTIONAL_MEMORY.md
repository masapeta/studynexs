# Institutional Memory

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

Institutional Memory captures how a specific school teaches, evaluates, communicates, and makes academic decisions.

It is more than configuration. It is governed institutional knowledge.

Examples:

- grading policies;
- accepted terminology;
- school-specific rubrics;
- teacher-approved answer variations;
- bilingual vocabulary preferences;
- moderation decisions;
- communication tone;
- historical academic decisions;
- curriculum adaptations.

---

## 2. Principle

Institutional Memory must be explicit, reviewable, versioned, and auditable.

It must not be hidden in:

- prompts;
- model weights;
- one-off service branches;
- undocumented teacher habits;
- untracked spreadsheets.

---

## 3. Memory categories

| Category | Examples |
|---|---|
| Academic policy | Grace marks, rounding, optional questions, moderation rules |
| Evaluation convention | Accepted answer variants, step-marking preferences, terminology |
| Teaching style | Explanation preference, pacing, preferred examples |
| Language convention | Local terms, bilingual vocabulary, code-mixed classroom language |
| Communication tone | Parent-facing tone, student encouragement style |
| Historical decisions | Teacher overrides, approved rubrics, recheck outcomes |
| Operational preference | Report format, review cadence, escalation route |

---

## 4. Relationship to EUI

Institutional Memory feeds ECE and EUI.

```text
Institutional Memory
        |
        v
Educational Context Engine
        |
        v
Educational Understanding Intelligence
        |
        v
Consumers
```

It should make intelligence school-aware without making behavior uncontrolled.

---

## 5. Governance

1. Institutional Memory is tenant-scoped.
2. Updates require an accountable source.
3. Consequential memory entries require review before becoming authoritative.
4. Historical decisions are evidence, not automatic future policy.
5. Teacher overrides can inform review queues but must not mutate live behavior.
6. Memory used in parent/student-facing output must be appropriate for that audience.

---

## 6. Production boundary

For v1.0 production, Institutional Memory should support the school-specific policies and terminology required by the supported scope. Capability expansion can add broader policy modeling, moderation history, and school-wide preference learning through governed releases.
