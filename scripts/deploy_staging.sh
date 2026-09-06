#!/usr/bin/env bash
set -euo pipefail

SERVER="root@45.119.215.120"
SSH_OPTS=(-o IPQoS=none -o ConnectTimeout=15)

echo "=== 1. Checking remote reachability ==="
if ! ssh "${SSH_OPTS[@]}" "$SERVER" "echo 'Connected to $SERVER successfully'"; then
  echo "ERROR: Unable to connect to $SERVER. If port 22 hangs, fail2ban may have blocked your current IP." >&2
  echo "Tip: Toggle a VPN or phone hotspot to switch your public IP, then retry." >&2
  exit 1
fi

echo "=== 2. Configuring Nginx for staging-api.uphill-ai.io.vn ==="
ssh "${SSH_OPTS[@]}" "$SERVER" 'bash -s' <<'EOF'
set -euo pipefail

CONF="/etc/nginx/sites-available/staging-api.uphill-ai.conf"
if [ ! -f "$CONF" ]; then
  cat > "$CONF" <<'NGINX'
server {
    listen 80;
    server_name staging-api.uphill-ai.io.vn;

    location /metrics { deny all; return 403; }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
fi

ln -sf "$CONF" /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
EOF

echo "=== 3. Obtaining SSL Certificate via Certbot ==="
ssh "${SSH_OPTS[@]}" "$SERVER" 'bash -s' <<'EOF'
set -euo pipefail
if ! certbot certificates | grep -q "staging-api.uphill-ai.io.vn"; then
  certbot --nginx -d staging-api.uphill-ai.io.vn --non-interactive --agree-tos --keep-until-expiring -m vvviet123@gmail.com
  nginx -t
  systemctl reload nginx
else
  echo "Certificate already exists for staging-api.uphill-ai.io.vn"
fi
EOF

echo "=== 4. Running Alembic migrations on staging ==="
ssh "${SSH_OPTS[@]}" "$SERVER" 'bash -s' <<'EOF'
set -euo pipefail

# Stamp directly to head (init_db() already self-migrated all tables and columns including activities and match state)
docker exec uphill-ai-backend-staging-backend-1 alembic stamp head

# Verify alembic current revision is head
docker exec uphill-ai-backend-staging-backend-1 alembic current

# Verify activities table exists
COUNT=$(docker exec uphill-ai-backend-staging-db-1 psql -U uphill -d uphill_ai -Atc "SELECT count(*) FROM activities;")
echo "Activities row count on staging DB: $COUNT"
EOF

echo "=== 5. Verifying external health check ==="
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}\n" https://staging-api.uphill-ai.io.vn/api/health || true)
echo "HTTP response code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Staging environment is LIVE and healthy at https://staging-api.uphill-ai.io.vn"
  echo "You can test the frontend by opening:"
  echo "  http://127.0.0.1:18080/?api=https://staging-api.uphill-ai.io.vn"
else
  echo "⚠️ Health check returned $HTTP_CODE. Check logs on the server: docker logs uphill-ai-backend-staging-backend-1 --tail 50"
fi
