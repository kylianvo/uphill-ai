# Native Android parity inventory

Reference: approved iOS base `afa2893`; latest iOS main inspected at `5597527`
(2026-10-15). Health Connect remains excluded by explicit user decision.
This inventory separates implemented behavior from verified visual parity. A matching
service or a passing fixture test does not establish matching layout or animation.

| Area | Android implementation / evidence | Remaining parity work |
| --- | --- | --- |
| Auth, launch, shell | Email/register, Credential Manager, secure session restore, video launch, Plan/Coach/Me/Athletes routing; sign-in and nested-tab evidence | Live signed-release Google round trip passed; transient restore errors now keep the token and offer localized retry; compare launch/video timing, dark-frame error contrast and remaining auth/error states |
| Onboarding and generation | Four source-based goal cards, guidance, Back/Close/progress, bounded UTC-day date pickers, persisted job polling and generation; Road/Close/date-window tests | Compare all EN/VI steps and failure/resume states with iOS; inspect newer iOS setup changes |
| Plan summary and day list | Carousel, weeks, goal pill, coach review, sharpen checklist, workout actions; EN/VI normal/large-text captures | Compare all chart/data variants, row types, transitions and empty/offline states |
| Workout detail | Metrics, execution timeline, treadmill ranges, reasons/warnings, feeling/log confirmation, scoped coach actions/notes | Pace range formatting and font1.3 rendering check pass; remaining type/interval/rest/coach variants need evidence |
| Plan management | Move/swap, adapt/next, schedule, review, goal, select/delete, ICS sharing; mutation flow tests | Sheet-by-sheet UI/state comparison; direct calendar writes deferred, token-bearing webcal removed |
| Month calendar | Latest iOS #134 month model and weekly bars/day preview ported; day-to-week emulator flow passes | Next/Today/swipe/day-to-week and haptic checks pass; refreshed EN/VI/larger-text evidence inspected; weekly-column label, Open Week styling and VI single-line caption confirmed |
| Coach chat | SSE, proposals/rebuild/apply, rich cards, clarification, citations, feedback, persistent history; contract/UI tests | Compare every rich-card/source/proposal/error/streaming state and motion |
| Me/profile | Grouped profile, PBs/badges/rotation, settings, language, COROS, developer menu | Authenticated release round trip; backend notes/key-preservation fixes need deployment; compare every editor |
| Goal | Assessment/context toggles, race search, field curve, tiers, pacing handoff | Result-state chart/layout and every context card comparison |
| Gear | Recommendation packshots, preferences, rotation assignment/edit/mileage/retire, debounced saves; neutral empty slots and wear colors tested/captured | Compare recommendation/rotation/detail layouts and latest iOS rotation changes |
| Nutrition | Fueling preferences, catalog/results and feedback | Result-state composition and product/copy comparison |
| Pace | GPX picker/parser, course profile, splits/checkpoints, debounced calculation, target handoff; real Downloads picker EN/VI checks, source course card and locked GPX fields | Source-based GPX target initialization and edited-target preservation through interval changes verified; result/chart/table, defaults and automatic recalculation comparison remains |
| Knowledge | Source header/search, daily widget, topic pills/count, full-card expansion/tags, empty state and source accordion; EN/VI key-point, retry and role checks | Larger-text expanded/empty search content can extend beneath the open keyboard; broader loading/focus/TalkBack states remain |
| Race history | Search/claims/bib verification, manual results/edit/delete, detail/PBs/badges; fixture/UI tests | Compare every link/claim/detail/course state against iOS |
| Coaching | Roster/invites, overview/actions, athlete physiology/provenance, scoped plan/actions/notes; live backend flow | Adherence chart, seven-day bars, workout mix, Overview/Roster sections, 7/14/30-day and Elite filters, roster search ported and tested. Inline invite, action counts, roster progress, race-to-roster search and separate Profile sheet ported, tested and visually confirmed. Remaining state/motion comparison pending |
| COROS | Custom Tab callback/state, sync/push/status, foreground sync and manual matching | Existing live COROS sync passed; fresh OAuth/push and cancellation/error flows unverified; Health import excluded |
| Accessibility/motion/fonts | Font1.3 and zero-animation captures, shared tokens, variable Plus Jakarta Sans body/launch and platform mono | TalkBack and all focus/error states; full motion audit; user-chosen body font differs from iOS system face; platform mono differs by device |
| Release | Matching certificate/code10, earlier emulator upgrade preservation, minified signed-out smoke, earlier CI green at842a7c0; dea06bb test-lint error fixed locally, fresh signed build verified | Signed minified Google sign-in and existing COROS sync passed; physical phone upgrade, fresh COROS OAuth and all remaining release flows unverified |

Current verified batch includes Coach Hub/Profile confirmation, onboarding goal/navigation/date
controls and rotation placeholders. Lint, 93 debug +93 release JVM tests and 35 instrumentation
tests pass across isolated runs; 126 fixture screenshots are confirmed. Latest signed release builds and verifies; controlled app restart, APK replacement and full emulator reboot all restore the
authenticated shell after a fresh Google login. See HANDOFF.md. Full feature/layout/font-rendering/motion parity is not established.
