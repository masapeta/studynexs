# Educational Understanding Intelligence (EUI)

- **Status:** Accepted
- **Version:** v1 architecture baseline
- **Date:** 2026-07-27
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Related ADR:** [`../decisions/ADR-0002-educational-understanding-intelligence-platform-architecture.md`](../decisions/ADR-0002-educational-understanding-intelligence-platform-architecture.md)
- **Related subsystem:** [`AEI.md`](./AEI.md)

---

## 1. First principle

> Educational understanding is the platform capability. Evaluation is one application of that capability.

This is the architectural distinction for StudyNexs v1 and beyond.

Academic Evaluation Intelligence (AEI) remains a protected, certified subsystem for teacher-approved academic evaluation. Educational Understanding Intelligence (EUI) is the broader platform capability that makes curriculum, teaching, learning, assessment, tutoring, analytics, and school intelligence operate from one shared educational understanding layer.

---

## 2. Purpose

EUI exists to convert educational inputs, context, curriculum structure, institutional memory, and student evidence into reusable, governed educational knowledge.

StudyNexs should not accumulate isolated files, prompt fragments, answer extracts, or feature-specific interpretations. It should transform school activity into explainable educational knowledge that can be safely consumed by platform intelligence.

Core operating rule:

> Every piece of educational information should become reusable educational knowledge.

Examples:

- A lesson plan becomes curriculum knowledge.
- A teacher rubric becomes assessment knowledge.
- A corrected answer becomes misconception knowledge.
- A student's work becomes learning evidence.
- A teacher override becomes governance evidence.
- A worksheet becomes instructional knowledge.

---

## 3. Scope

EUI v1 defines the platform architecture for:

- Educational Knowledge Graph (EKG)
- Educational Identity
- Knowledge Acquisition Intelligence (KAI)
- Educational Context Engine (ECE)
- Institutional Memory
- Platform Capability Registry
- Trust Framework
- Learning Loop Governance
- EUI Consumer Contracts
- Production Scope and Versioning

This architecture program does not implement runtime behavior.

---

## 4. Non-goals

EUI is not:

- a replacement for AEI;
- a new grading engine;
- a new ERP module;
- a direct LLM integration path;
- a second knowledge store that bypasses Curriculum Intelligence;
- a self-training or self-modifying AI loop;
- a permission to hardcode board, school, or teacher rules in code.

---

## 5. Platform position

StudyNexs should be described as an AI-first School Operating System whose intelligence flows through EUI.

```text
StudyNexs Intelligence Platform

Educational Knowledge Graph
        |
        v
Educational Understanding Intelligence
        |
        +-- Educational Identity
        +-- Knowledge Acquisition Intelligence
        +-- Educational Context Engine
        +-- Institutional Memory
        +-- Platform Capability Registry
        +-- Trust Framework
        |
        v
Subject Intelligence
        |
        v
Academic Evaluation Intelligence
        |
        +-- Learning Intelligence
        +-- Teacher Intelligence
        +-- Parent Intelligence
        +-- Student Intelligence
        +-- Principal Intelligence
        +-- School Intelligence
```

AEI is therefore not the center of the platform. It is one specialized consumer of EUI.

---

## 6. Relationship to AEI

AEI is feature-frozen as a protected subsystem except for authorized controlled integration waves.

EUI does not weaken the AEI constitution. Instead:

- EUI supplies educational context, knowledge, capability declarations, trust inputs, and institutional memory.
- AEI consumes those inputs when making evaluation suggestions.
- AEI still owns reasoning, policy, teacher review, and evaluation evidence for academic evaluation.
- Student, Parent, Principal, and School Intelligence still consume teacher-approved evidence for consequential evaluation outcomes.

No future EUI component may bypass AEI for evaluation decisions.

---

## 7. EUI responsibilities

EUI owns platform-level educational understanding:

| Responsibility | Meaning |
|---|---|
| Educational knowledge modeling | Model curriculum, concepts, competencies, evidence, and learning relationships. |
| Educational identity | Provide stable educational identity references for artifacts, questions, lessons, assessments, and interventions. |
| Input acquisition | Convert PDFs, worksheets, images, voice, notes, lesson plans, rubrics, and answer keys into structured candidates. |
| Context resolution | Resolve board, grade, subject, exam type, school policy, language medium, accommodations, and academic year. |
| Institutional memory | Capture school-specific policies, terminology, rubrics, and historical decisions as governed data. |
| Capability declaration | Define what StudyNexs supports, assists, routes to review, or does not claim. |
| Trust reporting | Explain input quality, understanding quality, evidence, policy, review, and auditability. |
| Learning loops | Convert human decisions into governed improvement evidence, not live behavior drift. |
| Consumer contracts | Ensure every intelligence surface consumes EUI instead of reimplementing understanding. |

---

## 8. Boundary rules

1. EUI is platform capability; AEI is evaluation capability.
2. Educational knowledge is governed data, not prompt text.
3. Educational context is resolved once and consumed by all intelligence layers.
4. Institutional memory is explicit and auditable; it is not hidden model behavior.
5. Capability claims come from the Platform Capability Registry.
6. Trust is a report with multiple dimensions, not a single confidence score.
7. Teacher corrections do not become live model updates.
8. Every consequential academic output remains human-in-the-loop.
9. No consumer may create a parallel educational understanding path.
10. Platform capabilities should be extended by introducing new providers, registry entries, graph relationships, or consumer contracts, not by duplicating educational understanding logic inside individual consumers.
11. New EUI architecture changes require ARM approval and an ADR.

---

## 9. Canonical educational flow

```text
Input
  PDF | worksheet | image | voice | teacher note | rubric | answer key | student work
        |
        v
Knowledge Acquisition Intelligence
        |
        v
Canonical Educational Artifact
        |
        v
Educational Context Engine
        |
        v
Educational Knowledge Graph
        |
        v
Educational Understanding Intelligence
        |
        v
Consumer Contract
        |
        +-- Academic Evaluation Intelligence
        +-- Teacher Copilot
        +-- Lesson Planner
        +-- Question Generator
        +-- AI Tutor
        +-- Parent Assistant
        +-- Principal Dashboard
        +-- School Analytics
```

---

## 10. Canonical educational artifact

EUI should converge all educational inputs into a canonical artifact before downstream interpretation.

Conceptual shape:

```text
EducationalArtifact
  artifact_id
  tenant_scope
  educational_identity
  source_type
  provenance
  extracted_content
  normalized_content
  detected_language
  detected_script
  modality
  subject
  grade
  board
  curriculum_reference
  evidence_references
  trust_report
  capability_claims
  metadata
```

This is an architecture contract, not a schema change in this program.

Provenance and trust are intentionally separate:

- Provenance answers where the artifact came from, who approved it, and which version it belongs to.
- Trust answers how reliable the artifact or interpretation is and whether review is required.

---

## 11. Extension model

New educational capabilities must extend EUI through the platform contracts:

1. Add capability declaration to the Platform Capability Registry.
2. Resolve educational context through ECE.
3. Convert inputs through KAI if acquisition is involved.
4. Map concepts or evidence to EKG when educational knowledge is created.
5. Assign or reference a stable Educational Identity.
6. Preserve provenance separately from trust.
7. Produce a Trust Report.
8. Expose the result through a consumer contract.
9. Add certification evidence before production claims expand.

Do not add one-off understanding logic inside individual consumers.

---

## 12. Supporting specifications

| Specification | Path |
|---|---|
| Educational Knowledge Graph | [`eui/EDUCATIONAL_KNOWLEDGE_GRAPH.md`](./eui/EDUCATIONAL_KNOWLEDGE_GRAPH.md) |
| Educational Identity | [`eui/EDUCATIONAL_IDENTITY.md`](./eui/EDUCATIONAL_IDENTITY.md) |
| Knowledge Acquisition Intelligence | [`eui/KNOWLEDGE_ACQUISITION_INTELLIGENCE.md`](./eui/KNOWLEDGE_ACQUISITION_INTELLIGENCE.md) |
| Educational Context Engine | [`eui/EDUCATIONAL_CONTEXT_ENGINE.md`](./eui/EDUCATIONAL_CONTEXT_ENGINE.md) |
| Institutional Memory | [`eui/INSTITUTIONAL_MEMORY.md`](./eui/INSTITUTIONAL_MEMORY.md) |
| Platform Capability Registry | [`eui/PLATFORM_CAPABILITY_REGISTRY.md`](./eui/PLATFORM_CAPABILITY_REGISTRY.md) |
| Trust Framework | [`eui/TRUST_FRAMEWORK.md`](./eui/TRUST_FRAMEWORK.md) |
| Learning Loop Governance | [`eui/LEARNING_LOOP_GOVERNANCE.md`](./eui/LEARNING_LOOP_GOVERNANCE.md) |
| Consumer Contracts | [`eui/CONSUMER_CONTRACTS.md`](./eui/CONSUMER_CONTRACTS.md) |
| Production Scope and Versioning | [`eui/PRODUCTION_SCOPE_AND_VERSIONING.md`](./eui/PRODUCTION_SCOPE_AND_VERSIONING.md) |

---

## 13. Governance status

This document is the accepted EUI v1 architecture baseline.

EUI is architecture-frozen. Future changes require:

1. ARM approval;
2. ADR update or new ADR;
3. compatibility assessment against AEI and existing consumers;
4. versioning decision.

AEI remains feature-frozen except for authorized controlled integration waves.
