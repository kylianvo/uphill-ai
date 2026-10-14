# Native Android handoff

Draft PR: https://github.com/kylianvo/uphill-ai/pull/127
Branch: `codex/android-native`; approved iOS reference base: `afa2893`.
Checkout: `/Users/vietvo/.codex/worktrees/android-native/uphill-ai`.
Plan: `docs/superpowers/plans/2026-10-14-android-native.md`.

## Current checkpoint — 2026-10-15

The user requested PR/handoff at 15% remaining account allowance. Work resumed after
the previous checkpoint. Latest allowance check: 47% five-hour / 18% weekly remaining.
Checkpoint again when either account window reaches 15% remaining.
Health Connect stays deferred by explicit user decision. Google Android OAuth
registration is complete; the physical phone upgrade test is deferred.

The Kotlin/Compose port covers auth, onboarding/generation, Plan, coach chat,
Goal/Gear/Nutrition/Pace/Knowledge, race history, COROS and coaching.
Package `ai.uphill.app`, version 2.0.0/code10, min26/target36, existing signing key.
Full feature and visual parity are not yet established. Keep PR #127 draft.

The earlier pass adds:
- Scoped coach workout detail Edit/Approve/Remove and coach/athlete note threads.
- Source-based workout metrics, execution timeline, treadmill ranges, reason/benefit,
  warnings, coach note and the five-level feeling selector. Save Log keeps the detail
  open with confirmation; pending coach approval hides athlete completion actions.
- Wrapping Plan titles, compact generation progress, pink Health match icon and
  active bottom-tab selection retained through nested tools.
- Opt-in EN/VI emulator screenshot capture, including larger text and reduced motion.
- Isolated live local-backend flow covering registration, plan generation, profile,
  workout logging, rotation, coach invite/accept, scoped actions and note visibility.
- Final review fixes: suggested watch matches cannot mark workouts complete; confirmed
  matches also respect date/rest/already-completed guards. AI workout requests now
  include the typed `intent`. Both defects have regression tests.
- Coaching invite consumes the actual backend response without decoding unused fields.

Two additive backend fixes are included and **not deployed**: auth/profile responses
now expose saved `athlete_notes`; profile edits preserve an omitted `gemini_api_key`
while explicit empty string still clears it. Production needs these fixes deployed
before the profile behavior can be fully verified there. No schema migration.

The latest parity pass adds the iOS #134 month calendar with weekly distance bars,
month totals, day preview, Next/Today/swipe navigation and selection haptics. It also
adds coach adherence/weekday/mix charts, Overview/Roster sections, 7/14/30-day and
Elite filters, roster search, shared iOS workout colors and pace range formatting.
A localization fix prevents raw percent labels from being treated as format strings.
The pace metric now wraps between complete times at font scale 1.3.
See `docs/PARITY.md` for the area-by-area inventory against iOS main `5597527`.

## Verification

- 90 debug JVM tests and 90 release JVM tests passed; lint passed. Minified signed
  release build passed in 3m44s, verifying certificate/package/versionCode >6.
  APK: `/Users/vietvo/Desktop/Uphill-AI-2.0.0.apk`; log: `/tmp/uphill-parity-release.log`.
- Final direct instrumentation passed all 21 tests: 19 recorded HTTP/native UI flows,
  one isolated live local-backend flow and one opt-in screenshot capture test.
  Log: `/tmp/uphill-parity-device-check.log` (192.509 seconds).
- All 1,265 backend unit tests passed; targeted native-auth tests: 10 passed.
  Logs: `/tmp/uphill-backend-final-unit.log`, `/tmp/uphill-profile-response-green.log`.
- Final fresh-context review found two Important defects, both fixed as above. No
  Critical findings. One fix pass; tests verify it, without a repeated review loop.
- Translation converter previously passed four tests; catalog has 1,461 EN/VI entries.
- Earlier exact Capacitor1.0.5/code6 → matching-signed native debug code10 upgrade
  passed on emulator without uninstall; app-private marker survived.
- Screenshot capture passed: 29 normal EN/VI captures and 17 font1.3/zero-animation
  captures under `docs/screenshots/parity-2026-10-15/`. Device settings were restored.
  Batched Impeccable inspection compared calendar/day views with current iOS references
  and checked coach charts/roster and complete pace times at larger text.
  Logs: `/tmp/uphill-coach-evidence.log`, `/tmp/uphill-current-accessible-evidence.log`.
- Signed-out minified release emulator smoke passed: matching-signed APK installed,
  cold MainActivity launch succeeded, UI hierarchy showed Uphill AI / Google / Sign in.
  Existing `release-sign-in-en.png` records the previous 6208d6d smoke. The updated
  signed release installed and cold-launched successfully for the live OAuth checks.
  No fictional-account writes to production. This does not validate authenticated
  release flows or live OAuth.

## Remaining work, in order

1. Continue the inventory in `docs/PARITY.md`: every sheet/state, TalkBack and motion
   still need comparison. Coach inline invite and race-to-roster filtering remain.
   Calendar weekly-column label is `km` rather than iOS `km/wk` / `km/tuần`; day preview's
   Open Week button styling also differs. Fixture descriptions keep their recorded language.
2. Live Google/COROS round trips are in progress with the user. Original `uphill_test`
   has old Play services 23.18.18; logs report failure to parse the button request.
   Switched OAuth checks to installed `uphill_playstore` on emulator-5556, with Play
   services 26.33.32. The actual Google account sign-in page is open for the user.
   Updated release APK is installed on both emulators; no live round trip yet. Do not clear/uninstall app data or run instrumentation after sign-in.
   Physical-phone upgrade remains explicitly deferred.
3. Deploy the two backend profile fixes when explicitly requested; current production
   has not been changed by this work.
4. Keep Health Connect/push/widgets/WearOS/Play Store/Apple/Facebook auth excluded.
   ICS sharing remains; direct calendar writes were deferred in the approved plan.
   This consolidated draft does not fulfill the original one-PR-per-phase structure.

## Commands and environment

SDK: `/opt/homebrew/share/android-commandlinetools`; JDK17/21.
Emulator: `uphill_test` / `emulator-5554`, cold host-GPU boot in this chat.
UI runner uninstalls main/test APKs; reinstall before standalone smoke checks.
The owned live backend runs on port8016, isolated database `uphill_android_native_oct15`
on the local PostgreSQL container at port5433. Source is this worktree; runtime is
main checkout's backend virtualenv. No real Gemini key is configured. Launch helper:
`/tmp/uphill-native-local-backend.py`; log: `/tmp/uphill-native-local-backend.log`.
Port8000 belongs to unrelated work; do not stop or reuse it.

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
