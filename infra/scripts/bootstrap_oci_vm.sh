#!/usr/bin/env bash
# StudyNexs — Gate 1A OCI VM bootstrap.
#
# Creates the /opt/studynexs host layout defined in docs/DEPLOYMENT_CONVENTIONS.md,
# syncs deploy artifacts from the repo, and generates deploy/env/api.env with
# strong secrets. Idempotent: safe to re-run; NEVER overwrites an existing
# api.env (your secrets survive re-runs).
#
# Usage (on the OCI VM, as a user with sudo):
#   sudo bash bootstrap_oci_vm.sh [--repo-url https://github.com/<owner>/<repo>.git] [--branch develop]
#
# After this script, continue with the numbered next steps it prints
# (build → migrate → seed → verify), or run deploy.sh for the standard cycle.

set -euo pipefail

BASE=/opt/studynexs
REPO_URL=""
BRANCH="develop"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo-url) REPO_URL="$2"; shift 2 ;;
        --branch)   BRANCH="$2";   shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

say()  { printf '\n== %s\n' "$*"; }
note() { printf '   %s\n' "$*"; }

# ── 1. Host layout (conventions §2) ──────────────────────────────
say "Creating $BASE layout"
mkdir -p "$BASE"/{repo,runtime,backups,monitoring}
mkdir -p "$BASE"/data/{postgres,qdrant,uploads}
mkdir -p "$BASE"/backups/{postgres,manifests}
mkdir -p "$BASE"/deploy/{compose,env,nginx,scripts,ssl}

# ── 2. Repository clone / update ─────────────────────────────────
if [[ -d "$BASE/repo/.git" ]]; then
    say "Repo exists — fetching $BRANCH"
    git -C "$BASE/repo" fetch origin "$BRANCH"
    git -C "$BASE/repo" checkout "$BRANCH"
    git -C "$BASE/repo" pull --ff-only origin "$BRANCH"
elif [[ -n "$REPO_URL" ]]; then
    say "Cloning $REPO_URL ($BRANCH)"
    git clone --branch "$BRANCH" "$REPO_URL" "$BASE/repo"
else
    echo "No repo at $BASE/repo and no --repo-url given." >&2
    exit 2
fi

# ── 3. Sync repo/infra → deploy (conventions §3) ─────────────────
say "Syncing deploy artifacts from repo/infra"
cp -f  "$BASE"/repo/infra/docker/docker-compose.prod.yml "$BASE"/deploy/compose/
cp -f  "$BASE"/repo/infra/nginx/nginx.conf               "$BASE"/deploy/nginx/
cp -rf "$BASE"/repo/infra/scripts/.                      "$BASE"/deploy/scripts/ 2>/dev/null || true
chmod +x "$BASE"/deploy/scripts/*.sh 2>/dev/null || true

# ── 4. Secrets: deploy/env/api.env (conventions §5) ──────────────
API_ENV="$BASE/deploy/env/api.env"
if [[ -f "$API_ENV" ]]; then
    say "api.env already exists — leaving it untouched (secrets are never regenerated)"
else
    say "Generating $API_ENV"
    # Fernet key = urlsafe-base64 of 32 random bytes (what cryptography expects).
    FERNET_KEY=$(openssl rand -base64 32 | tr '+/' '-_')
    umask 177
    cat > "$API_ENV" <<EOF
# StudyNexs production environment — generated $(date -u +%Y-%m-%dT%H:%M:%SZ)
# chmod 600, never in git, never in backups. Rotation: conventions doc §5.2.
# KEEP AN OFFLINE COPY OF AADHAAR_ENCRYPTION_KEY — losing it makes encrypted
# Aadhaar data permanently unrecoverable. The other secrets rotate freely.

JWT_SECRET_KEY=$(openssl rand -base64 48 | tr -d '\n' | tr '+/' '-_')
WEBHOOK_SECRET=$(openssl rand -base64 32 | tr -d '\n' | tr '+/' '-_')
AADHAAR_ENCRYPTION_KEY=${FERNET_KEY}
METRICS_TOKEN=$(openssl rand -base64 32 | tr -d '\n' | tr '+/' '-_')
POSTGRES_PASSWORD=$(openssl rand -hex 24)

# ── Host paths (conventions §6) ──────────────────────────────────
STUDYNEXS_UPLOADS_DIR=/opt/studynexs/data/uploads
STUDYNEXS_METRICS_TOKEN_FILE=/opt/studynexs/deploy/env/metrics_token

# ── Nginx binding ────────────────────────────────────────────────
# Default (127.0.0.1:8080) keeps the stack private for verification.
# To serve real traffic, uncomment — and terminate TLS at the edge
# (Cloudflare proxy + origin cert in deploy/ssl/) BEFORE going public.
#STUDYNEXS_NGINX_BIND=0.0.0.0
#STUDYNEXS_NGINX_PORT=80

# ── AEI v1.0 pilot activation (authorized: Stages 1–2, 2026-08-04) ──
# Uncomment ONLY after the baseline is verified (docs/runbooks/aei-pilot-activation.md):
# /health + /ready green, one real login, smokes pass, backup taken.
#AEI_V1_MATH_NORMALIZATION_ENABLED=true
#AEI_V1_REVIEW_POLICY_ENABLED=true
#AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=true
#AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=true
#AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=true
# Stage 3/4 are NOT authorized — do not add their flags without ARM's word.
EOF
    umask 022
    chmod 600 "$API_ENV"
    note "Secrets generated. Store AADHAAR_ENCRYPTION_KEY in the password manager NOW."
fi

# Prometheus reads the metrics token from a file mount.
TOKEN_FILE="$BASE/deploy/env/metrics_token"
if [[ ! -f "$TOKEN_FILE" ]]; then
    grep '^METRICS_TOKEN=' "$API_ENV" | cut -d= -f2- | tr -d '\n' > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
fi

# ── 5. Docker presence check ─────────────────────────────────────
say "Checking Docker"
if ! command -v docker >/dev/null 2>&1; then
    note "Docker is not installed. Install it, then re-run this script:"
    note "  curl -fsSL https://get.docker.com | sh"
    note "  sudo usermod -aG docker \$USER   # then re-login"
    exit 1
fi
docker compose version >/dev/null 2>&1 || { note "docker compose plugin missing."; exit 1; }

# ── Done: print the exact next steps ─────────────────────────────
say "Bootstrap complete. Next (run each, verify, then move on):"
cat <<'STEPS'

  1. Build + start the stack (fails loudly if any secret is missing):
       cd /opt/studynexs/deploy/compose
       docker compose --env-file ../env/api.env -f docker-compose.prod.yml build api
       docker compose --env-file ../env/api.env -f docker-compose.prod.yml up -d

  2. Migrate the database (inside the image — no host Python needed):
       docker compose --env-file ../env/api.env -f docker-compose.prod.yml \
           run --rm api alembic upgrade head

  3. Seed demo data (scripts/ is not baked into the image — mount it read-only
     from the repo clone for this one-off run):
       docker compose --env-file ../env/api.env -f docker-compose.prod.yml \
           run --rm -v /opt/studynexs/repo/apps/api/scripts:/app/scripts:ro \
           api python scripts/seed_demo_ssc.py

  4. Verify locally (stack is bound to 127.0.0.1:8080 until you open it up):
       curl -fsS http://127.0.0.1:8080/health && echo OK
       curl -fsS http://127.0.0.1:8080/ready  && echo OK

  5. Take + verify a backup BEFORE exposing anything:
       docker exec studynexs-prod-postgres pg_dump -U studynexs studynexs \
           | gzip > /opt/studynexs/backups/postgres/studynexs_$(date +%Y%m%d_%H%M).sql.gz

  6. Edge: point DNS at this VM, sort TLS (Cloudflare proxy + origin cert),
     THEN set STUDYNEXS_NGINX_BIND=0.0.0.0 / PORT=80 in api.env and
     `up -d nginx`. Run the HTTPS smokes from a dev machine.

  7. AEI Stage 1–2 (already authorized): after 1–6 are green, uncomment the
     five AEI lines in /opt/studynexs/deploy/env/api.env and run:
       docker compose --env-file ../env/api.env -f docker-compose.prod.yml up -d api worker
     Then the teacher walkthrough in docs/runbooks/aei-pilot-activation.md.

  Redeploys after this: bash /opt/studynexs/deploy/scripts/deploy.sh
STEPS
