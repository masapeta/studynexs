# Assessment Intelligence v1.0 Batch G Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Authorization ID: ASSESSMENT-V1-BATCH-G-AUTH-001
> Classification: Implementation authorization contract
> Program: Assessment Intelligence v1.0
> Batch: G - Teacher Workflow / Browser Proof
> Implementation authorization: Authorized for Batch G only
> Runtime behavior changes: Not authorized
> Design baseline: [`ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_DESIGN_BRIEF.md`](./ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_DESIGN_BRIEF.md)
> ARM review: Accepted; Batch G may begin within this contract only

---

## 1. Purpose

Batch G exists to prove the supported Assessment Intelligence v1.0 teacher
workflow in the browser.

It should answer:

> Can a teacher or authorized staff member navigate the supported assessment
> workflow, verify the certified readiness posture, link approved assessment
> artifacts toward evaluation, and preserve teacher authority without runtime
> regressions?

Batch G is a browser-proof and certification batch. It is not a feature
expansion batch.

---

## 2. Authorization status

This contract has been accepted by ARM.

It authorizes Batch G implementation within this contract only.

This contract authorizes only the narrow browser proof foundation described
below. It does not authorize product behavior changes, schema changes, API
changes, UI redesigns, marks changes, evidence-ledger changes, AEI behavior
changes, EUI source adoption, or public product claim expansion.

---

## 3. Baselines

This contract depends on:

- Assessment Intelligence v1.0 Production Readiness Review;
- Assessment Intelligence v1.0 Implementation Design Brief;
- Batch A Canonical Assessment Contract and Supported Scope Capability Matrix;
- Batch B Blueprint Readiness foundation;
- Batch C Rubric and Model-Answer Readiness foundation;
- Batch D Question Bank and Reuse Readiness foundation;
- Batch E Paper-to-Evaluation Linkage Readiness foundation;
- Batch F Bilingual / Multilingual Assessment Readiness foundation;
- AEI v1.0 Certification;
- AEI Teacher Evaluation UX-A through UX-E certification;
- Operational Proof baseline;
- Topic-ID / Mastery Spine passive resolution baseline;
- frozen AEI v1 architecture;
- frozen EUI v1 architecture.

---

## 4. Batch G objective

Introduce the Assessment Intelligence v1.0 Teacher Workflow / Browser Proof
foundation:

1. a deterministic browser proof scenario for the supported teacher workflow;
2. a browser harness or harness extension for the Assessment Intelligence flow;
3. screenshot and/or trace evidence capture;
4. console/API/tenant guard evidence;
5. supported-scope and no-overclaim assertions;
6. focused validation evidence;
7. Batch G certification report.

The result should prove the existing teacher-facing assessment workflow without
changing production behavior.

---

## 5. Authorized implementation scope

Batch G may implement the following only.

### 5.1 Browser proof scenario

Define a deterministic browser proof scenario for:

```text
SSC / Telangana reference material / Grade 6 / Science / Unit Test / English
```

The proof may also include a secondary smoke scenario for:

```text
SSC / Reference curriculum / Grade 10 / Mathematics / Unit Test or Term-style paper / English
```

The secondary scenario is optional. The primary scenario is required unless ARM
explicitly revises the contract.

### 5.2 Browser proof harness

Add or extend browser-proof code for Assessment Intelligence v1.0.

Permitted behavior:

- authenticate through the existing e2e harness pattern;
- navigate existing teacher/staff surfaces;
- verify page rendering;
- verify tenant context;
- verify absence of blocking console/API failures;
- verify certified supported-scope language/readiness posture where visible or
  inspectable;
- verify teacher authority messaging or posture where visible;
- verify paper-to-exam/evaluation navigation where existing data permits;
- capture screenshots or trace artifacts.

Browser proof should prefer deterministic existing/reference data over live AI
generation.

### 5.3 Deterministic fixture/reference strategy

Batch G may define deterministic fixture assumptions or reference-tenant
requirements for browser proof.

Permitted fixture posture:

- use existing Reference tenant data where available;
- use existing approved papers/exams where available;
- document missing prerequisite data as a certification blocker;
- add test-only harness fixtures only if they do not change production runtime.

Batch G does not authorize production seed-data changes, database migrations, or
tenant data mutations outside an explicitly test-scoped harness flow.

### 5.4 Product-claim assertions

Browser proof should assert that the product does not present unsupported claims
as supported.

Minimum checks:

- English remains the supported paper-language baseline;
- bilingual/multilingual universal support is not claimed;
- teacher approval remains required for authoritative outcomes;
- AEI remains the answer-evaluation path;
- parent/student evidence is not exposed before teacher-approved outcomes.

### 5.5 Certification report

Produce:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_CERTIFICATION_REPORT.md`

The report should include:

- scope compliance;
- browser proof scenario;
- environment assumptions;
- commands run;
- screenshot/trace artifact location;
- route list exercised;
- console/API/tenant guard evidence;
- supported-scope assertion evidence;
- teacher-authority evidence;
- no-overclaim evidence;
- validation evidence;
- no runtime behavior change statement;
- schema/API/UI impact statement;
- AEI/EUI impact statement;
- risk assessment;
- recommendation.

---

## 6. Repository boundary

Modifications are limited to:

### Documentation

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_DESIGN_BRIEF.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_CERTIFICATION_REPORT.md`

### Browser proof harness

- `apps/admin-web/e2e-assessment-intelligence-v1.cjs`
- `apps/admin-web/e2e-harness-utils.cjs`, only if a small reusable guard or
  helper is required;
- `apps/admin-web/package.json`, only to add a script for the Batch G browser
  proof command if needed.

### Tests / validation

- `apps/api/tests/test_assessment_intelligence_v1_contract.py`
- `apps/api/tests/test_assessment_intelligence_v1_blueprint_readiness.py`
- `apps/api/tests/test_assessment_intelligence_v1_rubric_model_answer_readiness.py`
- `apps/api/tests/test_assessment_intelligence_v1_question_bank_reuse_readiness.py`
- `apps/api/tests/test_assessment_intelligence_v1_paper_to_evaluation_linkage_readiness.py`
- `apps/api/tests/test_assessment_intelligence_v1_bilingual_multilingual_readiness.py`
- AEI regression tests only as validation commands, not edited unless separately
  authorized.

Batch G does not authorize editing production API, service, schema, UI page, or
database files.

### Generated proof artifacts

Screenshots or Playwright traces may be generated locally. They should not be
committed unless the implementation contract or ARM review explicitly requires
committed proof artifacts.

### Protected areas

Any changes outside the boundaries above require separate ARM authorization.

---

## 7. Explicitly not authorized

Batch G does not authorize:

- database schema changes;
- Alembic migrations;
- API contract changes;
- public endpoint changes;
- production UI page changes;
- UI redesign;
- runtime product behavior changes;
- production feature flags;
- AI provider changes;
- LLM inference changes;
- LLM prompt changes;
- OCR behavior changes;
- translation behavior changes;
- question-paper generation behavior changes;
- blueprint behavior changes;
- question-bank service behavior changes;
- exam service behavior changes;
- answer-sheet evaluation behavior changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger behavior changes;
- parent/student visibility changes;
- principal analytics changes;
- mastery updates;
- public product claim expansion;
- Assessment Intelligence v1.0 final certification Batch H.

---

## 8. Runtime constraints

Batch G should not introduce new production runtime paths.

Browser proof may exercise existing runtime behavior, but it must not:

- change production source code;
- rely on hidden production state changes;
- call provider SDKs directly;
- bypass the AI gateway;
- bypass authentication;
- bypass tenant scoping;
- bypass teacher authority;
- create authoritative marks;
- publish unapproved evidence.

If the browser proof needs test data, the implementation should document the
requirement and stop if creating that data would require unauthorized behavior
changes.

---

## 9. Browser proof requirements

The Batch G browser proof should verify:

- authenticated staff/teacher route access;
- tenant context preserved;
- AI Papers route renders;
- Exams route renders;
- evaluation route renders for a linked or existing exam where available;
- supported scope is visible or verifiable;
- paper status / approval posture is visible or verifiable;
- question schema / marks posture is visible or verifiable;
- AEI remains the evaluation path;
- teacher final authority remains visible or verifiable;
- unsupported bilingual/multilingual claims are not shown as supported;
- no blocking console errors;
- no unexpected API failures;
- screenshot or trace evidence captured.

Where a route cannot be exercised because reference data is missing, the
certification report must record that as a blocker rather than claiming proof.

---

## 10. Validation requirements

Before ARM acceptance of Batch G implementation, the following evidence should
be produced where practical:

### Frontend

- `npm run build`;
- focused lint for touched browser-harness files;
- Batch G browser proof command;
- screenshot/trace evidence;
- console/API guard evidence;
- tenant guard evidence.

### Backend / regression

- `python -c "import app.main"`;
- focused Assessment Intelligence v1.0 tests from Batches A-F;
- focused AEI tests where evaluation path is exercised;
- `git diff --check`.

### Documentation

- certification report complete;
- design brief and contract statuses correct;
- no unsupported product claim expansion.

---

## 11. Rollback proof

Rollback for Batch G should be simple:

- remove the added browser proof harness file;
- remove any package script added for the browser proof command;
- remove the certification report;
- revert any documentation status changes.

Because Batch G must not alter production runtime behavior, rollback should not
require:

- database rollback;
- API versioning;
- feature flag disablement;
- tenant data cleanup;
- evidence-ledger cleanup;
- marks cleanup.

---

## 12. Certification criteria

Batch G can be accepted only if the implementation proves:

- browser proof executed against the supported teacher assessment flow;
- evidence artifacts were captured or their absence is explicitly justified;
- tenant context remained intact;
- console/API guards passed or failures were resolved;
- teacher authority remained intact;
- AEI remained the answer-evaluation path;
- unsupported bilingual/multilingual claims were not surfaced as supported;
- no production UI/API/schema/runtime behavior changed;
- no marks, evidence-ledger, teacher routing, parent/student visibility, or
  mastery behavior changed;
- focused frontend/backend validation passed;
- certification report is complete.

---

## 13. Suggested implementation metadata

If Batch G is implemented and accepted after code review, recommended commit
metadata:

```text
feat(assessment): add v1 teacher workflow browser proof
```

Recommended annotated tag:

```text
assessment-v1-batch-g-teacher-workflow-browser-proof-certified
```

Publication should follow the established sequence:

```text
commit
tag
push develop
push tag
update docs/STATUS.md separately as docs-only post-publication commit
```

---

## 14. ARM gate

ARM decision:

```text
Decision: Accepted
Implementation authorization: Granted for Batch G only
```

Implementation may begin within this contract only.
