# Teacher Copilot

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**✅ Complete — Batch 15** · Verified: **tests_passing**

## Depends on

| | Modules |
|---|---------|
| **Satisfied** | Embeddings · RAG · Curriculum Intelligence · AI Platform |
| **Optional (deferred)** | Knowledge Graph (enhances grounding; not required for MVP) |

## Owner

Learning + Assessment pillars (grounded assistance)

## Shipped features

- **Grounded lesson-plan assistance** — RAG + approved CurriculumPack via `TeacherCopilotService.generate_grounded_lesson_plan`
- **QP review / refinement** — curriculum-grounded suggestions with citations (`POST /api/v1/ai/copilot/question-papers/{id}/review`)
- **Feedback drafting** — constructive draft for teacher edit before send (`POST /api/v1/ai/copilot/feedback-draft`)
- Metered via shared gateway + credits (`lesson_plan`: 2, `quality_check`: 1, `feedback_draft`: 1)

## API

| Route | Purpose |
|-------|---------|
| `POST /api/v1/lesson-plans/generate` (with `pack_id`) | Grounded lesson plan → draft LessonPlan |
| `POST /api/v1/ai/copilot/question-papers/{id}/review` | QP quality review (grounded papers only) |
| `POST /api/v1/ai/copilot/feedback-draft` | Feedback draft for student work |

## Files

- `apps/api/app/modules/ai/services/teacher_copilot_service.py`
- `apps/api/app/modules/ai/schemas/teacher_copilot.py`
- `apps/api/app/modules/ai/endpoints/ai.py` (copilot routes)
- `apps/api/app/modules/curriculum/endpoints/lesson_plan.py` (pack_id path)
- `apps/admin-web/src/app/dashboard/teaching/lesson-plans/page.tsx`
- `apps/admin-web/src/app/dashboard/teaching/ai-papers/page.tsx`

## Tests

- `apps/api/tests/test_teacher_copilot.py` (5 passed, 2026-07-12)

## Docs

✅ this module doc · ROADMAP Batch 15 · AGENT_HANDOVER Session 04
