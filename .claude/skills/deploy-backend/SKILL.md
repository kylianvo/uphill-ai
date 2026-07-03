---
name: deploy-backend
description: Deploy the backend to the production SSH server via deploy_server.sh. User-invoked only — this pushes to a real production server (root@45.119.215.120) and restarts live containers.
disable-model-invocation: true
---

# Deploy backend to production

Wraps `./deploy_server.sh`, which rsyncs `backend/`, `docker-compose.yml`, and
`grafana/` to the production server and restarts its containers. This is a
real, hard-to-reverse action against a live server — never run it without the
user explicitly asking to deploy right now.

## Preflight checklist (before running the script)

1. **Working tree state**: run `git status`. If there are uncommitted changes
   the user cares about, flag it — `deploy_server.sh` deploys whatever is on
   disk, not what's committed, so uncommitted local changes silently ship too.
2. **`backend/.env.production` exists and is correct**, since the script
   prefers it over `backend/.env` when syncing:
   - `ENVIRONMENT=production` must be set (disables `/docs`, `/redoc`,
     `/openapi.json`, and the `mock-login` endpoint).
   - `JWT_SECRET` must be a real production secret, not the dev default.
   - If `backend/.env.production` doesn't exist, the script falls back to
     `backend/.env` — confirm that's actually intended before proceeding.
3. **`deploy.env` exists** (copied from `deploy.env.example`) with
   `DEPLOY_SERVER` / `DEPLOY_TARGET_DIR` set, or confirm the script's
   defaults (`root@45.119.215.120`, `/opt/uphill-ai-backend`) are correct.

## Running the deploy

```bash
./deploy_server.sh
```

This automatically runs the backend preflight test suite (unit + integration)
against a local throwaway Postgres database before touching the server, and
aborts the deploy if tests fail. Do not pass `--skip-tests` unless the user
explicitly says this is an emergency — it bypasses that safety net.

After it completes, verify the deploy actually landed:
```bash
ssh root@45.119.215.120 "docker compose -f /opt/uphill-ai-backend/docker-compose.yml ps"
ssh root@45.119.215.120 "curl -sf http://localhost:8000/api/health" || echo "health check failed"
```
(`/api/health` is defined in `backend/main.py`; hit it via SSH against the
server's local port since the public production hostname/proxy isn't fixed
here — confirm with the user if there's an external URL to check too.)

## After deploying

Report back concretely: what was synced, whether preflight tests passed, and
the container status — not just "deploy succeeded."
