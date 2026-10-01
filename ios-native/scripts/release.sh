#!/usr/bin/env bash
# Builds a signed App Store .ipa of the native app. Does not upload and does not touch git.
# Usage: ios-native/scripts/release.sh <build-number>
# The build number must be higher than every build already on TestFlight for ai.uphill.app,
# including the Capacitor builds.
set -euo pipefail
cd "$(dirname "$0")/.."

BUILD="${1:-}"
if [[ -z "$BUILD" ]]; then
  read -r -p "Last build number on TestFlight for ai.uphill.app: " LAST
  BUILD=$((LAST + 1))
fi

xcodegen generate --quiet
rm -rf build/UphillAI.xcarchive build/export
xcodebuild archive \
  -project UphillAI.xcodeproj \
  -scheme UphillAI \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  -archivePath build/UphillAI.xcarchive \
  -allowProvisioningUpdates \
  CURRENT_PROJECT_VERSION="$BUILD" \
  -quiet
xcodebuild -exportArchive \
  -archivePath build/UphillAI.xcarchive \
  -exportPath build/export \
  -exportOptionsPlist scripts/ExportOptions.plist \
  -allowProvisioningUpdates \
  -quiet

echo "Built build $BUILD: $(pwd)/build/export/UphillAI.ipa"
echo "Upload with Xcode Organizer or Transporter, then add release notes in App Store Connect."
