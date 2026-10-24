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
TalkBack, animation or device parity. The user chose bundled variable Plus Jakarta Sans for body and launch text;
mono uses FontFamily.Monospace. This differs from the iOS system body face. The large-text workout pace value
now wraps between complete times, verified through rendered text layout. Titles and descriptions from the recorded
English backend fixtures retain their original language.

Current evidence contains **68 normal and 60 accessible captures**, including welcome,
goal selection, Road details, race date, shoe rotation, Coach Hub and athlete Profile.
The final bounded confirmation passed after correcting fixed Profile navigation,
placeholder/status layout and VI weekly-caption auto-size. New goal/date, rotation and Pace course/imported-GPX
states were inspected against current SwiftUI source. The old Phase2b goal screenshot
has obsolete choices; the current source's four choices are authoritative.

Reproduce captures on the fixture emulator **5554 only**. Preserve5556's real account.
Build and install explicitly, then run each class separately; avoid external
`uiautomator dump` commands while instrumentation owns the accessibility connection.

```sh
./android-native/gradlew -p android-native assembleDebug assembleDebugAndroidTest \
  -PuphillReleaseSigningForDebug=true
adb -s emulator-5554 install -r android-native/app/build/outputs/apk/debug/app-debug.apk
adb -s emulator-5554 install -r android-native/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
for evidence_test in NativeFlowTest GpxImportFlowTest VisualEvidenceTest; do
  adb -s emulator-5554 shell am instrument -w \
    -e class ai.uphill.app.$evidence_test -e captureEvidence true \
    ai.uphill.app.test/androidx.test.runner.AndroidJUnitRunner
done
```

PNG files are saved under `/sdcard/Download/uphill-evidence/normal/` on the emulator.
For accessible captures, set font scale 1.3 and animator/window/transition scales zero,
then add `-e captureVariant accessible` to the instrumentation call;
restore the previous settings afterward.

The `pace-course-*` and `pace-gpx-*` captures exercise the real Downloads document
picker with a synthetic GPX file, including imported-field locking and source-based
target initialization. These dedicated Pace captures omit the app shell bottom bar;
`normal/pace-*` captures show the route inside the app shell. The normal/large-text
confirmation includes EN/VI imported metadata and integer gain formatting. Runner
weight, pacing controls, profile charts and split results still need broader iOS comparison.

`knowledge-keypoint-search-en.png` demonstrates matching only a card key point with
mixed-case input. `session-restore-error-en/vi.jpg` shows the localized503 retry state
at normal and font1.3/zero-animation settings. The device checks verify that retry
preserves the token and restores the user; fixture responses contain no real account.

The photo-heavy launch video captures are exported as quality95 JPEG at the original
1080×2400 size to meet the repository file-size limit; other captures remain PNG.

Knowledge captures include full-card expansion/tags, empty search, source503 retry,
success and a reader-only attribution list. Admin-only ingestion matches backend
authorization. Normal and larger-text captures use the same Surface/inset wrapper
as MainActivity. The focused window-sizing fix now verifies expanded tags and empty-search guidance
above the open keyboard at font1.3 in EN/VI.

The latest captures use the user-selected Plus Jakarta Sans variable body face
(weights200–800), including chart and calendar labels. System mono remains explicit.

Font confirmation passed after constraining the search hint to one line with an
ellipsis. Logs: `/tmp/uphill-font-confirm-{normal,accessible}-{NativeFlowTest,VisualEvidenceTest}.log`.
The original normal launch retry evidence caught a dark loading frame. The loading
shutter now matches the app surface; the updated accessible retry capture is readable.
The full video loop and other devices remain outside this focused check.

Latest focused update: six accessible expansion/empty/retry captures reflect the
keyboard/shutter fix. Unchanged captures, including normal/, remain font baseline
39dfca4. Four targeted flows passed in43.204s (`/tmp/uphill-keyboard-focused.log`);
only the expanded-card and retry captures were inspected in this pass.

`accessible/pace-controls-en/vi.png` shows the source-based target/strategy card with
five-minute target steps, split bias and side-by-side weight/start fields. Only three
related device flows were run for this update; two captures were inspected once.
Pace results/charts/benchmark layout remain outside this pass.

The Pace pass used one copy correction and one VI-only confirmation: source-specific
Thận trọng/Đều/Tấn công captions replace ambiguous shared translations. The GPX
confirmation passed in3.917s; other screens and flows were not recaptured.

`normal/pace-auto-calculation-en.png` is the only new capture in the release review.
The targeted flow first asserts Race summary appears without tapping Calculate, then
confirms the incoming Goal target and all three strategy thresholds. It passed in7.228s;
EN/VI GPX checks passed in11.653s. No other captures were refreshed. Collection total:
129 (69 normal +60 accessible). This is not a full result/chart parity audit.
