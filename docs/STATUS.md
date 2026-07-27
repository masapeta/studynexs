# StudyNexs — Master Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-07-27
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
| Phase 4 | Knowledge Acquisition Intelligence | Not started |

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
| Phase 4 - Knowledge Acquisition Intelligence | Design draft / ARM review pending |
| Runtime consumer migration | Not authorized |

---

## Published EUI runtime milestones

| Roadmap phase | Status | Commit | Tag | Historical artifact label |
|---|---|---|---|---|
| Phase 1 - Educational Identity | Published / certified | `221601e611bdb0fac13279af7fe4a8e89d31f99a` | `eui-runtime-phase1-sprint1-educational-identity-certified` | Phase 1 Sprint 1 |
| Phase 2 - Educational Context Engine | Published / certified | `a559faeba7389bb583bfdcd64f8119f3811613d6` | `eui-runtime-phase1-sprint2-educational-context-certified` | Phase 1 Sprint 2 |
| Phase 3 - Platform Capability Registry | Published / certified | `5f3babf007fcbaba7a8a33ec316e80b974d8df7b` | `eui-runtime-phase1-sprint3-platform-capability-registry-certified` | Phase 1 Sprint 3 |

---

## Current engineering gate

The current review artifact is:

```text
EUI Runtime Phase 4 — Knowledge Acquisition Intelligence Design Brief
```

Phase 4 implementation is not authorized.

The project should pause at this gate until ARM reviews the design brief and
either accepts it, requests revisions, or chooses a different next milestone.

---

## Explicitly not authorized

Until ARM separately authorizes a future implementation contract, the following
remain out of scope:

- Knowledge Acquisition Intelligence implementation;
- Educational Knowledge Graph expansion;
- Trust Framework implementation;
- schema changes;
- API changes;
- UI changes;
- consumer migration;
- AEI behavior changes;
- EUI contract changes outside accepted design;
- product capability claim changes;
- replacement of the AEI Subject Capability Registry;
- public use of Platform Capability Registry entries for UI badges, sales
  claims, support documentation, or product scope documentation.

---

## Current source-of-truth statement

StudyNexs has a frozen AEI/EUI architecture, a published Phase 1 Educational
Identity runtime foundation, a published Phase 2 Educational Context passive
runtime foundation, and a published Phase 3 Platform Capability Registry
passive runtime foundation. Phase 4 Knowledge Acquisition Intelligence has a
draft design brief pending ARM review; implementation is not authorized.

---

## Validation posture

Latest published runtime phase:

```text
EUI Runtime Phase 3 — Platform Capability Registry
```

Historical artifact label:

```text
Phase 1 Sprint 3 — Platform Capability Registry
```

Certified evidence:

- Focused EUI Ruff: PASS
- Phase 3 / Sprint 3 tests: 20 passed
- Phase 1/2 Educational Identity and Context regression: 31 passed
- AEI / evaluation / KG regression slice: 57 passed
- API import: PASS
- git diff --check: PASS
- EUI DB-write scan: PASS with note for existing non-database `seen.add(key)`

Certification report:

[`product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_CERTIFICATION_REPORT.md`](./product/eui-runtime/phase-1/EUI_PHASE_1_SPRINT_3_PLATFORM_CAPABILITY_REGISTRY_CERTIFICATION_REPORT.md)

---

## Standing rule

Every published runtime phase must end by updating this Master Status before the
next phase begins.
