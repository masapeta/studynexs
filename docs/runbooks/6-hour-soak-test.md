# 6-hour API soak test runbook

## Prerequisites

- Docker: PostgreSQL, Redis, API, Nginx
- Python venv with `psutil`, `locust`
- Seeded admin user for load test credentials

## 1. Start stack

```bash
docker compose -f infra/docker/docker-compose.dev.yml up -d postgres redis api nginx
```

Run API **without** `--reload` for realistic behavior:

```bash
cd apps/api
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 2. Terminals

| Terminal | Command |
|----------|---------|
| Memory | `python scripts/memory_sampler.py --interval 60 --duration 21600` |
| DB | `while ($true) { python scripts/monitor_snapshot.py; sleep 300 }` |
| Load | `locust -f locustfile.py --host=http://localhost:80 --users 20 --spawn-rate 2 --run-time 6h --headless` |

## 3. Metrics to record

| Metric | Source |
|--------|--------|
| p50 / p95 / p99 latency | Locust report or `http_request` structlog events |
| Error rate (5xx, 429) | Locust + logs |
| RSS memory | `memory_samples.jsonl` |
| `audit_logs` rows & size | `monitor_snapshot.py` |
| DB connections by state | `monitor_snapshot.py` |

## 4. Pass / fail criteria (initial)

- p95 stable (no steady climb > 2x after hour 2)
- RSS not growing unbounded (> 30% over 6h without plateau)
- 5xx rate < 0.1%
- 429 only under intentional abuse tests

## 5. Results template

| Hour | p95 ms | 5xx % | 429 % | RSS MB | audit rows | DB active conns |
|------|--------|-------|-------|--------|------------|-----------------|
| 0 | | | | | | |
| 1 | | | | | | |
| … | | | | | | |

## Notes

- `X-Response-Time-Ms` header added by metrics middleware on each response.
- Run against **nginx** (`:80`) to include edge rate limits.
