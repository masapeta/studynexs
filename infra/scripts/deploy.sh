#!/usr/bin/env bash
# StudyNexs — standard redeploy cycle for the OCI VM (after bootstrap).
#
#   pull → sync deploy artifacts → build → migrate → restart → verify → record
#
# Follows docs/DEPLOYMENT_CONVENTIONS.md §8: migrations run before traffic
# switches, smoke verification after, image tag recorded in runtime/current.json.
#
# Usage (on the VM):
#   bash /opt/studynexs/deploy/scripts/deploy.sh [--branch develop] [--skip-pull]

set -euo pipefail

BASE=/opt/studynexs
COMPOSE_DIR="$BASE/deploy/compose"
ENV_FILE="$BASE/deploy/env/api.env"
BRANCH="develop"
SKIP_PULL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)    BRANCH="$2"; shift 2 ;;
        --skip-pull) SKIP_PULL=1; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

say() { printf '\n== %s\n' "$*"; }

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE — run bootstrap_oci_vm.sh first." >&2; exit 1; }

compose() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_DIR/docker-compose.prod.yml" "$@"
}

# ── 1. Pull the release ──────────────────────────────────────────
if [[ "$SKIP_PULL" -eq 0 ]]; then
    say "Pulling $BRANCH"
    git -C "$BASE/repo" fetch origin "$BRANCH"
    git -C "$BASE/repo" checkout "$BRANCH"
    git -C "$BASE/repo" pull --ff-only origin "$BRANCH"
fi
GIT_SHA=$(git -C "$BASE/repo" rev-parse --short HEAD)

# ── 2. Sync deploy artifacts (Git is canonical; the VM never is) ─
say "Syncing deploy artifacts (sha $GIT_SHA)"
cp -f  "$BASE"/repo/infra/docker/docker-compose.prod.yml "$COMPOSE_DIR"/
cp -f  "$BASE"/repo/infra/nginx/nginx.conf               "$BASE"/deploy/nginx/
cp -rf "$BASE"/repo/infra/scripts/.                      "$BASE"/deploy/scripts/ 2>/dev/null || true

# ── 3. Build the API image ───────────────────────────────────────
say "Building studynexs-api ($GIT_SHA)"
STUDYNEXS_IMAGE_TAG="$GIT_SHA" compose build api

# ── 4. Migrate BEFORE switching traffic (conventions §8.3) ───────
say "Running migrations"
STUDYNEXS_IMAGE_TAG="$GIT_SHA" compose run --rm api alembic upgrade head

# ── 5. Restart onto the new image ────────────────────────────────
say "Restarting services"
STUDYNEXS_IMAGE_TAG="$GIT_SHA" compose up -d

# ── 6. Verify ────────────────────────────────────────────────────
say "Verifying health"
BIND_HOST=$(grep -E '^STUDYNEXS_NGINX_BIND=' "$ENV_FILE" | cut -d= -f2- || true)
BIND_PORT=$(grep -E '^STUDYNEXS_NGINX_PORT=' "$ENV_FILE" | cut -d= -f2- || true)
BASE_URL="http://${BIND_HOST:-127.0.0.1}:${BIND_PORT:-8080}"
for _ in $(seq 1 30); do
    if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then break; fi
    sleep 2
done
curl -fsS "$BASE_URL/health" >/dev/null || { echo "FAIL: /health not responding at $BASE_URL" >&2; exit 1; }
curl -fsS "$BASE_URL/ready"  >/dev/null || { echo "FAIL: /ready failed — check DB/Redis" >&2; exit 1; }
echo "   /health and /ready OK at $BASE_URL"

# ── 7. Record what this host runs (conventions §8.8) ─────────────
cat > "$BASE/runtime/current.json" <<EOF
{
  "image_tag": "$GIT_SHA",
  "git_sha": "$(git -C "$BASE/repo" rev-parse HEAD)",
  "branch": "$BRANCH",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
say "Deployed $GIT_SHA. Recorded in runtime/current.json."
echo "   Next: run smoke tests against the public URL when the edge is live."
