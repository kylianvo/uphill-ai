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

echo "Deploying backend to $SERVER..."

# 1. Create target directory on server
ssh $SERVER "mkdir -p $TARGET_DIR/qdrant_storage"

# 2. Sync backend files
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    ./backend/ $SERVER:$TARGET_DIR/backend/

# Sync docker-compose.yml and grafana configs
rsync -avz ./docker-compose.yml $SERVER:$TARGET_DIR/ 
rsync -avz ./grafana/ $SERVER:$TARGET_DIR/grafana/

# 4. Sync .env file
rsync -avz ./backend/.env $SERVER:$TARGET_DIR/backend/

# 5. Start/update docker containers (Metabase, Postgres, etc.)
ssh $SERVER "cd $TARGET_DIR && docker compose up -d --remove-orphans"

echo "Backend deployment completed (uvicorn --reload handles restarting automatically)!"
