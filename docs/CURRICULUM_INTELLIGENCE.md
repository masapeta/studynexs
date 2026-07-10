# Curriculum Intelligence (Pillar 1)

> **Engineering companion** to [`/CLAUDE.md`](../CLAUDE.md) §38–§39.3 (canonical). Records current
> implementation + code + roadmap. *The source of truth for all academic AI.*

## What it is

Board-grounded curriculum knowledge — the **CurriculumPack**, retrieval (**RAG**), the **School
Knowledge Graph**, and **Document Intelligence** — that grounds every academic AI action so output is
correct, cited, and copyright-safe. Generic "Class 7 Science" prompts are a liability; grounded packs
are the moat.

## CurriculumPack (built)

- **Module:** `apps/api/app/modules/curriculum/` (`pack_service.py`, `schemas/pack.py`, endpoints `pack.py` + `lesson_plan.py`; migration `curriculum_packs`).
- **Model:** versioned source of truth for a school's `class × subject × academic-year`: book edition + **chapter → topic → concept** hierarchy.
- **Lifecycle:** draft → **HOD approval → immutable**; new version per year (never overwrite); cross-year concept mapping.
- **Rule:** all academic AI runs against an **approved** pack — never free-text topics.

## RAG grounding (foundation built — see [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md))

- `app/modules/ai/rag/service.py`: `index_pack` chunks the approved pack's chapter→topic tree, embeds
  (OpenAI `text-embedding-3-small`), and indexes into Qdrant; `retrieve` is **tenant- and pack-scoped**;
  `build_context` returns cited context (`[n] (source: chapter › topic)`).
- **Grounding unit = the curriculum topic** (structured), not textbook prose — copyright-safe (§39.1).
- **Next:** wire `RagService` into question-paper generation (the immediate batch) so QP output is grounded + cited.

## Document Intelligence (planned — `CLAUDE.md` §38.1)

One **shared** pipeline for all school documents (textbooks, circulars, notes, worksheets, answer
sheets, policies, timetables): **OCR → parse → chunk → embed → metadata → index → version**. Feeds RAG
+ the Knowledge Graph; never re-implemented per feature. Today only fragments exist (`pytesseract` for
admissions docs; vision models for answer sheets). All extracted text is **untrusted** (sanitize before
prompt/DB); uploads deduped, retention-limited, never warehoused as copyrighted text.

## Knowledge Graph
Curriculum modeled as an explicit relationship graph — see [`KNOWLEDGE_GRAPH.md`](./KNOWLEDGE_GRAPH.md). Spine-first, derived from approved sources.

## No textbook warehousing (settled — `DECISION_LOG` 2026-06-17)
Store structured curriculum maps + approved Concept Cards, not full copyrighted textbooks. Real
copyright risk under Indian law. NCERT/ePathshala with reuse-rights checks.

## Current state / gaps

| Capability | State |
|---|---|
| CurriculumPack model + versioning + approval | ✅ |
| RAG index/retrieve/build_context | ✅ foundation |
| QP generation grounded in packs | ⬜ next batch |
| Document Intelligence pipeline | 🔧 fragments only |
| ConceptCard first-class table | ⬜ planned (tutor grounding) |
| Curriculum management UI | ⬜ planned |
| Knowledge Graph tables | ⬜ planned |

> **Owner handoff:** ARM has textbooks + question papers in a separate folder — request it when starting
> full Document Intelligence ingestion.
