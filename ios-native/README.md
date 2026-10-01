# Uphill AI — native iOS app

SwiftUI app that replaces the Capacitor iOS shell (same bundle ID `ai.uphill.app`).
Design and roadmap: `docs/superpowers/specs/2026-10-01-ios-native-app-design.md`.

## Setup

Requires Xcode 27 with the iOS 27 simulator runtime installed (Xcode > Settings > Components).

```bash
ios-native/scripts/bootstrap.sh     # installs XcodeGen, generates UphillAI.xcodeproj
open ios-native/UphillAI.xcodeproj
```

The `.xcodeproj` is generated from `project.yml` and git-ignored. Change settings in `project.yml`, not in
Xcode's target editor, and re-run `xcodegen generate` after pulling.

## Test

```bash
ios-native/scripts/test.sh
```

`test.sh` regenerates the project, then runs the unit tests on the first iPhone of the newest installed iOS
simulator runtime. Override the simulator with `DESTINATION`:

```bash
DESTINATION='platform=iOS Simulator,name=iPhone 18 Pro,OS=27.0' ios-native/scripts/test.sh
```

If a run hangs before any test starts (usually Developer mode or stale Xcode test services), reset them and retry:

```bash
pkill -f DTServiceHub; pkill testmanagerd; killall com.apple.CoreSimulator.CoreSimulatorService
```

CI (`.github/workflows/ios-native.yml`) runs the same script on a macOS runner for PRs touching `ios-native/**`.

## End-to-end (local backend)

```bash
ios-native/scripts/e2e.sh
```

Seeds `ios-preview@uphill.ai` (password `uphill-preview-1`, local only) with plans around today, then runs
`UphillAIUITests`. Not part of CI: it needs the local Docker stack.

## Backends

Debug builds default to the local Docker backend (`http://localhost:8000`; `docker compose up -d` at the repo root).
Long-press the version label in Me to switch to staging or production. Release builds always use production.

## Fixtures

DTO tests decode JSON recorded from a LOCAL backend (the script refuses anything else):

```bash
ios-native/scripts/record_fixtures.sh
```

Re-record after a backend response changes. Never hand-edit a recorded fixture; fix the Swift type instead.

## Sign-in configuration

- Sign in with Apple needs the capability enabled on App ID `ai.uphill.app` in the Apple Developer portal.
- Google client IDs (`GIDClientID` and the URL scheme) live in `project.yml`.

## Release (TestFlight)

1. Find the last build number for `ai.uphill.app` in App Store Connect (Capacitor builds count).
2. `ios-native/scripts/release.sh <that number + 1>` (needs your Apple account signed in to Xcode)
3. Upload `ios-native/build/export/UphillAI.ipa` with Xcode Organizer or Transporter.

The script builds the `.ipa` only; it never uploads.

OnboardingFlowUITests registers a new `ios-e2e-<timestamp>@uphill.ai` account on each run (local database only).
