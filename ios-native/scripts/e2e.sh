#!/usr/bin/env bash
# Seeds the local preview athlete and runs the UI tests against the LOCAL backend.
# Requires the Docker stack (API on :8000, Postgres on :5433).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
curl -sf http://localhost:8000/api/health >/dev/null || { echo "Local backend is not running on :8000" >&2; exit 1; }
PY="${PYTHON:-python3}"
[ -x "$ROOT/backend/.venv/bin/python" ] && PY="$ROOT/backend/.venv/bin/python"
"$PY" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" ||
  { echo "Python >= 3.10 required for the backend seed ($PY is too old). Set PYTHON=/path/to/backend/.venv/bin/python" >&2; exit 1; }
(cd "$ROOT/backend" && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai "$PY" scripts/seed_ios_preview.py)
cd "$ROOT/ios-native"
xcodegen generate --quiet
# Default: the first iPhone on the newest installed iOS simulator runtime (same as test.sh).
if [ -z "${DESTINATION:-}" ]; then
  DESTINATION="$(xcrun simctl list devices available -j | python3 -c '
import json, sys
devs = json.load(sys.stdin)["devices"]
def ver(rt): return tuple(int(x) for x in rt.rsplit("iOS-", 1)[1].split("-"))
for rt in sorted((r for r in devs if "SimRuntime.iOS-" in r), key=ver, reverse=True):
    phones = sorted(d["name"] for d in devs[rt] if d["name"].startswith("iPhone"))
    if phones:
        print("platform=iOS Simulator,name=%s,OS=%s" % (phones[0], ".".join(map(str, ver(rt)))))
        break
')"
fi
echo "Testing on: $DESTINATION"
xcodebuild test -project UphillAI.xcodeproj -scheme UphillAI-E2E -destination "$DESTINATION" \
  -test-timeouts-enabled YES -collect-test-diagnostics never \
  -default-test-execution-time-allowance 300 -maximum-test-execution-time-allowance 360 \
  2>&1 | tail -n 40
