# EUI Runtime Phase 4 Design Brief — Knowledge Acquisition Intelligence

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 4 - Knowledge Acquisition Intelligence
- **Roadmap mapping:** Knowledge Acquisition Intelligence runtime phase
- **Classification:** Design brief
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27
- **Architecture baseline:** [`../../../architecture/eui/KNOWLEDGE_ACQUISITION_INTELLIGENCE.md`](../../../architecture/eui/KNOWLEDGE_ACQUISITION_INTELLIGENCE.md)
- **Runtime roadmap baseline:** [`../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md`](../EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md)
- **Depends on:** Phase 1 - Educational Identity; Phase 2 - Educational Context Engine; Phase 3 - Platform Capability Registry
- **ARM review:** Accepted with source-admission and provider-boundary clarifications incorporated

---

## 1. Purpose

Knowledge Acquisition Intelligence (KAI) answers:

> How does StudyNexs safely turn educational inputs into governed educational knowledge candidates?

Schools continuously produce educational material:

- PDFs;
- worksheets;
- scanned pages;
- images;
- answer keys;
- rubrics;
- teacher notes;
- lesson plans;
- board circulars;
- student work;
- future voice transcripts.

Without KAI, each consumer would be tempted to parse those materials itself.
That would create duplicated extraction logic, inconsistent provenance, weak
trust boundaries, and scattered educational interpretation.

KAI exists to provide one governed acquisition path:

```text
Educational input
      ↓
Acquisition
      ↓
Extraction
      ↓
Normalization
      ↓
Identity + Context association
      ↓
Capability posture lookup
      ↓
Candidate educational artifact
      ↓
Review / later authorized consumers
```

Phase 4 is design-only until ARM separately authorizes implementation.

---

## 2. Why KAI is needed now

StudyNexs now has three published passive EUI runtime foundations:

1. Phase 1 - Educational Identity: what educational object is this?
2. Phase 2 - Educational Context Engine: in what educational situation is it being used?
3. Phase 3 - Platform Capability Registry: what does the platform claim for this scope?

Earlier certification artifacts may refer to Phase 2 and Phase 3 as
`Phase 1 Sprint 2` and `Phase 1 Sprint 3`. Those names are historical
implementation-batch labels. The EUI Runtime Roadmap phase names are the source
of truth going forward.

KAI is the next dependency-order layer because acquisition needs all three:

- Identity anchors extracted artifacts to curriculum entities.
- Context explains where and how the artifact is being used.
- Capability Registry defines whether the extraction posture is supported,
  assistive, checklist-only, manual-review, unsupported, or expansion.

KAI should not lead with OCR or AI-provider implementation. It should lead with
contracts, provenance, candidate state, review posture, and passive acquisition
evidence.

---

## 3. Core principle

KAI produces candidates, not truth.

Machine-extracted educational content must never silently become authoritative
curriculum, evaluation evidence, tutor grounding, parent communication, or
analytics input.

The first implementation posture should be:

```text
Extract → normalize → attach provenance → mark confidence/review posture
      ↓
Candidate only
      ↓
No consumer depends on it
```

Human approval, certification, or later explicitly authorized consumer
migration is required before KAI output becomes authoritative.

---

## 4. Responsibilities

KAI is responsible for:

- representing educational acquisition inputs;
- recording source provenance;
- classifying input modality;
- representing extracted content;
- normalizing extracted content into safe internal structures;
- associating artifacts with Educational Identity where available;
- associating artifacts with Educational Context where available;
- consulting Platform Capability Registry for internal capability posture;
- producing candidate artifact records or value objects;
- marking unsupported, ambiguous, low-confidence, or review-required cases;
- generating operational evidence for certification.

KAI is not responsible for:

- final academic evaluation;
- updating the Educational Knowledge Graph as trusted knowledge;
- changing tutor behavior;
- changing question generation behavior;
- changing parent/principal reporting;
- making product capability claims;
- bypassing the AI Gateway;
- replacing human review.

---

## 5. Relationship to existing EUI layers

KAI consumes existing EUI foundations. It does not redefine them.

```text
Educational Identity
        ↓
Educational Context
        ↓
Platform Capability Registry
        ↓
Knowledge Acquisition Intelligence
```

KAI should reference these contracts rather than re-derive educational identity,
context, or capability posture independently.

If input lacks enough information to resolve identity or context, KAI should
produce a partial candidate with structured ambiguity rather than inventing
authority.

---

## 6. Candidate artifact contract

The eventual runtime implementation should define a canonical candidate object.

Conceptual shape:

```text
EducationalArtifactCandidate
  id
  tenant_id
  source
  source_reference
  artifact_type
  modality
  input_quality
  extracted_text
  extracted_regions
  normalized_content
  detected_language
  detected_script
  educational_identity_id
  educational_context_summary
  capability_mode
  provenance
  trust_signals
  review_status
  metadata
```

This is a contract concept, not a database schema authorization.

Phase 4 design does not authorize persistence.

---

## 7. Provenance and trust separation

KAI must preserve the EUI architecture distinction:

```text
Provenance answers: where did this come from?
Trust answers: how reliable is it?
```

Provenance examples:

- uploaded by teacher;
- imported from CurriculumPack;
- extracted from PDF page 4;
- derived from answer key file;
- generated by approved internal workflow;
- source version or checksum.

Trust signal examples:

- input quality;
- extraction confidence;
- language confidence;
- OCR confidence;
- capability mode;
- ambiguity count;
- review requirement;
- unsupported modality.

Phase 4 may define trust-signal placeholders for future Trust Framework
integration. It must not implement the full Trust Framework unless separately
authorized.

---

## 8. Supported acquisition surfaces for initial design

Phase 4 should begin with bounded acquisition surfaces.

| Surface | Initial posture |
|---|---|
| PDF | Candidate extraction; page/source provenance required. |
| OCR input | Candidate extraction; confidence and review posture required. |
| Worksheet | Candidate artifact; question/answer boundaries may be partial. |
| Answer key | Candidate artifact; never authoritative until approved. |
| Teacher note | Candidate artifact; local terminology retained. |
| Lesson plan | Candidate artifact; identity/context association where available. |

The design should not claim universal extraction quality for all layouts,
handwriting styles, languages, scans, or degraded images.

Unsupported or low-confidence inputs should resolve to candidate-only,
manual-review, or unsupported posture.

### Source admission boundary

Not every educational input is safe to acquire in the first KAI runtime
implementation.

The initial implementation authorization should explicitly define which source
types are admitted. Inputs outside that source list must resolve to
`unsupported` or `needs_review`, not silently enter the acquisition pipeline.

Student work is especially sensitive. Although KAI architecture eventually
includes student work as an input channel, the first implementation should not
ingest student work unless the implementation contract explicitly authorizes it
with tenant isolation, PII minimization, retention, and review safeguards.

---

## 9. Provider boundary

KAI is a governance and candidate-contract layer before it is an extraction
provider layer.

The first implementation should not introduce new OCR, LLM, ASR, layout parser,
or external AI-provider integrations unless the implementation authorization
contract explicitly permits them.

Allowed early approaches may include:

- manually supplied extracted text;
- deterministic metadata classification;
- stubbed extraction evidence for Golden Harness cases;
- read-only references to already-existing artifact metadata.

This keeps Phase 4 focused on safe candidate posture rather than provider
quality claims.

---

## 10. Capability Registry interaction

KAI should use the Platform Capability Registry to describe acquisition posture.

Examples:

```text
Hindi printed OCR → supported for declared scope
Hindi handwriting OCR → assist
Sanskrit handwriting OCR → manual_review
Pixel-perfect diagram grading → unsupported
```

KAI must not upgrade capability posture.

If the registry says `assist`, KAI output remains assistive.

If the registry says `manual_review`, KAI output must remain review-bound.

If the registry has no matching entry, KAI must not assume support.

---

## 11. Review posture

KAI candidate outputs should support a small review posture model.

Conceptual statuses:

| Status | Meaning |
|---|---|
| `candidate` | Extracted or represented, but not approved. |
| `needs_review` | Requires human review before academic use. |
| `unsupported` | Input or capability cannot be interpreted safely. |
| `ambiguous` | Multiple plausible interpretations exist. |
| `approved_source` | Source is already approved or certified. |

The initial implementation should be conservative. Anything machine-extracted
from unapproved input should default to candidate/review posture rather than
authority.

---

## 12. Explicit non-goals

Phase 4 is deliberately not attempting to:

- implement full OCR;
- integrate a new OCR provider;
- implement handwriting OCR quality improvements;
- implement LLM-based understanding;
- integrate ASR or voice transcription;
- implement KAI persistence;
- implement EKG writes;
- update CurriculumPacks;
- create approved educational knowledge;
- evaluate student answers;
- update AEI behavior;
- change tutor prompts;
- change question generation;
- expose API endpoints;
- add UI upload flows;
- create background workers;
- create product analytics;
- generate sales/support/product capability claims.

This design is about safe acquisition contracts and candidate posture, not
feature rollout.

---

## 13. Runtime posture

If later authorized, the first KAI implementation should be:

- passive;
- read-only with respect to existing product data;
- deterministic where possible;
- exception-isolated;
- tenant-safe;
- candidate-only;
- non-authoritative;
- hidden from users;
- disabled by default if any runtime observer is introduced.

No production consumer should depend on KAI output in the first implementation
unless a later authorization explicitly permits it.

---

## 14. Feature flag strategy

If passive KAI runtime observation is implemented later, expected flag:

```text
EUI_KAI_PASSIVE_ENABLED=false
```

Expected behavior:

- default-off;
- environment configurable;
- no-op when disabled;
- passive candidate generation only when enabled;
- no schema/API/UI/product behavior change;
- rollback by disabling the flag.

The exact flag name should be finalized in a future implementation
authorization contract.

---

## 15. Observability

KAI observability should be operational, not product analytics.

Expected metrics may include:

```text
eui_kai.acquire_invoked
eui_kai.acquire_completed
eui_kai.acquire_failed
eui_kai.unsupported_input
eui_kai.ambiguous
eui_kai.needs_review
eui_kai.duration
```

Structured logs should capture low-cardinality technical information:

- artifact type;
- modality;
- candidate status;
- capability mode;
- extraction status;
- failure category;
- duration.

Logs and metrics must not include:

- student names;
- parent data;
- free-text answers;
- uploaded content;
- tenant slugs;
- raw OCR text;
- sensitive educational evidence.

---

## 16. Testing strategy

Future implementation should include focused tests and Golden Harness cases.

### Unit tests

Expected coverage:

- candidate model validation;
- provenance/trust separation;
- unsupported input posture;
- ambiguous acquisition posture;
- capability mode mapping;
- tenant-safe candidate representation;
- default-off feature flag behavior if a passive observer is introduced;
- exception isolation if a passive observer is introduced.

### Golden Harness

Golden cases should cover:

- PDF worksheet candidate;
- scanned OCR candidate;
- answer key candidate;
- teacher note candidate;
- Hindi printed OCR candidate posture;
- handwriting OCR assist/manual-review posture;
- unsupported image/diagram posture;
- ambiguous worksheet extraction;
- missing identity/context fallback.
- source-admission rejection for unauthorized input types.

### Regression verification

Before certification, validation should demonstrate:

- existing EUI Identity tests still pass;
- existing EUI Context tests still pass;
- Platform Capability Registry tests still pass;
- AEI/evaluation regression slice still passes;
- API import succeeds;
- focused lint for KAI files passes;
- `git diff --check` passes.

---

## 17. Certification criteria

Phase 4 should be accepted only if certification can truthfully state:

- KAI candidate contracts exist as authorized;
- KAI outputs candidates, not authoritative knowledge;
- source admission boundaries are enforced;
- provenance and trust signals remain separate;
- unsupported and low-confidence inputs are handled safely;
- capability posture is not upgraded;
- no EKG trusted writes occur;
- no consumer depends on KAI output;
- no schema/API/UI changes were introduced unless separately authorized;
- no AEI behavior changed;
- no new OCR/LLM/ASR provider integration was introduced unless separately
  authorized;
- Golden Harness KAI cases pass;
- observability evidence exists if passive runtime is introduced;
- rollback is verified;
- certification report is complete;
- phase retrospective is complete.

---

## 18. Relationship to later phases

KAI prepares for later phases but does not perform them.

| Later phase | Relationship |
|---|---|
| Educational Knowledge Graph Expansion | KAI provides candidates that may later become graph evidence after review. |
| Trust Framework | KAI supplies acquisition/extraction signals that can feed Trust Reports later. |
| Institutional Memory | KAI may later ingest approved school-specific rubrics or terminology. |
| AEI Consumer Migration | AEI may later consume approved KAI evidence, never raw unreviewed extraction. |
| Teacher Copilot / Tutor | Later consumers may use reviewed or trusted KAI artifacts after migration authorization. |

---

## 19. ARM review gate

This design brief has been accepted by ARM as the Phase 4 KAI design baseline.

It does not authorize:

- implementation;
- production code changes;
- schema changes;
- API changes;
- UI changes;
- consumer migration;
- EKG writes;
- AEI behavior changes;
- LLM integration;
- OCR provider integration.

The next governance action, if ARM accepts this brief, should be a Phase 4 KAI
Implementation Authorization Contract defining:

- exact implementation scope;
- permitted files/modules;
- feature flag name;
- Golden Harness requirements;
- observability requirements;
- rollback proof;
- certification evidence;
- explicit exclusions.
