# Assessment Intelligence v1.0 Batch B Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Accepted  
> Authorization ID: ASSESSMENT-V1-BATCH-B-AUTH-001  
> Classification: Implementation authorization contract  
> Program: Assessment Intelligence v1.0  
> Batch: B - Blueprint Readiness  
> Implementation authorization: Authorized for Batch B only  
> Runtime behavior changes: Not authorized  
> Design baseline: [`ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_DESIGN_BRIEF.md`](./ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_DESIGN_BRIEF.md)
> ARM review: Accepted; Batch B may begin within this contract only

---

## 1. Purpose

Batch B exists to make assessment blueprint behavior explicit, deterministic,
and non-universal before any runtime generation behavior is changed.

It should answer:

> Which assessment blueprints does StudyNexs support, how are they declared, and
> how do we prove the structure without turning a code helper into a product
> claim?

Batch B is a readiness foundation. It should not change teacher-visible
behavior.

---

## 2. Authorization status

This contract has been accepted by ARM.

It authorizes Batch B only. It does not authorize Batch C rubric/model-answer
work, runtime blueprint adoption, question-paper generation changes, or product
claim expansion.

---

## 3. Baselines

This contract depends on:

- Assessment Intelligence v1.0 Production Readiness Review;
- Assessment Intelligence v1.0 Implementation Design Brief;
- Batch A Canonical Assessment Contract;
- Batch A Supported Scope Capability Matrix;
- Batch B Blueprint Readiness Design Brief;
- frozen AEI v1 architecture;
- frozen EUI v1 architecture.

---

## 4. Batch B objective

Introduce the Blueprint Readiness foundation:

1. blueprint declaration contract;
2. static/read-only blueprint declarations for the initial supported scope;
3. deterministic blueprint Golden Harness cases;
4. focused tests validating declaration structure and calculation posture;
5. Batch B certification report.

The result should make paper structure auditable without touching runtime
generation paths.

---

## 5. Authorized implementation scope

Batch B may implement the following.

### 5.1 Blueprint declaration contract

Add a documentation artifact defining the blueprint declaration schema.

The declaration must include:

- stable `blueprint_id`;
- board;
- curriculum;
- grade;
- subject;
- paper type;
- version;
- support mode;
- total marks;
- duration;
- ordered sections;
- internal-choice posture;
- validation rules;
- product-claim posture.

### 5.2 Static blueprint declarations

Add static blueprint declarations for the initial supported scope.

Minimum declarations:

- supported Grade 10 Mathematics term-style/internal-choice blueprint;
- supported Grade 6 Science unit-test blueprint;
- manual-review or assist posture for school-custom blueprint;
- unsupported universal blueprint claim;
- expansion posture for future board/grade/subject coverage.

These declarations must be read-only artifacts. They must not be wired into
runtime request paths in Batch B.

### 5.3 Deterministic blueprint validation posture

Add deterministic validation logic only if it remains outside production
request paths.

Permitted validation may calculate:

- printed question count;
- answer-required question count;
- printed marks total;
- effective answer-required marks total;
- internal-choice posture;
- MCQ option requirements;
- product-claim eligibility.

This validation may live in tests or a pure test-support module only if needed.
No production service behavior may depend on it in Batch B.

### 5.4 Golden Harness blueprint cases

Add Golden Harness cases for:

- supported blueprint declaration loads;
- internal-choice effective marks calculation;
- printed total vs answer-required total distinction;
- unsupported blueprint posture;
- expansion blueprint posture;
- MCQ option requirement posture;
- requested-total mismatch posture;
- teacher-review requirement for assist/manual-review blueprints;
- no autonomous grading or approval from blueprint support.

### 5.5 Focused tests

Add focused tests validating:

- blueprint declarations load;
- declaration IDs are stable and unique;
- required fields exist;
- support modes are explicit;
- internal-choice calculations are deterministic;
- unsupported/expansion declarations do not permit product claims;
- Golden Harness cases reference known declarations;
- no case implies autonomous grading, autonomous approval, or AEI bypass.

### 5.6 Certification report

Produce:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_CERTIFICATION_REPORT.md`

The report should include:

- scope compliance;
- artifact inventory;
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

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_DECLARATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BLUEPRINT_SUPPORTED_SCOPE_DECLARATIONS.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_CERTIFICATION_REPORT.md`
- this authorization contract, only to mark accepted status after ARM approval;
- supporting assessment-intelligence docs in the same directory if strictly
  necessary.

### Golden Harness data

- `apps/api/tests/golden/assessment_intelligence_v1/blueprint_readiness_cases.json`

### Tests

- `apps/api/tests/test_assessment_intelligence_v1_blueprint_readiness.py`

### Protected areas

Any changes outside the boundaries above require separate ARM authorization.

---

## 7. Explicitly not authorized

Batch B does not authorize:

- database schema changes;
- Alembic migrations;
- API contract changes;
- public endpoint changes;
- UI changes;
- runtime behavior changes;
- feature flags;
- AI provider changes;
- LLM inference;
- LLM prompt changes;
- runtime blueprint source switching;
- question-paper generation behavior changes;
- question-bank runtime behavior changes;
- exam service behavior changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger behavior changes;
- parent/student visibility changes;
- principal analytics changes;
- browser workflow changes;
- public product claim expansion;
- Batch C rubric/model-answer work;
- broad board/grade/subject expansion.

---

## 8. Runtime constraints

Batch B should be effectively non-runtime.

If any code is added, it must be limited to tests or static artifact validation.
It must not execute in production request paths.

There should be:

- no new environment variables;
- no feature flags;
- no background jobs;
- no network calls;
- no database writes;
- no provider SDK calls;
- no LLM gateway calls.

---

## 9. Existing helper posture

The existing `_ssc_blueprint(total_marks)` helper in
`question_paper_service.py` must not be deleted, rewritten, or wired to a new
runtime source in Batch B.

Batch B may document its current behavior and certify corresponding static
declarations. Runtime replacement or adoption requires a later contract.

---

## 10. AEI and EUI constraints

AEI remains the only academic answer-evaluation pipeline.

EUI architecture and runtime behavior remain unchanged.

Batch B must not:

- duplicate AEI evaluation logic;
- alter AEI contracts;
- weaken teacher authority;
- authorize unapproved downstream evidence;
- reopen EUI source adoption;
- change EUI runtime behavior.

---

## 11. Validation requirements

Before ARM acceptance of Batch B implementation, the following evidence should
be produced:

- focused blueprint-readiness tests pass;
- Golden Harness blueprint cases load and validate;
- no runtime imports changed;
- no API/schema/UI changes are present;
- `git diff --check` passes;
- relevant docs render/read cleanly;
- certification report is complete.

If practical in the current environment, also run adjacent assessment tests:

- `apps/api/tests/test_assessment_intelligence_v1_contract.py`;
- `apps/api/tests/test_question_paper.py`;
- `apps/api/tests/test_question_bank_compose.py`;
- `apps/api/tests/test_assessment_grounding.py`;
- `apps/api/tests/test_exam_questions.py`.

---

## 12. Rollback proof

Rollback for Batch B should be simple:

- remove the added Blueprint Readiness documentation artifacts;
- remove the Golden Harness blueprint dataset;
- remove the focused blueprint-readiness test file.

Because Batch B must not alter production runtime, rollback should not require:

- disabling flags;
- database rollback;
- schema downgrade;
- API versioning;
- data migration;
- tenant data cleanup.

---

## 13. Certification criteria

Batch B can be accepted only if the implementation proves:

- blueprint declaration contract exists;
- static blueprint declarations exist;
- support modes are explicit;
- declaration IDs are stable and unique;
- internal-choice behavior is deterministic;
- unsupported/expansion declarations do not become product claims;
- Golden Harness blueprint cases exist;
- focused tests validate the artifacts;
- no runtime behavior changed;
- no schema/API/UI changes were introduced;
- no AEI behavior changed;
- no EUI behavior changed;
- no autonomous grading or approval claim was introduced;
- certification report is complete.

---

## 14. Suggested implementation metadata

If Batch B is implemented and accepted after code review, recommended commit
metadata:

```text
feat(assessment): add v1 blueprint readiness foundation
```

Recommended annotated tag:

```text
assessment-v1-batch-b-blueprint-readiness-certified
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

## 15. ARM gate

ARM decision:

```text
Decision: Accepted
Implementation authorization: Granted for Batch B only
Runtime behavior changes: Not authorized
```

Implementation must remain within this contract. Any runtime adoption,
question-paper generation behavior change, product claim expansion, Batch C
rubric/model-answer work, or consumer migration requires separate ARM
authorization.
