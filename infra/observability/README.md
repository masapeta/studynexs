# StudyNexs Observability Stack

OpenTelemetry collects **metrics and traces** from the API. Grafana visualizes them and fires **alerts** via Prometheus.

```
┌─────────────┐   OTLP gRPC    ┌──────────────────┐
│ studynexs-  │───────────────►│ otel-collector   │
│ api         │                └────────┬─────────┘
│             │                         │
│ /metrics    │              ┌──────────┼──────────┐
└──────┬──────┘              ▼          ▼          ▼
       │ scrape         Prometheus   Tempo    (debug)
       │                    │          │
       └────────────────────┼──────────┘
                            ▼
                       ┌─────────┐
                       │ Grafana │
                       └─────────┘
```

## Quick start (local)

```bash
# From repo root — starts API + Postgres + Redis + observability stack
docker compose -f infra/docker/docker-compose.dev.yml \
               -f infra/docker/docker-compose.observability.yml up -d

# Rebuild API image after first pull (installs opentelemetry deps)
docker compose -f infra/docker/docker-compose.dev.yml build api
docker compose -f infra/docker/docker-compose.observability.yml up -d
```

| Service    | URL                         | Credentials        |
|------------|-----------------------------|--------------------|
| Grafana    | http://localhost:3001       | admin / studynexs_dev |
| Prometheus | http://localhost:9090       | —                  |
| API metrics| http://localhost:8000/metrics | —               |
| API telemetry | GET /api/v1/ai/telemetry (admin JWT) | — |

## What is instrumented

| Signal  | Source | Notes |
|---------|--------|-------|
| **Traces** | FastAPI, httpx (LLM HTTP), `ai.llm.generate` spans | Exported to Tempo |
| **Metrics** | AI LLM/TTS counters + histograms, HTTP server | API `/metrics` + OTel collector |
| **Logs** | structlog `ai_llm_call` events | Correlate via `request_id` / trace ID |

## API configuration (`apps/api/.env`)

```env
OTEL_ENABLED=true
OTEL_SERVICE_NAME=studynexs-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_SAMPLE_RATE=1.0
```

For local Python (no Docker), point at the collector:

```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

Install deps:

```bash
cd apps/api
pip install -e ".[ai,observability]"
```

## Grafana dashboard

Pre-provisioned: **StudyNexs → StudyNexs AI Telemetry**

Panels: request rate, error rate, fallback usage, token throughput, p95 latency by feature, provider breakdown.

## Alerts (Prometheus)

Defined in `prometheus-alerts.yml`:

- `StudyNexsAPIDown` — API `/metrics` target unavailable
- `StudyNexsHTTP5xxHigh` — sustained 5xx responses
- `StudyNexsJobStatusScrapeError` — job status metrics could not read DB state
- `StudyNexsFailedJobBacklog` — failed jobs require operator review
- `StudyNexsStaleJobBacklog` — queued/running jobs older than 30 minutes
- `AI_LLM_ErrorRateHigh` — >10% errors for 5m
- `AI_LLM_FallbackSpike` — fallback provider active
- `AI_LLM_LatencyP95High` — p95 > 30s

Wire Alertmanager in production (PagerDuty, Slack, email).

Operational response is documented in
`docs/runbooks/production-operations.md`.

## Production notes

- Set `OTEL_TRACES_SAMPLE_RATE=0.1` (or lower) at high traffic
- Run collector + Prometheus + Tempo + Grafana as managed services (Azure Monitor, Grafana Cloud, or self-hosted)
- Restrict Grafana/Prometheus ports — not public internet
- `/metrics` and `/api/v1/ai/telemetry` should stay internal or auth-protected

## Architecture split (your table)

| Capability | Tool |
|------------|------|
| Collect metrics & traces | **OpenTelemetry** (in API + collector) |
| Store metrics | **Prometheus** |
| Store traces | **Tempo** |
| Dashboards & alerts | **Grafana** |
