# EUI Phase 1 Sprint 2 Design Brief — Educational Context

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 1 - Educational Identity and Context
- **Sprint:** Sprint 2 - Educational Context
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Depends on:** Phase 1 Sprint 1 - Educational Identity passive runtime foundation
- **ARM review:** Accepted with clarification recommendations incorporated

---

## 1. Purpose

Educational Identity answers:

> What educational object is this?

Educational Context answers:

> In what educational situation is this object being used?

Educational Identity is necessary but not sufficient because the same chapter, concept, question, answer, lesson, or worksheet may need different handling depending on the school, academic year, grade, section, subject, language medium, assessment type, curriculum version, teacher intent, and institutional policy.

Sprint 2 exists to define the runtime foundation for resolving that surrounding educational situation through one canonical context contract, without allowing consumers to rediscover or reinvent context independently.

The intended long-term direction is:

```text
EducationalIdentity
        |
        v
EducationalContext
        |
        v
Future consumers
```

Sprint 2 should keep the result passive and non-authoritative until later consumer migration is explicitly authorized.

---

## 2. Why Educational Identity is not enough

Educational Identity gives StudyNexs a stable reference such as:

```text
ei://cbse/ncf2023/g6/science/ch05/concept08
```

That identity can identify a concept, chapter, topic, learning objective, or competency. It does not, by itself, answer runtime questions such as:

- Is this being used for homework, a unit test, a term exam, or remediation?
- Which school and academic year does this belong to?
- Which grade, section, and subject instance is involved?
- Which language medium is expected?
- Which curriculum pack version is active?
- Is this teacher draft, teacher approved, or principal reviewed?
- Are there institutional policies or student accommodations that affect interpretation?

Those questions belong to Educational Context.

---

## 3. Responsibilities

Educational Context is responsible for resolving and carrying the educational situation around an intelligence action.

It should eventually provide a stable contract for:

- tenant-derived school scope;
- academic year and term scope;
- board, curriculum, curriculum version, grade, section, and subject;
- curriculum pack and Educational Identity references;
- chapter, topic, concept, learning objective, and competency context where available;
- assessment mode such as homework, practice, unit test, term exam, or board-style assessment;
- language medium and code-mixed posture where already known;
- teacher, class, and institution context where already available;
- review or evidence posture, such as draft, approved, or passive;
- context confidence and ambiguity metadata for later Trust Framework consumption.

Educational Context is not responsible for academic grading, AI reasoning, consumer migration, UI display, or product-visible decision-making in Sprint 2.

---

## 4. Relationship to AEI and other consumers

AEI remains protected and feature-frozen except for separately authorized integration waves.

Sprint 2 must not change AEI behavior.

Future AEI integration may consume Educational Context, but Sprint 2 does not authorize that migration. In Sprint 2, Educational Context may be constructed and passively observed, but existing evaluation remains the source of truth.

Other consumers such as AI Tutor, Teacher Copilot, Question Generator, Lesson Planner, Parent Assistant, Principal Dashboard, and analytics must not consume Educational Context until a later consumer-specific migration is authorized.

---

## 5. Dependencies

Sprint 2 depends on:

- accepted EUI architecture baseline;
- accepted Educational Context Engine architecture;
- Phase 0 feature flag, observability, certification, and rollback guidance;
- Phase 1 Sprint 1 Educational Identity model, resolver, registry, cache, and passive runtime foundation;
- existing CurriculumPack and Knowledge Graph references, read-only;
- existing tenant and runtime settings patterns.

Sprint 2 should not introduce dependencies on:

- Educational Knowledge Graph expansion;
- Platform Capability Registry;
- Knowledge Acquisition Intelligence;
- Trust Framework;
- Institutional Memory runtime behavior;
- LLM inference;
- UI surfaces;
- API consumers.

---

## 6. Inputs and outputs

### Candidate inputs

Sprint 2 may design for context resolution from existing runtime inputs such as:

- authenticated tenant/session scope;
- CurriculumPack references;
- EducationalIdentity references;
- grade, section, subject, chapter, topic, or assessment metadata already present in existing flows;
- artifact metadata from question paper, lesson plan, homework, assessment, or worksheet paths where read-only access already exists.

### Output

The output should be a canonical `EducationalContext` domain object or equivalent runtime contract.

It should represent context only. It should not score, grade, recommend, route, or authorize any downstream behavior.

Conceptual shape:

```text
EducationalContext
  tenant_scope
  academic_year
  board
  curriculum
  curriculum_version
  grade
  section
  subject
  curriculum_pack
  educational_identity
  chapter
  topic
  concepts
  competencies
  learning_objectives
  assessment_mode
  language_medium
  evidence_posture
  resolution_status
  ambiguity_reasons
  provenance
  metadata
```

The exact implementation shape requires separate ARM authorization before coding begins.

---

## 7. Context resolution precedence

Educational Context may be assembled from multiple existing sources. If those
sources conflict, the resolver should follow an explicit precedence model rather
than letting individual consumers decide.

The intended precedence order for Sprint 2 implementation is:

1. Tenant and authenticated runtime scope derived from trusted server-side
   session context.
2. Explicit artifact references, such as an existing CurriculumPack ID,
   EducationalIdentity ID, assessment ID, lesson plan ID, question paper ID, or
   homework ID.
3. Approved CurriculumPack metadata and existing Knowledge Graph references.
4. Existing runtime metadata attached to the artifact, such as grade, section,
   subject, chapter, topic, assessment mode, or language medium.
5. Derived or inferred labels from non-authoritative text fields.

If a lower-precedence source conflicts with a higher-precedence source, the
higher-precedence source should win and the conflict should be recorded in
context metadata for passive validation.

Example:

```text
CurriculumPack: Grade 6 Science
Runtime metadata: Grade 7 Science
Resolution: Grade 6 Science, with conflict recorded
```

Sprint 2 must not silently use lower-precedence metadata to override trusted
curriculum or tenant context.

---

## 8. Ambiguity behavior

Ambiguity is an expected outcome, not an exceptional product failure.

When Educational Context cannot resolve a single deterministic context, the
resolver should produce a non-authoritative ambiguity result rather than forcing
a choice.

Expected behavior:

- return a structured unresolved or partial context result where safe;
- include candidate context references when available and non-sensitive;
- record ambiguity reasons;
- record the source fields that caused ambiguity;
- emit operational metrics and structured logs;
- keep legacy product behavior unchanged;
- avoid exposing the ambiguous context to any consumer.

Examples of ambiguity:

- the same chapter label exists across multiple boards;
- runtime metadata supplies a subject but no grade;
- an artifact references a CurriculumPack but free-text metadata points to a
  different subject;
- language medium is missing or conflicts with curriculum metadata.

Ambiguity handling in Sprint 2 is for passive validation only. It must not route
teacher review, alter evaluation, change UI, or affect product-visible behavior.

---

## 9. Sprint 2 scope

Sprint 2 should be scoped to the passive runtime foundation for Educational Context.

The future implementation authorization may allow:

- canonical Educational Context domain model;
- deterministic context resolver;
- read-only context source adapters over existing data;
- in-process cache if needed;
- default-off feature flag;
- passive observer;
- operational metrics and structured logs;
- Golden Harness context-resolution cases;
- certification report.

The design intent is:

```text
Existing runtime input
        |
        v
Educational Identity reference, where available
        |
        v
Educational Context Resolver
        |
        v
Canonical EducationalContext
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

## 10. Explicit exclusions

Sprint 2 does not authorize:

- runtime implementation without a separate ARM authorization;
- database schema changes;
- database migrations;
- persistent context storage;
- API contract changes;
- public endpoint changes;
- UI changes;
- consumer migration;
- AEI runtime behavior changes;
- EUI consumer behavior changes;
- grading, scoring, or evaluation logic;
- Trust Framework implementation;
- Platform Capability Registry implementation;
- Knowledge Acquisition Intelligence;
- Educational Knowledge Graph expansion;
- Institutional Memory runtime behavior;
- LLM inference;
- prompt changes;
- background workers;
- distributed cache infrastructure;
- product capability claim expansion.

---

## 11. Non-goals

Sprint 2 is deliberately not attempting to:

- model pedagogy;
- perform educational reasoning;
- recommend lessons, remediation, or interventions;
- decide whether an answer is correct;
- replace AEI decisions;
- become a general knowledge graph;
- infer unsupported educational context using AI;
- define school policy behavior;
- expose context to teachers, students, parents, principals, or administrators;
- make Educational Context a source of truth for any consumer.

These non-goals prevent Educational Context from becoming a hidden feature layer.

---

## 12. Feature flag strategy

Sprint 2 should follow the Phase 0 feature flag strategy.

Expected posture:

- default-off;
- environment-configurable;
- passive execution only;
- rollback by disabling the flag;
- no product-visible behavior when enabled;
- no downstream consumer dependency on the output.

Possible future flag name:

```text
EUI_CONTEXT_PASSIVE_ENABLED=false
```

The exact flag name should be finalized in the implementation authorization, not by this design brief.

---

## 13. Runtime behavior

Sprint 2 runtime behavior, if later authorized, must be:

- passive;
- read-only;
- deterministic where inputs are deterministic;
- exception-isolated;
- tenant-safe;
- invisible to users;
- non-authoritative for all consumers.

If context resolution fails, legacy behavior must continue unchanged.

The resolver may record failure, ambiguity, not-found, fallback, and duration signals for internal validation only.

---

## 14. Observability

Sprint 2 should define operational observability, not product analytics.

Expected metrics may include:

```text
eui_context_resolver.invoked
eui_context_resolver.completed
eui_context_resolver.failed
eui_context_resolver.ambiguous
eui_context_resolver.not_found
eui_context_resolver.cache_hit
eui_context_resolver.cache_miss
eui_context_resolver.duration
```

Structured logs should capture:

- resolution status;
- ambiguity reason;
- failure reason;
- fallback path;
- feature flag state;
- non-sensitive correlation metadata.

Metrics and logs must not use student names, parent data, tenant slugs, free-text answers, uploaded content, or other sensitive educational content as labels.

---

## 15. Testing strategy

Sprint 2 should be backed by focused tests and Golden Harness coverage.

### Unit tests

Expected coverage:

- model validation;
- deterministic resolver output;
- read-only adapter behavior;
- ambiguity handling;
- not-found handling;
- disabled feature flag behavior;
- exception isolation;
- cache behavior if a cache is introduced.

### Golden Harness

Golden cases should cover:

- CBSE curriculum context;
- ICSE curriculum context;
- State Board Telugu-medium context;
- same Educational Identity used in different assessment modes;
- same chapter name across different boards or subjects;
- missing optional context;
- ambiguous grade or section references;
- language medium differences;
- passive resolution without consumer migration.

### Regression verification

Before certification, validation should demonstrate:

- existing product behavior unchanged;
- existing AEI behavior unchanged;
- existing Educational Identity tests still pass;
- API import succeeds;
- focused lint for Sprint 2 files passes;
- `git diff --check` passes.

---

## 16. Certification criteria

Sprint 2 should be accepted only if certification can truthfully state:

- canonical Educational Context contract exists as authorized;
- resolver is deterministic for supported inputs;
- resolver is read-only;
- feature flag defaults off;
- passive observer is no-op when disabled;
- enabled passive mode does not affect product behavior;
- no consumer depends on Educational Context;
- context precedence conflicts are recorded without changing product behavior;
- ambiguity produces non-authoritative passive evidence only;
- no schema/API/UI changes were introduced;
- no AEI behavior changed;
- Golden Harness context cases pass;
- observability evidence exists for invocation, completion, failure, ambiguity, and duration;
- rollback is verified by disabling the feature flag;
- certification report is complete;
- phase retrospective is complete.

---

## 17. Master Status update requirement

Every published sprint must end by updating the Master Status before the next sprint begins.

For Sprint 2, the post-publication Master Status update should record:

- Phase 1 Sprint 2 status;
- commit and annotated tag, if implementation is later authorized and published;
- whether runtime behavior remained unchanged;
- whether consumer migration remains unauthorized;
- next gated milestone.

This keeps future sessions anchored on:

- where the project is;
- what has been completed;
- what is being designed or implemented;
- what is explicitly out of scope.

---

## 18. ARM review gate

This design brief has been accepted by ARM.

It does not authorize implementation.

The next governance action should be a separate Sprint 2 implementation
authorization contract defining repository boundaries, permitted files/modules,
feature flag names, validation evidence, rollback proof, and certification
requirements.

No Sprint 2 code should be written until ARM separately authorizes implementation.
