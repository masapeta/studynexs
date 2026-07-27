# EUI Runtime Phase 6 Design Brief - Trust Framework

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 6 - Trust Framework
- **Roadmap mapping:** Trust Framework runtime phase
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Architecture baseline:** [`../../../architecture/eui/TRUST_FRAMEWORK.md`](../../../architecture/eui/TRUST_FRAMEWORK.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Depends on:** Phase 1 - Educational Identity; Phase 2 - Educational Context Engine; Phase 3 - Platform Capability Registry; Phase 4 - Knowledge Acquisition Intelligence Candidate Foundation; Phase 5 - Educational Knowledge Graph Proposal Foundation
- **ARM review:** Accepted with deterministic trust, posture precedence, dimension-shape, and visibility-boundary clarifications incorporated

---

## 1. Purpose

The Trust Framework answers:

> How does StudyNexs explain how reliable an educational artifact, recommendation, evaluation signal, or graph proposal is without hiding uncertainty behind a single confidence score?

StudyNexs already has several trust-related placeholders:

- KAI has trust signals for acquisition candidates.
- EKG proposals have trust placeholders.
- Educational Context records conflicts and ambiguities.
- Platform Capability Registry records support posture.
- AEI has confidence, policy, and teacher-review concepts.

Those are useful but fragmented. Phase 6 should define a common Trust Report
contract that can sit beside existing outputs and explain uncertainty in a
consistent, reviewable way.

This design brief does not authorize implementation.

---

## 2. Core principle

Trust is a report, not a score.

A single value like `91%` is not enough for school workflows. Teachers and
leaders need to know which part is trustworthy and which part needs review.

Trust must answer:

```text
What do we know?
How do we know it?
Where are we uncertain?
What review posture is required?
What may downstream consumers safely use?
```

Trust must not silently create academic authority.

---

## 3. Why Trust Framework is needed now

The first five EUI runtime phases created the educational substrate:

| Phase | Capability | Trust-relevant output |
|---|---|---|
| Phase 1 | Educational Identity | Identity provenance and resolution scope. |
| Phase 2 | Educational Context Engine | Conflicts, ambiguity, field sources. |
| Phase 3 | Platform Capability Registry | Capability mode and review posture. |
| Phase 4 | Knowledge Acquisition Intelligence | Input/extraction/language confidence placeholders. |
| Phase 5 | Educational Knowledge Graph Expansion | Candidate graph relationship posture. |

Without a shared Trust Report, each future consumer could interpret these
signals differently.

That would create inconsistent teacher explanations, unsafe parent messaging,
and fragile consumer migration.

Phase 6 should establish the common trust language before consumers migrate.

---

## 4. Responsibilities

The Trust Framework is responsible for designing how StudyNexs represents:

- input quality;
- extraction quality;
- OCR confidence;
- language confidence;
- understanding confidence;
- subject confidence;
- reasoning confidence;
- policy confidence;
- evidence availability;
- human review status;
- auditability;
- capability mode;
- warnings;
- manual-review signals;
- consumer-safe explanation posture.

It is not responsible for:

- determining Educational Identity;
- resolving Educational Context;
- acquiring content from files or OCR;
- creating graph relationships;
- evaluating answers;
- assigning marks;
- replacing AEI policy or teacher review;
- changing UI explanations;
- changing parent/student/principal output;
- making product capability claims.

---

## 5. Provenance and trust boundary

This boundary is non-negotiable:

```text
Provenance answers: where did this come from?
Trust answers: how reliable is it and what review posture is required?
```

Examples:

| Question | Belongs to |
|---|---|
| Uploaded by which teacher? | Provenance |
| Extracted from which PDF page? | Provenance |
| Which CurriculumPack version? | Provenance |
| Is OCR reliable enough? | Trust |
| Does this require teacher review? | Trust |
| Is evidence available? | Trust |

Trust Reports may reference provenance summaries, but they must not replace
provenance records or merge source lineage into a confidence score.

---

## 6. Trust Report contract

The eventual runtime implementation should define a canonical Trust Report
object.

Conceptual shape:

```text
TrustReport
  id
  tenant_id
  subject_ref
  subject_type
  overall_posture
  input_quality
  extraction_quality
  ocr_confidence
  language_confidence
  understanding_confidence
  subject_confidence
  reasoning_confidence
  policy_confidence
  evidence_available
  human_review_status
  auditability
  capability_mode
  warnings[]
  review_required
  consumer_visibility
  provenance_refs[]
  metadata
```

This is a contract concept, not a database schema authorization.

Phase 6 design does not authorize persistence.

---

## 7. Trust dimension contract

Trust dimensions should be structured, not loose numbers.

Conceptual shape:

```text
TrustDimension
  status
  score
  reason
  evidence_refs[]
  warnings[]
  metadata
```

Suggested dimension statuses:

| Status | Meaning |
|---|---|
| `strong` | Signal is sufficient for the supported scope. |
| `partial` | Signal exists but has limitations. |
| `weak` | Signal is low quality or low confidence. |
| `missing` | Required signal is absent. |
| `unsupported` | Signal cannot be produced safely for this capability. |
| `not_applicable` | Dimension does not apply to this subject type. |

Scores, where present, should explain a dimension. They should not replace the
dimension status or reason.

The first implementation should not average dimension scores into authority.

---

## 8. Trust dimensions

Initial dimensions should follow the accepted EUI architecture.

| Dimension | Meaning |
|---|---|
| Input quality | Source readability, completeness, suitability. |
| Extraction quality | Whether acquisition produced reliable text or structure. |
| OCR confidence | Machine transcription reliability, where OCR exists. |
| Language confidence | Language, script, and code-mixing reliability. |
| Understanding confidence | Whether EUI understood the artifact meaningfully. |
| Subject confidence | Whether subject capability is inside supported scope. |
| Reasoning confidence | Whether reasoning is deterministic or uncertain. |
| Policy confidence | Whether workflow policy applied cleanly. |
| Evidence availability | Whether citable evidence exists. |
| Human review status | Draft, reviewed, approved, overridden, or required. |
| Auditability | Whether inputs, context, decisions, and provenance can be traced. |
| Capability mode | Supported, assist, checklist, manual-review, unsupported, or expansion. |

The first implementation should not require every dimension to be populated for
every subject. Missing dimensions should be explicit rather than silently
treated as high trust.

---

## 9. Overall posture

Trust Reports should expose a conservative overall posture.

Suggested initial postures:

| Posture | Meaning |
|---|---|
| `trusted` | All required signals are strong and evidence/provenance exist. |
| `review_recommended` | Some uncertainty exists; human review should happen before authority. |
| `manual_review_required` | The output must not be used authoritatively without human review. |
| `unsupported` | The platform does not support this capability or input safely. |
| `insufficient_evidence` | Required evidence is missing or too weak. |

The first runtime implementation should be conservative. It is safer to route
uncertainty to review than to overstate trust.

### Posture precedence

Overall posture should be derived by conservative precedence, not by averaging
dimension scores.

Recommended precedence:

1. `unsupported`
2. `manual_review_required`
3. `insufficient_evidence`
4. `review_recommended`
5. `trusted`

Examples:

- Any unsupported required dimension should produce `unsupported`.
- Any mandatory review signal should produce `manual_review_required`.
- Missing required evidence should produce `insufficient_evidence`.
- Weak or partial non-blocking signals should produce `review_recommended`.
- `trusted` should require all required dimensions to be strong or explicitly
  not applicable.

This prevents a high OCR score from masking an unsupported capability, missing
evidence, or unreviewed candidate source.

---

## 10. Compatibility with existing confidence fields

Phase 6 must not remove or replace existing confidence fields immediately.

Instead, Trust Reports should run alongside existing fields.

Examples:

```text
existing confidence field
        +
Trust Report dimension
        +
compatibility mapping
```

This protects existing consumers while allowing future migration.

Confidence-to-trust mapping should be explicit, not implicit. For example:

| Existing signal | Trust dimension |
|---|---|
| KAI extraction confidence | Extraction quality / OCR confidence |
| KAI language confidence | Language confidence |
| Context ambiguity count | Understanding confidence / auditability warning |
| Capability mode | Capability mode / subject confidence |
| EKG proposal status | Evidence availability / auditability |
| AEI policy decision | Policy confidence / human review status |

---

## 11. Deterministic trust generation

The first Trust Framework implementation should be deterministic.

It should not call an LLM or external AI provider to decide trust posture,
dimension status, or review requirement.

Allowed early sources:

- existing numeric confidence fields;
- existing review status fields;
- existing ambiguity/conflict metadata;
- existing capability modes;
- existing provenance references;
- deterministic contract mappings.

LLMs may later help generate human-readable explanations only if separately
authorized, reviewed, and guarded. They must not become the source of trust
truth.

---

## 12. Review and authority behavior

Trust affects workflow readiness. It does not create final academic authority.

Rules:

1. Low trust routes to review.
2. Unsupported trust posture must not produce polished authoritative output.
3. Parent/student-facing explanations require approved, non-alarming language.
4. Internal trust metadata may be more technical than user-facing explanations.
5. Teacher-approved evidence remains the source of consequential academic output.
6. Trust Reports should help humans decide; they should not replace human authority.

---

## 13. Consumer visibility

Trust Reports should distinguish internal technical detail from future
consumer-safe explanations.

Suggested visibility levels:

| Visibility | Meaning |
|---|---|
| `internal_only` | Technical diagnostics for engineering/operations. |
| `teacher_safe` | Can be shown to teachers with clear review language. |
| `school_leader_safe` | Can be summarized for principal/management review. |
| `parent_safe` | Requires teacher-approved, non-alarming wording. |
| `student_safe` | Requires supportive, age-appropriate wording. |

Phase 6 design does not authorize UI copy or consumer messaging changes.

Visibility labels are classification metadata, not permission to display.

For example, a Trust Report marked `parent_safe` still must not be shown to a
parent until a later consumer migration explicitly authorizes the parent-facing
surface and copy.

---

## 14. Relationship to existing EUI layers

Trust Framework consumes signals from previous EUI foundations.

```text
Educational Identity
        ↓
Educational Context
        ↓
Platform Capability Registry
        ↓
KAI Candidate
        ↓
EKG Proposal
        ↓
Trust Report
```

Expected inputs:

| Source | Trust contribution |
|---|---|
| Educational Identity | Identity resolution confidence, provenance availability. |
| Educational Context | Conflicts, ambiguity, field-source auditability. |
| Platform Capability Registry | Capability mode, support posture, review requirement. |
| KAI Candidate | Input quality, extraction quality, language/OCR confidence, review status. |
| EKG Proposal | Relationship posture, evidence availability, ambiguity, provenance. |
| AEI | Reasoning, policy, teacher-review signals in a later authorized integration. |

Phase 6 should not require any earlier EUI layer to change shape unless a
separate compatibility review approves it.

---

## 15. Subject scope for first implementation

The first implementation should focus on EUI-owned subjects only.

Recommended initial subject types:

- `educational_context`;
- `platform_capability_lookup`;
- `kai_candidate`;
- `ekg_relationship_proposal`.

AEI Trust Report integration should remain deferred unless a future
implementation authorization explicitly includes it. This preserves AEI's
protected status and avoids changing evaluation behavior during Phase 6.

---

## 16. Scope for the first implementation authorization

If this design brief is accepted, the first implementation authorization should
remain narrow.

Recommended first implementation scope:

1. Define immutable Trust Report contracts.
2. Define trust dimension value objects.
3. Define deterministic Trust Report ID generation.
4. Add builders/mappers from existing EUI signals:
   - KAI candidate;
   - EKG relationship proposal;
   - Educational Context ambiguity/conflict;
   - Platform Capability Registry result.
5. Add a passive observer behind `EUI_TRUST_REPORT_ENABLED=false`.
6. Add Golden Harness cases for trust dimensions and provenance separation.
7. Add certification evidence proving existing confidence consumers still work.

Recommended first implementation exclusion:

- no UI;
- no persistence;
- no API;
- no consumer migration;
- no AEI behavior change;
- no workflow enforcement.

---

## 17. Explicit non-goals

Phase 6 is deliberately not attempting to:

- replace AEI policy;
- replace teacher review;
- assign marks;
- decide final correctness;
- change evaluation behavior;
- change tutor behavior;
- change parent/student/principal surfaces;
- implement UI trust badges;
- create public trust explanations;
- persist Trust Reports;
- introduce a Trust Report API;
- remove existing confidence fields;
- migrate any consumer;
- implement Trust Framework in AEI;
- call an LLM to decide trust posture;
- generate public trust explanations;
- auto-approve KAI candidates;
- make EKG proposals trusted;
- create product capability claims.

This phase is about trust contracts and passive trust-report generation design,
not rollout.

---

## 18. Runtime posture

If later authorized, the first Phase 6 runtime implementation should be:

- passive;
- default-off;
- deterministic where possible;
- contract-first;
- provenance-aware;
- non-authoritative;
- exception-isolated;
- tenant-safe;
- invisible to users;
- compatible with existing confidence fields.

Existing confidence fields and existing consumer behavior must remain active
until a later certified migration.

---

## 19. Feature flag strategy

Phase 0 reserved the expected flag:

```text
EUI_TRUST_REPORT_ENABLED=false
```

Expected behavior if implemented later:

- default-off;
- environment configurable;
- no-op when disabled;
- produces Trust Reports beside existing outputs when enabled;
- does not remove existing confidence fields;
- rollback by disabling the flag;
- no UI/API/product behavior change.

The exact flag name and execution mode should be finalized in a future
implementation authorization contract.

---

## 20. Observability

Trust Framework observability should be operational, not product analytics.

Expected metrics may include:

```text
eui_trust_report.invoked
eui_trust_report.completed
eui_trust_report.failed
eui_trust_report.manual_review
eui_trust_report.unsupported
eui_trust_report.insufficient_evidence
eui_trust_report.duration
```

Structured logs should capture low-cardinality technical details only:

- subject type;
- overall posture;
- review requirement;
- missing dimension count;
- warning count;
- capability mode;
- duration;
- failure category.

Logs and metrics must not include:

- student names;
- raw answers;
- uploaded document text;
- parent data;
- tenant slugs;
- raw OCR text;
- free-text teacher notes;
- sensitive educational evidence.

---

## 21. Testing strategy

Future implementation should include focused tests and Golden Harness coverage.

### Unit tests

Expected coverage:

- Trust Report model validation;
- strict field rejection;
- deterministic Trust Report IDs;
- provenance references remain separate from trust dimensions;
- posture precedence;
- KAI candidate trust mapping;
- EKG proposal trust mapping;
- context conflict/ambiguity trust mapping;
- unsupported capability posture;
- manual-review posture;
- default-off passive observer behavior if introduced;
- exception isolation if passive observer is introduced.

### Golden Harness

Golden cases should cover:

- high-quality KAI candidate with complete identity/context;
- low-confidence OCR candidate requiring review;
- ambiguous context producing trust warnings;
- unsupported capability producing unsupported posture;
- EKG candidate proposal remaining non-authoritative;
- evidence-available vs evidence-missing cases;
- provenance reference present but not merged into trust;
- parent/student visibility withheld for unapproved outputs;
- manual-review-required posture;
- compatibility mapping from existing confidence signals.
- unsupported dimension dominating otherwise strong signals.

### Regression verification

Before certification, validation should demonstrate:

- KAI tests still pass;
- EKG proposal tests still pass;
- Educational Context tests still pass;
- Platform Capability Registry tests still pass;
- existing confidence consumers still pass;
- AEI/evaluation regression slice still passes;
- API import succeeds;
- focused lint for Trust Framework files passes;
- `git diff --check` passes.

---

## 22. Certification criteria

Phase 6 should be accepted only if certification can truthfully state:

- Trust Report contracts exist as authorized;
- provenance and trust remain separate;
- Trust Reports run beside existing confidence fields;
- existing confidence consumers remain functional;
- overall posture follows conservative precedence;
- trust generation is deterministic and does not call LLMs;
- low-confidence or unsupported cases do not become authoritative;
- no consumer depends on Trust Reports;
- no AEI behavior changed;
- no API/UI/product behavior changed;
- no persistence or schema changes were introduced unless separately authorized;
- Golden Harness Trust Framework cases pass;
- existing EUI and AEI regression tests pass;
- rollback is verified;
- certification report is complete;
- phase retrospective is complete.

---

## 23. Relationship to later phases

Phase 6 prepares trust qualification for consumer migration. It does not migrate
consumers.

| Later phase | Relationship |
|---|---|
| AEI Consumer Migration | AEI may later use Trust Reports for review explanations and workflow readiness. |
| Teacher Copilot Migration | Recommendations may later display teacher-safe trust summaries. |
| AI Tutor Migration | Tutor may later use trust to choose fallback or ask for teacher-approved material. |
| Parent Assistant Migration | Parent-facing explanations must use approved evidence and parent-safe trust posture. |
| Principal Dashboard Migration | Trends may later distinguish measured evidence from weak/inferred signals. |
| Institutional Memory | School-specific trust preferences may later affect review posture. |

---

## 24. ARM review gate

This design brief has been accepted by ARM as the Phase 6 Trust Framework
design baseline.

It does not authorize:

- implementation;
- production code changes;
- schema changes;
- API changes;
- UI changes;
- consumer migration;
- AEI behavior changes;
- Trust Report persistence;
- LLM-based trust generation;
- workflow enforcement;
- parent/student-facing explanations;
- product capability claims.

If ARM accepts this brief, the next governance action should be a Phase 6 Trust
Framework Implementation Authorization Contract defining:

- exact implementation scope;
- permitted files/modules;
- feature flag name;
- Trust Report contract boundaries;
- Golden Harness requirements;
- observability requirements;
- rollback proof;
- certification evidence;
- explicit exclusions.
