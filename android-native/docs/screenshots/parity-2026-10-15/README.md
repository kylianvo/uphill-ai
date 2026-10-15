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
retain their originating tab selection. The pictured states passed the bounded Impeccable inspection/correction/confirmation workflow. The source of truth is current
SwiftUI code where older iOS screenshots differ.

This evidence covers the pictured states. It does not establish complete screen,
TalkBack, animation or device parity. Android uses its system font in place of SF Pro;
the launch title shares bundled Plus Jakarta Sans. The large-text workout pace value
now wraps between complete times, verified through rendered text layout. Titles and descriptions from the recorded
English backend fixtures retain their original language.

Current evidence contains **49 normal and 37 accessible captures**, including welcome,
goal selection, Road details, race date, shoe rotation, Coach Hub and athlete Profile.
The final bounded confirmation passed after correcting fixed Profile navigation,
placeholder/status layout and VI weekly-caption auto-size. New goal/date and rotation
states were inspected against current SwiftUI source. The old Phase2b goal screenshot
has obsolete choices; the current source's four choices are authoritative.

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
