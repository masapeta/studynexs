# Vector Store

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**✅ Complete**

## Owner

`app/modules/ai/vectorstore/`

## Features

| Feature | State |
|---------|-------|
| `VectorStore` ABC | ✅ |
| Qdrant adapter | ✅ |
| In-memory adapter (tests) | ✅ |
| Tenant-scoped search (`school_id` required) | ✅ |
| Namespace / collection naming | ✅ |

## Files

`apps/api/app/modules/ai/vectorstore/`

## Config

`VECTOR_STORE=qdrant` · Qdrant URL via env

## Used by

RAG service only (features never touch store directly)

## Tests

`tests/test_vectorstore.py` (6)

## Batch

9–11
