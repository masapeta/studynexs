# Azure production edge (WAF)

## Overview

Deploy **Azure Front Door** with **WAF policy** in front of Container Apps / App Service hosting the API.

Files:

- `front-door-waf.bicep` — Front Door profile, endpoint, WAF policy (OWASP 3.2), rate limit rule

## Deploy (example)

```bash
az group create -n rg-studynexs-prod -l centralindia

az deployment group create \
  -g rg-studynexs-prod \
  -f infra/azure/front-door-waf.bicep \
  -p apiBackendHost=api.studynexs.com \
       apiBackendAddress=studynexs-api.azurecontainerapps.io
```

## Rollout phases

1. **Detection** — set `wafPolicyMode` to `Detection` in Bicep; monitor logs 1–2 weeks
2. **Prevention** — switch to `Prevention` after tuning false positives
3. Add exclusions for known-good payloads (long notice text, etc.)

## Complements app limits

| Layer | Role |
|-------|------|
| Front Door WAF | DDoS L7, OWASP, geo (optional) |
| Nginx | Per-IP burst (compose / VM) |
| FastAPI + Redis | Per-user/school limits |

See [docs/runbooks/rate-limits-and-waf.md](../../docs/runbooks/rate-limits-and-waf.md).
