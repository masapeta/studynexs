# AI Platform

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) · Canonical: [`/CLAUDE.md`](../../CLAUDE.md) §33–44

## Status

**✅ Complete** (shared foundation)

## Owner

Shared Intelligence Platform — all pillars consume; no feature calls provider SDKs directly.

## Features

| Feature | State |
|---------|-------|
| LLM gateway (OpenAI, Gemini, Anthropic, Ollama) | ✅ |
| Fallback + metering + pricing | ✅ |
| Input/output guards | ✅ |
| AI credits (school pool + quotas) | ✅ |
| Telemetry | ✅ |
| Commit-before-response (`CommitOnSuccessRoute`) | ✅ |
| Aadhaar encryption (`EncryptedString`) | ✅ |

## Files

```
apps/api/app/modules/ai/gateway/
apps/api/app/core/api_route.py
apps/api/app/core/encryption.py
apps/api/app/modules/ai/services/ai_credits.py
```

## Dependencies

Postgres · Redis · configured provider API keys (env)

## Used by

Embeddings · RAG · Assessment Intelligence · Tutor · (planned) Copilots

## Tests

`tests/test_ai_credits.py` · `tests/test_commit_route.py` · `tests/test_encryption.py`

## Batch history

Batches 1–11 (hardening + foundation) · merge restore commit `cb3862d`
