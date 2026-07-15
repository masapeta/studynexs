# Parent Copilot

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**✅ MVP complete** — Batches 27–28 · Verified: **tests passing** + **build passing**

## Owner

Parent portal (`/parent/child/[studentId]`)

## Features

| Feature | State |
|---------|-------|
| Grounded progress briefing (metered) | ✅ Batch 27 |
| Home support tips from mastery + graph | ✅ Batch 27 |
| Parent Q&A on child's learning (minimal PII) | ✅ Batch 27 |
| Parent UI — briefing card + ask panel | ✅ Batch 28 |

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /parent-copilot/students/{id}/briefing` | Grounded learning briefing |
| `POST /parent-copilot/students/{id}/ask` | Parent Q&A with home tips |

## Files

`apps/api/app/modules/parent_copilot/` · `apps/admin-web/src/app/parent/child/[studentId]/page.tsx`

## Tests

`tests/test_parent_copilot.py` (3)

## Next

Fee / attendance narrative summaries (deterministic first); DPDP consent + retention before expanded PII
