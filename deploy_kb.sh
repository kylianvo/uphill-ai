#!/bin/bash
set -e

# Lightweight companion to deploy_server.sh for KB-seed-only changes (editing
# backend/kb_seed/*.json by hand and reloading it into prod Postgres/Qdrant).
# Skips the full backend rsync, preflight test suite, and container restart —
# none of which matter when the only thing that changed is seed data.
#
# Usage: ./deploy_kb.sh [--domain gear|nutrition|scheduler|all]
# Defaults to --domain all.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/deploy.env" ]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/deploy.env"
fi

SERVER="${DEPLOY_SERVER:-root@45.119.215.120}"
TARGET_DIR="${DEPLOY_TARGET_DIR:-/opt/uphill-ai-backend}"

DOMAIN="all"
while [ $# -gt 0 ]; do
  case "$1" in
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    *)
      echo "ERROR: unknown argument '$1'. Usage: ./deploy_kb.sh [--domain gear|nutrition|scheduler|all]" >&2
      exit 1
      ;;
  esac
done

case "$DOMAIN" in
  gear|nutrition|scheduler|all) ;;
  *)
    echo "ERROR: invalid --domain '$DOMAIN'. Must be one of: gear, nutrition, scheduler, all." >&2
    exit 1
    ;;
esac

if [ "$DOMAIN" = "all" ]; then
  SEED_FILES="./backend/kb_seed/gear.json ./backend/kb_seed/nutrition.json ./backend/kb_seed/scheduler.json"
else
  SEED_FILES="./backend/kb_seed/$DOMAIN.json"
fi

echo "Syncing KB seed file(s) for domain '$DOMAIN' to $SERVER..."
ssh "$SERVER" "mkdir -p $TARGET_DIR/backend/kb_seed"
# shellcheck disable=SC2086
rsync -avz $SEED_FILES "$SERVER:$TARGET_DIR/backend/kb_seed/"

echo "Reloading KB on $SERVER (domain: $DOMAIN)..."
ssh "$SERVER" "cd $TARGET_DIR && docker compose exec -T backend python scripts/load_kb.py --domain $DOMAIN"

echo "Verifying kb_chunks counts on $SERVER..."
ssh "$SERVER" "cd $TARGET_DIR && docker compose exec -T db psql -U uphill -d uphill_ai -c \"SELECT domain, count(*) FROM kb_chunks GROUP BY 1;\""

echo "KB deployment completed (no backend restart needed — kb_chunks is read at request time)."
