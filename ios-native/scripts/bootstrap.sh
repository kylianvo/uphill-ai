#!/usr/bin/env bash
# One-time setup: installs XcodeGen if missing, then generates UphillAI.xcodeproj.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v xcodegen >/dev/null 2>&1; then
  brew install xcodegen
fi
xcodegen generate
