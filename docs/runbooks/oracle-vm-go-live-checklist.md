# Oracle VM Go-Live Checklist (One Page)

Use this checklist immediately before and after public go-live.

Related runbooks:

- [oracle-vm-production-deployment.md](./oracle-vm-production-deployment.md)
- [oracle-vm-production-deployment-openai-only.md](./oracle-vm-production-deployment-openai-only.md)
- [production-operations.md](./production-operations.md)

## A) Pre-go-live controls

- [ ] Change window approved.
- [ ] Rollback owner assigned.
- [ ] Team communication channel active.
- [ ] Last known good commit SHA recorded.

## B) Infrastructure and network

- [ ] Oracle VM reachable via SSH.
- [ ] Inbound open only on 22, 80, 443.
- [ ] 5432, 6379, 6333 are not internet-exposed.
- [ ] Docker and docker compose are healthy.

Quick check:

```bash
sudo ss -tulpn | grep -E ':22|:80|:443|:5432|:6379|:6333'
docker ps
docker compose version
```

## C) Runtime configuration

- [ ] File exists: /opt/studynexs/deploy/env/api.env
- [ ] Permissions are strict: chmod 600
- [ ] ENVIRONMENT=production
- [ ] COOKIE_SECURE=true
- [ ] ALLOWED_ORIGINS points to real HTTPS app hosts
- [ ] AI provider keys are present for selected provider
- [ ] AADHAAR_ENCRYPTION_KEY is set and backed up securely offline

Quick check:

```bash
ls -l /opt/studynexs/deploy/env/api.env
grep -E '^(ENVIRONMENT|COOKIE_SECURE|ALLOWED_ORIGINS|AI_DEFAULT_PROVIDER|TENANT_BASE_DOMAIN)=' /opt/studynexs/deploy/env/api.env
```

## D) Deploy and migrate

- [ ] Latest code pulled from develop.
- [ ] docker-compose.prod.yml synced from repo to deploy folder.
- [ ] API image built successfully.
- [ ] alembic upgrade head successful.
- [ ] Stack up with no restart loops.

Quick check:

```bash
cd /opt/studynexs/deploy/compose
docker compose --env-file ../env/api.env -f docker-compose.prod.yml ps
docker compose --env-file ../env/api.env -f docker-compose.prod.yml logs --tail=150 api
```

## E) Health and readiness gates

- [ ] Local ingress is healthy.
- [ ] Readiness confirms DB and Redis status.
- [ ] Public HTTPS health endpoint responds.

Quick check:

```bash
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/ready
curl -fsS https://api.studynexs.com/health
curl -fsS https://api.studynexs.com/ready
```

## F) Web and user journey validation

- [ ] Cloudflare deployment completed.
- [ ] Login flow works on demo/app host.
- [ ] Dashboard loads without hard errors.
- [ ] Smoke test passes.

Quick check from local machine:

```powershell
Set-Location d:/Projects/studynexs-platform/studynexs-dev/apps/admin-web
$env:E2E_BASE_URL="https://demo.studynexs.com"
npm run e2e-smoke:prod
```

## G) Backup and rollback readiness

- [ ] Fresh PostgreSQL backup created and file size verified.
- [ ] Rollback command tested in dry-run plan.
- [ ] runtime/current.json updated with deployed SHA and timestamp.

Quick backup command:

```bash
mkdir -p /opt/studynexs/backups/postgres
docker exec studynexs-prod-postgres pg_dump -U studynexs studynexs | gzip > /opt/studynexs/backups/postgres/studynexs_$(date +%Y%m%d_%H%M).sql.gz
ls -lh /opt/studynexs/backups/postgres | tail -n 3
```

## H) First 24-hour watch

- [ ] Monitor API logs every 30 minutes for 4 hours.
- [ ] Monitor 429 and 5xx rates.
- [ ] Verify AI generation path with one real smoke request.
- [ ] Confirm no tenant mismatch or auth errors.

Operational command:

```bash
cd /opt/studynexs/deploy/compose
docker compose --env-file ../env/api.env -f docker-compose.prod.yml logs --tail=300 api
```

## I) Go / no-go decision

Go only if all sections A-H are complete.

No-go if any of the following is true:

1. /ready fails
2. Smoke test fails
3. AI provider is unreachable for configured default provider
4. Backup is missing
5. Any cross-tenant or auth regression appears
