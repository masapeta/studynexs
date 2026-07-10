# AI Architecture — the Shared Intelligence Platform

> **Engineering companion** to [`/CLAUDE.md`](../CLAUDE.md) Part V (§33–§44). CLAUDE.md is canonical
> policy; this doc records the **current implementation, code locations, and how to extend it**. When
> they disagree, CLAUDE.md wins and this doc is corrected.

## Principle

The four pillars (Curriculum / Assessment / Learning / School-Ops Intelligence) **consume** one shared
platform; they never re-implement AI. If you find yourself adding a second gateway, embedder, vector
store, memory store, or OCR path — stop and extend the shared service (`CLAUDE.md` §4.1, §32/§33.1).

```
Applications → Four Pillars → Shared Intelligence Platform
                               (gateway · prompts · routing · metering · RAG · vector search ·
                                knowledge graph · AI memory · document intelligence · safety · audit)
```

## Services & code locations (`apps/api/app/modules/ai/`)

| Service | Path | State | Notes |
|---|---|---|---|
| **LLM gateway** | `gateway/` (`base.py`, `invoke.py`, `factory.py`, adapters `openai/gemini/anthropic/ollama`, `metering.py`, `pricing.py`, `input_guard.py`, `output_guard.py`, `errors.py`) | ✅ built | Single door for all model calls. `generate_llm(...)` with fallback + telemetry on every path. Providers lazy-imported. **Never call a provider SDK from feature code.** |
| **Embeddings** | `embeddings/` (`base.py` ABC, `openai_provider.py`, `stub_provider.py`, `factory.py`, `service.py`) | ✅ built | Provider→model separation. Config `EMBEDDING_PROVIDER=openai`, `EMBEDDING_MODEL=text-embedding-3-small` (1536-dim). `EmbeddingService` is the DI entry point. |
| **Vector store** | `vectorstore/` (`base.py` ABC, `qdrant_store.py`, `memory_store.py`, `factory.py`) | ✅ built | `VectorStore.search` **requires `school_id`** (tenant rule in the type). Config `VECTOR_STORE=qdrant`. `qdrant-client` in the `[rag]` extra. `collection_name(namespace, provider, dim)`. |
| **RAG** | `rag/service.py` | ✅ foundation | `index_pack` (chunk pack chapter→topic tree → embed → index), `retrieve(query, school_id, pack_id)` (tenant + pack scoped), `build_context` with `[n] (source: chapter › topic)` citations. **Grounding unit = curriculum topic** (structured, copyright-safe). **Not yet wired into QP generation.** |
| **Metering & credits** | `services/ai_credits.py`, `gateway/metering.py`, `telemetry/` | ✅ built | Row-locked credit reservation before the call; school pool + per-user quotas; IST month boundary; admin bypass by policy (`DECISION_LOG` 2026-06-15). |
| **Safety / guards** | `gateway/input_guard.py`, `output_guard.py` | ✅ built | Untrusted input; validate model output against a schema before use. |
| **Knowledge Graph** | — | ⬜ planned | → [`KNOWLEDGE_GRAPH.md`](./KNOWLEDGE_GRAPH.md) |
| **Document Intelligence** | partial (`pytesseract` admissions, vision eval) | 🔧 partial | One shared pipeline is the target → [`CURRICULUM_INTELLIGENCE.md`](./CURRICULUM_INTELLIGENCE.md) §Document Intelligence. |

## AI Memory vs. the system of record (`CLAUDE.md` §33.2)

- **System of record** = Postgres, authoritative, audited (students, marks, fees, approved papers, final evaluations). **This is the truth.**
- **AI Memory** = contextual/disposable (conversation, tutor session state, retrieval context, caches). Never store authoritative academic data *only* in AI memory; promote it into the owning module (human-reviewed where it carries authority). Losing AI memory must lose **zero** facts.

## How to add an AI capability (the only correct path)

1. Rule out a deterministic solution first (`CLAUDE.md` §79.5).
2. Write a **service** that composes `LLMMessage`s and calls the gateway `invoke` helper — never a provider SDK.
3. Ground it (RAG via `RagService` against an approved CurriculumPack); request structured output + validate against a Pydantic schema.
4. Guard inputs (`input_guard`); keep PII/secrets out of prompts and logs.
5. Meter it + enforce credits at generation; add a fallback/graceful path.
6. Human-in-the-loop if the output carries authority (§42, §40.5).
7. Emit telemetry; test malformed-output + tenant/pack scoping.

## Open decision
Final **production LLM provider** is unbenchmarked (`AI_DEFAULT_PROVIDER` config default is `gemini`;
embeddings run on OpenAI). Qualify on golden sets before locking (`DECISION_LOG` D5).
