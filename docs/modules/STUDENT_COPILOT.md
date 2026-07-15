# Student Copilot

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**🟡 In progress (API MVP)** — Batch 25 · Verified: **tests passing**

## Owner

Learning Intelligence · student portal (`/student/tutor`)

## Features

| Feature | State |
|---------|-------|
| Template Mistake Recovery Tutor | ✅ (pre-Batch 25) |
| ConceptCard-grounded lessons | ✅ Batch 18 |
| Graph weak-concept recommendations | ✅ Batch 25 |
| Hybrid RAG study context | ✅ Batch 25 |
| Grounded ask Q&A (metered) | ✅ Batch 25 |
| Student UI — ask panel + focus chips | ⬜ Batch 26 |

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /tutor/students/{id}/study-context` | Weak concepts + RAG context |
| `POST /tutor/students/{id}/ask` | Grounded study Q&A |
| `GET /tutor/students/{id}/recommendations` | Graph-first topic list |

## Files

`apps/api/app/modules/tutor/services/student_copilot_service.py`

## Tests

`tests/test_student_copilot.py` (4) · `tests/test_tutor.py`
