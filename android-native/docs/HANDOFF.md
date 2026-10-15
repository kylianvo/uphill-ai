# Native Android handoff

Draft PR: https://github.com/kylianvo/uphill-ai/pull/127
Branch: `codex/android-native`; approved iOS reference base: `afa2893`.
Checkout: `/Users/vietvo/.codex/worktrees/android-native/uphill-ai`.
Plan: `docs/superpowers/plans/2026-10-14-android-native.md`.

## Current checkpoint — 2026-10-15

The user extended the allowance checkpoint to around 5%, then explicitly requested
stopping and updating this handoff/PR. Feature work and the in-progress release build
were stopped at that request. No deployment or merge was performed.
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

## Latest Coach Hub pass

- Inline athlete invite with success/error state replaces the modal. Roster search can
  be opened from a target-race row; clearing it restores the roster.
- Source-based action counts/links, phase alerts, roster progress, adherence badges,
  target-race counts and Coach Hub refresh. Roster rows now have a separate Profile action.
- Athlete Profile sheet: physiology/threshold tiles and provenance, training preferences,
  injury/athlete notes, general coach-note thread and the existing threshold editor.
  Requests stay athlete-scoped; edits send only changed fields. Failed saves retain the
  loaded profile and keep the editor open for retry.
- Calendar weekly column uses localized `km/wk` / `km/tuần`; Open Week matches the
  source's tinted list button.
- One batched screenshot comparison found large-text VI header wrapping, scrolling
  Profile navigation and wrapping placeholders. The final correction uses text auto-size
  for the column caption, a fixed Profile header, single-line placeholders, an inline
  physiology Edit header and a wrapping status/email row. Confirmation is pending below.

## Verification and artifact freshness

- **91 debug JVM tests + 91 release JVM tests passed**, zero failures. Includes the
  failed-save/retry and general-note request regression. Translation converter: four
  tests passed; generated catalog has 1,469 EN/VI entries. `git diff --check` passed.
- **23 instrumentation tests passed** before the final visual correction: 21 native UI
  flows, one isolated live local-backend flow and one normal screenshot capture test.
  Log: `/tmp/uphill-hub-device-check.log` (86.836s).
- New inline-invite/race-navigation and Profile edit/general-note flows each failed
  against their missing baseline and passed after implementation. Profile flow: 9.231s.
  Logs: `/tmp/uphill-coach-inline-red.log`, `/tmp/uphill-coach-inline-green.log`,
  `/tmp/uphill-coach-profile-red.log`, `/tmp/uphill-coach-profile-green.log`.
- **39 normal + 27 font1.3/zero-animation fixture captures** were produced and inspected
  with iOS Phase6/calendar references. They precede the final visual correction; do not
  present them as confirmation of the sticky header or single-line VI caption.
  Accessible log: `/tmp/uphill-hub-accessible-evidence.log`; device settings restored.
- Final correction compiled; debug unit tests passed. The **24-test confirmation run
  was interrupted after 15 native tests when the emulator processes exited**. It has no
  pass/fail result for the full run. Play Store emulator process exited137; both devices
  disappeared from adb. No app data was cleared. Log: `/tmp/uphill-hub-confirm-device.log`.
- Latest release unit tests passed, but signed build/lint completion is **unverified**.
  Build was stopped during R8 on the user's request. Log: `/tmp/uphill-hub-release.log`.
  Desktop `/Users/vietvo/Desktop/Uphill-AI-2.0.0.apk` remains the **earlier verified
  release**, before this Coach Hub/Profile pass. Rebuild before sharing the latest UI.
- Earlier checkpoint: signed/minified release build, certificate/package/code10 checks,
  90 debug/release tests, and 21 instrumentation tests passed. Google sign-in and existing
  COROS Sync now then passed live with the user on `uphill_playstore`; no production
  credentials, account details, health counts or screenshots are committed.
- Backend unchanged in this pass: prior 1,265 unit tests and ten targeted auth/profile
  tests passed. The two included profile fixes remain **not deployed**.
- Earlier emulator Capacitor1.0.5/code6 → matching-signed native debug code10 upgrade
  preserved an app-private marker. Physical-phone upgrade remains deferred.
- Fresh-context whole-branch review was completed at the earlier checkpoint; suggested
  watch completion and omitted AI intent defects were fixed with regressions. No new
  repeated whole-branch review was run for this scoped pass.

## Remaining work, in order

1. Boot **only the fixture emulator `uphill_test` (5554)** first. Rerun final 24-test
   instrumentation and the bounded normal/accessible confirmation captures. Confirm
   the VI weekly caption has one line and Profile Done stays visible while scrolling.
   Then build the signed APK sequentially to limit host memory pressure. Do not claim
   this Coach Hub/Profile pass complete until these checks finish.
   Continue the inventory in `docs/PARITY.md` afterward: remaining sheets/states,
   TalkBack, all motion, onboarding and tools still need comparison.
2. Live Google sign-in passed on the signed minified release in `uphill_playstore`
   (emulator-5556). User selected their account; authenticated Plan/Coach/Me/Athletes
   tabs were confirmed. Google Play services updated to 26.39.33 during setup.
   Original `uphill_test` has old Play services 23.18.18 and a request-parsing failure.
   Existing production COROS connection loaded; “Sync now” returned a success notice.
   Fresh COROS OAuth is unverified: disconnecting would delete received COROS data,
   so the existing connection was preserved. No credentials, tokens, health counts,
   profile data or production screenshots are committed. Do not clear/uninstall app
   data or run instrumentation on emulator-5556: it now holds the user's session.
   Physical-phone upgrade remains explicitly deferred.
3. Deploy the two backend profile fixes when explicitly requested; current production
   has not been changed by this work.
4. Keep Health Connect/push/widgets/WearOS/Play Store/Apple/Facebook auth excluded.
   ICS sharing remains; direct calendar writes were deferred in the approved plan.
   This consolidated draft does not fulfill the original one-PR-per-phase structure.

## Commands and environment

SDK: `/opt/homebrew/share/android-commandlinetools`; JDK17/21.
Emulators: `uphill_test` /5554 for fixtures; `uphill_playstore` /5556 holds the live
user session. Both processes exited during confirmation; userdata remains on disk.
Do not wipe either AVD. Boot/test5554 first; boot5556 only for read-only release smoke.
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
