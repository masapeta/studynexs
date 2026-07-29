# Assessment Intelligence v1.0 Batch A Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Accepted  
> Classification: Implementation authorization contract  
> Program: Assessment Intelligence v1.0  
> Batch: A - Contract and Capability Matrix  
> Authorization ID: ASSESSMENT-V1-BATCH-A-AUTH-001  
> Implementation authorization: Authorized for Batch A only  
> Runtime behavior changes: Not authorized
> ARM review: Accepted; Batch A may begin within this contract only

---

## 1. Purpose

Batch A exists to freeze the minimum contract foundation for Assessment
Intelligence v1.0 before product-facing implementation begins.

It should answer:

> What is an assessment capability in StudyNexs, what contract do question
> papers/exams/evaluation/mastery share, and what supported scope may the
> product honestly claim?

Batch A is a foundation batch. It should not change user-visible behavior.

---

## 2. Baselines

This contract depends on the accepted planning artifacts:

- [`ASSESSMENT_INTELLIGENCE_V1_PRODUCTION_READINESS_REVIEW.md`](./ASSESSMENT_INTELLIGENCE_V1_PRODUCTION_READINESS_REVIEW.md)
- [`ASSESSMENT_INTELLIGENCE_V1_IMPLEMENTATION_DESIGN_BRIEF.md`](./ASSESSMENT_INTELLIGENCE_V1_IMPLEMENTATION_DESIGN_BRIEF.md)
- frozen AEI v1 architecture;
- frozen EUI v1 architecture;
- published AEI v1.0 supported-scope baseline;
- published EUI runtime foundation;
- deferred EUI source adoption posture.

---

## 3. Authorization status

This file is currently a draft contract.

Until ARM explicitly accepts this contract, Batch A implementation is not
authorized.

If accepted, this contract authorizes Batch A only. It does not authorize Batch
B, runtime behavior changes, or any source-of-truth switch.

---

## 4. Batch A objective

Introduce the Assessment Intelligence v1.0 foundation artifacts:

1. canonical assessment contract;
2. supported-scope capability matrix;
3. Golden Harness starter cases;
4. focused tests validating the contract/matrix artifacts;
5. Batch A certification report.

The result should be reviewable, testable, and reusable by later batches.

---

## 5. Authorized implementation scope

If accepted, Batch A may implement the following.

### 5.1 Canonical assessment contract

Add a contract artifact that defines the shared Assessment Intelligence fields
used across:

- question papers;
- question bank;
- exam question schemas;
- AEI evaluation inputs;
- teacher review;
- approved evidence;
- mastery/topic linkage.

The contract should include, at minimum:

- identity fields;
- curriculum fields;
- blueprint fields;
- question fields;
- answer key fields;
- rubric/model-answer fields;
- provenance fields;
- evaluation linkage fields;
- support posture fields.

This may be documentation-only unless a small test fixture or schema-like
example is required for Golden Harness validation.

### 5.2 Supported-scope capability matrix

Add an Assessment Intelligence v1.0 supported-scope matrix that declares:

- supported boards;
- supported grades;
- supported subjects;
- supported paper types;
- supported blueprint posture;
- supported language posture;
- rubric/model-answer posture;
- question bank posture;
- paper-to-evaluation linkage posture;
- unsupported/future scope.

The matrix must avoid universal claims.

### 5.3 Golden Harness starter cases

Add starter Golden Harness cases that validate the contract and matrix posture.

Cases should include:

- supported grounded question paper case;
- unsupported board/grade/subject posture case;
- blueprint internal-choice posture case;
- objective answer-key posture case;
- model-answer posture case;
- rubric/manual-review posture case;
- question-bank reuse posture case;
- paper-to-evaluation linkage posture case;
- multilingual unsupported or manual-review posture case.

These cases should validate metadata and posture only. They should not require
LLM calls, browser execution, provider credentials, database migrations, or
runtime feature enablement.

### 5.4 Focused tests

Add focused tests only for the Batch A artifacts.

Tests may validate:

- matrix loads;
- required fields exist;
- supported/unsupported postures are explicit;
- Golden Harness case IDs are stable;
- Golden Harness cases reference declared capabilities;
- no case implies autonomous grading;
- no case bypasses AEI for answer evaluation.

### 5.5 Certification report

Produce:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_A_CONTRACT_CAPABILITY_MATRIX_CERTIFICATION_REPORT.md`

The report should include:

- scope compliance;
- artifact list;
- validation evidence;
- no runtime behavior change statement;
- AEI impact statement;
- EUI impact statement;
- schema/API/UI impact statement;
- risk assessment;
- recommendation.

---

## 6. Repository boundary

If accepted, modifications are limited to:

### Documentation

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_CANONICAL_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_A_CONTRACT_CAPABILITY_MATRIX_CERTIFICATION_REPORT.md`
- this authorization contract, only to mark accepted status after ARM approval;
- supporting assessment-intelligence docs in the same directory if strictly
  necessary.

### Golden Harness data

- `apps/api/tests/golden/assessment_intelligence_v1/assessment_contract_cases.json`

### Tests

- `apps/api/tests/test_assessment_intelligence_v1_contract.py`

### Protected areas

Any changes outside the boundaries above require separate ARM authorization.

---

## 7. Explicitly not authorized

Batch A does not authorize:

- database schema changes;
- Alembic migrations;
- API contract changes;
- public endpoint changes;
- UI changes;
- runtime behavior changes;
- feature flag changes;
- AI provider changes;
- LLM inference;
- OCR behavior changes;
- question paper generation behavior changes;
- question bank runtime behavior changes;
- exam service behavior changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence ledger behavior changes;
- parent/student visibility changes;
- principal analytics changes;
- browser workflow changes;
- public product claims;
- implementation of Batch B or later.

---

## 8. Runtime constraints

Batch A should be effectively non-runtime.

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

## 9. AEI and EUI constraints

AEI remains the only academic answer-evaluation pipeline.

Batch A must not:

- duplicate AEI evaluation logic;
- alter AEI contracts;
- weaken teacher authority;
- authorize unapproved downstream evidence;
- reopen EUI source adoption;
- change EUI runtime behavior.

Assessment Intelligence may describe how later batches should consume AEI/EUI,
but it must not modify those consumers in Batch A.

---

## 10. Validation requirements

Before ARM acceptance of Batch A implementation, the following evidence should
be produced:

- focused contract/matrix tests pass;
- Golden Harness starter cases load and validate;
- no runtime imports changed;
- no API/schema/UI changes are present;
- `git diff --check` passes;
- relevant docs render/read cleanly;
- certification report is complete.

If possible within the current environment, also run:

- targeted `pytest` for the new test file;
- adjacent existing assessment tests where practical:
  - `apps/api/tests/test_assessment_grounding.py`
  - `apps/api/tests/test_question_paper.py`
  - `apps/api/tests/test_question_bank.py`
  - `apps/api/tests/test_question_bank_compose.py`
  - `apps/api/tests/test_exam_questions.py`

---

## 11. Rollback proof

Rollback for Batch A should be simple:

- remove the added documentation artifacts;
- remove the Golden Harness starter dataset;
- remove the focused test file.

Because Batch A must not alter production runtime, rollback should not require:

- disabling flags;
- database rollback;
- schema downgrade;
- API versioning;
- data migration;
- tenant data cleanup.

---

## 12. Certification criteria

Batch A can be accepted only if the implementation proves:

- canonical assessment contract exists;
- supported-scope matrix exists;
- Golden Harness starter cases exist;
- focused tests validate the artifacts;
- no runtime behavior changed;
- no schema/API/UI changes were introduced;
- no AEI behavior changed;
- no EUI behavior changed;
- no autonomous grading claim was introduced;
- no public product claim was broadened;
- certification report is complete.

---

## 13. Suggested implementation metadata

If Batch A is implemented and accepted after code review, recommended commit
metadata:

```text
feat(assessment): add v1 contract and capability matrix foundation
```

Recommended annotated tag:

```text
assessment-v1-batch-a-contract-capability-matrix-certified
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

ARM may choose one of three decisions after reviewing this contract:

1. Accept and authorize Batch A implementation within this contract only.
2. Accept with conditions.
3. Reject and request revision.

Until ARM chooses option 1 or 2 explicitly, no Batch A implementation is
authorized.
