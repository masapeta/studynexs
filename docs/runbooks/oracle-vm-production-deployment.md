# StudyNexs Oracle VM Production Deployment Runbook

This runbook is an end-to-end, copy-paste deployment guide for:

1. Oracle VM API deployment using Docker Compose
2. Cloudflare web deployment for admin-web
3. Real StudyNexs domains
4. AI provider choice: Gemini for LLM + OpenAI for embeddings
5. Safe production api.env template with placeholders only (no secrets)

References:

- [infra/scripts/bootstrap_oci_vm.sh](../../infra/scripts/bootstrap_oci_vm.sh)
- [infra/scripts/deploy.sh](../../infra/scripts/deploy.sh)
- [infra/docker/docker-compose.prod.yml](../../infra/docker/docker-compose.prod.yml)
- [infra/nginx/nginx.conf](../../infra/nginx/nginx.conf)
- [docs/DEPLOYMENT_ARCHITECTURE.md](../DEPLOYMENT_ARCHITECTURE.md)
- [docs/DEPLOYMENT_CONVENTIONS.md](../DEPLOYMENT_CONVENTIONS.md)
- [docs/URL_ARCHITECTURE.md](../URL_ARCHITECTURE.md)

## 0) Production values used in this runbook

This runbook is customized to these domains:

- Root domain: studynexs.com
- API: api.studynexs.com
- Demo web: demo.studynexs.com
- App web: app.studynexs.com

Provider choice in this runbook:

- LLM provider: Gemini
- Embedding provider: OpenAI

## 1) Pre-flight checklist

Before running commands:

1. Oracle VM is created (Ubuntu 22.04 or 24.04 recommended).
2. Security list allows inbound:
   - 22 from your admin IP only
   - 80 and 443 for public traffic
3. 5432, 6379, 6333 are not open to public internet.
4. Cloudflare zone for studynexs.com is active.
5. You have repo access and Cloudflare deploy access.

## 2) Safe production api.env template (placeholders only)

Create this on VM at /opt/studynexs/deploy/env/api.env with chmod 600.

```dotenv
# StudyNexs production environment template (placeholders only)
# No real secrets in this file template.

# Core
ENVIRONMENT=production
DEBUG=false
APP_NAME=StudyNexs API

# Security and auth
JWT_SECRET_KEY=<REPLACE_WITH_STRONG_SECRET_MIN_32_CHARS>
WEBHOOK_SECRET=<REPLACE_WITH_STRONG_WEBHOOK_SECRET>
METRICS_TOKEN=<REPLACE_WITH_METRICS_BEARER_TOKEN>

# Aadhaar encryption (Fernet key)
# Generate once and store safely offline.
AADHAAR_ENCRYPTION_KEY=<REPLACE_WITH_FERNET_KEY_BASE64_URLSAFE>

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=studynexs
POSTGRES_PASSWORD=<REPLACE_WITH_DB_PASSWORD>
POSTGRES_DB=studynexs

# Redis
REDIS_URL=redis://redis:6379/0

# Tenant and domain
TENANT_BASE_DOMAIN=studynexs.com
DEFAULT_TENANT_SLUG=reference

# CORS and cookie security
COOKIE_SECURE=true
ALLOWED_ORIGINS=["https://demo.studynexs.com","https://app.studynexs.com"]

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=<OPTIONAL_QDRANT_API_KEY_OR_EMPTY>

# AI provider choice (this runbook)
AI_DEFAULT_PROVIDER=gemini
AI_DEFAULT_MODEL=
AI_FALLBACK_PROVIDER=
AI_FALLBACK_MODEL=
GEMINI_API_KEY=<REPLACE_WITH_GEMINI_API_KEY>

# Embeddings choice (this runbook)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=<REPLACE_WITH_OPENAI_API_KEY>

# Optional providers (leave empty if unused)
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=
OLLAMA_API_KEY=

# VM host paths
STUDYNEXS_UPLOADS_DIR=/opt/studynexs/data/uploads
STUDYNEXS_METRICS_TOKEN_FILE=/opt/studynexs/deploy/env/metrics_token

# Nginx public bind (go-live)
STUDYNEXS_NGINX_BIND=0.0.0.0
STUDYNEXS_NGINX_PORT=80

# Optional image tag override
STUDYNEXS_IMAGE_TAG=live

# Optional observability
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_SAMPLE_RATE=1.0

# Optional demo provisioning hardening
DEMO_PROVISIONING_ENABLED=false
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=

# Optional tutor voice
TUTOR_TTS_PROVIDER=edge
TUTOR_TTS_VOICE=en-IN-NeerjaExpressiveNeural
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=centralindia

# AEI flags (keep false unless explicitly activating)
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=false
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
```

## 3) One-time Oracle VM bootstrap and first deploy (exact command sequence)

Run the following on the Oracle VM shell.

```bash
set -euo pipefail

# ---------- customize once ----------
REPO_URL="https://github.com/masapeta/studynexs.git"
BRANCH="develop"

# Real domains (customized)
ROOT_DOMAIN="studynexs.com"
API_DOMAIN="api.studynexs.com"
DEMO_DOMAIN="demo.studynexs.com"
APP_DOMAIN="app.studynexs.com"

# ---------- base packages ----------
sudo apt update
sudo apt install -y git curl ca-certificates

# ---------- clone temporary working copy ----------
cd /tmp
rm -rf studynexs-dev-bootstrap
git clone --branch "$BRANCH" "$REPO_URL" studynexs-dev-bootstrap

# ---------- bootstrap host layout ----------
cd /tmp/studynexs-dev-bootstrap/infra/scripts
sudo bash bootstrap_oci_vm.sh --repo-url "$REPO_URL" --branch "$BRANCH"

# ---------- write safe env from template ----------
sudo tee /opt/studynexs/deploy/env/api.env >/dev/null <<EOF
ENVIRONMENT=production
DEBUG=false
APP_NAME=StudyNexs API
JWT_SECRET_KEY=<REPLACE_WITH_STRONG_SECRET_MIN_32_CHARS>
WEBHOOK_SECRET=<REPLACE_WITH_STRONG_WEBHOOK_SECRET>
METRICS_TOKEN=<REPLACE_WITH_METRICS_BEARER_TOKEN>
AADHAAR_ENCRYPTION_KEY=<REPLACE_WITH_FERNET_KEY_BASE64_URLSAFE>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=studynexs
POSTGRES_PASSWORD=<REPLACE_WITH_DB_PASSWORD>
POSTGRES_DB=studynexs
REDIS_URL=redis://redis:6379/0
TENANT_BASE_DOMAIN=$ROOT_DOMAIN
DEFAULT_TENANT_SLUG=reference
COOKIE_SECURE=true
ALLOWED_ORIGINS=["https://$DEMO_DOMAIN","https://$APP_DOMAIN"]
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=<OPTIONAL_QDRANT_API_KEY_OR_EMPTY>
AI_DEFAULT_PROVIDER=gemini
AI_DEFAULT_MODEL=
AI_FALLBACK_PROVIDER=
AI_FALLBACK_MODEL=
GEMINI_API_KEY=<REPLACE_WITH_GEMINI_API_KEY>
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=<REPLACE_WITH_OPENAI_API_KEY>
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=
OLLAMA_API_KEY=
STUDYNEXS_UPLOADS_DIR=/opt/studynexs/data/uploads
STUDYNEXS_METRICS_TOKEN_FILE=/opt/studynexs/deploy/env/metrics_token
STUDYNEXS_NGINX_BIND=0.0.0.0
STUDYNEXS_NGINX_PORT=80
STUDYNEXS_IMAGE_TAG=live
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_SAMPLE_RATE=1.0
DEMO_PROVISIONING_ENABLED=false
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
TUTOR_TTS_PROVIDER=edge
TUTOR_TTS_VOICE=en-IN-NeerjaExpressiveNeural
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=centralindia
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=false
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
EOF
sudo chmod 600 /opt/studynexs/deploy/env/api.env

# ---------- create production override for provider + CORS ----------
sudo tee /opt/studynexs/deploy/compose/docker-compose.prod.override.yml >/dev/null <<EOF
services:
  api:
    environment:
      ALLOWED_ORIGINS: '["https://$DEMO_DOMAIN","https://$APP_DOMAIN"]'
      AI_DEFAULT_PROVIDER: gemini
      AI_DEFAULT_MODEL: ""
      AI_FALLBACK_PROVIDER: ""
      AI_FALLBACK_MODEL: ""
      EMBEDDING_PROVIDER: openai
      EMBEDDING_MODEL: text-embedding-3-small
      OLLAMA_BASE_URL: ""
  worker:
    environment:
      ALLOWED_ORIGINS: '["https://$DEMO_DOMAIN","https://$APP_DOMAIN"]'
      AI_DEFAULT_PROVIDER: gemini
      AI_DEFAULT_MODEL: ""
      AI_FALLBACK_PROVIDER: ""
      AI_FALLBACK_MODEL: ""
      EMBEDDING_PROVIDER: openai
      EMBEDDING_MODEL: text-embedding-3-small
      OLLAMA_BASE_URL: ""
EOF

# ---------- first build and start ----------
cd /opt/studynexs/deploy/compose
sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml build api

sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml up -d

# ---------- run DB migrations ----------
sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml \
  run --rm api alembic upgrade head

# ---------- optional: seed demo data ----------
sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml \
  run --rm -v /opt/studynexs/repo/apps/api/scripts:/app/scripts:ro \
  api python scripts/seed_demo_ssc.py

# ---------- verify local VM ingress ----------
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/ready

# ---------- verify containers ----------
sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml ps
```

## 4) DNS and Cloudflare setup

In Cloudflare DNS:

1. A record: api.studynexs.com -> Oracle VM public IP
2. CNAME: demo.studynexs.com -> Cloudflare Pages project domain
3. CNAME: app.studynexs.com -> Cloudflare Pages project domain
4. Proxy enabled for public routes.

Ensure SSL/TLS mode is Full (strict) if origin certificate is configured.

## 5) Deploy web to Cloudflare (from your local machine)

Run in repository folder apps/admin-web:

```powershell
Set-Location d:/Projects/studynexs-platform/studynexs-dev/apps/admin-web

$env:NEXT_PUBLIC_API_URL="https://api.studynexs.com"
$env:NEXT_PUBLIC_TENANT_BASE_DOMAIN="studynexs.com"
$env:NEXT_PUBLIC_TENANT_SLUG="demo"

npm ci
npm run cf:deploy
```

## 6) End-to-end production verification

From your local machine:

```powershell
# API checks
curl.exe -I https://api.studynexs.com/health
curl.exe -I https://api.studynexs.com/ready

# Frontend smoke check
Set-Location d:/Projects/studynexs-platform/studynexs-dev/apps/admin-web
$env:E2E_BASE_URL="https://demo.studynexs.com"
npm run e2e-smoke:prod
```

From Oracle VM:

```bash
cd /opt/studynexs/deploy/compose
sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml logs --tail=200 api
```

## 7) Backup before live traffic

Run on Oracle VM:

```bash
set -euo pipefail
mkdir -p /opt/studynexs/backups/postgres
docker exec studynexs-prod-postgres pg_dump -U studynexs studynexs \
  | gzip > /opt/studynexs/backups/postgres/studynexs_$(date +%Y%m%d_%H%M).sql.gz
ls -lh /opt/studynexs/backups/postgres | tail -n 5
```

## 8) Standard redeploy sequence (copy-paste)

Use this instead of the base deploy script so provider/CORS override remains active.

```bash
set -euo pipefail
BRANCH="develop"

cd /opt/studynexs/repo
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

cp -f /opt/studynexs/repo/infra/docker/docker-compose.prod.yml /opt/studynexs/deploy/compose/
cp -f /opt/studynexs/repo/infra/nginx/nginx.conf /opt/studynexs/deploy/nginx/

GIT_SHA=$(git rev-parse --short HEAD)

cd /opt/studynexs/deploy/compose
sudo STUDYNEXS_IMAGE_TAG="$GIT_SHA" docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml build api

sudo STUDYNEXS_IMAGE_TAG="$GIT_SHA" docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml \
  run --rm api alembic upgrade head

sudo STUDYNEXS_IMAGE_TAG="$GIT_SHA" docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml up -d

curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/ready

cat >/opt/studynexs/runtime/current.json <<EOF
{
  "image_tag": "$GIT_SHA",
  "git_sha": "$(git rev-parse HEAD)",
  "branch": "$BRANCH",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
```

## 9) Rollback sequence (copy-paste)

```bash
set -euo pipefail
GOOD_SHA="<REPLACE_WITH_PREVIOUS_GOOD_GIT_SHA>"

cd /opt/studynexs/repo
git checkout "$GOOD_SHA"

cp -f /opt/studynexs/repo/infra/docker/docker-compose.prod.yml /opt/studynexs/deploy/compose/

cd /opt/studynexs/deploy/compose
sudo STUDYNEXS_IMAGE_TAG="$GOOD_SHA" docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml build api

sudo STUDYNEXS_IMAGE_TAG="$GOOD_SHA" docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml up -d

curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/ready
```

## 10) Production go-live checklist

1. API /health and /ready are green on public origin.
2. Frontend smoke test is green on demo/app domains.
3. AI generation path works with configured provider keys.
4. Backups are being created and verified.
5. No public exposure of Postgres, Redis, Qdrant ports.
6. Cloudflare SSL and DNS are stable.
7. Deploy metadata file is updated at /opt/studynexs/runtime/current.json.

## 11) Notes on secrets and safety

1. Do not commit api.env to Git.
2. Keep api.env permission as 600.
3. Keep Aadhaar encryption key in secure vault and offline backup.
4. Rotate JWT, webhook, database, and provider keys per your security policy.
