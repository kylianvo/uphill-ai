#!/bin/bash
set -e

# Load deploy configuration from deploy.env (not committed to git).
# Copy deploy.env.example → deploy.env and fill in your values.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/deploy.env" ]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/deploy.env"
fi

SERVER="${DEPLOY_SERVER:-root@45.119.215.120}"
TARGET_DIR="${DEPLOY_TARGET_DIR:-/opt/uphill-ai-backend}"

# --- Preflight: run the backend test suite locally before deploying. ---
# Uses the local docker-composed Postgres (the same `db` service local dev
# already runs), pointed at a dedicated uphill_ai_test database, so it never
# touches production data.
#
# Escape hatch: pass --skip-tests to bypass (NOT recommended -- emergencies
# only). Deliberately a flag rather than an env var, so it can't be left
# "on" accidentally in a shell profile.
SKIP_TESTS=false
for arg in "$@"; do
  if [ "$arg" = "--skip-tests" ]; then
    SKIP_TESTS=true
  fi
done

if [ "$SKIP_TESTS" = true ]; then
  echo "WARNING: --skip-tests passed. Skipping preflight test suite. Use with caution."
else
  echo "Running backend preflight test suite (unit + integration) against local Postgres..."

  if ! docker compose up -d db; then
    echo "ERROR: failed to start local Postgres for preflight tests. Aborting deploy." >&2
    exit 1
  fi

  for i in $(seq 1 15); do
    docker compose exec -T db pg_isready -U uphill -d uphill_ai >/dev/null 2>&1 && break
    sleep 2
  done

  docker compose exec -T db psql -U uphill -d uphill_ai -c "CREATE DATABASE uphill_ai_test;" >/dev/null 2>&1 || true

  export DATABASE_URL="postgresql://uphill:uphill_secret@localhost:5433/uphill_ai_test"
  export ENVIRONMENT="development"
  if ! (cd "$SCRIPT_DIR/backend" && .venv/bin/pytest tests/unit tests/integration -q); then
    echo "ERROR: backend test suite failed. Aborting deploy. Re-run with --skip-tests to force (not recommended)." >&2
    exit 1
  fi
  echo "Preflight tests passed."
fi

echo "Deploying backend to $SERVER..."

# 1. Create target directory on server
ssh $SERVER "mkdir -p $TARGET_DIR/qdrant_storage"

# 2. Sync backend files
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    ./backend/ $SERVER:$TARGET_DIR/backend/

# Sync docker-compose.yml and grafana configs
rsync -avz ./docker-compose.yml $SERVER:$TARGET_DIR/
rsync -avz ./grafana/ $SERVER:$TARGET_DIR/grafana/

# 4. Sync .env file (prefer .env.production if it exists)
if [ -f ./backend/.env.production ]; then
    rsync -avz ./backend/.env.production $SERVER:$TARGET_DIR/backend/.env
else
    rsync -avz ./backend/.env $SERVER:$TARGET_DIR/backend/
fi

# 5. Start/update docker containers (Metabase, Postgres, etc.)
ssh $SERVER "cd $TARGET_DIR && docker compose up -d --remove-orphans"

echo "Backend deployment completed (uvicorn --reload handles restarting automatically)!"
