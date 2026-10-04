# Resolved workout display evidence

Captured on 2026-10-05 (Australia/Sydney) from the local running app, using only synthetic accounts in `uphill_ai_test`. Screenshots use existing Execution/About tabs and the timeline. The fixture is a 75-minute mixed Treadmill/Strength session from the retained v7 evaluation, rendered through the updated prescription resolver; this is UI evidence, not a v8 model result.

- [EN desktop ranges](resolved-treadmill-en-desktop.jpg)
- [EN desktop session and fueling](resolved-treadmill-en-desktop-details.jpg)
- [EN mobile ranges](resolved-treadmill-en-mobile.jpg)
- [VI desktop session and fueling](resolved-treadmill-vi-desktop.jpg)
- [VI mobile ranges](resolved-treadmill-vi-mobile.jpg)
- [VI mobile session and fueling](resolved-treadmill-vi-mobile-details.jpg)

The card retains whole-session distance, complete speed/grade ranges, exact resolved ascent and named exercise targets. The Main Set does not repeat whole-session distance. Fueling uses the existing application bands and total session duration; it adds no physiological threshold claim. EN/VI retain the same quantities and caveats; Carbs, Sodium, Treadmill and Strength remain technical terms.

Verification: frontend 462 tests passed; static build passed; lint 0 errors and 131 existing warnings. Synthetic users 11/12, plans 4/5 and their sessions were deleted after verification. Owned preview servers stopped, preview tab closed and viewport reset. No integration tests or truncation.
