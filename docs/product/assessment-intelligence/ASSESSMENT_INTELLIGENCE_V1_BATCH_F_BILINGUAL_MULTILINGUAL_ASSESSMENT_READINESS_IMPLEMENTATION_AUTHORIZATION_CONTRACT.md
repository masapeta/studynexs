# Assessment Intelligence v1.0 Batch F Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Authorization ID: ASSESSMENT-V1-BATCH-F-AUTH-001
> Classification: Implementation authorization contract
> Program: Assessment Intelligence v1.0
> Batch: F - Bilingual / Multilingual Assessment Readiness
> Implementation authorization: Authorized for Batch F only
> Runtime behavior changes: Not authorized
> Design baseline: [`ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_READINESS_DESIGN_BRIEF.md`](./ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_READINESS_DESIGN_BRIEF.md)
> ARM review: Accepted; Batch F may begin within this contract only

---

## 1. Purpose

Batch F exists to make bilingual and multilingual assessment posture explicit,
testable, and bounded before any school-facing language claim is expanded.

It should answer:

> Which assessment language scenarios are supported, which are assist-only or
> manual-review-only, which are unsupported, and how do we prove that Assessment
> Intelligence is not claiming universal bilingual or multilingual capability?

Batch F is a readiness foundation. It should not change teacher-visible
behavior.

---

## 2. Authorization status

This contract has been accepted by ARM.

It authorizes Batch F only. It does not authorize Batch G browser proof, runtime
generation behavior changes, translation behavior, OCR behavior, UI changes, API
changes, schema changes, AEI language/OCR changes, product claim expansion, or
consumer migration.

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
- Batch E Paper-to-Evaluation Linkage Declaration Contract;
- Batch E Paper-to-Evaluation Linkage Supported Scope Declarations;
- Batch F Bilingual / Multilingual Assessment Readiness Design Brief;
- AEI v1.0 Batch D Language/OCR Assist baseline;
- frozen AEI v1 architecture;
- frozen EUI v1 architecture.

---

## 4. Batch F objective

Introduce the Bilingual / Multilingual Assessment Readiness foundation:

1. bilingual/multilingual assessment declaration contract;
2. static/read-only language supported-scope declarations;
3. deterministic language-readiness Golden Harness cases;
4. focused tests validating language posture, support modes, and no-overclaim
   boundaries;
5. Batch F certification report.

The result should make assessment language posture auditable without touching
question-paper generation, rendering, translation, OCR, answer-sheet evaluation,
AEI language/OCR, teacher approval, marks, evidence, mastery, API, schema, or UI
behavior.

---

## 5. Authorized implementation scope

Batch F may implement the following.

### 5.1 Bilingual/multilingual assessment declaration contract

Add a documentation artifact defining the assessment language declaration
schema.

The declaration must include:

- stable `language_declaration_id`;
- support mode;
- assessment language posture;
- tenant/school scope;
- board, curriculum, grade, subject, and paper type;
- primary and secondary language posture;
- script posture where relevant;
- language medium posture;
- question text language posture;
- instructions language posture;
- answer-key language posture;
- model-answer language posture;
- rubric/checklist language posture;
- translation source posture;
- code-mixed posture;
- AEI language/OCR relationship;
- teacher-review requirement;
- approved-evidence requirement;
- product-claim posture;
- runtime behavior change posture.

### 5.2 Static language supported-scope declarations

Add static declarations for the initial supported scope.

Minimum declarations:

- supported English assessment contract posture for declared scope;
- supported English grounded-paper posture where earlier readiness
  requirements are met;
- supported or assist English answer-key/model-answer/rubric posture according
  to Batch C;
- manual-review teacher-authored bilingual paper posture;
- manual-review AI-assisted bilingual draft posture;
- assist bilingual rendering posture for already-reviewed teacher content;
- assist Hindi language-answer evaluation relationship to AEI;
- assist Telugu handwriting/OCR answer relationship to AEI;
- assist Hinglish/Tinglish/code-mixed answer posture;
- manual-review local-language answer key or model answer without reviewed
  source;
- unsupported automatic question-paper translation;
- unsupported automatic rubric/model-answer translation;
- unsupported universal multilingual assessment generation;
- expansion posture for future Telugu-medium/state-board assessment packs.

These declarations must be read-only artifacts. They must not be wired into
runtime request paths in Batch F.

### 5.3 Deterministic language validation posture

Add deterministic validation logic only if it remains outside production request
paths.

Permitted validation may check:

- stable declaration IDs;
- known support modes;
- required tenant/school scope;
- explicit board/curriculum/grade/subject/paper type for supported claims;
- English supported posture does not imply bilingual support;
- bilingual/manual-review postures block production claims;
- unsupported universal multilingual posture blocks product claims;
- question text, instructions, answer key, model answer, and rubric language
  posture exists;
- translation source posture exists;
- code-mixed posture routes to AEI assist or teacher review;
- AEI language/OCR relationship is declared without duplication;
- teacher-review requirement;
- approved-evidence requirement;
- runtime behavior remains unchanged.

This validation may live in tests or a pure test-support helper only if needed.
No production service behavior may depend on it in Batch F.

### 5.4 Golden Harness language-readiness cases

Add Golden Harness cases for:

- English assessment contract supported for declared scope;
- English grounded-paper posture supported where earlier requirements are met;
- English answer-key/model-answer/rubric posture aligned with Batch C;
- teacher-authored bilingual paper manual-review posture;
- AI-assisted bilingual draft manual-review posture;
- bilingual rendering assist posture only;
- Hindi language-answer evaluation assist relationship to AEI;
- Telugu handwriting/OCR answer assist relationship to AEI;
- Hinglish/Tinglish/code-mixed answer assist posture;
- local-language answer key without reviewed source manual-review posture;
- automatic question-paper translation unsupported;
- automatic rubric/model-answer translation unsupported;
- universal multilingual assessment unsupported;
- future Telugu-medium/state-board assessment expansion posture.

### 5.5 Focused tests

Add focused tests validating:

- language declarations load;
- declaration IDs are stable and unique;
- support modes are explicit;
- supported claims are scoped and do not imply universal language support;
- bilingual/manual-review posture blocks production product claims;
- unsupported and expansion declarations do not permit product claims;
- AEI language/OCR assist relationship is declared without duplication;
- Golden Harness cases reference known declarations;
- no case implies translation execution, OCR execution, autonomous language
  grading, autonomous paper approval, autonomous marks, direct parent evidence,
  direct mastery update, AEI bypass, EUI source adoption, or runtime behavior
  changes.

Focused tests may inspect existing Assessment, AEI, and EUI static artifacts
and pure constants where useful, but must not alter production runtime behavior.

### 5.6 Certification report

Produce:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_READINESS_CERTIFICATION_REPORT.md`

The report should include:

- scope compliance;
- artifact inventory;
- validation evidence;
- language posture evidence;
- no-overclaim posture;
- AEI language/OCR relationship;
- no runtime behavior change statement;
- schema/API/UI impact statement;
- AEI/EUI impact statement;
- risk assessment;
- recommendation.

---

## 6. Repository boundary

Modifications are limited to:

### Documentation

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_DECLARATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BILINGUAL_MULTILINGUAL_SUPPORTED_SCOPE_DECLARATIONS.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_READINESS_CERTIFICATION_REPORT.md`
- this authorization contract, only to mark accepted status after ARM approval;
- supporting assessment-intelligence docs in the same directory if strictly
  necessary.

### Golden Harness data

- `apps/api/tests/golden/assessment_intelligence_v1/bilingual_multilingual_assessment_readiness_cases.json`

### Tests

- `apps/api/tests/test_assessment_intelligence_v1_bilingual_multilingual_readiness.py`

### Existing code/static inspection

Tests may import or inspect existing Assessment, AEI, and EUI static artifacts,
schemas, constants, or pure helpers from:

- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`
- `apps/api/app/modules/eui/registry/platform_capability_registry.v1.json`
- `apps/api/app/modules/examinations/services/aei_v1_language_ocr_assist.py`
- `apps/api/app/modules/examinations/services/academic_understanding_engine.py`
- `apps/api/app/modules/eui/schemas/educational_context.py`
- `apps/api/app/modules/eui/schemas/trust_report.py`

Batch F does not authorize editing those runtime files.

### Protected areas

Any changes outside the boundaries above require separate ARM authorization.

---

## 7. Explicitly not authorized

Batch F does not authorize:

- database schema changes;
- Alembic migrations;
- API contract changes;
- public endpoint changes;
- UI changes;
- runtime behavior changes;
- feature flags;
- translation engine integration;
- new OCR behavior;
- AI provider changes;
- LLM inference;
- LLM prompt changes;
- question-paper generation behavior changes;
- bilingual paper generation behavior changes;
- multilingual paper rendering behavior changes;
- question-bank service behavior changes;
- exam service behavior changes;
- answer-sheet evaluation behavior changes;
- AEI language/OCR behavior changes;
- AEI grading behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger behavior changes;
- parent/student visibility changes;
- principal analytics changes;
- mastery updates;
- browser workflow changes;
- public bilingual/multilingual product claim expansion;
- Batch G teacher workflow/browser proof.

---

## 8. Runtime constraints

Batch F should be effectively non-runtime.

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

Existing Assessment, AEI, EUI, and teacher evaluation runtime behavior must not
be deleted, rewritten, or replaced in Batch F.

Current useful behavior includes:

- Assessment Batch A capability matrix declaring English as the initial
  supported assessment language;
- bilingual paper generation marked as manual-review posture;
- universal multilingual assessment marked unsupported;
- AEI language/OCR assist metadata for selected evaluation scenarios;
- EUI language medium and trust report schema posture;
- Teacher Evaluation UX-D language/OCR assist display when metadata exists.

Batch F may document this behavior and certify corresponding static
declarations. Runtime replacement, generation behavior changes, source
switching, translation execution, OCR execution, or behavior changes require a
later contract.

---

## 10. AEI and EUI constraints

AEI remains the only academic answer-evaluation pipeline.

EUI architecture and runtime behavior remain unchanged.

Batch F must not:

- duplicate AEI language/OCR logic;
- alter AEI contracts;
- alter AEI marks, policy, confidence, teacher review, or evidence behavior;
- weaken teacher authority;
- authorize automatic language grading;
- authorize unapproved downstream evidence;
- directly update marks, parent evidence, or mastery;
- reopen EUI source adoption;
- change EUI runtime behavior.

---

## 11. Validation requirements

Before ARM acceptance of Batch F implementation, the following evidence should
be produced:

- focused bilingual/multilingual readiness tests pass;
- Golden Harness language-readiness cases load and validate;
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
- `apps/api/tests/test_assessment_intelligence_v1_paper_to_evaluation_linkage_readiness.py`;
- `apps/api/tests/test_aei_v1_language_ocr_assist.py`;
- `apps/api/tests/test_academic_understanding_engine.py`;
- `apps/api/tests/test_golden_evaluation_harness.py`;
- `apps/api/tests/test_evaluation_policy.py`.

---

## 12. Rollback proof

Rollback for Batch F should be simple:

- remove the added bilingual/multilingual assessment documentation artifacts;
- remove the Golden Harness language-readiness dataset;
- remove the focused language-readiness test file.

Because Batch F must not alter production runtime, rollback should not require:

- disabling flags;
- database rollback;
- schema downgrade;
- API versioning;
- data migration;
- tenant data cleanup.

---

## 13. Certification criteria

Batch F can be accepted only if the implementation proves:

- bilingual/multilingual assessment declaration contract exists;
- static language supported-scope declarations exist;
- support modes are explicit;
- declaration IDs are stable and unique;
- English supported posture is declared without implying universal support;
- bilingual/manual-review posture blocks production claims;
- universal multilingual assessment is explicitly unsupported;
- automatic question-paper translation is unsupported;
- automatic rubric/model-answer translation is unsupported;
- AEI language/OCR assist relationship is declared without duplication;
- Golden Harness language-readiness cases exist;
- focused tests validate the artifacts;
- no runtime behavior changed;
- no schema/API/UI changes were introduced;
- no AEI language/OCR behavior changed;
- no EUI behavior changed;
- no autonomous language-grading or bilingual-generation claim was introduced;
- no direct parent evidence or direct mastery update is implied;
- certification report is complete.

---

## 14. Suggested implementation metadata

If Batch F is implemented and accepted after code review, recommended commit
metadata:

```text
feat(assessment): add v1 bilingual multilingual readiness foundation
```

Recommended annotated tag:

```text
assessment-v1-batch-f-bilingual-multilingual-readiness-certified
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
Implementation authorization: Granted for Batch F only
Runtime behavior changes: Not authorized
```

Implementation must remain within this contract. Any runtime multilingual
behavior change, translation behavior, product claim expansion, Batch G work, AEI
behavior change, EUI source adoption, or consumer migration requires separate ARM
authorization.
