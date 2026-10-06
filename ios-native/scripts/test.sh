#!/usr/bin/env bash
# Regenerates the project and runs the unit tests on a simulator.
# Override the simulator: DESTINATION='platform=iOS Simulator,name=iPhone 18 Pro,OS=27.0' ios-native/scripts/test.sh
set -euo pipefail
cd "$(dirname "$0")/.."
xcodegen generate --quiet
# Default: the first iPhone on the newest installed iOS simulator runtime.
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
LOG="${XCODEBUILD_LOG:-$(mktemp -t uphill-xcodebuild).log}"
if xcodebuild test \
  -project UphillAI.xcodeproj \
  -scheme UphillAI \
  -destination "$DESTINATION" \
  -collect-test-diagnostics never \
  "$@" >"$LOG" 2>&1; then
  echo "Tests passed (full log: $LOG)"
else
  status=$?
  echo "--- errors ---"
  # `error:` covers compiler errors; the rest covers Swift Testing and XCTest failures, crashes and timeouts.
  grep -E "error:|✘|recorded an issue|Test Case .* failed|crashed|timed out|Timed out" "$LOG" | sort -u | head -n 80 || true
  echo "--- tail ---"
  tail -n 25 "$LOG"
  echo "Full log: $LOG"
  exit "$status"
fi
