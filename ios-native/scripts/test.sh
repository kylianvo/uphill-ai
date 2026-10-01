#!/usr/bin/env bash
# Regenerates the project and runs the unit tests on a simulator.
# Override the simulator: DESTINATION='platform=iOS Simulator,name=iPhone 16' ios-native/scripts/test.sh
set -euo pipefail
cd "$(dirname "$0")/.."
xcodegen generate --quiet
DESTINATION="${DESTINATION:-platform=iOS Simulator,name=iPhone 17 Pro}"
xcodebuild test \
  -project UphillAI.xcodeproj \
  -scheme UphillAI \
  -destination "$DESTINATION" \
  -quiet "$@"
