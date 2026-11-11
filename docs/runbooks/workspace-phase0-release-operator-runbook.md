# Workspace Phase 0 Release Operator Runbook

This runbook packages and publishes the current Teacher Workspace Phase 0 release using the repo's existing deployment scripts and release checks.

It is intentionally narrow:

1. API deploy to the Oracle VM
2. Admin web deploy to Cloudflare
3. Post-deploy smoke verification for the current release slice

Related canonical references:

- [oracle-vm-production-deployment.md](./oracle-vm-production-deployment.md)
- [oracle-vm-go-live-checklist.md](./oracle-vm-go-live-checklist.md)
- [DEPLOYMENT_CONVENTIONS.md](../DEPLOYMENT_CONVENTIONS.md)
- [DEPLOYMENT_ARCHITECTURE.md](../DEPLOYMENT_ARCHITECTURE.md)

## 0) Fixed values for this release

These values are either committed in the repo or explicitly provided for this operator run.

| Item | Value | Source |
|------|-------|--------|
| Git branch | `develop` | release commit already pushed |
| Oracle VM SSH target | `ubuntu@140.245.202.69` | operator-provided |
| SSH key | `~/.ssh/studynexs_prod` | [SSH_KEYS.md](../../infra/inventory/SSH_KEYS.md) |
| Root domain | `studynexs.com` | [URL_ARCHITECTURE.md](../URL_ARCHITECTURE.md) |
| API host | `api.studynexs.com` | [URL_ARCHITECTURE.md](../URL_ARCHITECTURE.md) |
| Demo web host | `demo.studynexs.com` | [URL_ARCHITECTURE.md](../URL_ARCHITECTURE.md) |
| App web host | `app.studynexs.com` | [URL_ARCHITECTURE.md](../URL_ARCHITECTURE.md) |
| Admin web Cloudflare deploy target | `academix-platform` | [wrangler.jsonc](../../apps/admin-web/wrangler.jsonc) |
| Marketing site deploy target | `studynexs-web` | [wrangler.toml](../../wrangler.toml) |

## 1) Preconditions

Before you run the commands below, confirm:

- `develop` already contains the four workspace phase 0 commits.
- The VM already has the StudyNexs host layout under `/opt/studynexs/`.
- `/opt/studynexs/deploy/env/api.env` already exists on the VM.
- Cloudflare access is available for the admin web deploy target `academix-platform`.
- The custom domains `demo.studynexs.com` and `app.studynexs.com` already point at the correct Cloudflare deployment target.

If the VM has not been bootstrapped yet, stop here and use [oracle-vm-production-deployment.md](./oracle-vm-production-deployment.md) first.

## 2) API release on the Oracle VM

Open the VM shell:

```bash
ssh -i ~/.ssh/studynexs_prod ubuntu@140.245.202.69
```

Run the standard repo deploy script on the VM:

```bash
set -euo pipefail

bash /opt/studynexs/deploy/scripts/deploy.sh --branch develop
```

If `/opt/studynexs/deploy/compose/docker-compose.prod.override.yml` exists, `deploy.sh` stops
before doing anything. Review that file, then re-run with `--include-prod-override`. The
flag only acknowledges intentional use; it is not a review.

If the installed script answers `Unknown argument: --include-prod-override`, it predates the
override check and has done nothing. Upgrade it first by re-running bootstrap from the updated
repo (`oracle-vm-production-deployment.md` §8a); do not run the old script to upgrade itself.

Verify the deployed runtime state on the VM:

```bash
set -euo pipefail

cd /opt/studynexs/deploy/compose
docker compose --env-file ../env/api.env -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/ready
cat /opt/studynexs/runtime/current.json
```

If answer-sheet or other background jobs are in scope for this release window, ensure the worker is running too:

```bash
set -euo pipefail

cd /opt/studynexs/deploy/compose
docker compose --env-file ../env/api.env -f docker-compose.prod.yml up -d worker
docker compose --env-file ../env/api.env -f docker-compose.prod.yml ps worker
```

## 3) Admin web release to Cloudflare

Run this from your local machine in the repo checkout:

```powershell
Set-Location "d:/Projects/studynexs-platform/studynexs-dev/apps/admin-web"

$env:NEXT_PUBLIC_API_URL = "https://api.studynexs.com"
$env:NEXT_PUBLIC_TENANT_BASE_DOMAIN = "studynexs.com"
$env:NEXT_PUBLIC_TENANT_SLUG = "demo"

npm ci
npm run build
npm run cf:build
npm run cf:deploy
```

Notes:

- The committed Wrangler deploy target for `apps/admin-web` is `academix-platform`.
- The repo does not store the Cloudflare custom-domain project record in `infra/inventory/` yet, so domain mapping remains an operator-owned Cloudflare check.
- The root-level `wrangler.toml` targets the separate marketing site `studynexs-web`; it is not part of this workspace release.

## 4) API smoke verification

Run the API smoke against the live API host from your local machine:

```powershell
Set-Location "d:/Projects/studynexs-platform/studynexs-dev/apps/api"

$env:SMOKE_BASE_URL = "https://api.studynexs.com"
python scripts/smoke_pilot_readiness.py
```

Expected result:

- `/health` and `/ready` pass
- the tenant login succeeds
- the pilot-readiness JSON evidence is rewritten under `docs/pilot/naagarjuna-talent-school/t0-evidence/`

## 5) Browser smoke verification

Run the production browser smoke against the demo host from your local machine:

```powershell
Set-Location "d:/Projects/studynexs-platform/studynexs-dev/apps/admin-web"

$env:E2E_BASE_URL = "https://demo.studynexs.com"
$env:E2E_API_URL = "https://api.studynexs.com"
$env:E2E_TENANT_SLUG = "naagarjuna"

npm run e2e-smoke:prod
```

Expected result:

- login works over HTTPS
- dashboard routes render
- the smoke stays free of disallowed console errors

## 6) Fast failure checks

If any of these fail, stop the release and investigate before continuing:

1. `deploy.sh` fails to build, migrate, or restart cleanly.
2. `curl http://127.0.0.1:8080/ready` fails on the VM.
3. `https://api.studynexs.com/health` or `https://api.studynexs.com/ready` fails publicly.
4. `npm run cf:deploy` fails for `academix-platform`.
5. `python scripts/smoke_pilot_readiness.py` fails.
6. `npm run e2e-smoke:prod` fails.

## 7) Operator close-out

After a green publish, record these facts outside secrets-bearing files:

1. Save the `runtime/current.json` contents from the VM.
2. Record the Cloudflare deployment identifier shown by the deploy command.
3. Record the smoke results timestamp.
4. If the Cloudflare Pages or Workers custom-domain/project mapping is now known, add it to `infra/inventory/` in a follow-up inventory update.

## 8) What is still intentionally unresolved

This runbook is exact on the current VM host and live domains.

One inventory fact is still not committed in the repo:

- the exact Cloudflare project-domain mapping for `demo.studynexs.com` and `app.studynexs.com`

Until that is written into `infra/inventory/`, the deploy target name `academix-platform` is the committed source of truth for the admin-web publish command, and the custom-domain mapping remains a Cloudflare-side operator check.