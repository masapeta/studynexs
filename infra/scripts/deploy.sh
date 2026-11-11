#!/usr/bin/env bash
# StudyNexs — standard redeploy cycle for the OCI VM (after bootstrap).
#
#   pull → sync deploy artifacts → build → migrate → restart → verify → record
#
# Follows docs/DEPLOYMENT_CONVENTIONS.md §8: migrations run before traffic
# switches, smoke verification after, image tag recorded in runtime/current.json.
#
# Usage (on the VM):
#   bash /opt/studynexs/deploy/scripts/deploy.sh [--branch develop] [--skip-pull] \
#        [--include-prod-override]
#
# --include-prod-override acknowledges that deploy/compose/docker-compose.prod.override.yml
# is in use. It does not replace reviewing that file. Without the flag an existing override
# is a hard error, so a host-only file is never applied (or silently dropped) by accident.

set -euo pipefail

# STUDYNEXS_BASE exists for the contract tests; on the VM it is always /opt/studynexs.
BASE="${STUDYNEXS_BASE:-/opt/studynexs}"
COMPOSE_DIR="$BASE/deploy/compose"
ENV_FILE="$BASE/deploy/env/api.env"
BRANCH="develop"
SKIP_PULL=0
INCLUDE_OVERRIDE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)                [[ $# -ge 2 ]] || { echo "--branch needs a value" >&2; exit 2; }
                                 BRANCH="$2"; shift 2 ;;
        --skip-pull)             SKIP_PULL=1; shift ;;
        --include-prod-override) INCLUDE_OVERRIDE=1; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

say() { printf '\n== %s\n' "$*"; }

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE — run bootstrap_oci_vm.sh first." >&2; exit 1; }

# Compose only checks presence; the app would accept development/internal (engineering surfaces).
TIER=$(grep -E '^DEPLOYMENT_TIER=' "$ENV_FILE" | cut -d= -f2- || true)
case "$TIER" in
    staging|demo|production) say "Deploying with DEPLOYMENT_TIER=$TIER" ;;
    *) echo "$ENV_FILE must contain exactly one DEPLOYMENT_TIER=staging|demo|production (found: '${TIER//$'\n'/, }')." >&2; exit 1 ;;
esac

# One Compose file set for every compose call below; fixed here, before anything runs.
BASE_COMPOSE="$COMPOSE_DIR/docker-compose.prod.yml"
OVERRIDE="$COMPOSE_DIR/docker-compose.prod.override.yml"
COMPOSE_FILE_LIST=("$BASE_COMPOSE")
OVERRIDE_SHA256=""
if [[ "$INCLUDE_OVERRIDE" -eq 1 ]]; then
    [[ -f "$OVERRIDE" ]] || {
        echo "--include-prod-override given but $OVERRIDE does not exist." >&2; exit 1; }
    COMPOSE_FILE_LIST+=("$OVERRIDE")
    OVERRIDE_SHA256=$(sha256sum "$OVERRIDE" | cut -d' ' -f1)
    say "Including override $OVERRIDE (sha256 $OVERRIDE_SHA256)"
elif [[ -e "$OVERRIDE" ]]; then
    echo "$OVERRIDE exists but --include-prod-override was not given." >&2
    echo "Review it, then re-run with --include-prod-override, or retire it." >&2
    exit 1
else
    say "No override; using $BASE_COMPOSE only"
fi
COMPOSE_FILES=()
for f in "${COMPOSE_FILE_LIST[@]}"; do COMPOSE_FILES+=(-f "$f"); done

compose() {
    docker compose --env-file "$ENV_FILE" "${COMPOSE_FILES[@]}" "$@"
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
# Bash reads this script while running it; rewriting it in place would corrupt the run.
# Copy to a temp file, then rename: the running process keeps the old inode.
for src in "$BASE"/repo/infra/scripts/*; do
    [[ -f "$src" ]] || continue
    dst="$BASE/deploy/scripts/$(basename "$src")"
    tmp=$(mktemp "$dst.XXXXXX")
    if ! { cp "$src" "$tmp" && chmod 0755 "$tmp" && mv -f "$tmp" "$dst"; }; then
        rm -f "$tmp"
        echo "FAIL: could not install $dst" >&2
        exit 1
    fi
done

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
# File paths and a hash only; never the override's contents.
COMPOSE_JSON=$(printf '"%s",' "${COMPOSE_FILE_LIST[@]}")
cat > "$BASE/runtime/current.json" <<EOF
{
  "image_tag": "$GIT_SHA",
  "git_sha": "$(git -C "$BASE/repo" rev-parse HEAD)",
  "branch": "$BRANCH",
  "compose_files": [${COMPOSE_JSON%,}],
  "override_included": $([[ "$INCLUDE_OVERRIDE" -eq 1 ]] && echo true || echo false),
  "override_sha256": $([[ -n "$OVERRIDE_SHA256" ]] && echo "\"$OVERRIDE_SHA256\"" || echo null),
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
say "Deployed $GIT_SHA. Recorded in runtime/current.json."
echo "   Next: run smoke tests against the public URL when the edge is live."
