# StudyNexs Review Standards

**Version:** 1.0  
**Status:** Active  
**Effective:** Product Execution Phase (2026-07-17)

> **Answers:** *How is quality evaluated?*

---

## Review types

| Review | When | Focus |
|--------|------|-------|
| **Code review** | Every significant PR / batch increment | Correctness, tenant isolation, security, maintainability |
| **Architecture review** | Cross-module boundaries, new services | Fit with Architecture Constitution |
| **Design review** | UI changes | Design System v1 compliance; no unauthorized redesign |
| **Security review** | Auth, PII, money, external input | OWASP baseline, fail-secure |
| **UX review** | New workflows or shell changes | No Surprise Rule; persona fit |
| **AI review** | LLM features | Gateway routing, grounding, HITL, metering |
| **Performance review** | Hot paths, large payloads | Latency, query scope, N+1 |
| **Capability review** | Batch completion | Product Execution acceptance criteria |

---

## Code review checklist

- [ ] Scoped by `school_id` from `CurrentUser` (never client `school_id`)
- [ ] Authz on protected routes
- [ ] Parameterized queries / ORM only
- [ ] Money uses `Decimal`
- [ ] LLM calls via AI Gateway with metering
- [ ] No secrets or PII in logs
- [ ] Tests for non-trivial logic
- [ ] Build + lint clean

---

## Capability review checklist (batch completion)

Per [`../product/PRODUCT_EXECUTION_CONSTITUTION.md`](../product/PRODUCT_EXECUTION_CONSTITUTION.md):

- [ ] Capability Delivered documented
- [ ] Problem Solved + Primary Persona stated
- [ ] Business Outcome measurable
- [ ] Demonstration Scenario recorded
- [ ] Decision Log entry if architectural
- [ ] **Product success question answered:** *What can a school do today that it could not do yesterday?*

---

## Visual / platform review (when UI changes)

For platform-layer changes, follow the audit package standard:

**Reference:** [`../ui-audit/REVIEW_PACKAGE_STANDARD.md`](../ui-audit/REVIEW_PACKAGE_STANDARD.md)

Required: `REVIEW.md`, capture manifest, before/after screenshots, build status, ARM approval block.

**Product Execution Phase:** Most batch work uses existing DS v1 — visual review is lighter unless layout/workflow changes.

---

## AI review checklist

- [ ] Grounded in approved CurriculumPack where applicable
- [ ] Human approval for authoritative output
- [ ] Credit check before generation
- [ ] Provider via gateway only
- [ ] Refusal path when grounding unavailable (no silent hallucination)

---

## Security review triggers

Mandatory extra scrutiny when touching:

- Authentication / session
- File upload / ingest
- Cross-tenant queries
- Fee/payment flows
- Parent/student PII

---

## Review hierarchy

Higher governance constrains reviews:

```
Architecture Constitution → Engineering Governance → Design System v1
  → Product Execution Constitution → Product Execution Plan → Implementation
```

Reviews cannot approve work that contradicts constitutional documents.

---

## Recording outcomes

| Outcome | Action |
|---------|--------|
| Approved | Proceed; update Execution Plan if batch milestone |
| Approved with fixes | Fix then merge |
| Deferred | Document in Execution Plan blocked items |
| Architectural decision | [`../decisions/DECISION_LOG.md`](../decisions/DECISION_LOG.md) |
