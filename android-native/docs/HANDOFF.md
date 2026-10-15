# Native Android handoff

Draft PR: https://github.com/kylianvo/uphill-ai/pull/127
Branch: `codex/android-native`; approved iOS reference base: `afa2893`.
Checkout: `/Users/vietvo/.codex/worktrees/android-native/uphill-ai`.
Plan: `docs/superpowers/plans/2026-10-14-android-native.md`.

## Current checkpoint — 2026-10-15

The user resumed work toward around 3% **weekly allowance remaining**. The previous
stop checkpoint was committed as `dea06bb`. This continuation fixes its CI lint issue,
completes the interrupted UI confirmation and adds the onboarding/rotation work below.
The user subsequently removed the usage stop threshold and authorized continued work.
No deployment or merge has been performed.
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
  physiology Edit header and a wrapping status/email row. The bounded confirmation passed.

## Resumed onboarding and rotation pass

- iOS's four goal cards: Trail race, Road race, Distance and Getting started. Race
  selection carries its terrain into details; the old Return/Recovery model cases
  remain, as in iOS, but are not exposed on this first page. Current SwiftUI source
  wins over the obsolete five-choice Phase2b screenshot.
- Coaching guidance banner on each setup step; source-based page titles. The setup
  header has Back/progress/Close, hides the unused Goal footer and resets the form
  scroll on step changes. Close returns an onboarding user to Welcome.
- Graphical race/start calendars replace typed dates. Race dates start at today+14;
  start dates respect today through the existing latest-start rule. UTC day conversion
  avoids timezone shifts; a device regression checks both bounds and selection.
- Empty shoe slots display a neutral licensed sneaker vector instead of a product
  photo. Assigned-shoe imagery stays; wear percentage and bar share warning/danger
  colors. Slot action regression passes. Icon licensing: `android-native/licenses/`.

## Verification and artifact freshness

- **Lint, all 91 debug and 91 release JVM tests passed.** Converter four tests passed; catalog has
  1,469 EN/VI entries. `git diff --check` passed.
- **26 instrumentation tests passed**: 25 native UI flows and normal screenshot
  capture. Log: `/tmp/uphill-latest-device-confirm.log` (161.128s).
  Includes Profile editor/general notes, inline invite/race filtering, Road selection,
  empty slots, calendar caption and date-window regression.
- **49 normal +37 font1.3/zero-animation fixture captures** refreshed and visually
  confirmed. Profile navigation remains visible, VI `km/tuần` stays on one line, and
  onboarding/calendar controls fit the inspected states. Accessible capture passed in
  32.306s: `/tmp/uphill-latest-accessible-confirm.log`; settings restored.
- The CI lint error was a test reading configuration through LocalContext. It now
  reads LocalConfiguration; local lint passes. The fixed Profile header also required
  removing an obsolete scroll action from the screenshot helper.
- Latest signed/minified release build passed in 1m22s after closing the fixture
  emulator. Log: `/tmp/uphill-latest-signed-release.log`. Certificate, package and
  version verified; `/Users/vietvo/Desktop/Uphill-AI-2.0.0.apk` includes this pass.
- The cold-boot/replacement smoke on5556 opened signed out. This does not establish
  session preservation; the cause is not yet known. Earlier live Google login passed.
  The user is signing in again for a controlled force-stop/replacement check.
- Earlier isolated live-backend flow passed; Docker and port8016 are now stopped, so
  this continuation used fixtures. No backend/service contract changes were made.
  Earlier backend tests: 1,265 passed plus ten targeted profile/auth tests. The two
  included backend profile fixes remain **not deployed**.
- Earlier signed release passed live Google sign-in and existing COROS Sync now with
  the user. No production credentials, health counts, account details or screenshots
  are committed. Fresh COROS OAuth and physical-phone upgrade remain unverified.
- Earlier Capacitor1.0.5/code6 → matching-signed native debug code10 upgrade preserved
  an app-private marker. Whole-branch final review at the earlier checkpoint fixed
  suggested watch completion and omitted AI intent with regression coverage.

## Remaining work, in order

1. Finish the controlled authenticated session-restore smoke on `uphill_playstore`
   (5556). Preserve its real session: no instrumentation, uninstall or data clear.
   Then continue `docs/PARITY.md`: all setup/result/sheet/error
   states, TalkBack, full motion and other OS versions still need comparison. The
   pictured states establish bounded evidence, not complete iOS parity.
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
user session. Earlier processes exited during a concurrent build; userdata remained on disk.
This continuation cold-booted/tested5554 successfully, restored settings and closed it
before R8. Do not wipe either AVD; boot 5556 only for read-only release smoke.
UI runner uninstalls main/test APKs; reinstall before standalone smoke checks.
The owned live backend is now stopped. It used port8016 and isolated database `uphill_android_native_oct15`
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
