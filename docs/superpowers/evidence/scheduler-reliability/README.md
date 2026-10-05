# Scheduler prescription screenshots

Captured 2026-10-04 through the running local Next.js app and isolated backend on port 18010, against Docker `uphill_ai_test` on port 5433. Invented user and plan only; no integration tests or truncations. The screenshots show deterministic accounting examples seeded through `db.save_workouts`, not an independently verified ME training protocol.

| State | EN | VI |
| --- | --- | --- |
| Mixed session, desktop | [EN](mixed-session-en-desktop.jpg) | [VI](mixed-session-vi-desktop.jpg) |
| Mixed session, mobile | [EN](mixed-session-en-mobile.jpg) | [VI](mixed-session-vi-mobile.jpg) |
| Treadmill, desktop | [EN](treadmill-en-desktop.jpg) | [VI](treadmill-vi-desktop.jpg) |
| Treadmill, mobile | Covered by mixed-session mobile layout | [VI](treadmill-vi-mobile.jpg) |

Actual capture widths: 1280 px desktop, 390 px mobile. Scrolled the app's content panel to include the relevant card and prescription. Temporary viewport override reset.

Mixed example: 12-minute moving Warm-up + 24-minute strength segment + 6-minute moving Cool-down = 42 minutes and 3 km locomotion. The named exercise keeps 3 x 8 and 75 s rest in both languages. Treadmill example: 30 minutes at actual belt pace 6:00/km and 10% incline = 5 km, 10 kph, estimated indoor ascent 498 m. VI preserves the estimate caveat and all quantities; technical terms remain English. No visible wrapping/truncation problem in the changed instructions.

Running-app inspection exposed the generic library replacing resolved instructions with invented default Warm-up, exercises and Cool-down. Resolved instructions now display directly, and their surface cannot be switched into an unprescribed alternative. Two visible VI planner strings were corrected to `khối lượng tuần` and `plan`; EN strings unchanged. Legacy descriptions retain their existing library path.

Validation: 456 frontend tests passed; build passed; lint 0 errors, 131 existing warnings. Changed VI strings and resolved samples reviewed against R1–R6. Other legacy VI copy outside this scoped view still has skill violations; this is not a global copy audit.

Cleanup: removed exactly synthetic user 8 and plan 1, including their sessions/workouts; stopped both preview servers. No developer or staging data changed.
