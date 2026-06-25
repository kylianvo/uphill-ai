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

# 3. Dump local Qdrant data (from qdrant_storage) and sync to server
# Assuming local qdrant stores data in ./backend/qdrant_storage
if [ -d "./backend/qdrant_storage" ]; then
    echo "Syncing Qdrant storage..."
    rsync -avz ./backend/qdrant_storage/ $SERVER:$TARGET_DIR/backend/qdrant_storage/
else
    echo "Local Qdrant storage not found! Skipping..."
fi

# Sync docker-compose.yml 
rsync -avz ./docker-compose.yml $SERVER:$TARGET_DIR/ 

# 4. Sync .env file
rsync -avz ./backend/.env $SERVER:$TARGET_DIR/backend/

# 5. Build and restart Docker containers on server
ssh $SERVER "cd $TARGET_DIR && docker compose down && docker compose build && docker compose up -d"

echo "Backend deployment completed!"
