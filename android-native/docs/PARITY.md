# Native Android parity inventory

Reference: approved iOS base `afa2893`; latest iOS main inspected at `5597527`
(2026-10-15). Health Connect remains excluded by explicit user decision.
This inventory separates implemented behavior from verified visual parity. A matching
service or a passing fixture test does not establish matching layout or animation.

| Area | Android implementation / evidence | Remaining parity work |
| --- | --- | --- |
| Auth, launch, shell | Email/register, Credential Manager, secure session restore, video launch, Plan/Coach/Me/Athletes routing; sign-in and nested-tab evidence | Live Google round trip; compare launch/video timing and every auth/error state |
| Onboarding and generation | Setup steps, persisted job polling, resumed generation, inline Plan progress; onboarding flow tests | Compare all EN/VI steps and failure/resume states with iOS; inspect newer iOS setup changes |
| Plan summary and day list | Carousel, weeks, goal pill, coach review, sharpen checklist, workout actions; EN/VI normal/large-text captures | Compare all chart/data variants, row types, transitions and empty/offline states |
| Workout detail | Metrics, execution timeline, treadmill ranges, reasons/warnings, feeling/log confirmation, scoped coach actions/notes | Pace range formatting and font1.3 rendering check pass; remaining type/interval/rest/coach variants need evidence |
| Plan management | Move/swap, adapt/next, schedule, review, goal, select/delete, ICS sharing; mutation flow tests | Sheet-by-sheet UI/state comparison; direct calendar writes deferred, token-bearing webcal removed |
| Month calendar | Latest iOS #134 month model and weekly bars/day preview ported; day-to-week emulator flow passes | Next/Today/swipe/day-to-week and haptic checks pass; refreshed EN/VI/larger-text evidence inspected; weekly-column label and Open Week button styling still differ |
| Coach chat | SSE, proposals/rebuild/apply, rich cards, clarification, citations, feedback, persistent history; contract/UI tests | Compare every rich-card/source/proposal/error/streaming state and motion |
| Me/profile | Grouped profile, PBs/badges/rotation, settings, language, COROS, developer menu | Authenticated release round trip; backend notes/key-preservation fixes need deployment; compare every editor |
| Goal | Assessment/context toggles, race search, field curve, tiers, pacing handoff | Result-state chart/layout and every context card comparison |
| Gear | Recommendation packshots, preferences, rotation assignment/edit/mileage/retire, debounced saves | Compare recommendation/rotation/detail layouts and latest iOS rotation changes |
| Nutrition | Fueling preferences, catalog/results and feedback | Result-state composition and product/copy comparison |
| Pace | GPX picker/parser, course profile, splits/checkpoints, debounced calculation, target handoff | Real file import/device checks and result/chart/table comparison |
| Knowledge | Search/topics/cards, local shuffle, source attribution | Card/result/source sheets and empty/error UI comparison |
| Race history | Search/claims/bib verification, manual results/edit/delete, detail/PBs/badges; fixture/UI tests | Compare every link/claim/detail/course state against iOS |
| Coaching | Roster/invites, overview/actions, athlete physiology/provenance, scoped plan/actions/notes; live backend flow | Adherence chart, seven-day bars, workout mix, Overview/Roster sections, 7/14/30-day and Elite filters, roster search ported and tested. Inline invite form and remaining dashboard/athlete editor layouts still need comparison |
| COROS | Custom Tab callback/state, sync/push/status, foreground sync and manual matching | Live OAuth/sync/push, cancellation/error flows; Health import excluded |
| Accessibility/motion/fonts | Font1.3 and zero-animation captures, shared tokens and launch font, native system body font | TalkBack and all focus/error states; full motion audit; Android system font differs from SF Pro |
| Release | Matching certificate/code10, earlier emulator upgrade preservation, minified signed-out smoke, CI green at6208d6d | Authenticated minified release, physical phone upgrade, live OAuth, current signed artifact built and installed; Google account setup in progress |

Current verified batch: workout pace wrap, coach dashboard charts, latest month calendar.
90 debug + 90 release JVM tests, 21 instrumentation tests and 46 fixture screenshots pass.
No claim of complete feature, layout, font-rendering or animation parity is made.
