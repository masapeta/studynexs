# Learning Loop Governance

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

StudyNexs should learn from real educational usage without allowing live behavior to drift invisibly.

Teacher corrections, overrides, support incidents, and school feedback are valuable evidence. They should feed governed improvement loops, not automatic model updates.

---

## 2. Principle

No self-modifying AI.

Human feedback may create evidence for improvement. It must not silently change production academic behavior.

---

## 3. Governance loop

```text
Teacher Override
  -> Evidence Captured
  -> Review Queue
  -> Engineering Review
  -> Capability Proposal
  -> Certification
  -> Release
```

This loop preserves trust, auditability, and release discipline.

---

## 4. Feedback sources

| Source | Use |
|---|---|
| Teacher override | Identify accepted answer variants, rubric gaps, reasoning gaps |
| Manual review reason | Improve capability scope and Trust Report messaging |
| Parent complaint | Improve explanations, evidence display, communication policy |
| Student confusion | Improve tutor framing and intervention design |
| Principal review | Improve analytics interpretation and decision support |
| Support incident | Improve training, UX, operations, or capability claims |
| Shadow comparison | Measure differences before production behavior changes |

---

## 5. Evidence classification

| Evidence type | Meaning |
|---|---|
| Product defect | Current supported behavior is wrong. |
| Capability expansion | Useful behavior outside current support scope. |
| Policy gap | School-specific rule not represented. |
| Trust gap | Output correct internally but unclear or unconvincing to users. |
| Training gap | Product works but expectations or workflow understanding failed. |
| Data gap | Missing or low-quality curriculum, rubric, or source evidence. |

---

## 6. Release discipline

Learning loop outputs may change production behavior only through:

1. approved product decision;
2. architecture compatibility check;
3. capability registry update;
4. focused tests and Golden Harness coverage where academic behavior changes;
5. certification evidence;
6. controlled release.

---

## 7. Anti-patterns

- Automatically changing grading rules from teacher overrides.
- Fine-tuning or prompt-changing live behavior without certification.
- Treating one school's preference as global default.
- Hiding behavior changes inside prompt edits.
- Using student-linked evidence outside tenant and privacy boundaries.
