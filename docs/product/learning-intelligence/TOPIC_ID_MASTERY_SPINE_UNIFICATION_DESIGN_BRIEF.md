# Topic-ID / Mastery Spine Unification Design Brief

- **Program:** Product-facing learning intelligence readiness
- **Gate:** Topic-ID / mastery spine unification design
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized by this document
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)
- **AEI baseline:** [`../../architecture/AEI.md`](../../architecture/AEI.md)
- **EUI baseline:** [`../../architecture/EUI.md`](../../architecture/EUI.md)
- **AEI Activation / Trust baseline:** [`../aei-v1/AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md`](../aei-v1/AEI_ACTIVATION_TRUST_CERTIFICATION_REPORT.md)
- **EUI Educational Identity baseline:** [`../eui-runtime/phase-1/EUI_PHASE_1_SPRINT_1_EDUCATIONAL_IDENTITY_CERTIFICATION_REPORT.md`](../eui-runtime/phase-1/EUI_PHASE_1_SPRINT_1_EDUCATIONAL_IDENTITY_CERTIFICATION_REPORT.md)
- **EUI EKG baseline:** [`../eui-runtime/phase-5/EUI_PHASE_5_EDUCATIONAL_KNOWLEDGE_GRAPH_EXPANSION_DESIGN_BRIEF.md`](../eui-runtime/phase-5/EUI_PHASE_5_EDUCATIONAL_KNOWLEDGE_GRAPH_EXPANSION_DESIGN_BRIEF.md)
- **ARM review:** Accepted; implementation remains separately gated

---

## 1. Purpose

StudyNexs now has certified AEI evaluation foundations, EUI educational
identity foundations, and controlled AEI Activation / Trust proof.

The next product-facing learning intelligence question is:

> Can every evaluation, mastery, tutor, parent, and principal learning signal
> refer to the same canonical curriculum spine instead of repeatedly inferring
> meaning from free-text topic labels?

This design brief defines the target architecture and migration posture for
Topic-ID / mastery spine unification.

It does not authorize implementation, schema changes, API changes, UI changes,
runtime behavior changes, source switching, or consumer migration.

---

## 2. Core principle

Labels are display and provenance.

IDs are authority.

```text
CurriculumPack
      |
      v
CurriculumTopic / CurriculumConcept / LearningOutcome IDs
      |
      v
EducationalIdentity
      |
      v
Canonical mastery spine
      |
      v
Evaluation -> Mastery -> Tutor -> Parent -> Principal
```

Free-text topic labels may remain visible to teachers and parents, but they
must not remain the long-term source of truth for mastery aggregation,
intervention targeting, tutor grounding, or learning analytics.

---

## 3. Why this design gate is needed now

The repository already contains both sides of the future platform:

1. A curriculum/EUI identity spine:
   - `CurriculumPack`
   - `CurriculumChapter`
   - `CurriculumTopic`
   - `CurriculumConcept`
   - `CurriculumLearningOutcome`
   - `EducationalIdentity`
   - EKG proposal foundations

2. A mastery and learning-intelligence system that still primarily aggregates
   by free-text topic:
   - `Exam.topic`
   - `Exam.question_schema[].topic`
   - `StudentTopicMastery.topic`
   - `StudentTopicMastery.topic_display`
   - `MasteryFlag.topic`
   - `MasteryFlag.evidence.topic`
   - tutor / parent / student surfaces reading `mastery_topic`

The current implementation is useful and validated, but it creates long-term
risks:

- renamed topics may split mastery history;
- duplicate topic names across chapters may collapse incorrectly;
- multilingual labels may not map to the same concept;
- concept-level tutor recommendations need a stronger source than title
  matching;
- parent/principal insights can drift if each consumer maps topics separately;
- future curriculum rollover needs durable lineage, not only labels.

This gate exists so StudyNexs can move from topic-label mastery to
curriculum-identity mastery without destabilizing current product behavior.

---

## 4. Current repository observations

### 4.1 Mastery ledger

Current mastery storage is topic-label based:

- `StudentTopicMastery.topic`
- `StudentTopicMastery.topic_display`
- unique key: `student_id`, `subject_id`, `academic_year_id`, `topic`

The deterministic computation path is intentionally good:

- no LLM in mastery math;
- weighted by exam type and recency;
- history frozen for explainability;
- flags are teacher-reviewed before parent notification.

The issue is not the mastery math.

The issue is the aggregation key.

### 4.2 Topic computation

`topic_pcts_for_mark()` currently derives mastery buckets from:

- `question_schema[].topic`;
- fallback `Exam.topic`;
- normalized free-text via `normalize_topic()`.

This is reliable for simple same-label cases, but it cannot distinguish:

- same topic name in different chapters;
- renamed topics;
- equivalent labels across languages;
- topic versus concept versus learning objective;
- curriculum-pack version lineage.

### 4.3 Weak concept links

`StudentWeakConceptService.sync_from_ledger()` already bridges mastery to the
knowledge graph, but it maps ledger topic display text back to concepts by topic
title.

That bridge is useful today, but it repeats inference that EUI should own.

### 4.4 EUI identity foundation

EUI already defines `EducationalIdentity` and can resolve curriculum entities.
That gives the product the right long-term anchor:

```text
topic label -> CurriculumTopic.id -> EducationalIdentity.id
concept label -> CurriculumConcept.id -> EducationalIdentity.id
learning objective -> CurriculumLearningOutcome.id -> EducationalIdentity.id
```

The design challenge is not inventing identity.

The challenge is adopting identity into mastery safely.

---

## 5. Target concept: Mastery Spine Reference

Future implementation should introduce a canonical internal contract, not loose
dictionaries, for the learning-intelligence spine.

Suggested conceptual model:

```text
MasterySpineReference

tenant_id
school_id
academic_year_id
class_id
subject_id
pack_id
chapter_id
topic_id
concept_id
learning_outcome_id
educational_identity_id
spine_level
label
language
provenance
metadata
```

Where:

- `topic_id`, `concept_id`, and `learning_outcome_id` refer to existing
  curriculum/EKG entities where available;
- `educational_identity_id` refers to the stable EUI identity string;
- `label` is display-only;
- `provenance` records how the reference was resolved;
- unresolved or ambiguous cases preserve legacy labels and mark the reference as
  non-authoritative.

The design preference is:

```text
canonical ID present -> use canonical spine
canonical ID absent but label present -> legacy-compatible fallback
ambiguous label -> no automatic source switch
```

---

## 6. Target product flow

The long-term product loop should become:

```text
Approved CurriculumPack
        |
        v
Question / paper / exam tagged with canonical spine references
        |
        v
AEI teacher-approved evaluation evidence
        |
        v
Mastery recompute by canonical topic/concept identity
        |
        v
Weakness flags with canonical evidence
        |
        v
Tutor / parent / principal intelligence consumes approved mastery evidence
```

The immediate next implementation should not jump directly to this final state.
It should prove the bridge passively first.

---

## 7. Responsibilities

Topic-ID / mastery spine unification is responsible for:

- defining how mastery evidence references canonical curriculum IDs;
- preserving existing deterministic mastery math;
- replacing repeated topic-label inference with a shared resolution boundary;
- allowing future dual-read comparison between label-based and ID-based mastery;
- preserving teacher-approved evidence as the downstream authority;
- giving tutor, parent, and principal intelligence a stable learning-evidence
  reference;
- preserving tenant isolation and curriculum-pack/version boundaries.

It is not responsible for:

- changing AEI scoring or grading;
- changing teacher review workflow;
- introducing autonomous learning recommendations;
- changing parent/student/principal UI in this design gate;
- replacing the Educational Knowledge Graph;
- creating a new curriculum system;
- making EUI source-of-truth for AEI;
- implementing annual rollover;
- solving all historical data migration in one step.

---

## 8. Non-goals

This design does not attempt to:

- redesign mastery scoring;
- redesign weakness flag rules;
- implement a general graph database;
- replace `CurriculumPack`;
- replace `EducationalIdentity`;
- make topic labels disappear from UI;
- auto-merge all historical topic labels;
- infer curriculum alignment with an LLM;
- introduce new product claims;
- expose internal EUI evidence to parents or students directly.

---

## 9. Proposed migration strategy

The future implementation should be phased and reversible.

### Phase A — Passive spine resolution

Purpose:

Resolve existing exam/question/mastery topic labels to canonical
`MasterySpineReference` objects without changing stored mastery outputs.

Expected behavior:

- read current exam topic metadata;
- use existing EUI identity resolver and curriculum pack data;
- record internal resolution evidence;
- do not write canonical mastery rows;
- do not change UI/API responses;
- do not change flags or tutor recommendations.

Success criterion:

The system can say, internally:

> This mastery label would resolve to this curriculum topic/concept identity,
> or it is ambiguous/unresolved.

### Phase B — Additive schema readiness

Purpose:

Prepare the mastery ledger and flags to hold canonical spine references while
preserving legacy topic fields.

Possible additive fields, subject to future contract:

- `pack_id`
- `topic_id`
- `concept_id`
- `learning_outcome_id`
- `educational_identity_id`
- `spine_level`
- `spine_resolution_status`
- `spine_provenance`

Constraints:

- additive only;
- reversible migration posture;
- no destructive removal of legacy `topic` fields;
- no source switch.

### Phase C — Dual-write / dual-read proof

Purpose:

Compute legacy label-based mastery and canonical-ID mastery side by side.

Expected behavior:

- legacy mastery remains source of truth;
- canonical mastery output is internal evidence only;
- divergence is measured, classified, and certified;
- ambiguous or unresolved spine references never silently alter mastery.

### Phase D — Narrow source adoption

Purpose:

For stable, unambiguous supported curriculum scopes, allow canonical spine
references to become the selected mastery aggregation source.

Hard constraints:

- teacher/parent/student visible output must remain explainable;
- rollback must return to legacy topic-label aggregation;
- source adoption must be per supported scope, not global;
- ARM must authorize a separate implementation contract.

### Phase E — Consumer migration

Purpose:

Move consumers one at a time:

- tutor;
- student weakness dashboard;
- parent explanation;
- principal trends;
- intervention center.

Each consumer migration requires separate authorization and proof.

---

## 10. Resolution precedence

Future implementation should use deterministic precedence.

Recommended order:

1. Explicit curriculum ID already attached to question/exam/evidence.
2. EducationalIdentity metadata with curriculum entity IDs.
3. Approved `CurriculumPack` entity lookup within tenant/class/subject/year.
4. Exact topic/concept label match within the approved pack.
5. Normalized label match within the approved pack.
6. Legacy free-text topic fallback.
7. Ambiguous/unresolved result.

Important rule:

Lower-precedence sources must not override higher-precedence sources.

Conflicts must be recorded as passive evidence, not silently resolved.

---

## 11. Ambiguity behavior

Ambiguity is expected and should be safe.

Ambiguous cases include:

- same topic label appears in multiple chapters;
- label maps to multiple concepts;
- curriculum pack is missing or not approved;
- exam/class/subject/year context is incomplete;
- multilingual label has more than one possible canonical identity;
- historical topic label no longer exists in the current pack.

Expected behavior:

```text
Ambiguous input
      |
      v
Structured ambiguity evidence
      |
      v
Legacy behavior preserved
      |
      v
No consumer source switch
```

No future implementation may treat ambiguity as permission to guess.

---

## 12. Data authority model

| Data | Authority |
|---|---|
| Curriculum structure | Approved `CurriculumPack` and EUI Educational Identity |
| Evaluation decision | Teacher-approved AEI evidence |
| Mastery calculation | Deterministic mastery service |
| Learning recommendation | Approved mastery evidence plus consumer-specific policy |
| Parent/student display | Approved evidence only |
| Labels | Display/provenance only |

The spine unification work must not make AI-generated labels authoritative.

---

## 13. Observability expectations

Future implementation should record operational evidence, not student-facing
analytics.

Suggested metrics:

```text
mastery_spine.resolve.invoked
mastery_spine.resolve.completed
mastery_spine.resolve.failed
mastery_spine.resolve.ambiguous
mastery_spine.resolve.unresolved
mastery_spine.resolve.legacy_fallback
mastery_spine.resolve.duration
mastery_spine.dual_read.divergence
```

Metric labels must be low-cardinality and must not include student names, raw
answers, or raw topic text.

---

## 14. Golden Harness expectations

Future implementation should expand Golden Harness coverage before any source
switch.

Required case families:

- exact topic ID match;
- exact concept ID match;
- label-only legacy fallback;
- duplicate topic labels across chapters;
- renamed topic with known lineage;
- multilingual label mapping;
- missing approved pack;
- ambiguous label;
- topic-level versus concept-level aggregation;
- annual rollover / pack-version boundary;
- unresolved historical label.

The harness should prove:

- same input resolves deterministically;
- ambiguous inputs do not switch source;
- legacy output remains unchanged in passive/dual-read modes;
- canonical IDs preserve tenant/class/subject/year boundaries.

---

## 15. Feature flag posture

Future implementation should remain controlled by default-off flags.

Suggested flag families:

```text
MASTERY_SPINE_PASSIVE_ENABLED=false
MASTERY_SPINE_DUAL_READ_ENABLED=false
MASTERY_SPINE_SOURCE_ADOPTION_ENABLED=false
```

Only the lowest necessary flag should be authorized in each future
implementation contract.

No source-adoption flag should be enabled before passive and dual-read evidence
is certified.

---

## 16. Runtime constraints

Future implementation must preserve:

- tenant isolation through server-derived `school_id`;
- existing mastery math until a separate source-adoption contract;
- existing API response compatibility;
- existing UI behavior until separately authorized;
- existing teacher-review and parent-notification governance;
- existing AEI/EUI contract boundaries;
- rollback by disabling the relevant flag.

---

## 17. Explicit exclusions

This design brief does not authorize:

- production code changes;
- database schema changes;
- migrations;
- API changes;
- UI changes;
- mastery source switching;
- tutor migration;
- parent/student/principal behavior changes;
- AEI behavior changes;
- EUI contract changes;
- LLM inference;
- automatic historical backfill;
- deletion of legacy topic fields;
- product capability claim expansion.

---

## 18. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

```text
docs/product/learning-intelligence/
TOPIC_ID_MASTERY_SPINE_UNIFICATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Recommended first implementation scope:

```text
Phase A — Passive mastery spine resolution only
```

It should authorize only:

- internal `MasterySpineReference` model;
- deterministic resolver;
- read-only curriculum/EUI lookup;
- passive observer;
- default-off feature flag;
- Golden Harness readiness cases;
- metrics/logging;
- certification report.

It should explicitly exclude:

- schema changes;
- source switching;
- dual-write;
- consumer migration;
- UI/API changes;
- tutor/parent/principal behavior changes.

---

## 19. Acceptance criteria for this design brief

This design brief may be accepted if ARM agrees that it:

- correctly identifies the current topic-label versus ID-spine split;
- preserves existing mastery behavior until separately authorized;
- uses EUI Educational Identity and existing curriculum entities as the future
  canonical spine;
- defines ambiguity and precedence behavior;
- sequences migration through passive, additive, dual-read, source-adoption, and
  consumer-migration stages;
- keeps implementation separately gated.

---

## 20. ARM review posture

ARM decision:

```text
Design brief accepted.
Implementation not authorized.
Next required action: implementation authorization contract review.
```
