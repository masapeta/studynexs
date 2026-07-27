# EUI Phase 0 Dependency Inventory

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 0 - Engineering Preparation
- **Status:** Accepted
- **Implementation:** Not authorized
- **Date:** 2026-07-27

---

## 1. Purpose

Inventory the existing repository dependencies that future EUI runtime phases must respect.

This document does not authorize changes to any listed module.

---

## 2. Governance dependencies

| Dependency | Role |
|---|---|
| `AGENTS.md` | Engineering constitution and non-negotiable repository rules. |
| `docs/architecture/EUI.md` | Accepted EUI architecture baseline. |
| `docs/decisions/ADR-0002-educational-understanding-intelligence-platform-architecture.md` | Accepted EUI ADR. |
| `docs/architecture/AEI.md` | Protected AEI architecture baseline. |
| `docs/decisions/ADR-0001-academic-evaluation-intelligence-architecture-freeze.md` | AEI architecture freeze. |
| `docs/product/eui-runtime/EUI_RUNTIME_IMPLEMENTATION_ROADMAP.md` | Runtime implementation sequencing baseline. |
| `docs/product/eui-runtime/EUI_DEPENDENCY_MATRIX.md` | Dependency and migration order baseline. |
| `docs/product/eui-runtime/EUI_RUNTIME_READINESS_CHECKLIST.md` | Runtime readiness gate. |

---

## 3. Runtime foundation dependencies

| Path | Role |
|---|---|
| `apps/api/app/core/config.py` | Settings and feature flag pattern. |
| `apps/api/app/core/platform_metrics.py` | Platform metrics registry. |
| `apps/api/app/core/metrics_middleware.py` | HTTP metrics middleware. |
| `apps/api/app/core/otel.py` | Optional OpenTelemetry bootstrap. |
| `apps/api/app/main.py` | `/metrics`, `/health`, `/ready`, middleware wiring. |

---

## 4. Curriculum and knowledge dependencies

| Path | Role |
|---|---|
| `apps/api/app/db/models/curriculum_pack.py` | CurriculumPack persistence. |
| `apps/api/app/db/models/knowledge_graph.py` | Current curriculum concept and KG edge models. |
| `apps/api/app/db/models/concept_card.py` | Concept card model. |
| `apps/api/app/modules/curriculum/services/pack_service.py` | Pack approval and KG spine materialization. |
| `apps/api/app/modules/curriculum/services/curriculum_grounding.py` | Curriculum grounding. |
| `apps/api/app/modules/curriculum/services/intelligence_status.py` | Curriculum intelligence readiness status. |
| `apps/api/app/modules/curriculum/schemas/provenance.py` | Existing provenance schema pattern. |
| `apps/api/app/modules/curriculum/endpoints/graph.py` | Existing graph endpoint surface. |

---

## 5. AEI dependencies

| Path | Role |
|---|---|
| `apps/api/app/modules/examinations/schemas/academic_answer.py` | AEI canonical answer model. |
| `apps/api/app/modules/examinations/schemas/academic_reasoning_result.py` | AEI reasoning result contract. |
| `apps/api/app/modules/examinations/schemas/policy_decision.py` | AEI policy decision contract. |
| `apps/api/app/modules/examinations/schemas/teacher_review_decision.py` | AEI teacher review contract. |
| `apps/api/app/modules/examinations/services/academic_understanding_engine.py` | AEI understanding orchestration. |
| `apps/api/app/modules/examinations/services/academic_reasoning_engine.py` | AEI reasoning orchestration. |
| `apps/api/app/modules/examinations/services/evaluation_policy.py` | AEI policy engine. |
| `apps/api/app/modules/examinations/services/teacher_review.py` | AEI teacher review helpers. |
| `apps/api/app/modules/examinations/services/subject_capability_registry.py` | AEI subject capability registry service. |
| `apps/api/app/modules/examinations/services/aei_passive_integration.py` | AEI passive/shadow integration precedent. |
| `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py` | Existing evaluation lifecycle integration point. |

---

## 6. Test dependencies

| Path | Role |
|---|---|
| `apps/api/tests/test_aei_architecture.py` | AEI architecture guard tests. |
| `apps/api/tests/test_golden_evaluation_harness.py` | Existing Golden Harness tests. |
| `apps/api/tests/test_aei_passive_integration.py` | Passive/shadow integration test pattern. |
| `apps/api/tests/test_platform_metrics.py` | Platform metrics tests. |
| `apps/api/tests/test_health.py` | Health and metrics endpoint tests. |
| `apps/api/tests/test_knowledge_graph.py` | Current KG behavior tests. |
| `apps/api/tests/test_graph_queries.py` | Graph query behavior tests. |
| `apps/api/tests/test_question_concept_links.py` | Question-to-concept relationship tests. |
| `apps/api/tests/test_tenant_isolation.py` | Tenant isolation regression tests. |

---

## 7. Phase 1 dependency conclusion

Phase 1 - Educational Identity should depend first on:

- accepted EUI docs;
- existing CurriculumPack and Knowledge Graph concepts;
- tenant scope rules;
- existing AEI architecture tests;
- new identity-focused tests to be created only after Phase 1 authorization.

No runtime dependencies were modified in Phase 0.
