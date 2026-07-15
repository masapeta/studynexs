---
description: Testing and Quality Standards (pointer)
---

# Testing & Quality

> **Superseded by the Engineering Validation Standard:** [`004-validation-and-testing.md`](./004-validation-and-testing.md)

This file is retained as a short pointer. All validation expectations, batch gates, failure classification, and definition of done live in **004**.

For handover content before commit approval, use **Section 14 — Engineering Report** in 004.

## Environmental failures (quick policy)

Before classifying a batch as failing, verify that the **test environment is stable**.

Environmental failures — concurrent test execution, shared database contention, unavailable external services — must be identified **separately** from application regressions. Do not overstate product problems when the root cause is test infrastructure.

Full classification: [`004-validation-and-testing.md`](./004-validation-and-testing.md) Section 10.
