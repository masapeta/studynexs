# Assessment Intelligence v1.0 Batch H Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Authorization ID: ASSESSMENT-V1-BATCH-H-AUTH-001
> Implementation authorization: Authorized for Batch H only
> Runtime behavior changes: Not authorized
> Batch: H - Final Assessment Intelligence v1.0 Certification and Product-Claim Boundary
> ARM review: Accepted; Batch H may begin within this contract only

---

## 1. Purpose

Authorize the narrow implementation required to certify Assessment Intelligence
v1.0 and freeze its product-claim boundary.

Batch H is a certification batch. It is not a runtime feature batch.

---

## 2. Authorized implementation scope

If accepted by ARM, Batch H may implement only:

1. Final Assessment Intelligence v1.0 Certification Report.
2. Assessment Intelligence v1.0 Product-Claim Boundary document.
3. Focused static tests for final certification and product-claim rules.
4. Minor documentation cross-links needed to make the certification discoverable.

No runtime feature implementation is authorized.

---

## 3. Repository boundary

Authorized files:

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_H_FINAL_CERTIFICATION_DESIGN_BRIEF.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_H_FINAL_CERTIFICATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_FINAL_CERTIFICATION_REPORT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_PRODUCT_CLAIM_BOUNDARY.md`
- `apps/api/tests/test_assessment_intelligence_v1_final_certification.py`

Post-publication `docs/STATUS.md` updates must remain separate from the
implementation commit.

Any change outside this boundary requires separate ARM authorization.

---

## 4. Explicit exclusions

Batch H does not authorize:

- database schema changes;
- Alembic migrations;
- API contract changes;
- public endpoint changes;
- production UI changes;
- runtime product behavior changes;
- feature flag changes;
- question-paper generation behavior changes;
- question-bank behavior changes;
- exam service behavior changes;
- answer-sheet evaluation behavior changes;
- AEI behavior changes;
- EUI behavior changes;
- EUI source adoption;
- marks changes;
- teacher-review routing changes;
- evidence-ledger behavior changes;
- mastery behavior changes;
- parent/student visibility changes;
- AI provider changes;
- LLM inference changes;
- OCR behavior changes;
- translation behavior changes;
- public product claim expansion beyond certified supported scope.

---

## 5. Product-claim rules to enforce

Batch H must enforce the distinction between:

- certified supported claims;
- assist/manual-review claims;
- unsupported claims;
- expansion/future-scope claims.

The certification must explicitly preserve these rules:

1. Teachers retain final authority.
2. Generated papers remain non-authoritative until approved.
3. AEI remains the only academic answer-evaluation pipeline.
4. Parent/student/principal downstream evidence must be teacher-approved.
5. Universal board/grade/subject/language/OCR/visual support must not be
   claimed.
6. Autonomous paper approval, autonomous grading, and autonomous diagram grading
   must not be claimed.

---

## 6. Validation requirements

Before ARM acceptance, Batch H implementation must produce evidence for:

- focused static certification tests;
- product-claim boundary tests;
- existence and accepted status of Batch A through G-B artifacts;
- no-overclaim assertions;
- API import check;
- `git diff --check`;
- no unauthorized file changes.

Browser proof may reference the latest certified G-B browser proof. If the
Batch H implementation touches browser proof code, then `npm run
e2e-assessment-v1` must be re-run.

---

## 7. Rollback

Rollback is simple:

- remove the final certification report;
- remove the product-claim boundary document;
- remove the focused static test;
- revert minor documentation cross-links.

No database, API, UI, feature flag, runtime, marks, evidence-ledger, AEI, or EUI
rollback is required because none are authorized.

---

## 8. Exit criteria

Batch H may be considered complete only when:

- final certification report is complete;
- product-claim boundary is complete;
- focused tests pass;
- product claims are limited to certified supported scope;
- unsupported claims are explicitly blocked;
- no runtime behavior changes are introduced;
- certification recommends acceptance for commit/tag/publication.

---

## 9. Recommended implementation metadata

If accepted after code review:

```text
Commit: docs(assessment): certify assessment intelligence v1
Tag: assessment-v1-certified
```
