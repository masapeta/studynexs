# EUI Runtime Phase 4 Implementation Authorization Contract — Knowledge Acquisition Intelligence

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 4 - Knowledge Acquisition Intelligence
- **Classification:** Implementation Authorization Contract
- **Status:** Accepted
- **Implementation authorization:** Authorized
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_4_KNOWLEDGE_ACQUISITION_INTELLIGENCE_DESIGN_BRIEF.md`](./EUI_PHASE_4_KNOWLEDGE_ACQUISITION_INTELLIGENCE_DESIGN_BRIEF.md)
- **Prior runtime baseline:** Phase 3 - Platform Capability Registry passive runtime foundation
- **Authorization ID:** `EUI-PH4-KAI-AUTH-001`

---

## 1. Authorization boundary

ARM has accepted this contract and authorized Phase 4 KAI implementation within
the scope, repository boundary, runtime constraints, validation requirements,
and explicit exclusions defined below.

This authorization permits:

- passive KAI candidate foundation implementation;
- focused validation and certification evidence;
- no product-visible behavior change.

It does not permit:

- schema, API, UI, runtime behavior, consumer migration, EKG, or AEI behavior
  changes;
- any work outside the repository boundary without separate ARM approval.

---

## 2. Purpose

Phase 4 exists to implement a passive Knowledge Acquisition Intelligence (KAI)
runtime foundation.

KAI answers:

> How does StudyNexs safely represent educational inputs as governed candidate artifacts?

The purpose of the first implementation is to establish candidate contracts,
source admission, provenance, trust-signal placeholders, capability posture,
Golden Harness coverage, and passive observability without changing product
behavior.

The runtime objective is:

```text
Educational acquisition input
        |
        v
Source admission policy
        |
        v
Candidate artifact builder
        |
        v
Educational Identity / Context references where available
        |
        v
Platform Capability Registry lookup where applicable
        |
        v
EducationalArtifactCandidate
        |
        v
Metrics / logs / Golden Harness
        |
        v
Captured for verification only
        |
        v
No consumer uses the result
```

---

## 3. Implementation scope

If authorized, Phase 4 implementation is limited to the following work.

### 3.1 KAI candidate contracts

Implement strict runtime/domain contracts for passive acquisition candidates.

Required concepts:

- acquisition input reference;
- candidate artifact;
- source provenance;
- modality;
- source admission status;
- extraction status;
- normalized content placeholder;
- educational identity/context references;
- capability posture;
- trust-signal placeholders;
- review posture;
- metadata.

These are runtime/domain objects, not database tables.

### 3.2 Source admission policy

Implement deterministic source admission for explicitly admitted input types.

Initial admitted input types:

- `pdf`;
- `worksheet`;
- `ocr_text`;
- `answer_key`;
- `teacher_note`;
- `lesson_plan`.

All other source types must resolve to `unsupported` or `needs_review`.

Student work is not admitted in this implementation unless ARM explicitly amends
this contract.

### 3.3 Candidate artifact builder

Implement a deterministic builder that converts an admitted input reference into
an `EducationalArtifactCandidate`.

The builder may use:

- supplied extracted text;
- supplied artifact metadata;
- supplied Educational Identity ID;
- supplied Educational Context summary fields;
- Platform Capability Registry lookup;
- deterministic normalization such as trimming and metadata shaping.

The builder must not use:

- OCR provider calls;
- LLM inference;
- ASR or voice transcription;
- PDF parsing libraries;
- image processing libraries;
- database writes;
- external network calls.

### 3.4 Stable transient candidate IDs

Implement deterministic transient candidate identifiers.

IDs must be stable for identical candidate inputs but must not be persisted in
Phase 4.

Suggested prefix:

```text
kai://
```

### 3.5 Platform Capability Registry integration

KAI may call the existing Platform Capability Registry lookup service to attach
internal capability posture.

The implementation must not:

- modify Platform Capability Registry data;
- upgrade capability posture;
- generate public product claims;
- route workflow based on capability posture;
- replace AEI capability logic.

### 3.6 Passive observer

If passive runtime observation is implemented, it must be guarded by a
default-off feature flag.

The observer must:

- be no-op when disabled;
- isolate exceptions;
- preserve legacy product behavior when enabled;
- avoid writing product state;
- avoid exposing output to consumers.

### 3.7 Feature flag

If passive runtime observation is implemented, add one settings-based feature
flag:

```text
EUI_KAI_PASSIVE_ENABLED: bool = False
```

Default state must be `False`.

Rollback is achieved by disabling or leaving disabled this flag.

### 3.8 Observability

Add operational metrics and structured logs if passive runtime observation is
introduced.

Expected task name:

```text
eui_kai
```

Expected statuses include:

- `acquire_invoked`;
- `acquire_completed`;
- `acquire_failed`;
- `unsupported_input`;
- `ambiguous`;
- `needs_review`;
- `fallback`.

Metrics and logs must not expose student names, parent data, tenant slugs,
free-text answers, uploaded content, raw OCR text, or sensitive educational
evidence.

### 3.9 Golden Harness

Add Golden Harness cases for deterministic KAI candidate behavior.

Expected dataset:

```text
apps/api/tests/golden/eui_v1/kai_candidate_cases.json
```

Coverage should include:

- PDF worksheet candidate;
- OCR text candidate;
- answer key candidate;
- teacher note candidate;
- lesson plan candidate;
- Hindi printed OCR candidate posture;
- handwriting OCR assist/manual-review posture;
- unsupported source type;
- missing identity/context fallback;
- capability posture not upgraded.

### 3.10 Certification

Produce a Phase 4 certification report:

```text
docs/product/eui-runtime/phase-4/EUI_PHASE_4_KNOWLEDGE_ACQUISITION_INTELLIGENCE_CERTIFICATION_REPORT.md
```

The report must include certification evidence, validation commands, behavior
identity evidence, rollback proof, risk register, conditions, recommendation,
and phase retrospective.

---

## 4. Repository boundary

If authorized, changes are limited to the following repository areas.

### 4.1 Permitted source files

Allowed:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/knowledge_acquisition.py
apps/api/app/modules/eui/schemas/__init__.py
apps/api/app/modules/eui/services/knowledge_acquisition_candidate_id.py
apps/api/app/modules/eui/services/knowledge_acquisition_builder.py
apps/api/app/modules/eui/services/knowledge_acquisition_passive.py
apps/api/app/modules/eui/services/knowledge_acquisition_source_admission.py
apps/api/app/modules/eui/services/__init__.py
```

Notes:

- Existing Educational Identity, Educational Context, and Platform Capability
  Registry modules may be imported but must not be modified without explicit
  ARM approval.
- AEI modules may be read for compatibility understanding but must not be
  changed.

### 4.2 Permitted test and Golden Harness files

Allowed:

```text
apps/api/tests/golden/eui_v1/kai_candidate_cases.json
apps/api/tests/test_kai_candidate_model.py
apps/api/tests/test_kai_candidate_builder.py
apps/api/tests/test_kai_passive.py
apps/api/tests/test_kai_source_admission.py
apps/api/tests/test_eui_golden_harness.py
```

`test_eui_golden_harness.py` may be updated to load KAI cases alongside
existing EUI Golden Harness cases.

### 4.3 Permitted documentation files

Allowed:

```text
docs/product/eui-runtime/phase-4/EUI_PHASE_4_KNOWLEDGE_ACQUISITION_INTELLIGENCE_CERTIFICATION_REPORT.md
docs/product/eui-runtime/phase-4/EUI_PHASE_4_KNOWLEDGE_ACQUISITION_INTELLIGENCE_DESIGN_BRIEF.md
docs/product/eui-runtime/phase-4/EUI_PHASE_4_KNOWLEDGE_ACQUISITION_INTELLIGENCE_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

After implementation is certified and published, ARM may separately authorize a
Master Status update.

### 4.4 Protected areas

Phase 4 does not authorize changes to:

```text
apps/api/alembic/
apps/api/app/api/
apps/api/app/db/
apps/api/app/modules/examinations/
apps/api/app/modules/assessment*/
apps/api/app/modules/curriculum*/
apps/api/app/modules/files/
apps/api/app/modules/knowledge_graph/
apps/api/app/modules/tutor*/
apps/admin-web/
infra/
sites/
```

Any change outside the permitted boundary requires explicit ARM approval before
implementation.

---

## 5. Permitted artifacts

Permitted artifacts:

- KAI candidate contracts;
- deterministic candidate ID helper;
- source admission policy;
- candidate builder;
- optional passive observer;
- one settings flag if passive runtime observation is implemented;
- operational metrics/logging if passive runtime observation is implemented;
- focused tests;
- Golden Harness data;
- certification report;
- phase retrospective inside the certification report.

Not permitted:

- migrations;
- database tables;
- persistence logic;
- API schemas used by existing consumers;
- routers;
- UI components;
- background workers;
- OCR provider integrations;
- LLM calls;
- ASR/voice transcription;
- PDF parsing provider integration;
- image processing provider integration;
- product analytics dashboards;
- consumer migrations;
- AEI contract changes;
- EKG writes;
- public product-claim generation.

---

## 6. Runtime constraints

Phase 4 implementation must be:

- passive;
- candidate-only;
- read-only with respect to existing product data;
- deterministic where deterministic inputs are supplied;
- exception-isolated if runtime observation is introduced;
- tenant-safe where tenant context is involved;
- invisible to users;
- non-authoritative for every consumer.

If KAI candidate generation fails, legacy behavior must continue unchanged.

When disabled, any passive observer must return without building candidates or
recording captures.

When enabled, passive KAI execution must not change production output.

---

## 7. Explicit exclusions

The following remain out of scope:

- database schema changes;
- persistent KAI storage;
- database migrations;
- API contract changes;
- public endpoint changes;
- UI changes;
- consumer migration;
- AEI runtime behavior changes;
- EUI consumer behavior changes;
- Educational Knowledge Graph writes;
- CurriculumPack publishing changes;
- Trust Framework implementation;
- Institutional Memory implementation;
- LLM inference;
- prompt changes;
- OCR provider calls;
- handwriting OCR improvement;
- ASR or voice transcription;
- file upload workflow changes;
- background workers;
- public product capability claim expansion;
- support documentation generated from KAI output;
- student work ingestion.

---

## 8. Validation requirements

Before ARM acceptance, implementation evidence must include the following.

### 8.1 Focused lint

Expected command:

```text
cd apps/api
ruff check app/modules/eui tests/test_kai_candidate_model.py tests/test_kai_candidate_builder.py tests/test_kai_passive.py tests/test_kai_source_admission.py tests/test_eui_golden_harness.py
```

### 8.2 Focused Phase 4 tests

Expected command:

```text
cd apps/api
python -m pytest tests/test_kai_candidate_model.py tests/test_kai_candidate_builder.py tests/test_kai_passive.py tests/test_kai_source_admission.py tests/test_eui_golden_harness.py
```

### 8.3 Phase 1-3 EUI regression

Expected command:

```text
cd apps/api
python -m pytest tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_platform_capability_registry.py tests/test_platform_capability_lookup.py tests/test_platform_capability_passive.py tests/test_eui_golden_harness.py
```

### 8.4 AEI / evaluation / KG regression slice

Expected command:

```text
cd apps/api
python -m pytest tests/test_aei_architecture.py tests/test_aei_passive_integration.py tests/test_evaluation_policy.py tests/test_golden_evaluation_harness.py tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py tests/test_knowledge_graph.py tests/test_graph_queries.py tests/test_question_concept_links.py
```

### 8.5 API import

Expected command:

```text
cd apps/api
python -c "import app.main; print('api import ok')"
```

### 8.6 Whitespace check

Expected command:

```text
git diff --check
```

If broader repository lint remains blocked by pre-existing unrelated lint debt,
the certification report must document that explicitly and show that Phase 4
files and the affected regression neighborhood are clean.

---

## 9. Rollback proof

If a feature flag is introduced, certification must prove:

- `EUI_KAI_PASSIVE_ENABLED` defaults to `False`;
- disabled state executes no passive candidate generation;
- disabled state records no passive capture;
- enabled state does not change product output;
- exceptions are isolated;
- no schema, persistence, API, UI, EKG write, or consumer migration exists to
  roll back.

Rollback mechanism, if flag is introduced:

```text
Set EUI_KAI_PASSIVE_ENABLED=false
```

Because Phase 4 must not introduce persistence, rollback must not require data
repair.

---

## 10. Certification deliverables

Certification must include:

- scope certified;
- KAI candidate contract evidence;
- source admission evidence;
- provenance/trust separation evidence;
- unsupported/ambiguous/needs-review behavior evidence;
- capability posture evidence;
- feature flag evidence if applicable;
- observability evidence if applicable;
- rollback evidence;
- AEI impact evidence;
- EKG impact evidence;
- schema/API/UI unchanged evidence;
- test commands and results;
- behavior identity evidence;
- risks and mitigations;
- conditions, if any;
- phase retrospective;
- ARM recommendation.

Certification status may be:

- `PASS`;
- `PASS WITH CONDITIONS`;
- `FAIL`.

Commit authorization should not occur until ARM reviews the implementation
evidence and accepts the phase.

---

## 11. Exit criteria

Phase 4 implementation may be considered complete only when all of the
following are true:

- KAI candidate contracts exist as authorized;
- source admission policy exists as authorized;
- unsupported source types fail closed;
- student work is not admitted;
- candidate builder is deterministic for supported structured inputs;
- KAI outputs candidates, not authoritative knowledge;
- provenance and trust-signal placeholders remain separate;
- capability posture is not upgraded;
- no consumer depends on KAI output;
- no EKG writes occur;
- no schema/API/UI changes are introduced;
- no AEI behavior changes are introduced;
- no OCR/LLM/ASR provider integrations are introduced;
- Golden Harness KAI cases pass;
- observability and rollback are verified if passive runtime observation is
  introduced;
- focused tests and regression slices pass;
- certification report is complete;
- phase retrospective is complete;
- ARM accepts the implementation before commit.

---

## 12. Commit, tag, and publication guidance

If implementation is later authorized, completed, certified, and accepted, the
recommended commit message is:

```text
feat(eui): add knowledge acquisition candidate foundation
```

Recommended annotated tag:

```text
eui-runtime-phase4-kai-candidate-foundation-certified
```

Publication requires separate ARM approval after certification and commit.

---

## 13. ARM decision options

ARM decision:

```text
Decision: Accepted
Implementation authorization: Granted
Authorization ID: EUI-PH4-KAI-AUTH-001
```

Phase 4 implementation may proceed only within this contract. Completion of
Phase 4 does not authorize commit, publication, consumer migration, EKG writes,
AEI behavior changes, provider integration, or the next phase.
