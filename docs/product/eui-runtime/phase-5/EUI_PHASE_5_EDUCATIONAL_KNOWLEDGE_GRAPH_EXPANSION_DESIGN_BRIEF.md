# EUI Runtime Phase 5 Design Brief - Educational Knowledge Graph Expansion

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 5 - Educational Knowledge Graph Expansion
- **Roadmap mapping:** Educational Knowledge Graph Expansion runtime phase
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Architecture baseline:** [`../../../architecture/eui/EDUCATIONAL_KNOWLEDGE_GRAPH.md`](../../../architecture/eui/EDUCATIONAL_KNOWLEDGE_GRAPH.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Depends on:** Phase 1 - Educational Identity; Phase 2 - Educational Context Engine; Phase 3 - Platform Capability Registry; Phase 4 - Knowledge Acquisition Intelligence Candidate Foundation
- **ARM review:** Accepted with proposal-first and schema-boundary clarifications incorporated

---

## 1. Purpose

Educational Knowledge Graph Expansion answers:

> How does StudyNexs connect educational identities, contexts, capabilities, and acquired candidates into a governed graph of educational relationships?

StudyNexs already has an implementation-aligned Knowledge Graph spine for curriculum structure and concept relationships. Phase 5 should expand that spine toward the accepted EUI architecture without creating a second graph system or allowing unreviewed educational material to become trusted knowledge.

The intent is to move from:

```text
Curriculum spine
```

to:

```text
Curriculum spine
      +
Educational Identity links
      +
Learning objective / competency relationships
      +
Candidate evidence relationships
      +
Provenance-aware graph posture
```

This design brief does not authorize implementation.

---

## 2. Why Educational Identity, Context, Capability Registry, and KAI are not enough

The first four EUI runtime phases establish important platform primitives:

| Phase | Capability | What it answers |
|---|---|---|
| Phase 1 | Educational Identity | What educational object is this? |
| Phase 2 | Educational Context Engine | In what educational situation is it used? |
| Phase 3 | Platform Capability Registry | What does the platform claim for this scope? |
| Phase 4 | Knowledge Acquisition Intelligence | What candidate educational artifact was acquired? |

Those foundations still do not answer relationship questions such as:

- Which concepts belong to this learning objective?
- Which competency does this question assess?
- Which prerequisite concept is needed before this topic?
- Which KAI candidate can become evidence after review?
- Which misconception relates to this answer pattern?
- Which intervention maps to this concept gap?

Those are graph questions. If each consumer answers them independently, StudyNexs will accumulate private concept maps inside evaluation, tutoring, lesson planning, analytics, and reporting.

Phase 5 exists to prevent that drift.

---

## 3. Core principle

EKG owns educational relationships. Consumers do not maintain private concept maps.

Educational Identity gives stable references.
Educational Context gives situational meaning.
KAI gives candidate artifacts.
EKG connects them through governed relationships.

```text
Educational Identity
        ↓
Educational Context
        ↓
KAI Candidate
        ↓
Educational Knowledge Graph
        ↓
Future consumers
```

During Phase 5, graph expansion must remain conservative:

- existing Knowledge Graph behavior remains stable;
- new relationships must be provenance-aware;
- candidate-derived relationships must remain non-authoritative unless explicitly approved;
- no downstream consumer may depend on new graph relationships until later migration authorization.

---

## 4. Existing graph boundary

StudyNexs already has a Knowledge Graph implementation built around:

- curriculum concepts;
- tenant-scoped graph edges;
- pack-derived curriculum spine;
- question-to-concept links;
- student weak-concept links.

Phase 5 should extend this existing graph model and service boundary.

It must not introduce:

- a second graph database;
- a parallel graph service;
- a private EUI-only graph store;
- a consumer-specific concept map;
- direct graph writes outside approved graph services.

If implementation later reveals that the existing model cannot support a required relationship safely, that should trigger a separate ARM review and, if needed, an ADR. It should not be solved by quietly creating a bypass.

### Schema and enum boundary

The existing Knowledge Graph implementation uses database-backed graph tables and
enumerated node/edge types. Expanding those persisted enums or adding new graph
tables is a schema change.

The first Phase 5 implementation authorization should not assume schema or enum
changes. It should begin with relationship proposal contracts and read-only
resolution unless ARM explicitly authorizes a migration.

This avoids turning a design expansion into a hidden persistence expansion.

---

## 5. Responsibilities

Educational Knowledge Graph Expansion is responsible for designing how StudyNexs represents and governs:

- identity-linked graph references;
- learning objective relationships;
- competency relationships;
- prerequisite relationships;
- candidate evidence relationships;
- misconception relationships;
- intervention mappings;
- provenance metadata on new relationship types;
- review posture for untrusted or candidate-derived graph relationships;
- compatibility with existing Knowledge Graph queries.

It is not responsible for:

- replacing Educational Identity;
- replacing Educational Context;
- acquiring content from files or OCR;
- evaluating student answers;
- updating AEI behavior;
- changing tutor prompts;
- changing teacher, student, parent, or principal UI;
- creating product capability claims;
- implementing the full Trust Framework;
- migrating any consumer to depend on new graph relationships.

---

## 6. Relationship to existing EUI layers

Phase 5 should consume the existing EUI foundations instead of redefining them.

```text
Educational Identity
        ↓
Educational Context
        ↓
Platform Capability Registry
        ↓
Knowledge Acquisition Intelligence Candidate
        ↓
Educational Knowledge Graph Expansion
```

Expected relationships:

| EUI layer | Phase 5 usage |
|---|---|
| Educational Identity | Stable IDs anchor graph nodes and relationships. |
| Educational Context | Determines board, curriculum, grade, subject, language, assessment mode, and tenant posture. |
| Platform Capability Registry | Determines whether a relationship type or evidence posture is supported, assistive, manual-review, unsupported, or expansion. |
| KAI Candidate Foundation | Supplies candidate artifacts that may later become graph evidence after review. |

Phase 5 should not require any earlier EUI layer to change shape unless a separate compatibility review approves it.

---

## 7. Graph relationship categories

Phase 5 should define a bounded relationship vocabulary before implementation.

Initial relationship categories should be considered in this order:

| Category | Examples | Initial posture |
|---|---|---|
| Identity link | `identity_id -> existing KG node` | Supported for selected curriculum scope. |
| Learning objective | `chapter/topic/concept -> learning_objective` | Supported if present in approved curriculum data. |
| Competency | `concept -> competency` | Supported or candidate depending on source. |
| Prerequisite | `concept -> prerequisite_concept` | Manual-review unless derived from approved curriculum. |
| KAI candidate evidence | `candidate -> identity/context/concept` | Candidate only; not trusted evidence. |
| Misconception | `answer_pattern/evidence -> misconception` | Future or manual-review in first implementation. |
| Intervention | `gap/concept -> intervention` | Future unless approved intervention data exists. |

The first implementation should not attempt to model every EKG relationship from the accepted architecture. It should select the smallest set required to safely connect existing KG spine nodes with EUI identities and KAI candidates.

---

## 8. Candidate-to-graph promotion model

KAI outputs must not become trusted graph knowledge automatically.

The design posture should be:

```text
KAI Candidate
      ↓
Graph relationship proposal
      ↓
Candidate edge / non-authoritative evidence
      ↓
Review or certification gate
      ↓
Trusted graph edge only when later authorized
```

Phase 5 design may define candidate relationship posture, but implementation should not make candidate relationships authoritative unless explicitly authorized.

Candidate-derived graph links should carry:

- source candidate ID;
- source type;
- provenance summary;
- capability mode;
- confidence or trust placeholders;
- review status;
- created-by-system marker;
- tenant scope where school-specific data is involved.

---

## 9. Graph relationship proposal contract

The first implementation should introduce a proposal-level contract before any
trusted graph persistence.

Conceptual shape:

```text
EducationalGraphRelationshipProposal
  id
  tenant_id
  relationship_category
  from_reference
  to_reference
  educational_identity_id
  educational_context_summary
  source_candidate_id
  capability_mode
  authority_posture
  provenance
  trust_placeholders
  ambiguity
  metadata
```

This proposal object is not a database schema authorization.

It exists to let the platform deterministically say:

```text
"This candidate or identity appears to relate to this graph target,
but this relationship is not authoritative yet."
```

Downstream consumers must not treat proposals as trusted graph knowledge.

---

## 10. Provenance requirements

Every new relationship type introduced through EKG expansion should preserve provenance.

Provenance should answer:

- which source created the relationship;
- whether the source was approved, candidate, inferred, or manual;
- which curriculum pack or artifact produced it;
- which version or checksum was used where applicable;
- whether a human reviewed it;
- whether it is tenant-specific or curriculum-global.

Provenance must remain distinct from trust.

```text
Provenance: where did this relationship come from?
Trust: how reliable is it and can consumers use it?
```

Phase 5 should not collapse these into one `confidence` field.

---

## 11. Trust and authority posture

Until the Trust Framework phase is implemented, EKG expansion should use conservative review posture fields or metadata.

Suggested postures:

| Posture | Meaning |
|---|---|
| `trusted` | Derived from approved curriculum source or explicitly reviewed source. |
| `candidate` | Proposed by KAI or deterministic mapping but not approved. |
| `needs_review` | Requires human or certification review before academic use. |
| `unsupported` | Relationship cannot be safely represented under current capability scope. |
| `ambiguous` | Multiple plausible graph targets exist. |

Only trusted relationships should be eligible for future consumer use. Candidate, ambiguous, unsupported, and review-required relationships should remain passive/internal until a later consumer migration explicitly permits them.

---

## 12. Scope for the first implementation authorization

If this design brief is accepted, the next implementation authorization should remain narrow.

Recommended first implementation scope:

1. Define EKG expansion relationship contracts or constants.
2. Add read-only graph relationship resolver/proposal logic where possible.
3. Link Educational Identity IDs to existing KG concepts for selected supported cases.
4. Represent candidate graph relationship proposals from KAI candidates without making them authoritative.
5. Add deterministic Golden Harness cases for identity-to-graph and candidate-to-graph proposal behavior.
6. Add passive observability and exception isolation if a runtime observer is introduced.

The first implementation should prefer passive, read-only, or proposal-only behavior.

Recommended first implementation exclusion:

- no database schema changes;
- no persisted enum expansion;
- no trusted graph writes;
- no consumer-facing graph behavior change.

Any write path must be separately justified in the implementation authorization
contract and must preserve existing KG behavior.

---

## 13. Explicit non-goals

Phase 5 is deliberately not attempting to:

- replace the existing Knowledge Graph implementation;
- create a graph database;
- create a second graph store;
- migrate AEI, tutor, teacher copilot, analytics, parent reports, or principal dashboards;
- expose new API endpoints;
- add UI graph editing;
- add graph visualizations;
- ingest additional files;
- implement OCR, LLM, ASR, or layout extraction;
- implement Trust Framework;
- auto-approve KAI candidate outputs;
- auto-create misconceptions from student answers;
- change mastery calculations;
- change student weak-concept behavior;
- change evaluation behavior;
- change CurriculumPack approval behavior;
- change product capability claims.
- expand persisted graph enums or tables unless separately authorized.

This phase is about graph expansion design, not consumer rollout.

---

## 14. Runtime posture

If later authorized, the first Phase 5 runtime implementation should be:

- tenant-safe;
- deterministic where possible;
- provenance-aware;
- candidate-aware;
- exception-isolated;
- feature-flagged if any runtime path is introduced;
- backward-compatible with existing KG queries;
- invisible to users;
- non-authoritative for KAI-derived data.

Existing graph reads and writes must remain the source of truth until a later certified switch.

---

## 15. Feature flag strategy

Phase 0 reserved the expected flag:

```text
EUI_EKG_EXPANSION_ENABLED=false
```

Expected behavior if implemented later:

- default-off;
- environment configurable;
- no-op when disabled;
- passive or proposal-only when enabled unless explicitly authorized otherwise;
- rollback by disabling the flag;
- no change to existing KG query behavior.

The exact flag name and execution mode should be finalized in a future implementation authorization contract.

---

## 16. Observability

EKG expansion observability should be operational and tenant-safe.

Expected metrics may include:

```text
eui_ekg.resolve_invoked
eui_ekg.resolve_completed
eui_ekg.resolve_failed
eui_ekg.identity_link_found
eui_ekg.identity_link_missing
eui_ekg.candidate_relationship_proposed
eui_ekg.ambiguous
eui_ekg.unsupported
eui_ekg.duration
```

Structured logs should capture low-cardinality technical details only:

- relationship category;
- source posture;
- result status;
- ambiguity count;
- capability mode;
- duration;
- failure category.

Logs and metrics must not include:

- student names;
- raw student answers;
- uploaded document text;
- parent data;
- tenant slugs;
- raw OCR text;
- free-text teacher notes.

---

## 17. Testing strategy

Future implementation should include focused tests and Golden Harness coverage.

### Unit tests

Expected coverage:

- identity-to-existing-KG node mapping;
- missing identity behavior;
- ambiguous graph target behavior;
- candidate relationship proposal shape;
- provenance metadata preservation;
- trusted vs candidate posture separation;
- feature flag no-op if runtime observer is introduced;
- exception isolation if runtime observer is introduced;
- no regression to existing KG query behavior.
- no persisted enum/schema changes unless explicitly authorized.

### Golden Harness

Golden cases should cover:

- CBSE Grade 6 Science identity linked to an existing concept;
- learning objective linked to concept where approved curriculum data exists;
- KAI worksheet candidate proposing concept relationship;
- KAI answer-key candidate proposing question/answer-key relationship;
- duplicate or renamed concepts producing ambiguity;
- unsupported candidate source producing no trusted relationship;
- prerequisite proposal marked review-required unless approved;
- missing identity producing unresolved graph proposal;
- cross-board similar chapter names not collapsing into one identity;
- tenant-specific student/evidence relationship excluded from first implementation unless separately authorized.
- proposal IDs remain deterministic for identical inputs.

### Regression verification

Before certification, validation should demonstrate:

- existing Knowledge Graph tests still pass;
- existing graph query tests still pass;
- existing question-concept link tests still pass;
- existing student weak-concept link tests still pass;
- Educational Identity tests still pass;
- Educational Context tests still pass;
- Platform Capability Registry tests still pass;
- KAI tests still pass;
- AEI/evaluation regression slice still passes;
- API import succeeds;
- focused lint for EKG expansion files passes;
- `git diff --check` passes.

---

## 18. Certification criteria

Phase 5 should be accepted only if certification can truthfully state:

- existing Knowledge Graph behavior remains unchanged;
- no second graph store was introduced;
- no schema or persisted enum changes were introduced unless separately authorized;
- all new relationship definitions are tenant-safe where applicable;
- identity-linked graph relationships are deterministic for selected supported cases;
- candidate-derived relationships remain non-authoritative;
- provenance is preserved for new relationship proposals;
- ambiguity and unsupported cases are handled explicitly;
- no consumer depends on new EKG expansion output;
- no AEI behavior changed;
- no API/UI/product behavior changed unless separately authorized;
- Golden Harness EKG expansion cases pass;
- existing KG and EUI regression tests pass;
- rollback is verified;
- certification report is complete;
- phase retrospective is complete.

---

## 19. Relationship to later phases

Phase 5 prepares the graph backbone for later consumers. It does not migrate those consumers.

| Later phase | Relationship |
|---|---|
| Trust Framework | Trust Reports can later determine whether graph relationships are usable by consumers. |
| Institutional Memory | School-specific terminology and policy preferences may later attach to EKG relationships. |
| AEI Consumer Migration | AEI may later consume trusted concept/evidence relationships after explicit migration authorization. |
| AI Tutor Migration | Tutor grounding may later use trusted concept/prerequisite relationships. |
| Question Generator Migration | Question generation may later use trusted objective/concept/competency relationships. |
| Principal / Analytics Migration | Aggregates may later use trusted graph evidence, never candidate-only data. |

---

## 20. ARM review gate

This design brief has been accepted by ARM as the Phase 5 EKG Expansion design
baseline.

It does not authorize:

- implementation;
- production code changes;
- schema changes;
- API changes;
- UI changes;
- consumer migration;
- AEI behavior changes;
- KAI behavior expansion;
- Trust Framework implementation;
- LLM/OCR/ASR provider integration;
- graph writes;
- schema or persisted enum changes;
- product capability claims.

If ARM accepts this brief, the next governance action should be a Phase 5 EKG Expansion Implementation Authorization Contract defining:

- exact implementation scope;
- permitted files/modules;
- whether any graph writes are allowed;
- feature flag name and runtime mode;
- Golden Harness requirements;
- observability requirements;
- rollback proof;
- certification evidence;
- explicit exclusions.
