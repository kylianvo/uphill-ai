#!/usr/bin/env bash
# Records API response fixtures from a LOCAL backend (never staging/prod).
# Usage: ios-native/scripts/record_fixtures.sh [base_url]
# Signs in through the dev-only mock-login as ios-fixtures@uphill.ai.
set -euo pipefail
BASE="${1:-http://localhost:8000}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/UphillAITests/Fixtures"
mkdir -p "$OUT"

if [[ ! "$BASE" =~ ^http://(localhost|127\.0\.0\.1)(:[0-9]+)?(/|$) ]]; then
  echo "Refusing to record from $BASE: local backends only." >&2
  exit 1
fi

# Replaces the live session token so fixtures never hold a usable credential,
# and drops the per-user Gemini key the backend echoes back.
scrub() {
  python3 -c '
import json, sys
d = json.load(sys.stdin)
def walk(o):
    if isinstance(o, dict):
        if "session_token" in o:
            o["session_token"] = "fixture-session-token"
        o.pop("gemini_api_key", None)
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(d)
json.dump(d, sys.stdout, indent=2, sort_keys=True)
print()
'
}

LOGIN=$(curl -sf -X POST "$BASE/api/auth/mock-login" \
  -H 'Content-Type: application/json' -d '{"email":"ios-fixtures@uphill.ai"}')
TOKEN=$(printf '%s' "$LOGIN" | python3 -c 'import json,sys; print(json.load(sys.stdin)["session_token"])')
printf '%s' "$LOGIN" | scrub > "$OUT/auth_login.json"

get() {
  local tmp
  tmp=$(mktemp)
  if curl -sf "$BASE$1" -H "Authorization: Bearer $TOKEN" | scrub > "$tmp"; then
    mv "$tmp" "$OUT/$2"
  else
    rm -f "$tmp"
    return 1
  fi
}

get /api/auth/me auth_me.json

get /api/coach/active-plan active_plan_none.json   # ios-fixtures has no plan

# The preview athlete (backend/scripts/seed_ios_preview.py) has plans.
PREVIEW=$(curl -sf -X POST "$BASE/api/auth/mock-login" \
  -H 'Content-Type: application/json' -d '{"email":"ios-preview@uphill.ai"}')
TOKEN=$(printf '%s' "$PREVIEW" | python3 -c 'import json,sys; print(json.load(sys.stdin)["session_token"])')
get /api/coach/active-plan active_plan.json
get /api/coach/recent-plans recent_plans.json

echo "Recorded fixtures into $OUT"

PLAN_ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["plan"]["id"])' "$OUT/active_plan.json")
get "/api/coach/block-completion/$PLAN_ID" block_completion.json
get "/api/coach/week-review/$PLAN_ID/1" week_review.json
# Creates one assessment (rules tier unless GOAL_LLM_ENABLED). Limited per day on the server.
curl -sf -X POST "$BASE/api/plans/$PLAN_ID/goal/reassess" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"exclude":[],"lang":"en"}' >/dev/null || true
get "/api/plans/$PLAN_ID/goal" plan_goal.json
