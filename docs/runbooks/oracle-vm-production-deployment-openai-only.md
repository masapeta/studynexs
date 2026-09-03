# StudyNexs Oracle VM Production Deployment (OpenAI-only)

This is the OpenAI-only deployment variant for Oracle VM + Cloudflare.

Use this when you want:

1. OpenAI as primary LLM provider
2. OpenAI embeddings
3. No Gemini or Ollama runtime dependency

References:

- [oracle-vm-production-deployment.md](./oracle-vm-production-deployment.md)
- [../../infra/scripts/bootstrap_oci_vm.sh](../../infra/scripts/bootstrap_oci_vm.sh)
- [../../infra/docker/docker-compose.prod.yml](../../infra/docker/docker-compose.prod.yml)
- [../DEPLOYMENT_ARCHITECTURE.md](../DEPLOYMENT_ARCHITECTURE.md)

## 1) Customized values used here

- Root domain: studynexs.com
- API host: api.studynexs.com
- Demo host: demo.studynexs.com
- App host: app.studynexs.com
- Provider: OpenAI only

## 2) Safe production api.env template (placeholders only)

Create this file on VM:

- /opt/studynexs/deploy/env/api.env

Then set strict permissions:

- chmod 600 /opt/studynexs/deploy/env/api.env

```dotenv
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

TENANT_BASE_DOMAIN=studynexs.com
DEFAULT_TENANT_SLUG=reference
COOKIE_SECURE=true
ALLOWED_ORIGINS=["https://demo.studynexs.com","https://app.studynexs.com"]

QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=<OPTIONAL_QDRANT_API_KEY_OR_EMPTY>

AI_DEFAULT_PROVIDER=openai
AI_DEFAULT_MODEL=gpt-4.1-mini
AI_FALLBACK_PROVIDER=
AI_FALLBACK_MODEL=

OPENAI_API_KEY=<REPLACE_WITH_OPENAI_API_KEY>
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=
OLLAMA_API_KEY=

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

STUDYNEXS_UPLOADS_DIR=/opt/studynexs/data/uploads
STUDYNEXS_METRICS_TOKEN_FILE=/opt/studynexs/deploy/env/metrics_token
STUDYNEXS_NGINX_BIND=0.0.0.0
STUDYNEXS_NGINX_PORT=80

OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_SAMPLE_RATE=1.0

DEMO_PROVISIONING_ENABLED=false
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=

AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=false
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
```

## 3) One-time setup + first deploy (copy-paste)

Run on Oracle VM:

```bash
set -euo pipefail

REPO_URL="https://github.com/masapeta/studynexs.git"
BRANCH="develop"
ROOT_DOMAIN="studynexs.com"
API_DOMAIN="api.studynexs.com"
DEMO_DOMAIN="demo.studynexs.com"
APP_DOMAIN="app.studynexs.com"

sudo apt update
sudo apt install -y git curl ca-certificates

cd /tmp
rm -rf studynexs-dev-bootstrap
git clone --branch "$BRANCH" "$REPO_URL" studynexs-dev-bootstrap

cd /tmp/studynexs-dev-bootstrap/infra/scripts
sudo bash bootstrap_oci_vm.sh --repo-url "$REPO_URL" --branch "$BRANCH"

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
AI_DEFAULT_PROVIDER=openai
AI_DEFAULT_MODEL=gpt-4.1-mini
AI_FALLBACK_PROVIDER=
AI_FALLBACK_MODEL=
OPENAI_API_KEY=<REPLACE_WITH_OPENAI_API_KEY>
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=
OLLAMA_API_KEY=
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
STUDYNEXS_UPLOADS_DIR=/opt/studynexs/data/uploads
STUDYNEXS_METRICS_TOKEN_FILE=/opt/studynexs/deploy/env/metrics_token
STUDYNEXS_NGINX_BIND=0.0.0.0
STUDYNEXS_NGINX_PORT=80
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_SAMPLE_RATE=1.0
DEMO_PROVISIONING_ENABLED=false
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=false
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
EOF
sudo chmod 600 /opt/studynexs/deploy/env/api.env

sudo tee /opt/studynexs/deploy/compose/docker-compose.prod.override.yml >/dev/null <<EOF
services:
  api:
    environment:
      ALLOWED_ORIGINS: '["https://$DEMO_DOMAIN","https://$APP_DOMAIN"]'
      AI_DEFAULT_PROVIDER: openai
      AI_DEFAULT_MODEL: gpt-4.1-mini
      AI_FALLBACK_PROVIDER: ""
      AI_FALLBACK_MODEL: ""
      EMBEDDING_PROVIDER: openai
      EMBEDDING_MODEL: text-embedding-3-small
      OLLAMA_BASE_URL: ""
  worker:
    environment:
      ALLOWED_ORIGINS: '["https://$DEMO_DOMAIN","https://$APP_DOMAIN"]'
      AI_DEFAULT_PROVIDER: openai
      AI_DEFAULT_MODEL: gpt-4.1-mini
      AI_FALLBACK_PROVIDER: ""
      AI_FALLBACK_MODEL: ""
      EMBEDDING_PROVIDER: openai
      EMBEDDING_MODEL: text-embedding-3-small
      OLLAMA_BASE_URL: ""
EOF

cd /opt/studynexs/deploy/compose
sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml build api

sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml up -d

sudo docker compose --env-file ../env/api.env \
  -f docker-compose.prod.yml -f docker-compose.prod.override.yml \
  run --rm api alembic upgrade head

curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/ready
```

## 4) Deploy web (copy-paste)

Run on your local machine:

```powershell
Set-Location d:/Projects/studynexs-platform/studynexs-dev/apps/admin-web

$env:NEXT_PUBLIC_API_URL="https://api.studynexs.com"
$env:NEXT_PUBLIC_TENANT_BASE_DOMAIN="studynexs.com"
$env:NEXT_PUBLIC_TENANT_SLUG="demo"

npm ci
npm run cf:deploy
```

## 5) Verify public URLs

```powershell
curl.exe -I https://api.studynexs.com/health
curl.exe -I https://api.studynexs.com/ready

Set-Location d:/Projects/studynexs-platform/studynexs-dev/apps/admin-web
$env:E2E_BASE_URL="https://demo.studynexs.com"
npm run e2e-smoke:prod
```

## 6) Redeploy command sequence (copy-paste)

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
```
