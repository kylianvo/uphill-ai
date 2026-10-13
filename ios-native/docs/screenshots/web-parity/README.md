# Native iOS web parity evidence

Real SwiftUI views rendered in the iPhone 18 Pro / iOS 27.0 simulator with controlled local test data. No live backend or production account is used. Captures are 402 points wide; taller captures expose the next-block submit action and pace benchmarks below the fold.

| State | English | Vietnamese |
| --- | --- | --- |
| Block evaluation | [EN](next-block-evaluation-en.png) | [VI](next-block-evaluation-vi.png) |
| Coach block guidance | [EN](coach-next-block-en.png) | [VI](coach-next-block-vi.png) |
| Wrong watch run | [EN](workout-wrong-run-en.png) | [VI](workout-wrong-run-vi.png) |
| Watch run picker | [EN](watch-match-picker-en.png) | [VI](watch-match-picker-vi.png) |
| Watch picker: empty | [EN](watch-match-empty-en.png) | [VI](watch-match-empty-vi.png) |
| Watch picker: offline/retry | [EN](watch-match-failed-en.png) | [VI](watch-match-failed-vi.png) |
| Coach Manage guards | [EN](coach-manage-en.png) | [VI](coach-manage-vi.png) |
| Coach workout guards | [EN](coach-workout-en.png) | [VI](coach-workout-vi.png) |
| Pace benchmarks | [EN](pace-benchmarks-en.png) | [VI](pace-benchmarks-vi.png) |

Reviewed every EN/VI capture for wrapping, clipping, contrast and missing content. The benchmark labels remain visible; watch dates follow the selected language; unsupported coach controls are absent or disabled. New Vietnamese strings preserve technical terms and fit within the English source length. Backend evaluation narrative remains English.

Reproduce from the repository root:

```bash
touch ios-native/docs/screenshots/web-parity/.capture-enabled
DESTINATION='platform=iOS Simulator,name=iPhone 18 Pro,OS=27.0' ios-native/scripts/test.sh -only-testing:UphillAITests/WebParityScreenshots -parallel-testing-enabled NO
rm ios-native/docs/screenshots/web-parity/.capture-enabled
```

`SCREENSHOT_DIR` also works when forwarded into the test process. The local marker is an opt-in fallback for Xcode runners that drop environment variables. Remove the marker before normal unit runs so screenshot rendering and its temporary language changes remain isolated.

Final unit validation: `ios-native/scripts/test.sh -only-testing:UphillAITests -parallel-testing-enabled NO` on iPhone 18 Pro / iOS 27.0 passed 432 tests in 68 suites. Regression coverage includes unsupported coach actions, delayed plan/goal responses, generation completion after leaving an athlete view, watch-run replacement, preserved watch details and overlapping foreground sync.
