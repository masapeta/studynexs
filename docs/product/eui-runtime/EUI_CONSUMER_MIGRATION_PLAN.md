# EUI Consumer Migration Plan

- **Program:** EUI Runtime Implementation Roadmap v1
- **Classification:** Planning artifact
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

The Consumer Migration Plan defines how existing StudyNexs intelligence consumers move to EUI without destabilizing production behavior.

No consumer should be migrated in one step.

---

## 2. Standard migration pattern

```text
Current Consumer
        |
        v
Preparation
        |
        v
Compatibility Layer
        |
        v
Dual Read
        |
        v
Verification
        |
        v
Switch
        |
        v
Cleanup
```

---

## 3. Migration stage definitions

| Stage | Meaning | Exit evidence |
|---|---|---|
| Current Consumer | Existing implementation remains source of truth. | Baseline tests and behavior evidence. |
| Preparation | Contracts and dependencies are available. | Dependency matrix entry complete. |
| Compatibility Layer | EUI data can be translated into existing consumer shape. | Adapter tests pass. |
| Dual Read | Consumer reads legacy and EUI sources without changing output. | Difference report. |
| Verification | Differences are classified and accepted or fixed. | Certification report. |
| Switch | EUI becomes source for the consumer under feature flag. | Runtime proof and rollback proof. |
| Cleanup | Legacy path removed only after stable operation. | ARM approval and regression pass. |

---

## 4. Consumer plans

### 4.1 Academic Evaluation Intelligence

Current state: protected AEI v1 with controlled integration waves.

Preparation:

- Educational Identity available.
- ECE can represent existing evaluation context.
- Platform Capability Registry maps AEI registry entries.
- Trust Report runs alongside existing confidence.

Compatibility layer:

- Map EUI context into AEI `AcademicAnswer`, reasoning, policy, and review contracts without changing results.

Dual read:

- Existing AEI/evaluation inputs and EUI-resolved inputs run side by side.

Verification:

- Production evaluation outputs remain identical unless a later authorized phase explicitly changes behavior.

Switch:

- EUI context becomes AEI context source only after shadow evidence is accepted.

Cleanup:

- Remove old context construction only after rollback window.

### 4.2 Teacher Copilot

Preparation:

- ECE and EKG provide teacher-safe curriculum context.
- Institutional Memory provides approved teaching preferences where available.

Compatibility layer:

- Convert EUI context into existing copilot prompt/context format.

Dual read:

- Compare legacy recommendations with EUI-grounded recommendations.

Verification:

- Teacher-facing recommendations remain grounded and role-safe.

Switch:

- Enable EUI-grounded context behind feature flag.

Cleanup:

- Remove duplicated context assembly.

### 4.3 AI Tutor

Preparation:

- EKG concept/prerequisite mappings exist for the supported curriculum scope.
- ECE supplies grade, language, and learning context.
- Trust Framework qualifies weak or inferred evidence.

Compatibility layer:

- Translate EUI concept context into existing tutor retrieval and prompt format.

Dual read:

- Compare tutor outputs for grounding, grade appropriateness, language handling, and safety.

Verification:

- Tutor remains supportive, grounded, and age-appropriate.

Switch:

- Use EUI context for supported subjects and curriculum scopes.

Cleanup:

- Remove private tutor concept mapping only after coverage is proven.

### 4.4 Question Generator

Preparation:

- Educational Identity and EKG define concepts, competencies, and learning objectives.
- Capability Registry defines generation support scope.

Compatibility layer:

- Convert EUI identity/context into existing generation request format.

Dual read:

- Generate comparison papers/questions without user-facing switch.

Verification:

- Question coverage, difficulty, concept mapping, and grounding remain acceptable.

Switch:

- Route supported generation scopes through EUI context.

Cleanup:

- Remove duplicated curriculum resolution from generator.

### 4.5 Lesson Planner

Preparation:

- EKG provides concepts and prerequisites.
- Institutional Memory provides approved school/teacher preferences where available.

Compatibility layer:

- Convert EUI context to existing lesson-plan context.

Dual read:

- Compare legacy and EUI-grounded lesson plans.

Verification:

- Plans remain grounded, teachable, and aligned with curriculum.

Switch:

- Enable EUI context for supported curriculum packs.

Cleanup:

- Remove legacy context assembly once stable.

### 4.6 Principal Dashboard

Preparation:

- EKG evidence relationships and Trust Report are available.
- Approved evidence boundaries are clear.

Compatibility layer:

- Map EUI-linked evidence into current dashboard metrics.

Dual read:

- Compare dashboard aggregates from current source and EUI-linked source.

Verification:

- Trends remain accurate and not overstated from weak evidence.

Switch:

- Use EUI-linked aggregates for supported metrics.

Cleanup:

- Remove legacy aggregate logic only after acceptance.

### 4.7 Parent Assistant

Preparation:

- Approved evidence only.
- Parent-safe explanations defined.
- Trust Report supports explanation boundaries.

Compatibility layer:

- Convert approved EUI evidence into parent-safe response context.

Dual read:

- Compare existing parent responses with EUI-grounded responses internally.

Verification:

- No raw AI uncertainty or unapproved evidence appears to parents.

Switch:

- Enable EUI-grounded parent explanations only for approved evidence.

Cleanup:

- Remove duplicated evidence selection.

### 4.8 School Analytics

Preparation:

- EKG evidence relationships and Educational Identity are available.
- ECE defines comparable cohorts and time periods.

Compatibility layer:

- Map EUI-linked evidence into existing analytics shapes.

Dual read:

- Compare aggregate outputs.

Verification:

- Aggregates match or differences are explained by improved identity/context.

Switch:

- Enable EUI-linked analytics by metric group.

Cleanup:

- Remove legacy aggregation once stable.

---

## 5. Migration approval rule

Each consumer migration requires separate ARM authorization.

Approval should include:

- consumer;
- scope;
- feature flag;
- rollback;
- tests;
- certification gate;
- expected behavior impact.

---

## 6. Governance status

This migration plan is accepted as part of the EUI Runtime Planning Baseline.

No consumer migration is authorized by this document.
