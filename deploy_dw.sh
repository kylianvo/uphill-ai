#!/bin/bash
set -e

# Lean prod deploy for the Data Warehouse / Analytics layer (Postgres -> DuckDB
# -> dbt -> Metabase). Prod's box is 1 CPU / ~2GB RAM and already runs close to
# its memory limit -- it cannot carry docker-compose.yml's Airflow (webserver +
# scheduler), Kafka, or Spark services, which are dev/future-work only. Instead
# this ships just the warehouse/ dbt project (dbt installed into its own venv,
# not the backend image -- see step 2 below) and runs the pipeline via cron:
# `docker compose exec -T backend python scripts/run_dw_elt.py`, mirroring
# airflow/dags/dw_elt_dag.py's task sequence without an always-on orchestrator.
# Metabase is already deployed on prod and already mounts ./warehouse:/warehouse:ro
# with the DuckDB driver installed, so it picks up the refreshed
# uphill_dw.duckdb file automatically -- no Metabase changes needed here.
#
# Usage: ./deploy_dw.sh [--skip-cron]
#   --skip-cron: sync files and install deps, but don't (re)install the cron entry.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/deploy.env" ]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/deploy.env"
fi

SERVER="${DEPLOY_SERVER:-root@45.119.215.120}"
TARGET_DIR="${DEPLOY_TARGET_DIR:-/opt/uphill-ai-backend}"
BACKEND_CONTAINER="uphill-ai-backend-backend-1"
CRON_SCHEDULE="17 2 * * *"
CRON_MARKER="# uphill-ai dw_elt (deploy_dw.sh)"

INSTALL_CRON=true
for arg in "$@"; do
  if [ "$arg" = "--skip-cron" ]; then
    INSTALL_CRON=false
  fi
done

echo "Syncing warehouse/ project to $SERVER..."
ssh "$SERVER" "mkdir -p $TARGET_DIR/warehouse"
# .venv is the isolated dbt venv step 2 below creates ON THE SERVER (never on
# a dev machine -- but excluded defensively too, since it's bind-mounted into
# containers at the same /warehouse path and a local `python -m venv` run
# against that mount would otherwise land gigabytes of platform-specific
# binaries on the host and get swept up here).
rsync -avz --exclude 'target' --exclude 'dbt_packages' --exclude 'logs' --exclude '*.duckdb' --exclude '.venv' \
    ./warehouse/ "$SERVER:$TARGET_DIR/warehouse/"

# Sync updated docker-compose.yml (backend now mounts ./warehouse and carries
# DUCKDB_PATH/DBT_PROJECT_DIR/DBT_PROFILES_DIR) and the cron-driven runner script.
rsync -avz ./docker-compose.yml "$SERVER:$TARGET_DIR/"
ssh "$SERVER" "mkdir -p $TARGET_DIR/backend/scripts"
rsync -avz ./backend/scripts/run_dw_elt.py "$SERVER:$TARGET_DIR/backend/scripts/run_dw_elt.py"

# 1. Recreate the backend container so it picks up the new ./warehouse mount
#    and the DUCKDB_PATH/DBT_PROJECT_DIR/DBT_PROFILES_DIR env vars. This does
#    NOT rebuild the image (Docker Hub is unreachable from prod -- see the
#    prod-server-constraints notes); it only re-applies docker-compose.yml's
#    volumes/environment to the already-built uphill-backend:latest image.
echo "Recreating backend container with the new warehouse/ mount..."
ssh "$SERVER" "cd $TARGET_DIR && docker compose up -d --no-build --no-deps db backend grafana"

# 2. dbt-core hard-requires protobuf>=6.0, which conflicts with (deprecated
#    but still in use) google-generativeai's protobuf<6.0 pin -- installing
#    dbt-duckdb into the container's global site-packages (the usual
#    pip-install-then-commit workaround for this server's unreachable Docker
#    Hub, see prod-server-constraints memory) would silently bump protobuf
#    for the whole app and risk breaking every Gemini call. Instead, install
#    dbt into an isolated venv under the bind-mounted ./warehouse -- it lives
#    on the host, so it survives container recreation without a `docker
#    commit`, and never touches the app's own dependency tree.
echo "Ensuring the isolated dbt venv exists in ./warehouse/.venv..."
ssh "$SERVER" "docker exec $BACKEND_CONTAINER test -x /warehouse/.venv/bin/dbt || docker exec $BACKEND_CONTAINER python -m venv /warehouse/.venv"
ssh "$SERVER" "docker exec $BACKEND_CONTAINER /warehouse/.venv/bin/pip show dbt-duckdb >/dev/null 2>&1 || docker exec $BACKEND_CONTAINER /warehouse/.venv/bin/pip install --no-cache-dir dbt-duckdb==1.9.4"

# 3. Bootstrap / refresh run, synchronous, so failures surface here instead of
#    silently in tonight's cron log.
echo "Running an initial dw_elt pass (extract + dbt snapshot/run/test)..."
ssh "$SERVER" "cd $TARGET_DIR && docker compose exec -T backend python scripts/run_dw_elt.py"

# 4. Install the cron entry (idempotent -- replaces any prior line with the
#    same marker instead of appending a duplicate on repeat deploys).
if [ "$INSTALL_CRON" = true ]; then
  echo "Installing/updating cron entry on $SERVER..."
  ssh "$SERVER" "(crontab -l 2>/dev/null | grep -v '$CRON_MARKER'; echo \"$CRON_SCHEDULE cd $TARGET_DIR && docker compose exec -T backend python scripts/run_dw_elt.py >> /var/log/uphill-dw-elt.log 2>&1 $CRON_MARKER\") | crontab -"
  ssh "$SERVER" "crontab -l | grep dw_elt"
else
  echo "Skipping cron install (--skip-cron passed)."
fi

echo "DW deployment completed. Metabase (already running) reads $TARGET_DIR/warehouse/uphill_dw.duckdb via its existing read-only mount -- no Metabase restart needed."
