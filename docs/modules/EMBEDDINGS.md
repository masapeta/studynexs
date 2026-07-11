# Embeddings

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**✅ Complete** (OpenAI + stub)

## Owner

`app/modules/ai/embeddings/`

## Features

| Feature | State |
|---------|-------|
| `EmbeddingProvider` ABC | ✅ |
| OpenAI `text-embedding-3-small` (1536-dim) | ✅ |
| Stub provider (tests) | ✅ |
| `EmbeddingService` DI entry | ✅ |
| Ollama embeddings | ⬜ |
| Azure OpenAI embeddings | ⬜ |

## Files

`apps/api/app/modules/ai/embeddings/`

## Config

`EMBEDDING_PROVIDER=openai` · `EMBEDDING_MODEL=text-embedding-3-small`

## Used by

RAG (`index_pack`) · Vector store indexing

## Tests

`tests/test_embeddings.py` (7)

## Batch

9–11
