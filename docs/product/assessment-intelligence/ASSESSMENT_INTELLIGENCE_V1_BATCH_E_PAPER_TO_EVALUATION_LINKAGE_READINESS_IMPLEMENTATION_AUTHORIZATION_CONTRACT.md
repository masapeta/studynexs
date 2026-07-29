# Assessment Intelligence v1.0 Batch E Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Authorization ID: ASSESSMENT-V1-BATCH-E-AUTH-001
> Classification: Implementation authorization contract
> Program: Assessment Intelligence v1.0
> Batch: E - Paper-to-Evaluation Linkage Readiness
> Implementation authorization: Authorized for Batch E only
> Runtime behavior changes: Not authorized
> Design baseline: [`ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_READINESS_DESIGN_BRIEF.md`](./ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_READINESS_DESIGN_BRIEF.md)
> ARM review: Accepted; Batch E may begin within this contract only

---

## 1. Purpose

Batch E exists to make the approved-paper-to-evaluation path explicit,
testable, and teacher-governed before broader assessment flows depend on it.

It should answer:

> Which approved paper, exam schema, rubric context, answer input, AEI assist,
> teacher approval, evidence, marks, and mastery links are safe to treat as
> evaluation-ready, and how do we prove that no authority bypass occurs?

Batch E is a readiness foundation. It should not change teacher-visible
behavior.

---

## 2. Authorization status

This contract has been accepted by ARM.

It authorizes Batch E only. It does not authorize Batch F work, runtime
evaluation behavior changes, UI changes, API changes, schema changes, AEI
grading changes, EUI source adoption, product claim expansion, or consumer
migration.

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
- Batch D Question Bank and Reuse Declaration Contract;
- Batch D Question Bank and Reuse Supported Scope Declarations;
- Batch E Paper-to-Evaluation Linkage Readiness Design Brief;
- frozen AEI v1 architecture;
- frozen EUI v1 architecture.

---

## 4. Batch E objective

Introduce the Paper-to-Evaluation Linkage Readiness foundation:

1. paper-to-evaluation linkage declaration contract;
2. static/read-only linkage supported-scope declarations;
3. deterministic linkage Golden Harness cases;
4. focused tests validating linkage structure, support modes, and authority
   boundaries;
5. Batch E certification report.

The result should make approved-paper-to-evaluation linkage auditable without
touching exam creation, answer-sheet evaluation, teacher approval, marks,
evidence, mastery, API, schema, or UI behavior.

---

## 5. Authorized implementation scope

Batch E may implement the following.

### 5.1 Paper-to-evaluation linkage declaration contract

Add a documentation artifact defining the linkage declaration schema.

The declaration must include:

- stable `linkage_id`;
- tenant/school scope;
- `exam_id`;
- `source_paper_id`;
- `source_paper_status`;
- question-schema source and posture;
- question numbers;
- per-question max marks;
- topic/concept posture;
- Educational Identity posture where available;
- rubric/model-answer/answer-key source posture;
- OCR input posture;
- manual input posture;
- `can_evaluate_sheets` posture;
- AEI assist posture;
- teacher-review requirement;
- approved-evidence requirement;
- marks source;
- mastery source;
- product-claim posture.

### 5.2 Static paper-to-evaluation supported-scope declarations

Add static declarations for the initial supported scope.

Minimum declarations:

- supported same-tenant approved-paper-to-exam-schema linkage;
- supported source-paper-plus-schema evaluation-readiness posture;
- supported rubric/model-answer context handoff through linked source paper
  where Batch C context exists;
- assist OCR answer-input posture;
- assist manual answer-input posture;
- manual-review manual-schema-without-source-paper posture;
- unsupported draft/unapproved source paper posture;
- unsupported cross-tenant source paper posture;
- unsupported missing-question-schema posture;
- unsupported autonomous marks posture;
- unsupported downstream evidence before teacher approval posture;
- expansion posture for broader future paper/evaluation modes.

These declarations must be read-only artifacts. They must not be wired into
runtime request paths in Batch E.

### 5.3 Deterministic linkage validation posture

Add deterministic validation logic only if it remains outside production request
paths.

Permitted validation may check:

- stable declaration IDs;
- known linkage support modes;
- required tenant/school scope;
- approved-only source-paper posture;
- same-tenant linkage posture;
- required exam/source-paper references;
- question-schema source posture;
- unique question-number posture;
- per-question max-mark posture;
- `can_evaluate_sheets` posture;
- rubric/model-answer handoff posture;
- OCR/manual input non-authority posture;
- teacher-review requirement;
- approved-evidence requirement;
- marks/mastery authority posture;
- product-claim eligibility.

This validation may live in tests or a pure test-support helper only if needed.
No production service behavior may depend on it in Batch E.

### 5.4 Golden Harness linkage cases

Add Golden Harness cases for:

- approved source paper imports into an exam schema;
- draft/unapproved source paper unsupported;
- cross-tenant source paper unsupported;
- paper with no usable questions unsupported;
- duplicate question numbers invalid;
- source-paper max marks preserved into schema posture;
- `can_evaluate_sheets` true only with source paper and schema;
- evaluation unavailable without linked paper and schema;
- rubric/model-answer context sourced from linked paper;
- OCR answer input treated as assist only;
- manual answer input treated as assist only;
- AEI suggestions remaining non-authoritative;
- teacher approval required before marks/evidence authority;
- downstream evidence and mastery requiring approved marks/evidence.

### 5.5 Focused tests

Add focused tests validating:

- linkage declarations load;
- declaration IDs are stable and unique;
- support modes are explicit;
- approved-paper linkage is the supported source posture;
- unapproved and cross-tenant linkage are unsupported;
- `can_evaluate_sheets` posture requires source paper and schema;
- rubric/model-answer handoff references linked source paper posture;
- OCR/manual input cannot be treated as marks authority;
- unsupported and expansion declarations do not permit product claims;
- Golden Harness cases reference known declarations;
- no case implies autonomous grading, autonomous teacher approval, direct
  parent evidence, direct mastery update, AEI bypass, EUI source adoption, or a
  source-of-truth switch.

Focused tests may inspect existing models, schemas, constants, and pure helpers
where useful, but must not alter production runtime behavior.

### 5.6 Certification report

Produce:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_READINESS_CERTIFICATION_REPORT.md`

The report should include:

- scope compliance;
- artifact inventory;
- validation evidence;
- paper-to-evaluation linkage evidence;
- tenant-boundary posture;
- teacher-authority posture;
- no runtime behavior change statement;
- schema/API/UI impact statement;
- AEI/EUI impact statement;
- risk assessment;
- recommendation.

---

## 6. Repository boundary

Modifications are limited to:

### Documentation

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_DECLARATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_PAPER_TO_EVALUATION_LINKAGE_SUPPORTED_SCOPE_DECLARATIONS.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_READINESS_CERTIFICATION_REPORT.md`
- this authorization contract, only to mark accepted status after ARM approval;
- supporting assessment-intelligence docs in the same directory if strictly
  necessary.

### Golden Harness data

- `apps/api/tests/golden/assessment_intelligence_v1/paper_to_evaluation_linkage_readiness_cases.json`

### Tests

- `apps/api/tests/test_assessment_intelligence_v1_paper_to_evaluation_linkage_readiness.py`

### Existing code inspection

Tests may import existing examination, evaluation, and question-paper models,
schemas, constants, and pure helpers from:

- `apps/api/app/db/models/examination.py`
- `apps/api/app/modules/examinations/schemas/exam.py`
- `apps/api/app/modules/examinations/schemas/evaluation.py`
- `apps/api/app/modules/examinations/services/exam_service.py`
- `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py`
- `apps/api/app/modules/ai/services/question_bank_service.py`

Batch E does not authorize editing those runtime files.

### Protected areas

Any changes outside the boundaries above require separate ARM authorization.

---

## 7. Explicitly not authorized

Batch E does not authorize:

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
- OCR engine changes;
- question-paper generation behavior changes;
- question-bank service behavior changes;
- exam service behavior changes;
- answer-sheet evaluation behavior changes;
- paper approval behavior changes;
- teacher approval behavior changes;
- AEI grading behavior changes;
- AEI confidence behavior changes;
- AEI teacher-review routing changes;
- EUI source adoption;
- marks changes;
- evidence-ledger behavior changes;
- parent/student visibility changes;
- principal analytics changes;
- mastery updates;
- browser workflow changes;
- public product claim expansion;
- Batch F multilingual/bilingual behavior;
- broad board/grade/subject expansion.

---

## 8. Runtime constraints

Batch E should be effectively non-runtime.

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

Existing examination and answer-sheet evaluation runtime behavior must not be
deleted, rewritten, or replaced in Batch E.

Current useful behavior includes:

- `Exam.source_paper_id`;
- `Exam.question_schema`;
- `QuestionSchemaSet.source_paper_id`;
- `ExamOut.can_evaluate_sheets`;
- approved-paper schema import;
- duplicate question-number protection;
- source-paper and school-scoped rubric fetch;
- answer-sheet evaluation requiring linked paper/schema/input;
- teacher approval writing final marks;
- correction history exposing paper/curriculum grounding.

Batch E may document this behavior and certify corresponding static
declarations. Runtime replacement, source switching, enforcement changes, or
behavior changes require a later contract.

---

## 10. AEI and EUI constraints

AEI remains the only academic answer-evaluation pipeline.

EUI architecture and runtime behavior remain unchanged.

Batch E must not:

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

Before ARM acceptance of Batch E implementation, the following evidence should
be produced:

- focused paper-to-evaluation linkage readiness tests pass;
- Golden Harness linkage cases load and validate;
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
- `apps/api/tests/test_assessment_intelligence_v1_question_bank_reuse_readiness.py`;
- `apps/api/tests/test_answer_sheet_eval.py`;
- `apps/api/tests/test_exam_question_schema.py`;
- `apps/api/tests/test_academic_reasoning_engine.py`;
- `apps/api/tests/test_evaluation_policy.py`.

---

## 12. Rollback proof

Rollback for Batch E should be simple:

- remove the added Paper-to-Evaluation Linkage documentation artifacts;
- remove the Golden Harness linkage dataset;
- remove the focused linkage readiness test file.

Because Batch E must not alter production runtime, rollback should not require:

- disabling flags;
- database rollback;
- schema downgrade;
- API versioning;
- data migration;
- tenant data cleanup.

---

## 13. Certification criteria

Batch E can be accepted only if the implementation proves:

- paper-to-evaluation linkage declaration contract exists;
- static paper-to-evaluation linkage declarations exist;
- support modes are explicit;
- declaration IDs are stable and unique;
- approved-paper linkage posture is explicit;
- unapproved and cross-tenant linkage are unsupported;
- `can_evaluate_sheets` posture requires source paper and schema;
- rubric/model-answer context posture references the linked source paper;
- OCR and manual answer input remain non-authoritative;
- teacher approval remains the authority point for marks and evidence;
- downstream evidence and mastery are not authorized before approval;
- Golden Harness linkage cases exist;
- focused tests validate the artifacts;
- no runtime behavior changed;
- no schema/API/UI changes were introduced;
- no AEI behavior changed;
- no EUI behavior changed;
- no autonomous grading or approval claim was introduced;
- no direct parent evidence or direct mastery update is implied;
- certification report is complete.

---

## 14. Suggested implementation metadata

If Batch E is implemented and accepted after code review, recommended commit
metadata:

```text
feat(assessment): add v1 paper-to-evaluation linkage readiness foundation
```

Recommended annotated tag:

```text
assessment-v1-batch-e-paper-to-evaluation-linkage-readiness-certified
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
Implementation authorization: Granted for Batch E only
Runtime behavior changes: Not authorized
```

Implementation must remain within this contract. Any runtime
paper-to-evaluation behavior change, product claim expansion, Batch F work, AEI
behavior change, EUI source adoption, or consumer migration requires separate ARM
authorization.
