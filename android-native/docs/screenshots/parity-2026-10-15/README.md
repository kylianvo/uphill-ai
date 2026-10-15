# Android emulator UI evidence — 2026-10-15

These captures run the production Compose app shell on `uphill_test` (Android 14),
using recorded iOS API fixtures served through real HTTP requests. They contain
fixture data, not a production account.

- `release-sign-in-en.png`: signed-out minified release smoke capture from checkpoint 6208d6d.
- `normal/`: sign-in, Plan, workout detail, Coach, Me, Goal, Gear, Nutrition, Pace,
  Knowledge, race history, month calendar/day preview and coach charts/roster; signed-in screens are captured in English and Vietnamese.
- `accessible/`: sign-in, the four main screens, calendar/day preview and coach charts/roster, with font scale
  1.3 and all three Android animation scales set to zero. Device settings are restored.

The workout sheet includes source-based metrics and execution steps. Nested tools
retain their originating tab selection. The earlier states include a completed Impeccable confirmation pass; the latest
Coach Hub/Profile batch has inspection evidence with final confirmation pending. The source of truth is current
SwiftUI code where older iOS screenshots differ.

This evidence covers the pictured states. It does not establish complete screen,
TalkBack, animation or device parity. Android uses its system font in place of SF Pro;
the launch title shares bundled Plus Jakarta Sans. The large-text workout pace value
now wraps between complete times, verified through rendered text layout. Titles and descriptions from the recorded
English backend fixtures retain their original language.

Current evidence contains 39 normal and 27 accessible captures, including Coach Hub
invite/overview/race rows and athlete Profile/preferences. These were inspected against
iOS Phase6/calendar references. They precede the final correction to sticky Profile
navigation, placeholder layout, status/email layout and VI weekly-caption auto-size.
The confirmation run was interrupted by emulator exits; confirmation remains pending.

Reproduce the normal captures from the repository root:

```sh
./android-native/gradlew -p android-native connectedDebugAndroidTest \
  -PuphillReleaseSigningForDebug=true \
  -Pandroid.testInstrumentationRunnerArguments.class=ai.uphill.app.VisualEvidenceTest \
  -Pandroid.testInstrumentationRunnerArguments.captureEvidence=true
```

PNG files are saved under `/sdcard/Download/uphill-evidence/normal/` on the emulator.
For accessible captures, set font scale 1.3 and animator/window/transition scales zero,
then add `-Pandroid.testInstrumentationRunnerArguments.captureVariant=accessible`;
restore the previous settings afterward.
