#!/usr/bin/env bash
# Records API response fixtures from a LOCAL backend (never staging/prod).
# Usage: ios-native/scripts/record_fixtures.sh [base_url]
# Signs in through the dev-only mock-login as ios-fixtures@uphill.ai.
set -euo pipefail
BASE="${1:-http://localhost:8000}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/UphillAITests/Fixtures"
mkdir -p "$OUT"

case "$BASE" in
  http://localhost*|http://127.0.0.1*) ;;
  *) echo "Refusing to record from $BASE: local backends only." >&2; exit 1 ;;
esac

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

get() { curl -sf "$BASE$1" -H "Authorization: Bearer $TOKEN" | scrub > "$OUT/$2"; }

get /api/auth/me auth_me.json

echo "Recorded fixtures into $OUT"
