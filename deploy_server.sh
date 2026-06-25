#!/bin/bash
set -e

SERVER="root@45.119.215.120"
TARGET_DIR="/opt/uphill-ai-backend"

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
