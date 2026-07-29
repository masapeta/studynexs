# Assessment Intelligence v1.0 Batch D Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Authorization ID: ASSESSMENT-V1-BATCH-D-AUTH-001
> Classification: Implementation authorization contract
> Program: Assessment Intelligence v1.0
> Batch: D - Question Bank and Reuse Readiness
> Implementation authorization: Authorized for Batch D only
> Runtime behavior changes: Not authorized
> Design baseline: [`ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_DESIGN_BRIEF.md`](./ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_DESIGN_BRIEF.md)
> ARM review: Accepted; Batch D may begin within this contract only

---

## 1. Purpose

Batch D exists to make question-bank reuse, provenance, blueprint-slot
suitability, gap-fill posture, approval lineage, and teacher-review boundaries
explicit before any runtime question-bank behavior is changed.

It should answer:

> Which reused questions are safe to present as approved school-private assets,
> which reuse cases require teacher review, and how do we prove reuse without
> turning previous approval into automatic future authority?

Batch D is a readiness foundation. It should not change teacher-visible
behavior.

---

## 2. Authorization status

This contract has been accepted by ARM.

It authorizes Batch D only. It does not authorize Batch E paper-to-evaluation
linkage, runtime question-bank behavior changes, UI changes, API changes, schema
changes, AEI behavior changes, EUI source adoption, product claim expansion, or
any consumer migration.

---

## 3. Baselines

This contract depends on:

- Assessment Intelligence v1.0 Production Readiness Review;
- Assessment Intelligence v1.0 Implementation Design Brief;
- Batch A Canonical Assessment Contract;
- Batch A Supported Scope Capability Matrix;
- Batch B Blueprint Readiness Design Brief;
- Batch B Blueprint Declaration Contract;
- Batch B Blueprint Supported Scope Declarations;
- Batch C Rubric and Model-Answer Readiness Design Brief;
- Batch C Rubric and Model-Answer Declaration Contract;
- Batch C Rubric and Model-Answer Supported Scope Declarations;
- Batch D Question Bank and Reuse Readiness Design Brief;
- frozen AEI v1 architecture;
- frozen EUI v1 architecture.

---

## 4. Batch D objective

Introduce the Question Bank and Reuse Readiness foundation:

1. question-bank/reuse declaration contract;
2. static/read-only question-bank reuse supported-scope declarations;
3. deterministic question-bank/reuse Golden Harness cases;
4. focused tests validating declaration structure, provenance, and posture;
5. Batch D certification report.

The result should make question reuse auditable without touching runtime
question-paper generation, approval, evaluation, or teacher-facing request paths.

---

## 5. Authorized implementation scope

Batch D may implement the following.

### 5.1 Question-bank/reuse declaration contract

Add a documentation artifact defining the question-bank/reuse declaration
schema.

The declaration must include:

- stable `bank_item_id`;
- `source_paper_id`;
- `source_question_bank_item_id` where reused;
- tenant/school scope;
- class and subject scope;
- board and grade scope;
- topic, concept, and Educational Identity posture where available;
- section and question identifiers;
- question text, marks, type, and options;
- question source;
- approval status;
- approval lineage;
- `content_fingerprint`;
- usage metadata;
- answer-key/rubric/model-answer posture;
- blueprint-slot match posture;
- gap-fill provenance;
- teacher-review requirement;
- product-claim posture.

### 5.2 Static question-bank reuse supported-scope declarations

Add static declarations for the initial supported scope.

Minimum declarations:

- supported approved-paper ingestion posture;
- supported idempotent re-approval posture;
- supported same-school approved-bank reuse posture;
- supported blueprint-slot compose posture when marks/type match;
- assist gap-fill posture when bank coverage is incomplete;
- manual-review changed-context reuse posture;
- unsupported cross-tenant reuse posture;
- unsupported draft/unapproved bank item reuse posture;
- expansion posture for future global or marketplace-style bank reuse.

These declarations must be read-only artifacts. They must not be wired into
runtime request paths in Batch D.

### 5.3 Deterministic reuse validation posture

Add deterministic validation logic only if it remains outside production request
paths.

Permitted validation may check:

- stable declaration IDs;
- known reuse support modes;
- required provenance fields;
- required tenant/school scope;
- approved-only support posture;
- source-paper lineage;
- source-bank-item lineage where reused;
- stable content fingerprint posture;
- usage metadata posture;
- blueprint marks match posture;
- blueprint question-type match posture;
- topic/concept/EUI posture where available;
- gap-fill provenance;
- teacher-review requirement;
- product-claim eligibility;
- AEI handoff posture;
- downstream approved-evidence posture.

This validation may live in tests or a pure test-support helper only if needed.
No production service behavior may depend on it in Batch D.

### 5.4 Golden Harness question-bank/reuse cases

Add Golden Harness cases for:

- approved-paper ingestion posture;
- idempotent re-approval posture;
- source paper provenance present;
- source bank item provenance present for reuse;
- stable content fingerprint posture;
- answer-key/rubric context carried where available;
- compose marks match;
- compose question-type match;
- compose topic/concept overlap posture;
- gap-fill assist provenance;
- changed-context reuse requiring review;
- draft/unapproved bank item unsupported;
- cross-tenant reuse unsupported;
- no autonomous grading, approval, parent evidence, or mastery from reuse.

### 5.5 Focused tests

Add focused tests validating:

- question-bank/reuse declarations load;
- declaration IDs are stable and unique;
- support modes are explicit;
- required provenance fields exist;
- approved-only support posture is enforced in declarations;
- tenant boundary posture is explicit;
- gap-fill is distinguishable from approved-bank reuse;
- changed-context reuse requires teacher review;
- unsupported and expansion declarations do not permit product claims;
- Golden Harness cases reference known declarations;
- no case implies autonomous grading, autonomous paper approval, direct marks,
  direct parent evidence, direct mastery update, AEI bypass, or EUI source
  adoption.

Focused tests may inspect existing model/service constants and pure helpers
where useful, but must not alter production runtime behavior.

### 5.6 Certification report

Produce:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_CERTIFICATION_REPORT.md`

The report should include:

- scope compliance;
- artifact inventory;
- validation evidence;
- question-bank provenance evidence;
- tenant-boundary posture;
- no runtime behavior change statement;
- schema/API/UI impact statement;
- AEI/EUI impact statement;
- risk assessment;
- recommendation.

---

## 6. Repository boundary

Modifications are limited to:

### Documentation

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_DECLARATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_QUESTION_BANK_REUSE_SUPPORTED_SCOPE_DECLARATIONS.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_CERTIFICATION_REPORT.md`
- this authorization contract, only to mark accepted status after ARM approval;
- supporting assessment-intelligence docs in the same directory if strictly
  necessary.

### Golden Harness data

- `apps/api/tests/golden/assessment_intelligence_v1/question_bank_reuse_readiness_cases.json`

### Tests

- `apps/api/tests/test_assessment_intelligence_v1_question_bank_reuse_readiness.py`

### Existing code inspection

Tests may import existing question-bank models, constants, and pure helpers from:

- `apps/api/app/db/models/question_bank.py`
- `apps/api/app/modules/ai/services/question_bank_service.py`

Batch D does not authorize editing those runtime files.

### Protected areas

Any changes outside the boundaries above require separate ARM authorization.

---

## 7. Explicitly not authorized

Batch D does not authorize:

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
- question generation behavior changes;
- question-paper generation behavior changes;
- question-bank service behavior changes;
- paper approval behavior changes;
- answer-sheet evaluation behavior changes;
- exam service behavior changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger behavior changes;
- parent/student visibility changes;
- principal analytics changes;
- mastery updates;
- browser workflow changes;
- public product claim expansion;
- global question bank;
- cross-school question marketplace;
- paid question marketplace;
- Batch E paper-to-evaluation linkage;
- broad board/grade/subject expansion.

---

## 8. Runtime constraints

Batch D should be effectively non-runtime.

If any code is added, it must be limited to tests or static artifact validation.
It must not execute in production request paths.

There should be:

- no new environment variables;
- no feature flags;
- no background jobs;
- no network calls;
- no database writes from new production code;
- no provider SDK calls;
- no LLM gateway calls.

---

## 9. Existing runtime posture

Existing question-bank runtime behavior must not be deleted, rewritten, or
replaced in Batch D.

Current useful behavior includes:

- `QuestionBankItem`;
- `RubricBankItem`;
- approved-paper bank ingestion;
- idempotent re-approval;
- `content_fingerprint`;
- same-school/class/subject compose candidate filtering;
- answer-key carryover;
- gap-fill merge;
- bank item usage tracking;
- question concept linking during bank ingestion.

Batch D may document this behavior and certify corresponding static
declarations. Runtime replacement, source switching, enforcement changes, or
behavior changes require a later contract.

---

## 10. AEI and EUI constraints

AEI remains the only academic answer-evaluation pipeline.

EUI architecture and runtime behavior remain unchanged.

Batch D must not:

- duplicate AEI evaluation logic;
- alter AEI contracts;
- alter AEI marks, policy, confidence, teacher review, or evidence behavior;
- weaken teacher authority;
- authorize unapproved downstream evidence;
- directly update marks, parent evidence, or mastery;
- reopen EUI source adoption;
- change EUI runtime behavior.

---

## 11. Validation requirements

Before ARM acceptance of Batch D implementation, the following evidence should
be produced:

- focused question-bank/reuse readiness tests pass;
- Golden Harness question-bank/reuse cases load and validate;
- no runtime imports changed;
- no API/schema/UI changes are present;
- `git diff --check` passes;
- relevant docs render/read cleanly;
- certification report is complete.

If practical in the current environment, also run adjacent assessment and AEI
tests:

- `apps/api/tests/test_assessment_intelligence_v1_contract.py`;
- `apps/api/tests/test_assessment_intelligence_v1_blueprint_readiness.py`;
- `apps/api/tests/test_assessment_intelligence_v1_rubric_model_answer_readiness.py`;
- `apps/api/tests/test_question_bank.py`;
- `apps/api/tests/test_question_bank_compose.py`;
- `apps/api/tests/test_answer_sheet_eval.py`;
- `apps/api/tests/test_academic_reasoning_engine.py`;
- `apps/api/tests/test_evaluation_policy.py`.

---

## 12. Rollback proof

Rollback for Batch D should be simple:

- remove the added Question Bank and Reuse Readiness documentation artifacts;
- remove the Golden Harness question-bank/reuse dataset;
- remove the focused question-bank/reuse readiness test file.

Because Batch D must not alter production runtime, rollback should not require:

- disabling flags;
- database rollback;
- schema downgrade;
- API versioning;
- data migration;
- tenant data cleanup.

---

## 13. Certification criteria

Batch D can be accepted only if the implementation proves:

- question-bank/reuse declaration contract exists;
- static question-bank/reuse declarations exist;
- support modes are explicit;
- declaration IDs are stable and unique;
- provenance requirements are deterministic;
- tenant boundary posture is explicit;
- approved-only support posture is explicit;
- source paper and source bank item lineage are represented;
- gap-fill provenance is distinguishable from approved-bank reuse;
- changed-context reuse requires teacher review;
- unsupported/expansion declarations do not become product claims;
- Golden Harness question-bank/reuse cases exist;
- focused tests validate the artifacts;
- no runtime behavior changed;
- no schema/API/UI changes were introduced;
- no AEI behavior changed;
- no EUI behavior changed;
- no autonomous grading or approval claim was introduced;
- no direct marks, direct parent evidence, or direct mastery update is implied;
- certification report is complete.

---

## 14. Suggested implementation metadata

If Batch D is implemented and accepted after code review, recommended commit
metadata:

```text
feat(assessment): add v1 question bank reuse readiness foundation
```

Recommended annotated tag:

```text
assessment-v1-batch-d-question-bank-reuse-readiness-certified
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
Implementation authorization: Granted for Batch D only
Runtime behavior changes: Not authorized
```

Implementation must remain within this contract. Any runtime question-bank
behavior change, paper-to-evaluation linkage, product claim expansion, Batch E
work, AEI behavior change, EUI source adoption, or consumer migration requires
separate ARM authorization.
