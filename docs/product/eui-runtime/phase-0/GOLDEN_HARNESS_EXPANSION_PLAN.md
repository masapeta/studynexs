# EUI Phase 0 Golden Harness Expansion Plan

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 0 - Engineering Preparation
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

Plan how the existing Golden Harness should expand as EUI runtime capabilities are implemented.

This document does not add fixtures or tests. It defines the expansion plan.

---

## 2. Existing repository pattern

Current Golden Harness foundations:

- AEI Golden Harness tests exist in `apps/api/tests/test_golden_evaluation_harness.py`.
- AEI golden fixtures live under `apps/api/tests/golden/aei_v1/`.
- AEI architecture requires Golden Harness coverage for academic capabilities.
- Current cases validate stable IDs, subject, capability, input, rubric, expected capability mode, reasoning type, and manual-review requirement.

---

## 3. EUI expansion principle

EUI Golden Harness coverage should test foundational educational understanding contracts before consumer behavior changes.

Golden cases should be added when a phase introduces:

- a new contract;
- a new resolver;
- a new capability mode;
- new graph relationships;
- new Trust Report dimensions;
- a consumer migration path.

---

## 4. Proposed dataset families

Planning names only:

| Dataset family | Phase | Purpose |
|---|---:|---|
| `eui_identity_resolution_cases` | 1 | Verify stable identity from curriculum references. |
| `eui_context_resolution_cases` | 2 | Verify board, grade, subject, assessment mode, language, and curriculum context. |
| `eui_capability_registry_cases` | 3 | Verify supported, assist, checklist, manual_review, unsupported, and expansion modes. |
| `eui_acquisition_candidate_cases` | 4 | Verify artifact candidate shape, provenance, and review posture. |
| `eui_ekg_relationship_cases` | 5 | Verify identity-linked graph relationships. |
| `eui_trust_report_cases` | 6 | Verify Trust Report dimensions and provenance separation. |
| `eui_consumer_dual_read_cases` | 7 | Verify consumer compatibility and difference classification. |

---

## 5. Minimum case schema

Future EUI golden cases should include:

- stable case ID;
- curriculum scope;
- tenant scope marker;
- input artifact or reference;
- expected Educational Identity;
- expected context;
- expected capability mode where relevant;
- expected provenance;
- expected Trust Report signals;
- expected review posture;
- notes explaining the school-reality scenario.

---

## 6. Phase 1 minimum coverage

Before Phase 1 can be accepted, Educational Identity cases should cover:

- board/grade/subject/chapter identity;
- learning objective identity;
- concept identity;
- competency identity;
- curriculum version identity;
- missing or ambiguous identity;
- tenant scope preservation;
- legacy CurriculumPack reference compatibility.

---

## 7. Release gate

Golden Harness failures are blockers for the affected EUI capability.

Consumer migration should not proceed if the foundational EUI golden cases for that consumer's dependency chain are failing.

---

## 8. Phase 0 conclusion

The existing AEI Golden Harness pattern is sufficient for EUI expansion planning.

No Golden Harness fixtures or tests were added in Phase 0.
