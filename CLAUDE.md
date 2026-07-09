# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Uphill AI is an AI-powered adaptive training platform for trail and mountain runners. It uses Gemini 2.5 Flash as the LLM, grounded by a RAG knowledge base. The coach persona ("Coach Uphill") follows Scott Johnston's principles from *Training for the Uphill Athlete*.

## Architecture

### Backend (`/backend`)
FastAPI app (`main.py`) with SQLAlchemy Core against PostgreSQL. No ORM — all queries use parameterized raw SQL via `text()` helpers in `db.py`. Schema is managed by both `db.py:init_db()` (idempotent `CREATE TABLE IF NOT EXISTS`) and Alembic migrations in `alembic/versions/`.

Key modules:
- `config.py` — all env vars via `settings` singleton
- `db.py` — entire data access layer (no separate repo pattern)
- `services/` — stateless service classes: `PlanGenerator`, `RagService`, `CalendarService`, `PacingCalculator`, `gear_planner`, `nutrition_planner`, `knowledge_extractor`, `kb_distiller`, `kb_retrieval`, `kb_context`
- `parsers/` — `FitParser` (Garmin .fit files), `GpxParser` (route profiles)
- `routers/analytics.py` — analytics endpoints (the only router extracted from main.py)

Plan generation is async and job-based: `POST /api/coach/generate-plan` returns a `job_id`, and the frontend polls `GET /api/coach/plan-status/{job_id}`. Job state is in-memory (`plan_jobs` dict in main.py — not persisted across restarts).

### Knowledge-base RAG engine (Scheduler / Nutrition / Gear)
The three AI features run on a dual-engine design selected by `RAG_ENGINE` (`gemini` | `notebooklm`; whichever is primary, the other is the automatic fallback, and the Scheduler keeps its rule-based schedule as the final fallback):

- **gemini** (production): answers come from Gemini 2.5 Flash grounded on the distilled `kb_chunks` Postgres table. Gear/Nutrition inject their FULL catalog into the prompt (no retrieval-miss risk); the Scheduler retrieves top-k philosophy chunks from Qdrant (`uphill_kb_scheduler` collection, `services/kb_retrieval.py`). The Gemini engine refuses when the KB is empty — it never answers ungrounded.
- **notebooklm** (legacy): one slow (~2 min) runtime call per request to the NotebookLM notebooks.

**KB lifecycle**: sources are curated in the NotebookLM notebooks → `POST /api/kb/distill?domain=gear|nutrition|scheduler|all` (admin) sweeps them offline into `kb_chunks` via `services/kb_distiller.py` (brand whitelist `GEAR_BRANDS`, major-review-only curation, retries, atomic per-domain replace) → seeds are exported to `backend/kb_seed/<domain>.json` (committed to the repo, human-editable) → any environment imports them without re-distilling via `POST /api/kb/import` or `python scripts/load_kb.py` (also re-embeds scheduler chunks into that env's Qdrant). `GET /api/kb/distill/status` reports per-domain progress, chunk counts, and the Qdrant point count. Eval harness: `python scripts/golden_eval.py capture|compare --service <svc>`.

Treadmill `treadmill_speed`/`treadmill_incline` on workouts are TEXT range strings ("8.1-9.2" kph, "2-4" %) derived deterministically from each workout's own `target_pace` in `PlanGenerator.resolve_treadmill_settings` — never the AI's raw numbers.

Auth uses JWT sessions stored in the `sessions` table. Google and Facebook OAuth are supported alongside email/password. `mock-login` endpoint only exists in non-production.

### Frontend (`/frontend`)
Next.js 16 with App Router, exported as static HTML (`output: "export"`). State is managed via a single large `AppContext` (`src/contexts/AppContext.tsx`) — no external state library.

Views live in `src/views/`, shared components in `src/components/`. Hooks in `src/hooks/` encapsulate API calls (e.g., `useKnowledge`, `usePlanner`, `useTools`).

The API base URL can be overridden at runtime via `?api=<url>` query param (stored in localStorage as `UPHILL_API_URL_OVERRIDE`), useful for pointing at different backend instances without a rebuild.

The frontend `CLAUDE.md` points to `AGENTS.md`, which warns: **this is Next.js 16 with breaking changes — read `node_modules/next/dist/docs/` before writing App Router code.**

### Observability Stack
Docker Compose also runs Prometheus + Grafana (metrics), node-exporter, and Metabase (analytics dashboards against the same Postgres DB). The FastAPI app is auto-instrumented via `prometheus-fastapi-instrumentator`.

## Environments

### Local (dev)
Full stack runs via Docker Compose on the developer's machine:
```bash
docker compose up -d --build
# Frontend: http://localhost:8080
# Backend API + docs: http://localhost:8000/docs
# Grafana: http://localhost:3000
```

### Production
- **Frontend**: Static export deployed to GitHub Pages — repo at `https://github.com/kylianvo/uphill-ai`. Deployment is automatic on push to the main branch (GitHub Actions).
- **Backend**: Docker on SSH server `root@45.119.215.120`. Deployment is handled by `deploy_server.sh` (reads `deploy.env` for `DEPLOY_SERVER` and `DEPLOY_TARGET_DIR`). Set `ENVIRONMENT=production` in the backend `.env` on the server — this disables API docs and the mock-login endpoint. For KB-seed-only changes (hand-edited `backend/kb_seed/*.json`, no code change), use the lighter `./deploy_kb.sh [--domain gear|nutrition|scheduler|all]` instead — see the `deploy-backend` skill.

The frontend uses `NEXT_PUBLIC_API_URL` to point at the production backend. In GitHub Pages deployments, this must be set at build time since the output is static.

## Development Commands

### Backend only (local dev)
```bash
cd backend
pip install -r requirements.txt
# Set up backend/.env (see deploy.env.example for reference)
uvicorn main:app --reload --port 8000
```

Database migrations:
```bash
cd backend
alembic upgrade head
```

### Frontend only
```bash
cd frontend
npm install
npm run dev        # dev server at http://localhost:3000
npm run build      # static export to /out
npm run lint
```

### Tests
```bash
# E2E tests (requires frontend running at http://127.0.0.1:8080)
cd frontend
npm run test:e2e

# Update visual snapshots
npm run test:visual:update
```

## Environment Variables

Backend reads from `backend/.env`. Key variables:
- `GEMINI_API_KEY` — required for AI features; without it the coach runs in mock mode
- `DATABASE_URL` — PostgreSQL URL (defaults to local `uphill_ai` db)
- `JWT_SECRET` — must be overridden in production
- `ENVIRONMENT=production` — disables `/docs`, `/redoc`, `/openapi.json`, and `mock-login`
- `GOOGLE_CLIENT_ID` — for Google OAuth
- `ALLOWED_ORIGINS` — comma-separated CORS origins
- `NOTEBOOKLM_NOTEBOOK_ID`, `NOTEBOOKLM_GEAR_ID`, `NOTEBOOKLM_NUTRITION_ID`, `NOTEBOOKLM_AUTH_JSON` — the three NotebookLM notebooks (scheduler/gear/nutrition) used by the offline KB distiller and the legacy runtime engine
- `RAG_ENGINE` — `gemini` (distilled KB + Gemini, ~5-45s) or `notebooklm` (legacy runtime NotebookLM, ~2 min); the other engine remains the automatic fallback
- `QDRANT_URL` — defaults to `http://qdrant:6333` in Docker, `http://localhost:6333` otherwise

Per-user Gemini API keys are stored in the `users` table (`gemini_api_key` column) and take precedence over the server-level key for chat and plan generation (NOT yet for the gear/nutrition Gemini engines, which use the server key).

## Key Patterns

- **Dual database strategy**: The app uses PostgreSQL in production (via SQLAlchemy) and has legacy SQLite code paths. Always use the SQLAlchemy `engine`/`text()` pattern from `db.py`, not raw sqlite3.
- **Admin check**: `role == "admin"` is set when the email is `admin@uphill.ai` at OAuth login time.
- **Bilingual support**: The app supports English and Vietnamese (`lang: "en" | "vi"`). Knowledge cards and plan generation respect the `lang` parameter.
- **Qdrant**: A Qdrant vector DB container is in docker-compose. The KB RAG engine uses it via `services/kb_retrieval.py` (plain qdrant-client + `gemini-embedding-2`, collection `uphill_kb_scheduler`). `services/vector_service.py` is legacy (langchain-based, deps not in requirements.txt) kept only for the old `scripts/index_*.py`.
- **Dual schema**: every table/column change goes in BOTH `db.py:init_db()` and a hand-written Alembic migration (see the `db-migration` skill). `init_db()` also self-migrates existing dev databases via idempotent ALTERs at startup.
