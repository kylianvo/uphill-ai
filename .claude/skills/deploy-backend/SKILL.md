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

## Schema changes

`init_db()` runs at app startup and self-migrates the production database
(idempotent `CREATE TABLE IF NOT EXISTS` + `ALTER` list) — no manual Alembic
step is needed on the server. The Alembic history exists for environments
that upgrade via `alembic upgrade head` instead; keep both in sync per the
`db-migration` skill.

## Knowledge base (RAG engine)

**Seed-data-only change?** If you only edited `backend/kb_seed/*.json` by
hand and no backend code changed, skip this whole script and use
`./deploy_kb.sh [--domain gear|nutrition|scheduler|all]` instead. It rsyncs
just the changed seed file(s) and reloads them via `scripts/load_kb.py` —
no full backend rsync, no preflight test suite, no container restart
(`kb_chunks` is read at request time, so there's nothing to restart). Commit
the seed file change to git first, same as any other change. Verify with
the same `kb_chunks` count query below (the script prints it automatically).

The rest of this section covers the KB reload step as part of a full
`deploy_server.sh` run, when backend code changed too.

The distilled KB ships with the rsync (`backend/kb_seed/*.json`) but must be
loaded into the server's Postgres + Qdrant after the containers are up:

```bash
ssh root@45.119.215.120 "cd /opt/uphill-ai-backend && docker compose exec -T backend python scripts/load_kb.py"
```

This is idempotent (atomic per-domain replace) and re-embeds scheduler chunks
into the server's Qdrant using the server `GEMINI_API_KEY`. Verify with:

```bash
ssh root@45.119.215.120 "cd /opt/uphill-ai-backend && docker compose exec -T db psql -U uphill -d uphill_ai -c \"SELECT domain, count(*) FROM kb_chunks GROUP BY 1;\""
```

`RAG_ENGINE=gemini` in the server `.env` selects the fast KB engine
(NotebookLM stays as automatic fallback); without it the default is the
legacy `notebooklm` engine. If the KB import is skipped while
`RAG_ENGINE=gemini`, the app still works — the Gemini engine refuses on an
empty KB and every request falls back to slow NotebookLM.

## After deploying

Report back concretely: what was synced, whether preflight tests passed, the
container status, and the kb_chunks counts — not just "deploy succeeded."
