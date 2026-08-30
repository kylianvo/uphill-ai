#!/bin/bash
# Builds a signed, App Store-ready .ipa from the current working tree and
# registers the archive in Xcode's Archives store (Window > Organizer picks
# it up automatically). Does NOT upload anything -- the last step (Xcode
# Organizer > Distribute App > App Store Connect > Upload) stays manual.
#
# Does NOT touch git (no fetch/rebase) -- make sure you're on the commit you
# actually want to ship before running this. See MOBILE.md's "Release build
# (TestFlight)" section for the full routine including the git step.
#
# Usage: frontend/scripts/ios_release.sh [last_uploaded_build_number]
#   With no argument, prompts for the last build number you know was
#   uploaded to TestFlight (or use 0 if this is the first-ever upload) --
#   the script bumps CURRENT_PROJECT_VERSION to that + 1. There's no
#   reliable source of truth for this in git (build-number bumps have never
#   been committed), so this has to be supplied each time.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # frontend/

PBXPROJ="ios/App/App.xcodeproj/project.pbxproj"
if [ ! -f "$PBXPROJ" ]; then
  echo "ERROR: $PBXPROJ not found -- run this from a checkout with the iOS project synced (npx cap sync ios)." >&2
  exit 1
fi

if [ ! -f ".env.production" ]; then
  echo "ERROR: frontend/.env.production not found. This is gitignored/machine-local -- see MOBILE.md." >&2
  echo "It must set NEXT_PUBLIC_API_URL=https://api.uphill-ai.io.vn (the real backend, not localhost)." >&2
  exit 1
fi

LAST_BUILD="${1:-}"
if [ -z "$LAST_BUILD" ]; then
  read -r -p "Last build number you know was uploaded to TestFlight (0 if none yet): " LAST_BUILD
fi
if ! [[ "$LAST_BUILD" =~ ^[0-9]+$ ]]; then
  echo "ERROR: '$LAST_BUILD' isn't a plain integer." >&2
  exit 1
fi
NEW_BUILD=$((LAST_BUILD + 1))

TEAM_ID=$(grep -m1 "DEVELOPMENT_TEAM = " "$PBXPROJ" | sed -E 's/.*DEVELOPMENT_TEAM = ([A-Z0-9]+);/\1/')
MARKETING_VERSION=$(grep -m1 "MARKETING_VERSION = " "$PBXPROJ" | sed -E 's/.*MARKETING_VERSION = ([0-9.]+);/\1/')
if [ -z "$TEAM_ID" ] || [ -z "$MARKETING_VERSION" ]; then
  echo "ERROR: couldn't read DEVELOPMENT_TEAM / MARKETING_VERSION from $PBXPROJ." >&2
  exit 1
fi

echo "Releasing Uphill AI $MARKETING_VERSION ($NEW_BUILD), team $TEAM_ID..."

# The build-number bump is intentionally never committed (matches every
# prior release session) -- restore the file on exit no matter what happens.
cp "$PBXPROJ" "$PBXPROJ.orig"
restore_pbxproj() { mv -f "$PBXPROJ.orig" "$PBXPROJ"; }
trap restore_pbxproj EXIT

sed -i '' -E "s/CURRENT_PROJECT_VERSION = [0-9]+;/CURRENT_PROJECT_VERSION = $NEW_BUILD;/g" "$PBXPROJ"

echo "Building web export (npm run build, reads .env.production)..."
npm run build

echo "Syncing into the iOS shell (npx cap sync ios)..."
npx cap sync ios

TIMESTAMP=$(date "+%Y-%m-%d, %H.%M.%S")
ARCHIVE_DIR="$HOME/Library/Developer/Xcode/Archives/$(date +%Y-%m-%d)"
ARCHIVE_PATH="$ARCHIVE_DIR/Uphill AI $TIMESTAMP.xcarchive"
mkdir -p "$ARCHIVE_DIR"

echo "Archiving (xcodebuild archive, Release, generic iOS device)..."
(cd ios/App && xcodebuild archive \
  -project App.xcodeproj \
  -scheme App \
  -configuration Release \
  -destination "generic/platform=iOS" \
  -archivePath "$ARCHIVE_PATH" \
  -skipMacroValidation)

EXPORT_OPTIONS=$(mktemp -t ExportOptions).plist
cat > "$EXPORT_OPTIONS" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store-connect</string>
    <key>teamID</key>
    <string>$TEAM_ID</string>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>uploadSymbols</key>
    <true/>
</dict>
</plist>
PLIST

EXPORT_DIR=$(mktemp -d -t uphill_ios_export)
echo "Exporting signed .ipa (xcodebuild -exportArchive)..."
xcodebuild -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportPath "$EXPORT_DIR" \
  -exportOptionsPlist "$EXPORT_OPTIONS"

echo ""
echo "Done. Version $MARKETING_VERSION ($NEW_BUILD):"
echo "  Archive: $ARCHIVE_PATH"
echo "  IPA:     $EXPORT_DIR/App.ipa"
echo ""
echo "Next (manual): Xcode > Window > Organizer > select this archive >"
echo "  Distribute App > App Store Connect > Upload. Then attach build"
echo "  $MARKETING_VERSION ($NEW_BUILD) to the right TestFlight group."
