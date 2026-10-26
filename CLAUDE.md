# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Uphill AI is an AI-powered adaptive training platform for trail and mountain runners. It uses Gemini 3.8 Flash as the LLM, grounded by a RAG knowledge base. The coach persona ("Coach Uphill") follows Scott Johnston's principles from *Training for the Uphill Athlete*.

## Architecture

### Backend (`/backend`)
FastAPI app (`main.py`) with SQLAlchemy Core against PostgreSQL. No ORM — all queries use parameterized raw SQL via `text()` helpers in `db.py`. Schema is managed by both `db.py:init_db()` (idempotent `CREATE TABLE IF NOT EXISTS`) and Alembic migrations in `alembic/versions/`.

Key modules:
- `config.py` — all env vars via `settings` singleton
- `db.py` — entire data access layer (no separate repo pattern)
- `services/` — stateless service classes: `PlanGenerator`, `RagService`, `CalendarService`, `PacingCalculator`, `gear_planner`, `nutrition_planner`, `knowledge_extractor`, `kb_distiller`, `kb_retrieval`, `kb_context`
- `parsers/` — `FitParser` (Garmin .fit files), `GpxParser` (route profiles)
- `routers/` — `analytics.py`, `coach_chat.py`, `integrations.py` (the remaining routes still live in `main.py`)

Plan generation is async and job-based: `POST /api/coach/generate-plan` returns a `job_id`, and the frontend polls `GET /api/coach/plan-status/{job_id}`. Job state is in-memory (`plan_jobs` dict in main.py — not persisted across restarts).

### Knowledge-base RAG engine (Scheduler / Nutrition / Gear)
The three AI features run on a single engine: Gemini 3.8 Flash grounded on the distilled `kb_chunks` Postgres table. Gear/Nutrition inject their FULL catalog into the prompt (no retrieval-miss risk); the Scheduler retrieves top-k philosophy chunks from Qdrant (`uphill_kb_scheduler` collection, `services/kb_retrieval.py`), with a query built from tier, phase and adapt-week context and an audience filter that keeps chunks the tier's rules forbid out of the prompt (`services/scheduler_grounding.py`). The engine refuses when the KB is empty — it never answers ungrounded, so Gear/Nutrition return an empty result that explains itself.

The Scheduler alone has fallback tiers, since a plan must always be produced: **Gemini → one reduced-prompt Gemini retry** (drops the KB grounding block and asks for shorter descriptions, recovering the common truncated/unparseable response) **→ the rule-based schedule**. Telemetry labels the retry as `engine="gemini_retry"` so its hit rate is visible separately.

**KB lifecycle**: two source types feed `kb_chunks`, and the split between them is a safety boundary, not a detail:

- **Automated (`WEB_DOMAINS` = gear, nutrition)** — live web discovery via Tavily (gear's shoe catalog off RunRepeat/BelieveInTheRun, nutrition's product catalog off brand/retailer sites), brand-whitelisted by `GEAR_BRANDS`/`NUTRITION_BRANDS`. **Insert-only**: it appends new rows and never wipes existing ones, which is what makes it safe to run unattended. Triggered by `POST /api/kb/distill?domain=gear|nutrition|all` (admin) or the Airflow `kb_distill` DAG (`airflow/dags/kb_distill_dag.py`, weekly — currently paused for both domains).
- **Script-only (scheduler + nutrition principles)** — operator-curated doctrine swept from NotebookLM by `backend/scripts/distill_principles.py`. This path **replaces** a `(domain, kind)` wholesale, so an unattended run returning junk would overwrite a working KB. It is deliberately not an endpoint and not a DAG task: an operator runs it, reviews the seed diff, and commits. `save_domain` additionally refuses to replace principles when a sweep produced none. **This script is the only remaining NotebookLM consumer in the codebase.**

Both paths structure results through Gemini (retries, temperature 0) into the same row shape → seeds are exported to `backend/kb_seed/<domain>.json` (committed to the repo, human-editable) → any environment imports them without re-distilling via `POST /api/kb/import` or `python scripts/load_kb.py` (also re-embeds scheduler chunks into that env's Qdrant). `GET /api/kb/distill/status` reports per-domain progress, chunk counts, and the Qdrant point count. Golden-set regression harness: `python scripts/golden_eval.py capture|compare --service <svc>` (capture snapshots the current pipeline as the baseline; compare re-runs and diffs).

A separate `POST /api/kb/distill-race-results` (admin, `GET .../status`) enriches the hand-curated `race_courses` KB with newly-discovered result-year stats (winner times, finisher counts, percentiles, sourced from DUV) for races that already have a curated `results` block in their payload — it never invents results for an untracked race and never overwrites an already-curated `(year, distance_label)` entry (`kb_distiller.py`'s `discover_race_results_web`/`save_race_results`, merged in place via `db.update_kb_chunk_payload`). These stats feed the Goal Determiner's rank-transfer estimate (`services/race_estimator.py`, `race_matcher.race_benchmarks`) — only the numeric stats are auto-enriched; the qualitative race profile (location, terrain, climate, key climbs, runner reviews) stays hand-curated. A separate, optional `course_profiles` payload key holds real GPX-derived elevation checkpoints, admin-curated via the same two-step pattern (parse via `/api/parser/gpx`, then `POST /api/kb/race-courses/course-profile`, see `backend/kb_seed/RACE_COURSES_README.md`), and is consumed by the Goal Determiner's `RaceEstimator` to replace its synthetic uniform-grade course assumption when available.

Knowledge Hub cards (`knowledge_cards` table, distinct from `kb_chunks`) come from one source since the NotebookLM 8-topic sweep and its `POST /api/knowledge/trigger` endpoint were removed: `POST /api/knowledge/discover-podcast` (admin, `GET .../status`) incrementally appends cards from newly-published Evoke Endurance ("Evokecast") trail/ultrarunning podcast episodes without touching the existing library — it discovers new episode pages via Tavily, then fetches each episode page's raw HTML directly (not via Tavily, which strips the lazy-loaded video iframe) to find the embedded YouTube video, fetches its transcript (`RagService.get_youtube_transcript`), and structures it into cards with Gemini (`discover_podcast_knowledge_web`/`save_podcast_knowledge_cards`). Each episode is tracked as processed via its YouTube URL used as `source_label` (`db.get_knowledge_card_source_labels`). Cards are saved bilingual (en/vi).

**Race history** (`services/race_history.py`, spec in `docs/superpowers/specs/2026-09-17-race-history-design.md`): users claim their UTMB (trail) and bestmarathon.vn/VBM (road) profiles or add results by hand; results land in `race_results` and feed the plan prompt (a `RACE HISTORY` block beside the historical ceiling, plus a tier hint from imported finishes only), next block, adapt week, Coach Uphill chat and the Goal Determiner (`reference_result_id`). Search runs against local, identity-only copies of each source's runner list (`utmb_runners`, ~49k Vietnamese runners; `vbm_athletes`), falling back to the live source while a copy is empty. Full results are fetched only for claimed profiles, never for the whole list. Both sources are unofficial, unauthenticated endpoints, so each has a kill switch (`RACE_HISTORY_UTMB_ENABLED`/`RACE_HISTORY_VBM_ENABLED`). Admin `POST /api/race-history/admin/mirrors/refresh?source=utmb|vbm|all` re-copies the lists in the background (about 12 min, paced 1 req/s; `GET .../mirrors/status`). An in-process worker (`RACE_HISTORY_WORKER_ENABLED`, off in tests) syncs pending claims and, when `RACE_HISTORY_WEEKLY_REFRESH_ENABLED=true`, refreshes both lists weekly under a Postgres advisory lock, backing off 6 h after a failure.

**Goal estimation** (spec in `docs/superpowers/specs/2026-09-26-llm-goal-estimation-design.md`): the Goal Determiner modal and the plan-header Goal pill share one engine. `services/goal_context.py` gathers race history, UTMB index, watch trend, profile and block progress (each toggleable); `services/goal_anchors.py` turns every usable past result into numeric anchors (physics, own field rank, percentile transfer, or a volume/pace prior); `services/goal_judge.py` has Gemini pick A/B/C with reasoning, then validates it (ordering, spread, winner floor, anchor range), retries once with a reduced prompt, and falls back to the anchors' median. `services/goal_service.py` stores each run in `goal_assessments` (reused when `input_hash` matches; `PROMPT_VERSION` is part of the hash). Plans are re-assessed on demand (3/day) and once per completed week; the athlete confirms any Time Target change. `GOAL_LLM_ENABLED` (default off) gates the Gemini tier — enable after `python scripts/golden_eval.py compare --service goal` (hold-out backtest, `scripts/goal_backtest.py`) beats the old engine on production data. The old `/api/coach/goal-estimate` endpoints remain but the UI no longer calls them.

**Training venues** (`services/training_venues.py`): plans carry `training_environment` (home terrain) plus `mountain_days` (weekdays with hill/trail access, JSON text), `stair_access` and `treadmill_max_incline` (default 15). They become rule 5 "TRAINING VENUES" of the plan prompt (one venue ladder per session type) and post-processing moves hill sessions off days with no venue; edited in Schedule Preferences on web (`TrainingVenueFields`) and iOS (`TrainingVenueSection`).

**Beginner milestones** (`services/beginner_milestones.py`, spec `docs/superpowers/specs/2026-10-20-beginner-milestones-design.md`): a `start_running` plan can carry `plans.milestone_target` (`5k`/`10k`) and an optional event (`has_target_event`; `race_name`/`race_date` then hold the event, otherwise `race_date` stays the synthetic block end). A fixed nine-step ladder (first session, 5/10/20/30 min unbroken jog, first 5 km, then 45/60 min and first 10 km) lives in code; `plan_milestones` stores achievements (`auto`/`manual`/`baseline`, or `revoked` so an undo survives re-detection). Jog credit comes from completed run workouts (planned jog length), distance milestones from any synced run since the plan start; `safe_refresh_milestones(user_id)` is called from every hook that can earn credit (workout log, manual match, COROS/Apple Health sync, live matcher) and is idempotent. Reaching a jog milestone raises `users.max_continuous_jog_min`. The plan payload key is `beginner_milestones` (not `milestones`: `services/plan_journey.py` owns that word for calendar milestones). The LLM only receives milestone facts and never decides achievement.

**Apple Health** (spec `docs/superpowers/specs/2026-10-14-apple-health-run-import-design.md`): the iOS app reads runs, hikes/stairs (`hike`) and strength workouts from HealthKit (any app's, read-only, 12-week first import, background delivery) and posts summaries to `POST /api/integrations/apple-health/sync`; rows land in `activities` as `source_provider='apple_health'` and go through the same duplicate check and matcher as COROS. `fitness_snapshot` takes measured volume from whichever device provider synced most recently. `APPLE_HEALTH_ENABLED=false` hides it without an app release. Routes and HR series never leave the phone. Sub-project B (spec `docs/superpowers/specs/2026-10-14-apple-health-recovery-metrics-design.md`) adds resting HR, HRV (SDNN) and asleep minutes as one `daily_metrics` row per day (`sleep_minutes`), with HRV status from a personal 28-day baseline (`services/recovery_baseline.py`); readiness reads one provider at a time (newest wins, COROS on a tie), since COROS RMSSD and Apple SDNN don't mix, and also feeds Coach Uphill. `APPLE_HEALTH_RECOVERY_ENABLED=false` stops it server- and app-side.

**Goal-reliable plans** (specs `docs/superpowers/specs/2026-10-20-goal-reliable-plans-design.md`, `2026-10-21-plan-view-coach-design.md`): a plan must be built from the goal's demands, say honestly when the athlete's week cannot hold them, stay inside the doctrine whatever the model writes, and be tracked against the B/A path. Pieces: `services/goal_demands.py` (required pace, climb rate, time on feet, peak week; none below 48 km), `services/goal_feasibility.py` (`supported|stretch|unsupported` + levers, judged at the level the peak volume belongs to), `services/plan_lint.py` + `race_readiness.py` (structural lint, readiness floor incl. best-feasible build when the benchmark is unreachable, specificity checks anchored on the last pre-taper week) with one corrective retry that carries concrete per-session minutes (`race_readiness.suggest_minutes`), `services/athlete_tier.graduated_profile` (session caps follow trained volume; next-block feeds completed volume into level resolution), `services/week_layout.py` (rule-based fallback honours days, long-run day and spacing), `services/aerobic_speed.py` + `fitness_tracking.py` + `fitness_checkpoints` (weekly aerobic-speed index, B/A path), `services/a_gate.py` (A add-ons only while path, recovery, adherence and plan support allow), `services/plan_journey.py` and `services/coach_nudge.py` (journey strip, model-worded coach message with number-grounding and a rule-based fallback; `coach_nudges` table). Ultras with a mountain day follow coach Quang's long-run ladder, weekday minimums and an 8-week Zone 3 quality window (`services/ultra_rules.py`, spec `docs/superpowers/specs/2026-10-23-ultra-rules-design.md`, rules R-U in `docs/plan-rules.md`). Checks: `python scripts/plan_reliability.py` (rule-based scorecard, no model), `scripts/plan_live_check.py` and `scripts/plan_live_sim.py` (PAID real-model checks; key via `GEMINI_LIVE_KEY` / `GEMINI_API_KEY`, scratch DB + local Qdrant with `scripts/load_kb.py --domain scheduler`; run sparingly).

Treadmill `treadmill_speed`/`treadmill_incline` on workouts are TEXT range strings ("8.1-9.2" kph, "2-4" %) derived deterministically from each workout's own `target_pace` in `PlanGenerator.resolve_treadmill_settings` — never the AI's raw numbers.

Auth uses JWT sessions stored in the `sessions` table. Google and Facebook OAuth are supported alongside email/password. `mock-login` endpoint only exists in non-production.

### Frontend (`/frontend`)
Next.js 16 with App Router, exported as static HTML (`output: "export"`). State is managed via a single large `AppContext` (`src/contexts/AppContext.tsx`) — no external state library.

Views live in `src/views/`, shared components in `src/components/`. Hooks in `src/hooks/` encapsulate API calls (e.g., `useKnowledge`, `usePlanner`, `useTools`).

The API base URL can be overridden at runtime via `?api=<url>` query param (stored in localStorage as `UPHILL_API_URL_OVERRIDE`), useful for pointing at different backend instances without a rebuild.

The frontend `CLAUDE.md` points to `AGENTS.md`, which warns: **this is Next.js 16 with breaking changes — read `node_modules/next/dist/docs/` before writing App Router code.**

Any change to rendered UI (components, views, styling, visible copy) needs a real screenshot of it running locally as evidence before being called done — passing `tsc`/`eslint`/`vitest` doesn't prove it looks right. See the `ui-screenshot-evidence` skill for the local dev-server + auth + screenshot workflow.

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
- **Backend**: Docker on SSH server `root@45.119.215.120` inside `/opt/uphill-ai-backend` (port `8000`). Deployment is handled by `deploy_server.sh` (reads `deploy.env` for `DEPLOY_SERVER` and `DEPLOY_TARGET_DIR`). Set `ENVIRONMENT=production` in the backend `.env` on the server — this disables API docs and the mock-login endpoint. For KB-seed-only changes (hand-edited `backend/kb_seed/*.json`, no code change), use the lighter `./deploy_kb.sh [--domain gear|nutrition|scheduler|race_courses|all]` (`all` excludes the hand-curated `race_courses`) instead — see the `deploy-backend` skill.

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
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` — outbound email for password reset codes (`services/email_service.py`, implicit TLS via `smtplib.SMTP_SSL`). Prod sends from the domain mailbox `viet.vo@uphill-ai.io.vn` through `cp02hn.emailserver.net.vn:465`. Empty `SMTP_HOST` logs and skips sending (local dev, tests); failures count in `password_reset_email_failures_total`
- `GOAL_LLM_ENABLED` — Gemini tier of goal estimation (default `false` = anchors-median rules tier); `GOAL_ASSESS_ON_PLAN_CREATE` — assess a new plan's goal in a background thread (default `true`, off in tests)
- `PLAN_DEMANDS_ENABLED` — the goal's physical demands (`services/goal_demands.py`: required pace, climbing rate, time on feet) in the generation prompt, the specificity lint (`TIME_ON_FEET`, `LONG_RUN_GRADIENT`, `SPECIFICITY_LATE`) and the rule-based fallback's volume ramp; defaults `true` (off in tests)
- `PLAN_LINT_ENABLED`, `PLAN_LINT_RETRY` — structural lint (`services/plan_lint.py`) and race-readiness projection (`services/race_readiness.py`) on every generated week; the retry regenerates once with the problems spelled out and keeps the draft with fewer. Both default `true` (off in tests); set `PLAN_LINT_RETRY=false` to log findings only, or `PLAN_LINT_ENABLED=false` to disable
- `QDRANT_URL` — defaults to `http://qdrant:6333` in Docker, `http://localhost:6333` otherwise
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` — enable Langfuse tracing (EU cloud, `LANGFUSE_BASE_URL`); empty disables it. `services/observability.py` is the only module importing `langfuse`/`openinference`/`opentelemetry`
- `OBSERVABILITY_ID_SALT` — HMAC salt for pseudonymous user/thread ids; required when Langfuse keys are set
- `LANGFUSE_EXPORT_CONTENT` — must stay `false`: traces are metadata and scores only (no prompts, replies or health notes)
- `LANGFUSE_ENVIRONMENT`, `LANGFUSE_SAMPLE_RATE`, `LANGFUSE_TIMEOUT` — trace tagging, sampling, background export timeout
- `LANGFUSE_RELEASE` — git SHA of the deployed build, tagged on every trace (set at deploy: `git rev-parse --short HEAD`)
- `LLM_JUDGE_SAMPLE_RATE` — share of coach turns graded in-process by `services/llm_judge.py` (default 0.1; one extra Gemini call each; only scores are exported; 0 in tests)
- `LLM_PRICES_JSON` — optional override of the per-model USD price table in `config.py` used by the `llm_cost_usd_total` Prometheus counter
- `COACH_CHAT_DAILY_NEW_TURNS_LIMIT`, `COACH_CHAT_DAILY_RETRIES_LIMIT`, `COACH_CHAT_MAX_RETRIES_PER_ROOT` — daily athlete turn and retry limits (50 new turns, 10 retries, 2 retries per root)
- `COACH_CHAT_TURN_TIMEOUT_SECONDS`, `COACH_CHAT_SUMMARY_TIMEOUT_SECONDS` — turn execution (45s) and summary generation (10s) deadlines
- `COACH_CHAT_RETENTION_DAYS`, `COACH_CHAT_MAX_INPUT_CHARS` — conversation retention (90d) and maximum user prompt length (2000 chars)
- `COACH_CHAT_PROMPT_LABEL`, `COACH_CHAT_PROMPT_CACHE_TTL_SECONDS` — Langfuse prompt label ("production"/"staging") and SDK cache TTL (300s) for **every** managed prompt (coach_chat, chat_summary, plan_generation, plan_single_workout, block_narrative, gear_finder, nutrition_planner, goal_judge), not just coach chat. The in-code template constants are the fallback

Per-user Gemini API keys are stored in the `users` table (`gemini_api_key` column) and take precedence over the server-level key for chat and plan generation (NOT yet for the gear/nutrition Gemini engines, which use the server key).

## Key Patterns

- **Dual database strategy**: The app uses PostgreSQL in production (via SQLAlchemy) and has legacy SQLite code paths. Always use the SQLAlchemy `engine`/`text()` pattern from `db.py`, not raw sqlite3.
- **Admin check**: `role == "admin"` is set when the email is `admin@uphill.ai` at OAuth login time.
- **Bilingual support**: The app supports English and Vietnamese (`lang: "en" | "vi"`). Knowledge cards and plan generation respect the `lang` parameter.
- **Qdrant**: A Qdrant vector DB container is in docker-compose. The KB RAG engine uses it via `services/kb_retrieval.py` (plain qdrant-client + `gemini-embedding-2`, collection `uphill_kb_scheduler`). `services/vector_service.py` is legacy (langchain-based, deps not in requirements.txt) kept only for the old `scripts/index_*.py`.
- **Dual schema**: every table/column change goes in BOTH `db.py:init_db()` and a hand-written Alembic migration (see the `db-migration` skill). `init_db()` also self-migrates existing dev databases via idempotent ALTERs at startup.
- **Prompt management**: all LLM prompts are Langfuse text prompts with `{{variables}}`, fetched by `observability.load_prompt(name, FALLBACK)` and compiled locally by `observability.compile_prompt` (athlete data never leaves the process). A Langfuse version that drops a variable is rejected in favour of the fallback. Prompt name/version is linked to each generation span. Change process: `.claude/skills/llm-change-process/SKILL.md`.
- **LLM Observability**: Unified tracing and cost accounting across Coach Plan Generator, Gear Finder, Nutrition Lab, KB Distiller, and Knowledge Cards via `services/observability.py`. Metadata-only export to EU Langfuse (`LANGFUSE_EXPORT_CONTENT=false`); Prometheus counters record calls, tokens, latency, and costs. See [docs/observability-release-report.md](docs/observability-release-report.md).

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `kylianvo/uphill-ai`, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), unchanged. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` + `docs/adr/` at the repo root (created lazily, not yet present). See `docs/agents/domain.md`.

### LLM changes

Any prompt edit, new Gemini call, or new LLM-powered service goes through Langfuse prompt versioning, a golden-set eval pushed to Langfuse, and staging → production label promotion. Follow `.claude/skills/llm-change-process/SKILL.md` and put its checklist in the PR description.

### UI changes

Never call a frontend change done on the strength of `tsc`/`eslint`/`vitest` alone — run it locally and capture a screenshot as evidence. See `.claude/skills/ui-screenshot-evidence/SKILL.md`.
