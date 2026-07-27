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
# Run this once (and again whenever backend/.env's Airflow-relevant values
# change) before `docker compose up airflow-webserver airflow-scheduler`.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="backend/.env"
OUT="airflow/.env"
VARS=(
  GEMINI_API_KEY
  TAVILY_API_KEY
  NOTEBOOKLM_NOTEBOOK_ID
  NOTEBOOKLM_GEAR_ID
  NOTEBOOKLM_NUTRITION_ID
  NOTEBOOKLM_AUTH_JSON
)

if [ ! -f "$SRC" ]; then
  echo "error: $SRC not found — copy backend/.env.example or set it up first" >&2
  exit 1
fi

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
