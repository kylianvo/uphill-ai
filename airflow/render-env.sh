#!/usr/bin/env bash
# Generates airflow/.env — a narrow env file containing ONLY the vars the
# Airflow containers actually read (via config.py's settings singleton),
# sourced from backend/.env's real values.
#
# Why this exists: docker-compose's `env_file:` hands a container every
# variable in the referenced file, regardless of whether the app reads it.
# backend/.env also carries JWT_SECRET, GOOGLE_CLIENT_ID, and other
# session/OAuth secrets that Airflow (a UI-exposing, lower-trust adjacent
# service that will execute DAG-defined Python) has no business holding.
# Docker Compose only auto-loads a *root*-level .env for ${VAR}
# interpolation, and this repo intentionally keeps real secrets in
# backend/.env — not the root — so plain ${GEMINI_API_KEY} substitution in
# docker-compose.yml would resolve empty. Generating a small, git-ignored
# airflow/.env from backend/.env's actual values sidesteps both problems.
#
# This now also runs automatically as the first step of the `airflow-init`
# compose service (which airflow-webserver/airflow-scheduler both wait on
# via `depends_on: condition: service_completed_successfully`), with
# backend/ and airflow/ bind-mounted in so it can read/write across the
# container boundary — see docker-compose.yml. It remains safe (and
# supported) to run by hand on the host too: `./airflow/render-env.sh`.
#
# Usage: render-env.sh [SRC_ENV_FILE] [OUT_ENV_FILE]
#   Defaults (host invocation): backend/.env -> airflow/.env, relative to
#   the repo root. Pass absolute paths when invoking from inside a
#   container with different mount points.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${1:-backend/.env}"
OUT="${2:-airflow/.env}"
VARS=(
  GEMINI_API_KEY
  TAVILY_API_KEY
  NOTEBOOKLM_NOTEBOOK_ID
  NOTEBOOKLM_GEAR_ID
  NOTEBOOKLM_NUTRITION_ID
  NOTEBOOKLM_AUTH_JSON
)

if [ ! -f "$SRC" ]; then
  echo "error: render-env.sh: '$SRC' not found." >&2
  echo "       Set up backend/.env first (see deploy.env.example / README) — airflow/.env" >&2
  echo "       cannot be generated without it, and airflow-webserver/airflow-scheduler" >&2
  echo "       will fail to start without airflow/.env." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
: > "$OUT"
found=0
for v in "${VARS[@]}"; do
  line=$(grep -E "^${v}=" "$SRC" || true)
  if [ -n "$line" ]; then
    echo "$line" >> "$OUT"
    found=$((found + 1))
  fi
done

echo "Wrote $OUT with $found/${#VARS[@]} Airflow-relevant vars found in $SRC."
