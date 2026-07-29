# Assessment Intelligence v1.0 Batch C Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Status: Accepted  
> Authorization ID: ASSESSMENT-V1-BATCH-C-AUTH-001  
> Classification: Implementation authorization contract  
> Program: Assessment Intelligence v1.0  
> Batch: C - Rubric and Model-Answer Readiness  
> Implementation authorization: Authorized for Batch C only  
> Runtime behavior changes: Not authorized  
> Design baseline: [`ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_DESIGN_BRIEF.md`](./ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_DESIGN_BRIEF.md)
> ARM review: Accepted; Batch C may begin within this contract only

---

## 1. Purpose

Batch C exists to make answer keys, model answers, acceptable answers, rubric
posture, checklist posture, manual-review posture, and unsupported posture
explicit before any runtime evaluation behavior is changed.

It should answer:

> Which rubric and answer-context postures does StudyNexs support, how are they
> declared, and how do we prove the posture without creating a parallel
> evaluator?

Batch C is a readiness foundation. It should not change teacher-visible
behavior.

---

## 2. Authorization status

This contract has been accepted by ARM.

It authorizes Batch C only. It does not authorize Batch D question-bank/reuse
readiness, runtime rubric adoption, answer-sheet evaluation behavior changes,
AEI behavior changes, or product claim expansion.

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
- frozen AEI v1 architecture;
- frozen EUI v1 architecture.

---

## 4. Batch C objective

Introduce the Rubric and Model-Answer Readiness foundation:

1. rubric/model-answer declaration contract;
2. static/read-only rubric supported-scope declarations;
3. deterministic rubric/model-answer Golden Harness cases;
4. focused tests validating declaration structure and posture;
5. Batch C certification report.

The result should make expected answer context auditable without touching
runtime evaluation paths.

---

## 5. Authorized implementation scope

Batch C may implement the following.

### 5.1 Rubric/model-answer declaration contract

Add a documentation artifact defining the rubric/model-answer declaration
schema.

The declaration must include:

- stable `rubric_id`;
- related `blueprint_id` where available;
- question number or slot;
- question type;
- marks;
- rubric posture;
- answer key where applicable;
- model answer where applicable;
- acceptable answers where applicable;
- numeric tolerance where applicable;
- unit posture where applicable;
- scientific-notation posture where applicable;
- criteria where applicable;
- checklist items where applicable;
- manual-review reason where applicable;
- unsupported reason where applicable;
- AEI handoff posture;
- teacher-authority posture;
- product-claim posture.

### 5.2 Static rubric supported-scope declarations

Add static rubric/model-answer declarations for the initial supported scope.

Minimum declarations:

- supported objective-key posture for Grade 10 Mathematics MCQ;
- supported numeric-answer posture for Grade 10 Mathematics numeric answer;
- supported acceptable-answer variants for Grade 10 Mathematics numeric answer;
- supported tolerance/unit/scientific-notation posture where deterministic;
- assist model-answer posture for Grade 6 Science short answer;
- manual-review criterion-rubric posture for Grade 6 Science long answer;
- checklist posture for visual/science diagram or map evidence;
- manual-review posture for missing or weak answer key;
- unsupported universal subjective-grading claim;
- expansion posture for future rubric/capability coverage.

These declarations must be read-only artifacts. They must not be wired into
runtime request paths in Batch C.

### 5.3 Deterministic rubric validation posture

Add deterministic validation logic only if it remains outside production
request paths.

Permitted validation may check:

- stable rubric IDs;
- known rubric postures;
- answer-key presence for objective/numeric postures;
- MCQ option posture where applicable;
- model-answer presence for model-answer posture;
- criteria marks sum for criterion-rubric posture;
- checklist item presence for checklist posture;
- manual-review reason presence for manual-review posture;
- unsupported reason presence for unsupported posture;
- product-claim eligibility;
- AEI evaluation pipeline posture;
- teacher-authority posture;
- downstream approved-evidence posture.

This validation may live in tests or a pure test-support module only if needed.
No production service behavior may depend on it in Batch C.

### 5.4 Golden Harness rubric/model-answer cases

Add Golden Harness cases for:

- objective-key supported posture;
- numeric-answer supported posture with tolerance;
- acceptable-answer variants;
- unit posture;
- scientific-notation posture;
- model-answer assist posture;
- criterion-rubric manual-review posture;
- checklist-only visual/science posture;
- missing answer key manual-review posture;
- unsupported universal subjective-grading posture;
- no autonomous grading or approval from any rubric posture.

### 5.5 Focused tests

Add focused tests validating:

- rubric/model-answer declarations load;
- declaration IDs are stable and unique;
- required fields exist;
- support modes are explicit;
- answer-key/model-answer/criteria/checklist requirements are deterministic;
- criteria marks sum to question marks where applicable;
- unsupported/expansion declarations do not permit product claims;
- Golden Harness cases reference known declarations;
- no case implies autonomous grading, autonomous approval, direct marks,
  direct parent evidence, direct mastery update, or AEI bypass.

### 5.6 Certification report

Produce:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_CERTIFICATION_REPORT.md`

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

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_DECLARATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_RUBRIC_MODEL_ANSWER_SUPPORTED_SCOPE_DECLARATIONS.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_CERTIFICATION_REPORT.md`
- this authorization contract, only to mark accepted status after ARM approval;
- supporting assessment-intelligence docs in the same directory if strictly
  necessary.

### Golden Harness data

- `apps/api/tests/golden/assessment_intelligence_v1/rubric_model_answer_readiness_cases.json`

### Tests

- `apps/api/tests/test_assessment_intelligence_v1_rubric_model_answer_readiness.py`

### Protected areas

Any changes outside the boundaries above require separate ARM authorization.

---

## 7. Explicitly not authorized

Batch C does not authorize:

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
- rubric generation;
- runtime rubric source switching;
- answer-sheet evaluation behavior changes;
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
- Batch D question-bank/reuse readiness;
- broad board/grade/subject/rubric expansion.

---

## 8. Runtime constraints

Batch C should be effectively non-runtime.

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

## 9. Existing runtime posture

Existing rubric-related runtime behavior must not be deleted, rewritten, or
replaced in Batch C.

Current useful behavior includes:

- `RubricBankItem` answer-key storage;
- answer-key ingestion from approved papers;
- `fetch_rubrics_for_paper`;
- objective answer-key evaluation;
- subjective/model-answer assist;
- AEI Maths normalization metadata using answer keys, acceptable answers,
  tolerance, and unit posture;
- visual/science checklist metadata where already present.

Batch C may document this behavior and certify corresponding static
declarations. Runtime replacement, source switching, or behavior change requires
a later contract.

---

## 10. AEI and EUI constraints

AEI remains the only academic answer-evaluation pipeline.

EUI architecture and runtime behavior remain unchanged.

Batch C must not:

- duplicate AEI evaluation logic;
- alter AEI contracts;
- weaken teacher authority;
- authorize unapproved downstream evidence;
- directly update marks, parent evidence, or mastery;
- reopen EUI source adoption;
- change EUI runtime behavior.

---

## 11. Validation requirements

Before ARM acceptance of Batch C implementation, the following evidence should
be produced:

- focused rubric/model-answer readiness tests pass;
- Golden Harness rubric/model-answer cases load and validate;
- no runtime imports changed;
- no API/schema/UI changes are present;
- `git diff --check` passes;
- relevant docs render/read cleanly;
- certification report is complete.

If practical in the current environment, also run adjacent assessment and AEI
tests:

- `apps/api/tests/test_assessment_intelligence_v1_contract.py`;
- `apps/api/tests/test_assessment_intelligence_v1_blueprint_readiness.py`;
- `apps/api/tests/test_question_bank.py`;
- `apps/api/tests/test_question_bank_compose.py`;
- `apps/api/tests/test_answer_sheet_eval.py`;
- `apps/api/tests/test_academic_reasoning_engine.py`;
- `apps/api/tests/test_evaluation_policy.py`.

---

## 12. Rollback proof

Rollback for Batch C should be simple:

- remove the added Rubric and Model-Answer Readiness documentation artifacts;
- remove the Golden Harness rubric/model-answer dataset;
- remove the focused rubric/model-answer readiness test file.

Because Batch C must not alter production runtime, rollback should not require:

- disabling flags;
- database rollback;
- schema downgrade;
- API versioning;
- data migration;
- tenant data cleanup.

---

## 13. Certification criteria

Batch C can be accepted only if the implementation proves:

- rubric/model-answer declaration contract exists;
- static rubric/model-answer declarations exist;
- support modes are explicit;
- declaration IDs are stable and unique;
- answer-key/model-answer/criteria/checklist requirements are deterministic;
- criteria marks sum validation exists where applicable;
- unsupported/expansion declarations do not become product claims;
- Golden Harness rubric/model-answer cases exist;
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

If Batch C is implemented and accepted after code review, recommended commit
metadata:

```text
feat(assessment): add v1 rubric model-answer readiness foundation
```

Recommended annotated tag:

```text
assessment-v1-batch-c-rubric-model-answer-readiness-certified
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
Implementation authorization: Granted for Batch C only
Runtime behavior changes: Not authorized
```

Implementation must remain within this contract. Any runtime adoption,
answer-sheet evaluation behavior change, product claim expansion, Batch D
question-bank/reuse work, or consumer migration requires separate ARM
authorization.
