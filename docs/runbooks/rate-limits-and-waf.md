# Rate limits and WAF

## App-level (Redis)

Configured in `apps/api/app/core/config.py`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `RATE_LIMIT_ENABLED` | `true` | Master switch |
| `API_RATE_LIMIT_READ_PER_MIN` | 300 | List endpoints |
| `API_RATE_LIMIT_WRITE_PER_MIN` | 60 | Mutations |
| `API_RATE_LIMIT_UPLOAD_PER_MIN` | 20 | File upload |

Keys: `api:{action}:{school_id}:{user_id}` — not IP-only (schools behind NAT).

Protected routes: attendance mark, fees pay, file upload, users list, academic students list.

Auth routes use separate limits in `check_rate_limit` (OTP/login).

## Nginx (dev / edge)

`infra/nginx/nginx.conf`:

- Auth: 30 req/min per IP, burst 10
- API: 200 req/min per IP, burst 50
- `client_max_body_size 12m`
- Returns HTTP 429 when exceeded

## Azure WAF (production)

See `infra/azure/README.md` and `infra/azure/front-door-waf.bicep`.

Rollout: **Detection** mode first → tune exclusions → **Prevention**.

## Operations

- Watch 429 rate in logs (`status=429`).
- Tune limits using soak test data before lowering defaults.
- Set `RATE_LIMIT_ENABLED=false` only in local dev if needed.
