# StudyNexs — Master Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-07-28
> **Status role:** Current project anchor for architecture, runtime milestones, and next engineering gate.

---

## Executive status

StudyNexs is an AI-first School Operating System with a frozen AEI/EUI
architecture and a controlled EUI runtime implementation program.

The current engineering rhythm is:

```text
Architecture
      ↓
Design Brief
      ↓
ARM Authorization
      ↓
Implementation
      ↓
Validation
      ↓
Certification
      ↓
Commit
      ↓
Tag
      ↓
Publish
      ↓
Update Master Status
```

Architecture should not be reopened unless ARM explicitly authorizes an
architecture change.

---

## Runtime naming source of truth

The EUI Runtime Roadmap phase names are the source of truth going forward.

Earlier artifacts that say `Phase 1 Sprint 2` or `Phase 1 Sprint 3` are
historical implementation-batch labels from the first EUI runtime cycle. They
remain valid as artifact names, commit tags, and certification records, but the
canonical roadmap names are:

| Roadmap phase | Canonical capability | Historical implementation label |
|---|---|---|
| Phase 1 | Educational Identity | Phase 1 Sprint 1 |
| Phase 2 | Educational Context Engine | Phase 1 Sprint 2 |
| Phase 3 | Platform Capability Registry | Phase 1 Sprint 3 |
| Phase 4 | Knowledge Acquisition Intelligence | Phase 4 KAI Candidate Foundation |
| Phase 5 | Educational Knowledge Graph Expansion | Phase 5 EKG Proposal Foundation |
| Phase 6 | Trust Framework | Phase 6 Trust Report Foundation |
| Phase 7 | Consumer Migration | Phase 7A AEI Consumer Dual-Read Foundation; Phase 7B AEI Rich EUI Evidence Binding; Phase 7C AEI Divergence Readiness Review; Phase 7D Narrow AEI Source Readiness; Phase 7E Narrow AEI Source-Readiness Trial |

---

## Current baseline

| Layer | Status |
|---|---|
| StudyNexs vision | Stable |
| AEI v1 | Frozen / protected |
| EUI v1 architecture | Frozen / accepted |
| EUI Runtime Roadmap v1 | Accepted planning baseline |
| Phase 0 - Engineering Preparation | Complete / certified / published |
| Phase 1 - Educational Identity | Complete / certified / published |
| Phase 2 - Educational Context Engine | Complete / certified / published |
| Phase 3 - Platform Capability Registry | Complete / certified / published |
| Phase 4 - Knowledge Acquisition Intelligence | Candidate foundation complete / certified / published |
| Phase 5 - Educational Knowledge Graph Expansion | Proposal foundation complete / certified / published |
| Phase 6 - Trust Framework | Trust Report foundation complete / certified / published |
| Phase 7 - Consumer Migration | Closed at Phase 7E; 7F source adoption deferred / future scope |
| Runtime consumer migration | AEI passive dual-read with rich internal EUI evidence, internal divergence readiness review, narrow internal source-readiness candidate foundation, and internal source-readiness trial foundation published; source-of-truth switch not authorized |

---

## Published EUI runtime milestones

| Roadmap phase | Status | Commit | Tag | Historical artifact label |
|---|---|---|---|---|
| Phase 1 - Educational Identity | Published / certified | `221601e611bdb0fac13279af7fe4a8e89d31f99a` | `eui-runtime-phase1-sprint1-educational-identity-certified` | Phase 1 Sprint 1 |
| Phase 2 - Educational Context Engine | Published / certified | `a559faeba7389bb583bfdcd64f8119f3811613d6` | `eui-runtime-phase1-sprint2-educational-context-certified` | Phase 1 Sprint 2 |
| Phase 3 - Platform Capability Registry | Published / certified | `5f3babf007fcbaba7a8a33ec316e80b974d8df7b` | `eui-runtime-phase1-sprint3-platform-capability-registry-certified` | Phase 1 Sprint 3 |
| Phase 4 - Knowledge Acquisition Intelligence | Published / certified | `165c796e9bac6a6fc29226ed186b79664d0d5b5c` | `eui-runtime-phase4-kai-candidate-foundation-certified` | Phase 4 KAI Candidate Foundation |
| Phase 5 - Educational Knowledge Graph Expansion | Published / certified | `91a84f5fce1bb0acf4a5231593b0e1715e1baef8` | `eui-runtime-phase5-ekg-proposal-foundation-certified` | Phase 5 EKG Proposal Foundation |
| Phase 6 - Trust Framework | Published / certified | `0a5a5dd0a8b7054ede5d86f7b610328505b195f5` | `eui-runtime-phase6-trust-report-foundation-certified` | Phase 6 Trust Report Foundation |
| Phase 7A - AEI Consumer Migration | Published / certified | `c30bb2479e615d50aea97ae03bd3b6816d93c26b` | `eui-runtime-phase7a-aei-consumer-dual-read-certified` | Phase 7A AEI Consumer Dual-Read Foundation |
| Phase 7B - AEI Rich EUI Evidence Binding | Published / certified | `f279f8a04e82d66133cf9178676c8af51b9aeb54` | `eui-runtime-phase7b-aei-rich-evidence-binding-certified` | Phase 7B AEI Rich EUI Evidence Binding |
| Phase 7C - AEI Divergence Readiness Review | Published / certified | `d9fa9e8d44dab0bd6dc5874fb0ac84f0a7e6ee90` | `eui-runtime-phase7c-aei-divergence-readiness-certified` | Phase 7C AEI Divergence Review and Source Readiness |
| Phase 7D - Narrow AEI Source Readiness | Published / certified | `696501c270b3db893ea71c31babeb7448967f6a1` | `eui-runtime-phase7d-narrow-aei-source-readiness-certified` | Phase 7D Narrow AEI Source-Readiness Candidate Foundation |
| Phase 7E - Narrow AEI Source-Readiness Trial | Published / certified | `bf7e06e6f497d1e09234e4ba0a611b479d7ee1d1` | `eui-runtime-phase7e-narrow-aei-source-readiness-trial-certified` | Phase 7E Narrow AEI Source-Readiness Trial Foundation |

---

## Current engineering gate

The latest completed artifact is:

```text
EUI Runtime Phase 7E - Narrow AEI Source-Readiness Trial
```

Phase 7E is published and certified as an internal narrow AEI source-readiness
trial foundation. It adds a non-authoritative trial result model and
deterministic trial service over Phase 7D candidates for the
`context_metadata_only` scope without changing AEI, evaluation behavior, marks,
teacher review routing, evidence ledger behavior, API, UI, schema, or
source-of-truth posture.

No EUI source-of-truth switch is authorized. Phase 7 is closed at Phase 7E.
Phase 7F source adoption is deferred future scope, not the next active
implementation milestone.

Next gated milestone:

```text
Product-facing completion work, unless ARM explicitly reopens source adoption
```

Phase 7F should be implemented only when source adoption solves a real product
problem, not because the architecture can support it.

Deferred artifact:

[`product/eui-runtime/phase-7/EUI_PHASE_7F_NARROW_AEI_SOURCE_ADOPTION_DESIGN_BRIEF.md`](./product/eui-runtime/phase-7/EUI_PHASE_7F_NARROW_AEI_SOURCE_ADOPTION_DESIGN_BRIEF.md)

7F reopen conditions:

- a real product-facing flow needs EUI to become the selected metadata source;
- legacy AEI metadata starts blocking accuracy, consistency, or
  maintainability;
- Phase 7E trial evidence shows stable readiness across real usage;
- marks, routing, ledger, API, UI, and schema can be proven unchanged;
- rollback is simple: disable the flag and return to legacy AEI;
- ARM explicitly authorizes a 7F implementation contract.

---

## Explicitly not authorized

Until ARM separately authorizes a future implementation contract, the following
remain out of scope:

- additional Educational Knowledge Graph behavior beyond the published proposal
  foundation;
- additional Knowledge Acquisition Intelligence behavior beyond the published
  candidate foundation;
- additional Trust Framework behavior beyond the published Trust Report
  foundation;
- schema changes;
- API changes;
- UI changes;
- consumer migration beyond the published Phase 7E AEI internal
  source-readiness trial foundation;
- Phase 7F source adoption unless ARM reopens it under the documented reopen
  conditions;
- AEI behavior changes;
- AEI source-of-truth switching to EUI;
- EUI contract changes outside accepted design;
- product capability claim changes;
- replacement of the AEI Subject Capability Registry;
- public use of Platform Capability Registry entries for UI badges, sales
  claims, support documentation, or product scope documentation.

---

## Current source-of-truth statement

StudyNexs has a frozen AEI/EUI architecture, a published Phase 1 Educational
Identity runtime foundation, a published Phase 2 Educational Context passive
runtime foundation, a published Phase 3 Platform Capability Registry passive
runtime foundation, and a published Phase 4 Knowledge Acquisition Intelligence
candidate foundation, a published Phase 5 Educational Knowledge Graph proposal
foundation, a published Phase 6 Trust Framework Trust Report foundation, a
published Phase 7A AEI Consumer Migration passive dual-read foundation, a
published Phase 7B AEI Rich EUI Evidence Binding foundation, and a published
Phase 7C AEI Divergence Readiness Review foundation, and a published Phase 7D
Narrow AEI Source-Readiness Candidate foundation, and a published Phase 7E
Narrow AEI Source-Readiness Trial foundation. Phase 7 is closed at 7E. Phase
7F source adoption is deferred future scope. Further consumer migration,
including any EUI source-of-truth switch, is not authorized unless ARM reopens
source adoption under a separate implementation authorization contract.

---

## Validation posture

Latest published runtime phase:

```text
EUI Runtime Phase 7E - Narrow AEI Source-Readiness Trial
```

Historical artifact label:

```text
Phase 7E Narrow AEI Source-Readiness Trial Foundation
```

Certified evidence:

- Focused Phase 7E Ruff: PASS
- Focused Phase 7E + Golden Harness tests: 21 passed
- Phase 7A/7B/7C/7D/7E + Trust + AEI/evaluation regression slice: 94 passed
- API import: PASS
- git diff --check: PASS
- Phase 7E source-switch scan: PASS, no implementation activation found; only
  the negative model-validation test attempts `source_switch_active=True`
- Phase 7E LLM/provider-call scan: PASS, no provider call patterns found in
  AEI source-readiness trial files
- Phase 7E write-scan: PASS, no persistence/write patterns found in AEI
  source-readiness trial files
- Phase 7E API/router exposure scan: PASS, no user-facing exposure found
- Source flag remains inert: PASS

Certification report:

[`product/eui-runtime/phase-7/EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_CERTIFICATION_REPORT.md`](./product/eui-runtime/phase-7/EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_CERTIFICATION_REPORT.md)

---

## Standing rule

Every published runtime phase must end by updating this Master Status before the
next phase begins.
