#!/usr/bin/env bash
set -euo pipefail

SERVER="root@45.119.215.120"
SSH_OPTS=(-o IPQoS=none -o ConnectTimeout=15)
WORKTREE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== 1. Checking remote reachability to staging ($SERVER) ==="
if ! ssh "${SSH_OPTS[@]}" "$SERVER" "echo 'Connected successfully to staging host'"; then
  echo "ERROR: Unable to connect to $SERVER over SSH. Please check your network/VPN." >&2
  exit 1
fi

echo "=== 2. Syncing backend code from worktree to staging ==="
rsync -avz \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env' \
  "${WORKTREE_DIR}/backend/" "${SERVER}:/opt/uphill-ai-backend-staging/backend/"

echo "=== 3. Ensuring Staging .env (ALLOWED_ORIGINS & ENVIRONMENT) ==="
ssh "${SSH_OPTS[@]}" "$SERVER" 'bash -s' <<'EOF'
set -euo pipefail
ENV_FILE="/opt/uphill-ai-backend-staging/backend/.env"
if grep -q "ALLOWED_ORIGINS" "$ENV_FILE"; then
  if ! grep -q "http://localhost:3000" "$ENV_FILE"; then
    sed -i 's|^ALLOWED_ORIGINS=.*|&,http://localhost:3000,http://127.0.0.1:3000|' "$ENV_FILE"
    echo "Added http://localhost:3000 to ALLOWED_ORIGINS."
  fi
else
  echo "ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:18080,http://127.0.0.1:18080" >> "$ENV_FILE"
fi

if grep -q "^ENVIRONMENT=production" "$ENV_FILE"; then
  sed -i 's|^ENVIRONMENT=production|ENVIRONMENT=staging|' "$ENV_FILE"
  echo "Set ENVIRONMENT to staging."
fi
EOF

echo "=== 4. Resetting leftover chat tables in staging DB ==="
ssh "${SSH_OPTS[@]}" "$SERVER" 'bash -s' <<'EOF'
set -euo pipefail
docker exec uphill-ai-backend-staging-db-1 psql -U uphill -d uphill_ai -c "
  DROP TABLE IF EXISTS chat_llm_calls CASCADE;
  DROP TABLE IF EXISTS chat_daily_usage CASCADE;
  DROP TABLE IF EXISTS chat_turns CASCADE;
  DROP TABLE IF EXISTS chat_messages CASCADE;
  DROP TABLE IF EXISTS chat_threads CASCADE;
" || true
EOF

echo "=== 5. Guaranteeing memory headroom & updating backend image ==="
ssh "${SSH_OPTS[@]}" "$SERVER" 'bash -s' <<'EOF'
set -euo pipefail

# Ensure Metabase is unpaused
docker unpause $(docker ps -aq --filter name=metabase) 2>/dev/null || true

# Check if langgraph is already installed in image
if docker run --rm uphill-backend:latest python3 -c "import langgraph" 2>/dev/null; then
  echo "Coach chat packages already present in uphill-backend:latest. Skipping install."
else
  # Add 2GB swapfile if not already added to guarantee no OOM kill
  if [ ! -f /swapfile2 ]; then
    echo "Creating 2GB auxiliary swapfile to guarantee memory headroom..."
    fallocate -l 2G /swapfile2 || dd if=/dev/zero of=/swapfile2 bs=1M count=2048
    chmod 600 /swapfile2
    mkswap /swapfile2
    swapon /swapfile2
  fi

  # Spin up temporary stable container running sleep (no crashing uvicorn)
  echo "Spinning up stable worker container..."
  docker rm -f temp_chat_builder 2>/dev/null || true
  docker run -d --name temp_chat_builder uphill-backend:latest sleep 3600

  # Install the 4 Coach Chat packages inside the stable worker
  echo "Installing coach chat packages into worker..."
  docker exec temp_chat_builder pip install --no-cache-dir \
    langgraph==1.2.11 \
    langchain-core==1.6.3 \
    langchain-google-genai==4.4.0 \
    openinference-instrumentation-langchain==0.1.76

  # Commit installed packages directly to uphill-backend:latest image
  echo "Committing packages to uphill-backend:latest..."
  docker commit temp_chat_builder uphill-backend:latest
  docker rm -f temp_chat_builder
fi

# Ensure latest synced backend code is copied directly into container /app
echo "Syncing code directly into container /app..."
docker cp /opt/uphill-ai-backend-staging/backend/. uphill-ai-backend-staging-backend-1:/app/
docker commit uphill-ai-backend-staging-backend-1 uphill-backend:latest

# Restart the staging backend container to run the updated code
echo "Restarting backend container..."
cd /opt/uphill-ai-backend-staging
docker compose restart backend
sleep 6
EOF

echo "=== 7. Running Alembic database migrations ==="
ssh "${SSH_OPTS[@]}" "$SERVER" 'bash -s' <<'EOF'
set -euo pipefail
docker exec uphill-ai-backend-staging-backend-1 alembic upgrade head
echo "Alembic current revision:"
docker exec uphill-ai-backend-staging-backend-1 alembic current
EOF

echo "=== 8. Verifying staging API health ==="
sleep 4
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}\n" https://staging-api.uphill-ai.io.vn/api/health || true)
echo "HTTP response code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo ""
  echo "================================================================="
  echo "✅ Staging backend is LIVE and ready at https://staging-api.uphill-ai.io.vn"
  echo "================================================================="
  echo ""
  echo "To test the UI interactively:"
  echo "1. Run the local frontend dev server:"
  echo "     cd ${WORKTREE_DIR}/frontend && npm run dev"
  echo ""
  echo "2. Open this URL in your browser:"
  echo "     http://localhost:3000/?api=https://staging-api.uphill-ai.io.vn"
  echo ""
  echo "3. Go to the 'AI Coach' tab to start testing!"
  echo "================================================================="
else
  echo "⚠️ Staging health check returned $HTTP_CODE. Checking container logs:"
  ssh "${SSH_OPTS[@]}" "$SERVER" "docker logs uphill-ai-backend-staging-backend-1 --tail 30"
fi
