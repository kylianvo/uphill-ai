# Native Android handoff

Branch `codex/android-native`; base `afa2893` (approved iOS reference).
Checkout `/Users/vietvo/.codex/worktrees/android-native/uphill-ai`.
Plan `docs/superpowers/plans/2026-10-14-android-native.md`.

## Status

Initial Kotlin/Compose port covers all planned feature areas. Backend unchanged.
Package ai.uphill.app, 2.0.0/code10, min26/target36. This is a draft: complete behavior
and visual parity have NOT been verified. The user asked for PR/handoff at 15% account
allowance remaining, physical phone testing later, and Impeccable to match iOS design.
Handoff threshold reached: 15% five-hour allowance remaining, 55% weekly. Feature work stopped for the requested PR/handoff.

Latest UI pass aligns shared palette/type metrics/buttons/reduced motion/launch, Plan
hierarchy/carousel/day rows and grouped Me/profile editors/achievements/shoe rotation.
Android system face replaces iOS SF Pro; launch uses identical bundled Plus Jakarta Sans.
Do not claim exact font rendering or complete UI parity.

## Verified

- Translation converter: four tests passed; 1,426 EN/VI keys; no missing literal L/P/TT keys.
- Pre-design final check: lint, 60 debug JVM + 60 release JVM tests, seven emulator UI flows
  passed (`/tmp/uphill-android-final-flows.log`). Includes live proposal objects and rebuild
  draft/apply regressions.
- Independent contract review found five issues; all fixed/rechecked: proposal object
  crash, rebuild diff schema, pacing fields, full bearer export in webcal intent, unreachable
  athlete Plan. ICS sharing remains; subscription removed pending calendar-only credentials.
- Exact Capacitor1.0.5/code6 → native2.0.0/code10 matching-signed debug upgrade passed on
  emulator without uninstall; app-private marker survived. Physical phone is deferred.
- Latest design sources compiled. Its UI discovery failed on adb property timeout:
  `No compatible devices connected`; no UI cases ran (`/tmp/uphill-android-design-checks.log`).
  Cold restart in `/tmp/uphill-android-emulator-final.log`.
- Added eighth UI case: schedule edit enables changed-only rebuild and confirms it.
  Post-design eight-case rerun remains outstanding.
- Final release check initially failed on Media3 zoom API opt-in; the opt-in was added.
  Rerun is `/tmp/uphill-android-handoff-release.log`: inspect final exit.
  Earlier certificate inspection matched Capacitor exactly. Script now handles build-tools37
  `V2 Signer` output as well as older `Signer #1` output.
- Screenshots in docs/screenshots PRECEDE latest design changes. plan-en.png is a loading
  state. Replace captures; they are not final parity evidence. Impeccable detector returned
  []; native screenshot verification is still required.

## Resume

1. Boot emulator-5554; run lint/testDebugUnitTest/testReleaseUnitTest/assembleDebug/
   connectedDebugAndroidTest with `-PuphillReleaseSigningForDebug=true`; inspect results.
2. UI runner uninstalls main APK afterwards. Reinstall signed debug, then capture all major
   screens/states EN/VI, font_scale1.3, animator scale0; restore settings. Compare current
   iOS sources/screenshots. Impeccable requires batched inspection + one correction round.
3. Check dedicated Schedule sheet: current-week rebuild with fatigue medium, confirmation,
   changed-only button. ScheduleDraft properties now observable for validation/button updates.
4. Remaining source parity gaps: acting-as-coach add workout on scoped Plan; formatted
   goal-time pill; full coach fallback/takeaway narrative; embedded connected-account controls
   in Me; rich-card completeness; tool layouts and larger-font behavior. Audit behaviors.
5. Run scripts/build_release_apk.sh for final source, inspect cert/code and Desktop APK,
   install minified release on emulator. Final release URL is production; avoid fictional
   test-account writes to production.
6. User completed Google OAuth registration. Live Google/COROS rounds and physical-device
   upgrade remain manual. Keep PR draft until parity/verification pass. This consolidated
   draft does not fulfill the original one-PR-per-phase review structure.

## Runtime and choices

SDK /opt/homebrew/share/android-commandlinetools; JDK17/21. uphill_test/emulator-5554
cold host-GPU. Failed uphill_native_port AVD never booted due to space; leave unrelated
files alone. Backend8000 uses isolated uphill_android_dev DB in existing local Postgres
container ios-app-feasibility-c6b160-postgres-1 (host5433). Extra chat-owned backend8015
can be stopped; other stacks/backend8014 belong to other work. No prod DB touched.
Evidence user3 android-evidence@uphill.ai / development-only AndroidEvidence123;
21-workout plan, onboarding now complete. Local no-Gemini backend uses fallback mode.
/tmp/uphill-native-evidence.py reads UI/taps/captures; /tmp/uphill-android-ui.py logs in.

Keystore AES-GCM; DataStore settings/chat; file jobs/cache; Canvas charts; direct OkHttp
(unused Retrofit removed). No Capacitor token migration: upgraded users may need login.
Release production fixed, debug10.0.2.2:8000 with hidden environment menu. Release-signed
DEBUG only via explicit property. Ignored signing props reference main-checkout keystore.
Never commit keys/APKs/private tokens/local.properties/keystore.properties. Dynamic
strings/tool images retained during shrinking. HealthConnect/push/widgets/WearOS/PlayStore/
Apple/Facebook auth excluded. Phone test explicitly deferred by user.
