# Native Android handoff

Draft PR: https://github.com/kylianvo/uphill-ai/pull/127
Branch: `codex/android-native`; approved iOS reference base: `afa2893`.
Checkout: `/Users/vietvo/.codex/worktrees/android-native/uphill-ai`.
Plan: `docs/superpowers/plans/2026-10-14-android-native.md`.

## Current checkpoint — 2026-10-14

The user requested PR/handoff at 15% remaining account allowance. The latest check
showed 13% remaining in the five-hour window (40% weekly). Feature work stopped;
this checkpoint completes verification and preserves the remaining work.
Health Connect stays deferred by explicit user decision. Google Android OAuth
registration is complete; the physical phone upgrade test is deferred.

The initial Kotlin/Compose port covers auth, onboarding/generation, Plan, coach chat,
Goal/Gear/Nutrition/Pace/Knowledge, race history, COROS and coaching. Backend unchanged.
Package `ai.uphill.app`, version 2.0.0/code10, min26/target36, existing signing key.
Full feature and visual parity are not yet verified. Keep this PR draft.

This pass adds:
- Formatted goal-time pill, complete coach narrative/fallback, scoped coach Add Workout.
- Embedded COROS controls and inline profile saved confirmation.
- Nested chat week-review payloads, evidence sources, localized warning fallback,
  dismissible suggestions, retractable feedback, pacing checkpoints, proposal guards
  and richer card metadata.
- Rotation load guards/retry to prevent overwriting unloaded shoes; mileage assignment,
  presets/brands, race reset, nutrition levels, rest choices and debounced Pace requests.
- Persistent cross-tool targets, Goal pace strategy/context, Knowledge local shuffle
  and correct source labels for matched Apple Health activities.
- Explicit SDK packages in CI; configurable debug local API port; generated-resource
  newlines compatible with repository hooks; locale lookup through LocalConfiguration.

## Verification

- 74 debug JVM tests and 74 release JVM tests passed.
- All 11 emulator UI flows passed, including nested week review, proposal rebuild/apply,
  schedule confirmation and Pace/Nutrition handoff persistence.
- Combined check log: `/tmp/uphill-complete-parity-check.log`. Its only failure was a
  lint locale-lookup error in ProfileConnectedAccounts, subsequently corrected.
- Final lint, 74 release JVM tests and minified signed APK build passed (6m18s).
  Script verified certificate/package/version and copied
  `/Users/vietvo/Desktop/Uphill-AI-2.0.0.apk`. Log: `/tmp/uphill-latest-release.log`.
- Translation converter previously passed four tests; current generated catalog has
  1,440 EN/VI entries.
- Earlier independent contract review found five defects, all corrected/rechecked.
- Earlier exact Capacitor1.0.5/code6 → matching-signed native debug code10 upgrade
  passed on emulator without uninstall; app-private marker survived.
- Committed screenshots precede current changes; plan-en.png captures loading. They
  are not final parity evidence. Fresh screenshots remain outstanding.

## Remaining work, in order

1. Add scoped coach workout detail Edit/Remove/Approve and notes entry flow, using
   existing CoachingService contracts. Add Workout is already implemented.
2. Capture current major screens/states in EN/VI, font scale1.3 and animator scale0;
   restore settings. Compare with iOS source/screenshots using Impeccable's batched
   inspection and one correction round. Android uses its system face in place of
   iOS SF Pro; the launch title shares bundled Plus Jakarta Sans. Do not claim exact
   font rendering. Check Apple Health match-icon tint against iOS.
3. Verify against an isolated live local backend and smoke-test the minified release.
   Release always points to production: avoid fictional-account writes there.
4. Verify live Google/COROS round trips and the deferred physical-phone upgrade.
5. Keep Health Connect/push/widgets/WearOS/Play Store/Apple/Facebook auth excluded.
   This consolidated draft does not fulfill the original one-PR-per-phase structure.

## Commands and environment

SDK: `/opt/homebrew/share/android-commandlinetools`; JDK17/21.
Emulator: `uphill_test` / `emulator-5554`, cold host-GPU boot in this chat.
Boot log: `/tmp/uphill-emulator-resume.log`. UI runner uninstalls main/test APKs;
reinstall before screenshots. Older temporary helpers/logs were cleared during an
interruption. Do not assume old servers or scripts still exist. Port8000 was occupied
by task-creator; inspect listeners before starting an isolated backend.

From the checkout:
```sh
./android-native/gradlew -p android-native lint testDebugUnitTest testReleaseUnitTest assembleDebug connectedDebugAndroidTest -PuphillReleaseSigningForDebug=true
cd android-native
./scripts/build_release_apk.sh
```
Debug local port override: `-PuphillLocalApiPort=8016`; default10.0.2.2:8000.
AppContainer uses that BuildConfig default unless the hidden developer menu overrides
it. Release ignores debug environment overrides.

Signing properties and keystore stay ignored; the properties reference the existing
main-checkout key. Never commit keys, APKs, tokens or local.properties. Release script
verifies certificate/package/version and copies `/Users/vietvo/Desktop/Uphill-AI-2.0.0.apk`.
Keystore-backed AES-GCM token storage, DataStore settings/chat, file jobs/cache,
Canvas charts and direct OkHttp are intentional choices. Upgraded users may need to
log in again because Capacitor tokens are not migrated. ICS sharing remains; webcal
subscription was removed because it exposed a full session token.
