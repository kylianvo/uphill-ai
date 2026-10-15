# Native Android handoff

Draft PR: https://github.com/kylianvo/uphill-ai/pull/127
Branch: `codex/android-native`; approved iOS reference base: `afa2893`.
Checkout: `/Users/vietvo/.codex/worktrees/android-native/uphill-ai`.
Plan: `docs/superpowers/plans/2026-10-14-android-native.md`.

## Current checkpoint — 2026-10-15

The user resumed work toward around 3% **weekly allowance remaining**. The previous
stop checkpoint was committed as `dea06bb`. This continuation fixes its CI lint issue,
completes the interrupted UI confirmation and adds the onboarding/rotation/Pace work below.
The user subsequently removed the usage stop threshold and authorized continued work.
No deployment or merge has been performed.
Health Connect stays deferred by explicit user decision. Google Android OAuth
registration is complete; the physical phone upgrade test is deferred.

The Kotlin/Compose port covers auth, onboarding/generation, Plan, coach chat,
Goal/Gear/Nutrition/Pace/Knowledge, race history, COROS and coaching.
Package `ai.uphill.app`, version 2.0.0/code10, min26/target36, existing signing key.
Full feature and visual parity are not yet established. Keep PR #127 draft.
All three GitHub test jobs passed at `69e166c`; its backend COROS lifecycle failure
passed on rerun without code changes. Fresh checks run for the next push.

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

## Continued Pace course pass

- A real Downloads GPX file is selected through Android's system document picker,
  read through ContentResolver and removed again. EN/VI device tests cover this path;
  test files are deleted in cleanup. No production account is used.
- Course configuration now follows the source import/loaded-file card, side-by-side
  distance/gain inputs, source interval choices and haptics. GPX-owned inputs are
  disabled until removal. The enabled-input regression was reproduced before fixing.
- Import initializes the target with iOS's bounded course estimate; changing interval
  reparses checkpoints while preserving a runner-edited target. Both regressions were
  reproduced before the fix. Integer gain/distance display follows the source.
- Normal and font1.3/zero-animation EN/VI captures were inspected and the single
  correction batch confirmed. Pace controls/results/chart parity remains separate work.
- Final GPX tests passed twice (normal 6.356s, larger text 5.622s). Standalone app-shell
  capture passed in68.106s. Logs: `/tmp/uphill-pace-final-gpx-device.log`,
  `/tmp/uphill-pace-final-accessible.log`, `/tmp/uphill-pace-final-visual.log`.
  The earlier combined capture was interrupted by an external UI hierarchy probe;
  avoid running `uiautomator dump` while instrumentation owns UiAutomation.

## Continued search and session recovery pass

- Knowledge Hub now searches key points as well as title, summary and tags. Whitespace
  searches keep all cards and hide Daily Insight like iOS; topic filtering still applies.
  A failing device regression reproduced the omitted key point, then passed after the fix.
  Evidence: `normal/knowledge-keypoint-search-en.png` uses a synthetic sodium-only point.
- Session restore now keeps the token after HTTP/decoding/server errors and network
  failure without a cached user. Only unauthorized restore clears the session. A cached
  user still supports offline restore. Errors clear on retry/success/sign-out; cancellation
  propagates. Two failing JVM regressions reproduced token loss before the fix.
- RootNav presents the source-based launch error and Try again action. HTTP fallback
  status messages use the existing EN/VI catalog. The device tests exercise503→200,
  retained Authorization header, localized retry and successful restoration in EN/VI.
  Three selective flows passed (including search) in11.11s. Final NativeFlow:
  **28 tests passed in55.376s** (`/tmp/uphill-recovery-final-native.log`). EN/VI
  font1.3/zero-animation retry checks passed in3.899s
  (`/tmp/uphill-recovery-accessible.log`); settings restored. No new translations.
- This source difference could cause sign-out after a transient error. No evidence
  attributes the earlier unexplained cold-boot sign-out to this cause.
- Latest signed release includes this pass: build passed in1m31s, certificate/package/
  version verified (`/tmp/uphill-recovery-signed-release.log`). The Desktop APK is
  refreshed. GitHub checks at the prior Pace checkpoint `e2bf53a` all passed.

## Continued Knowledge Hub presentation

The Knowledge Hub follows the current SwiftUI header/search, daily widget,
topic icons/pills/counts, full-card expansion with tags, empty state and source rows.
Training cards use16dp; the daily wrapper uses12dp. Card motion maps the source
.3s/.8 spring to stiffness440/damping.8; sources use320/1. Reduced motion skips
transitions. Search includes key points and treats whitespace as an empty query.

EN/VI source503→retry checks retain the URL on failure and clear it on success.
Knowledge retains typed exceptions and localizes fallback errors beside the form.
The source form is admin-only, matching `/api/rag/link` authorization; signed-in
readers can browse attribution without an unusable ingestion control. This deliberately
corrects the iOS form's unconditional visibility. No backend changes were needed.
The inherited VI count said “comments”; a feature string now says “knowledge cards”.

The first batched inspection found a wrapping URL placeholder and incomplete keyboard
framing in direct-screen test captures. The placeholder now truncates to one line.
A shared test-only AppFixture mirrors MainActivity's Theme/Surface/safeDrawingPadding;
Native, GPX and visual tests now use the app's inset handling. No production keyboard
policy was changed. Whole-card scroll targets frame expansion/empty/source evidence.

## Requested body-font change

The user supplied `ios-native/UphillAI/Resources/Fonts/PlusJakartaSans.ttf` and chose
Plus Jakarta Sans for Android body text, with platform `FontFamily.Monospace` for mono.
Android already bundled the exact same file as `res/font/plus_jakarta_sans.ttf`.
Its variable `wght` axis is200–800 (default400). The theme explicitly maps each
100-weight step with FontVariation.weight; all Material typography slots, launch,
calendar BasicText and native Canvas chart labels use it. Existing mono overrides
remain platform-specific. This is the user's body-face choice, not an exact match to
iOS's system body face. System mono glyphs can also vary by Android device.
Font SHA-256: `89b3fb38aa0d275d7a731d0d817a4f1622b316b4d7fbdedcf02ee9099ff68bc8`.

## Focused keyboard and launch hardening

MainActivity now uses `adjustResize`; the debug Compose test activity uses the same
window policy. Existing safeDrawingPadding and scroll containers can then respond to
the keyboard. A larger-text VI regression reproduced expanded text bottom1720px
below keyboard top1517px before the fix (`/tmp/uphill-keyboard-before2.log`).
The regression now checks actual text bounds against the keyboard-visible window,
including the empty-search guidance. Search explicitly opens the keyboard before it.

Media3 PlayerView's default black loading shutter now uses UH.surface, matching the
launch background while the first video frame loads. This addresses the observed
dark loading frame; the complete video loop/other devices remain unverified.

**Latest focused verification:** four EN/VI Knowledge and session-retry flows passed
at font1.3 with animations disabled in43.204s (`/tmp/uphill-keyboard-focused.log`).
Two affected-state screenshots were inspected in one batch; six existing accessible
captures were refreshed. Settings restored;5554 closed before release packaging.
No full simulator matrix or new live-account run was repeated for this small change.

**User workflow preference:** continue with Ponytail and Impeccable, minimizing
simulator/screenshot token use. Compare source first, use targeted regressions and a
small changed-state evidence batch; reuse unchanged captures. No repeated full sweeps.

## Continued Pace controls

The controls now follow the source's target-time/strategy grouping: formatted target
with a five-minute slider, source bounds, split-bias slider/labels, and weight/start
fields side by side. Duplicate target entry and strategy chips are removed. The
course and control cards share the source16dp radius. Existing request, GPX target
initialization, edited-target preservation and Goal handoff behavior are retained.
New strategy descriptions have EN/VI resources; VI uses plain energy-economy wording.

Only three targeted device flows were run at font1.3/zero animation: Goal handoff and
strategy thresholds (1.800s), plus real EN/VI GPX picker/target preservation (6.927s).
Logs: `/tmp/uphill-pace-controls-{goal,gpx}.log`. Two controls captures were inspected
in one batch and added. One copy correction replaces generic VI captions with the
source-specific Thận trọng/Đều/Tấn công. Only the VI GPX flow was repeated (3.917s,
`/tmp/uphill-pace-copy-confirm.log`) and its control card confirmed. No broader
retest sweep was run. Device settings restored.
Benchmark placement/lookup, automatic initial calculation, summary/chart/split results
and broader error/state parity remain. Do not call the entire Pace feature visually complete.

## Verification and artifact freshness

The broad test baseline below is font checkpoint `39dfca4` (all three CI jobs green).
Artifact/evidence entries include the subsequent focused changes described above.
The subsequent keyboard/shutter change uses the focused checks above. Release lint
and release unit tests are also run by the packaging script.


- **Lint, all 93 debug and 93 release JVM tests passed.** Converter four tests passed; catalog has
  1,469 EN/VI entries. `git diff --check` passed.
- **35 instrumentation tests passed across isolated runs**: 32 NativeFlow tests, two real GPX picker tests, and app-shell capture.
  The font update reruns this matrix plus seven selected larger-text native tests,
  both GPX flows and app-shell capture. Normal:32 tests/140.234s, GPX2/17.510s,
  shell1/68.100s. Larger text:7 selected native/20.388s, GPX2/7.677s, shell1/23.791s.
  Logs: `/tmp/uphill-font-{normal,accessible}-*.log`. The single font correction
  truncates the search hint to one line; five Knowledge regressions and shell capture
  passed in each variant afterward (`/tmp/uphill-font-confirm-*.log`).
  The main flow wait was updated from42.0 to42 for source-based integer formatting;
  the selected 360-minute target assertion is retained.
- **68 normal +60 font1.3/zero-animation fixture captures** refreshed and visually
  confirmed. Profile navigation remains visible, VI `km/tuần` stays on one line, and
  onboarding/calendar controls fit the inspected states. Accessible capture passed in
  32.306s: `/tmp/uphill-latest-accessible-confirm.log`; settings restored.
- The CI lint error was a test reading configuration through LocalContext. It now
  reads LocalConfiguration; local lint passes. The fixed Profile header also required
  removing an obsolete scroll action from the screenshot helper.
- The latest signed/minified release includes Knowledge presentation, the requested
  variable body font, keyboard/shutter hardening and Pace controls. Certificate/package/version are checked by the release script;
  `/Users/vietvo/Desktop/Uphill-AI-2.0.0.apk` is refreshed after the font confirmation.
  Font checkpoint release passed in2m12s: `/tmp/uphill-font-published-release.log`.
  Keyboard/shutter release passed in1m18s: `/tmp/uphill-keyboard-release.log`.
  Latest Pace release passed in1m2s: `/tmp/uphill-pace-controls-copy-release.log`. The font OFL notice is
  packaged as an asset so resource shrinking retains it. Preserve5556's data when
  installing over it; only the static authenticated-shell result is recorded.
  At font checkpoint39dfca4, install-over and explicit cold launch on5556 restored the authenticated
  shell. The monkey shortcut returned251; explicit `am start -W` succeeded in871ms.
  No account data was cleared or production screenshot saved.
  The latest APK is refreshed on Desktop but is not reinstalled on5556;
  the change does not touch session storage or networking.
- The first cold boot opened signed out for an unknown reason. After a fresh Google
  login on the latest APK, controlled force-stop/relaunch, matching-signed APK
  replacement/relaunch and full emulator reboot all restored the authenticated
  Plan/Coach/Me shell. No app data was cleared or instrumentation run on5556.
  This verifies those controlled persistence paths without attributing the earlier state.
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

1. Continue `docs/PARITY.md`: all setup/result/sheet/error
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
In the continuation, 5556 passed controlled session persistence through full reboot;
5554 was restarted for isolated GPX and screenshot checks. Keep its settings restored.
The Gradle UI runner can uninstall main/test APKs; use the explicit5554-only manual
instrumentation commands in the capture index for account-safe fixture checks.
The owned live backend is now stopped. It used port8016 and isolated database `uphill_android_native_oct15`
on the local PostgreSQL container at port5433. Source is this worktree; runtime is
main checkout's backend virtualenv. No real Gemini key is configured. Launch helper:
`/tmp/uphill-native-local-backend.py`; log: `/tmp/uphill-native-local-backend.log`.
Port8000 belongs to unrelated work; do not stop or reuse it.

From the checkout:
```sh
./android-native/gradlew -p android-native lint testDebugUnitTest testReleaseUnitTest assembleDebug -PuphillReleaseSigningForDebug=true
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
