# Native Android app (Kotlin + Jetpack Compose), full parity with ios-native

## Context
Android today is the Capacitor web wrapper (`frontend/android`, `ai.uphill.app`, 1.0.4 / versionCode 5). iOS moved to a native SwiftUI app (`ios-native/`, 235 files, ~40k lines, phases through #124). Goal: a native Android app with the same features as iOS, talking to the same production backend, shipped as a signed APK that installs over the existing Capacitor app (sideload, no Play Store).

No backend changes are expected: every endpoint already exists and is used by iOS. The iOS app is the spec; the Android app copies its behaviour screen by screen.

## Decisions
- **Location**: new top-level `android-native/` (sibling of `ios-native/`). Capacitor `frontend/android` stays until the native APK replaces it, then is retired in a follow-up.
- **App identity**: `applicationId "ai.uphill.app"`, signed with the existing `uphill-release.keystore` (main checkout `frontend/android/keystore.properties`, gitignored, copy into worktrees). Start at `versionName 2.0.0`, `versionCode 10` so it upgrades in place over 1.0.x.
- **Stack** (mirrors iOS choices, minimal deps):
  - Kotlin 2.x, Compose + Material 3 (themed to our tokens, light only, portrait), minSdk 26, target/compile 36.
  - Single-activity, Navigation Compose; bottom bar Plan / Coach / Me (+ Athletes for coaches).
  - `ViewModel` + `StateFlow`, one VM per screen (= iOS `@Observable` VMs). Manual DI: one `AppContainer` built in `Application` (= `AppModel.swift`). No Hilt.
  - Networking: OkHttp + Retrofit + kotlinx.serialization (snake_case naming strategy), 30 s timeout, Bearer interceptor, 401 → sign out. SSE via OkHttp streaming body parser (port of `SSEStreamParser.swift`).
  - Token: EncryptedSharedPreferences / Keystore-backed DataStore (= Keychain). Settings, running job, chat (last 50/plan): DataStore. Offline cache of user + active plan: JSON files or Room single-table blob (= SwiftData `OfflineCache`).
  - Charts: Vico (Compose charts). Images: Coil, shoe/nutrition images bundled as drawables (copy from `Assets.xcassets`).
  - Google sign-in: Credential Manager + `googleid`, `serverClientId` = existing **web** client ID → ID token `aud` already accepted by backend `GOOGLE_CLIENT_IDS` (`backend/config.py:78`). Needs a new Android OAuth client in Google Cloud (package + release SHA-1) registered, nothing else. Apple sign-in: not on Android (email + Google only, same as Capacitor today).
  - COROS: Custom Tabs + `uphillai://coros/callback` intent filter (already used by Capacitor manifest), verify `state`, call `/api/integrations/coros/complete`.
  - Calendar export: share `.ics` from `/api/coach/export-ics` via FileProvider + `webcal://` intent (skip direct CalendarContract writes in v1).
  - GPX import: `ActivityResultContracts.OpenDocument`, port `GpxCourseParser.swift`.
- **Localization**: `values/strings.xml` + `values-vi/strings.xml` generated once from `ios-native/UphillAI/Resources/Localizable.xcstrings` (1,357 keys) by a script `android-native/scripts/xcstrings_to_android.py` (keys → snake ids, keep a mapping file). In-app language picker via `AppCompatDelegate.setApplicationLocales`; `lang` sent to backend like iOS. Fix the iOS spots that hardcode `isVietnamese ? … : …` as proper strings on Android. Review VI copy with the `uphill-ai-vietnamese-copy` skill.
- **Environments**: `BuildConfig` prod `https://api.uphill-ai.io.vn` for release; debug defaults to `http://10.0.2.2:8000` (emulator → host), switchable in a hidden dev menu (long-press version, = `DeveloperMenu.swift`). Release must never point at local — add a unit test asserting it.

## Project layout
```
android-native/
  app/src/main/java/ai/uphill/app/
    app/          AppContainer, MainActivity, RootNav, SessionGate   (ios App/)
    core/         networking, auth, models, persistence, plan, chat, generation,
                  goal, pace, gear, nutrition, racehistory, coaching, integrations,
                  knowledge, localization                             (ios Core/)
    designsystem/ Tokens.kt, Buttons, Cards, TrainingZoneBar          (ios DesignSystem/)
    feature/      plan, onboarding, coaching, chat, goal, gear, me, pace,
                  nutrition, racehistory, integrations, knowledge, auth, launch
  app/src/test/   JVM unit tests (MockWebServer + shared fixtures)
  app/src/androidTest/  Compose UI flow tests
  scripts/        xcstrings_to_android.py, build_release_apk.sh
```
Rule kept from iOS: `feature/*` depends only on `core` + `designsystem`.

## Phases (each = one PR, each ends with an installable debug APK + screenshots)

**Phase 0 — Skeleton & foundations**
Gradle project, version catalog, signing config reading `keystore.properties`, design tokens ported from `ios-native/UphillAI/DesignSystem/Tokens.swift` (colors, spacing, radii, Plus Jakarta Sans for launch title), `APIClient` + `APIError` (FastAPI `detail` string or `{code, params}`, 422 schedule-guard), JSON config, string resources script, CI workflow `.github/workflows/android-native.yml` (`./gradlew lint testDebugUnitTest assembleDebug`).

**Phase 1 — Auth, launch, shell**
Launch screen with looping `launch_bg.mp4` (Media3 ExoPlayer, respect reduced-motion via animator scale), email/password login + register, Google via Credential Manager, `/api/auth/me` restore with offline fallback to cached user, logout, bottom-nav shell, Me tab basics + language picker + dev menu.

**Phase 2 — Onboarding & plan generation**
Onboarding multi-step (`/api/auth/onboarding`, `/api/kb/match-race`, `/api/goal/assess`, fitness snapshot), `GenerationCenter` + `JobPoller` port (2 s poll, 240 s cap, 404 = lost, 5 failures = fail, persist running job so it resumes after process death).

**Phase 3 — Plan tab (largest: iOS Features/Plan 7.1k lines + Core/Plan 3.2k)**
Summary carousel charts, week switcher, day rows, workout detail (treadmill ranges, zones), mark done/missed + effort + notes, move/swap, adapt week, next block, week review, block evaluation, goal pill/sheet, manage/select/delete plan, schedule preferences + training venues, calendar grid, ICS export, watch matching, sharpen checklist with `TrainingDestination` deep jumps, offline read-only cache.

**Phase 4 — Coach chat**
SSE streaming (status/token/citations/tool_call/tool_result/clarify/done/error), retry_of, rich cards (gear, goal, nutrition, proposal), proposal poll (3 s / 240 s) + apply/discard, sources sheet, feedback, local history store.

**Phase 5 — Tools**
Goal Determiner + field-curve chart, Gear Vault + shoe rotation (600 ms debounced PUT), Nutrition Lab, Pace strategy (GPX import, elevation chart, splits), Knowledge Hub.

**Phase 6 — Race history, integrations, coaching**
Race history (search, claims, verify bib, manual add/edit, road PBs, race detail), connected accounts + COROS OAuth/sync/push + 15-min foreground auto-sync, coach mode (dashboard, roster, invites, athlete plan edit/approve, notes, AI-create workout).

**Phase 7 — Hardening & release**
Parity audit against iOS screen list, VI copy review, accessibility (TalkBack labels, font scale), R8/proguard rules for serialization, release APK via `scripts/build_release_apk.sh` (copies keystore, `assembleRelease`, verifies cert SHA-256 matches `10:04:51:3F…`, versionCode > 5), install-over-Capacitor test on a device with 1.0.5 installed, copy APK to `~/Desktop`.

## Reuse from iOS (port, don't redesign)
- Endpoint lists & request/response shapes: `ios-native/UphillAI/Core/*/…Service.swift`, `Core/Networking/Endpoint.swift`.
- Pure logic to port 1:1 with tests: `Core/Generation/JobPoller.swift`, `Core/Networking/SSEStreamParser.swift`, `Core/Pace/GpxCourseParser.swift`, `Core/Plan/ScheduleMessages.swift`, `Core/Plan/SharpenChecklist.swift`.
- Fixtures: `ios-native/UphillAITests/Fixtures/*.json` (26 raw backend responses) — point Android test resources at that folder via Gradle `sourceSets` so both apps decode the same JSON. Re-record with `ios-native/scripts/record_fixtures.sh`.
- Visual reference: `ios-native/docs/design-baseline.md` + `ios-native/docs/screenshots/`.

## One-time manual steps (user)
1. Google Cloud console: create Android OAuth client for `ai.uphill.app` + release SHA-1 (I'll print it from the keystore).
2. Confirm the `uphillai://coros/callback` redirect is what the backend sends for native clients (already true for Capacitor).

## Verification
- Every phase: `./gradlew lint testDebugUnitTest` green; fixture-decoding tests for every model; ported logic tests (poller, SSE, GPX, schedule messages) mirroring the iOS test cases.
- Every phase with UI: run on emulator against local backend (`docker compose up`, `10.0.2.2:8000`), screenshot each changed screen side by side with the iOS screenshot (CLAUDE.md UI evidence rule).
- Compose UI flow tests matching iOS UI tests: onboarding, plan flow, coach chat, race history, tool navigation.
- Release: install signed APK over Capacitor 1.0.5 on a real device, confirm session/login works against prod, Google sign-in, COROS connect round-trip, VI language switch.

## Out of scope (same as iOS today)
Health Connect, push notifications, widgets, Wear OS, Play Store listing, Apple sign-in, Facebook sign-in.
