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
The three AI features run on a single engine: Gemini 2.5 Flash grounded on the distilled `kb_chunks` Postgres table. Gear/Nutrition inject their FULL catalog into the prompt (no retrieval-miss risk); the Scheduler retrieves top-k philosophy chunks from Qdrant (`uphill_kb_scheduler` collection, `services/kb_retrieval.py`). The engine refuses when the KB is empty — it never answers ungrounded, so Gear/Nutrition return an empty result that explains itself.

The Scheduler alone has fallback tiers, since a plan must always be produced: **Gemini → one reduced-prompt Gemini retry** (drops the KB grounding block and asks for shorter descriptions, recovering the common truncated/unparseable response) **→ the rule-based schedule**. Telemetry labels the retry as `engine="gemini_retry"` so its hit rate is visible separately.

**KB lifecycle**: two source types feed `kb_chunks`, and the split between them is a safety boundary, not a detail:

- **Automated (`WEB_DOMAINS` = gear, nutrition)** — live web discovery via Tavily (gear's shoe catalog off RunRepeat/BelieveInTheRun, nutrition's product catalog off brand/retailer sites), brand-whitelisted by `GEAR_BRANDS`/`NUTRITION_BRANDS`. **Insert-only**: it appends new rows and never wipes existing ones, which is what makes it safe to run unattended. Triggered by `POST /api/kb/distill?domain=gear|nutrition|all` (admin) or the Airflow `kb_distill` DAG (`airflow/dags/kb_distill_dag.py`, weekly — currently paused for both domains).
- **Script-only (scheduler + nutrition principles)** — operator-curated doctrine swept from NotebookLM by `backend/scripts/distill_principles.py`. This path **replaces** a `(domain, kind)` wholesale, so an unattended run returning junk would overwrite a working KB. It is deliberately not an endpoint and not a DAG task: an operator runs it, reviews the seed diff, and commits. `save_domain` additionally refuses to replace principles when a sweep produced none. **This script is the only remaining NotebookLM consumer in the codebase.**

Both paths structure results through Gemini (retries, temperature 0) into the same row shape → seeds are exported to `backend/kb_seed/<domain>.json` (committed to the repo, human-editable) → any environment imports them without re-distilling via `POST /api/kb/import` or `python scripts/load_kb.py` (also re-embeds scheduler chunks into that env's Qdrant). `GET /api/kb/distill/status` reports per-domain progress, chunk counts, and the Qdrant point count. Golden-set regression harness: `python scripts/golden_eval.py capture|compare --service <svc>` (capture snapshots the current pipeline as the baseline; compare re-runs and diffs).

A separate `POST /api/kb/distill-race-results` (admin, `GET .../status`) enriches the hand-curated `race_courses` KB with newly-discovered result-year stats (winner times, finisher counts, percentiles, sourced from DUV) for races that already have a curated `results` block in their payload — it never invents results for an untracked race and never overwrites an already-curated `(year, distance_label)` entry (`kb_distiller.py`'s `discover_race_results_web`/`save_race_results`, merged in place via `db.update_kb_chunk_payload`). These stats feed the Goal Determiner's rank-transfer estimate (`services/race_estimator.py`, `race_matcher.race_benchmarks`) — only the numeric stats are auto-enriched; the qualitative race profile (location, terrain, climate, key climbs, runner reviews) stays hand-curated. A separate, optional `course_profiles` payload key holds real GPX-derived elevation checkpoints, admin-curated via the same two-step pattern (parse via `/api/parser/gpx`, then `POST /api/kb/race-courses/course-profile`, see `backend/kb_seed/RACE_COURSES_README.md`), and is consumed by the Goal Determiner's `RaceEstimator` to replace its synthetic uniform-grade course assumption when available.

Knowledge Hub cards (`knowledge_cards` table, distinct from `kb_chunks`) come from one source since the NotebookLM 8-topic sweep and its `POST /api/knowledge/trigger` endpoint were removed: `POST /api/knowledge/discover-podcast` (admin, `GET .../status`) incrementally appends cards from newly-published Evoke Endurance ("Evokecast") trail/ultrarunning podcast episodes without touching the existing library — it discovers new episode pages via Tavily, then fetches each episode page's raw HTML directly (not via Tavily, which strips the lazy-loaded video iframe) to find the embedded YouTube video, fetches its transcript (`RagService.get_youtube_transcript`), and structures it into cards with Gemini (`discover_podcast_knowledge_web`/`save_podcast_knowledge_cards`). Each episode is tracked as processed via its YouTube URL used as `source_label` (`db.get_knowledge_card_source_labels`). Cards are saved bilingual (en/vi).

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

### Staging
- **Backend**: Docker on SSH server `root@45.119.215.120` inside `/opt/uphill-ai-backend-staging` (port `8001`). Exposed via Nginx at `https://staging-api.uphill-ai.io.vn`.
- **Database / Vector**: Isolated Postgres on port `5434` and Qdrant on port `6336`.
- **Frontend testing**: Run local frontend on `http://127.0.0.1:18080` (or `http://localhost:8080`) pointing to staging either via `?api=https://staging-api.uphill-ai.io.vn` query override or via `docker-compose.override.yml`.
- **Full Guide**: See [docs/staging_deployment_and_testing.md](docs/staging_deployment_and_testing.md) for complete rsync deployment instructions, CORS setup, and gotchas.

### Production
- **Frontend**: Static export deployed to GitHub Pages — repo at `https://github.com/kylianvo/uphill-ai`. Deployment is automatic on push to the main branch (GitHub Actions).
- **Backend**: Docker on SSH server `root@45.119.215.120` inside `/opt/uphill-ai-backend` (port `8000`). Deployment is handled by `deploy_server.sh` (reads `deploy.env` for `DEPLOY_SERVER` and `DEPLOY_TARGET_DIR`). Set `ENVIRONMENT=production` in the backend `.env` on the server — this disables API docs and the mock-login endpoint. For KB-seed-only changes (hand-edited `backend/kb_seed/*.json`, no code change), use the lighter `./deploy_kb.sh [--domain gear|nutrition|scheduler|all]` instead — see the `deploy-backend` skill.

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
- `NOTEBOOKLM_NOTEBOOK_ID`, `NOTEBOOKLM_NUTRITION_ID`, `NOTEBOOKLM_AUTH_JSON` — read **only** by `backend/scripts/distill_principles.py`. No request path touches them; leave them unset in normal deployments and set them only when running that script
- `TAVILY_API_KEY` — search API key for gear's and nutrition's web-discovery KB distillation (`services/kb_distiller.py`'s `discover_gear_web`/`discover_nutrition_web`); without it `sweep_domain` raises
- `QDRANT_URL` — defaults to `http://qdrant:6333` in Docker, `http://localhost:6333` otherwise

Per-user Gemini API keys are stored in the `users` table (`gemini_api_key` column) and take precedence over the server-level key for chat and plan generation (NOT yet for the gear/nutrition Gemini engines, which use the server key).

## Key Patterns

- **Dual database strategy**: The app uses PostgreSQL in production (via SQLAlchemy) and has legacy SQLite code paths. Always use the SQLAlchemy `engine`/`text()` pattern from `db.py`, not raw sqlite3.
- **Admin check**: `role == "admin"` is set when the email is `admin@uphill.ai` at OAuth login time.
- **Bilingual support**: The app supports English and Vietnamese (`lang: "en" | "vi"`). Knowledge cards and plan generation respect the `lang` parameter.
- **Qdrant**: A Qdrant vector DB container is in docker-compose. The KB RAG engine uses it via `services/kb_retrieval.py` (plain qdrant-client + `gemini-embedding-2`, collection `uphill_kb_scheduler`). `services/vector_service.py` is legacy (langchain-based, deps not in requirements.txt) kept only for the old `scripts/index_*.py`.
- **Dual schema**: every table/column change goes in BOTH `db.py:init_db()` and a hand-written Alembic migration (see the `db-migration` skill). `init_db()` also self-migrates existing dev databases via idempotent ALTERs at startup.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `kylianvo/uphill-ai`, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), unchanged. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` + `docs/adr/` at the repo root (created lazily, not yet present). See `docs/agents/domain.md`.
