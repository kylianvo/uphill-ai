# Phase 2b design baseline and audit

The web components define behavior and copy; #81 SwiftUI sources define existing names. The initial audit used sources while screenshots were deferred. The owner reinstated after-shots for Tasks 2–8 in Task 9, before E2E. Simulator evidence and visual findings are recorded below.

| Screen | Web | iOS #81 | Kotcha rule | Decision |
|---|---|---|---|---|
| Welcome | OnboardingWizard introduces setup | Outcome, two-minute estimate, defer | 3: fast first value | Change estimate to About 1 minute |
| Goal | Race and non-race choices | Race, distance, start, return, recovery | 5: choices | Change to five named choices; retain distance model compatibility |
| Race | Race lookup, course fields | Manual name, distance, elevation, date and target | 1: one question | Split race and date; move target settings |
| Return | Time away and current fitness | Both on one screen | 1 | Split questions |
| Recovery | Finished distance, elapsed days, feeling | Three questions together | 1 | Split questions |
| Schedule | ScheduleFieldsEditor | Days, weekdays, long run, volume, terrain, gym, start | 1, 3 | Keep days and volume; separate start; move other fields to schedule |
| About you | ProfileSettingsModal | Optional demographics, HR, injury, notes | 3 | Move to checklist and settings |
| Review | Input summary | Summary and build action | 2 | Change title and coach line; keep summary facts |
| Plan checklist | Profile settings supply missing inputs | Missing | 4, 8 | Add Sharpen your plan |
| About you settings | Demographics and athlete notes | Read-only profile | 6, 8 | Add pushed editor |
| Heart rate settings | Thresholds and watch guide | Read-only thresholds | 6, 8 | Add pushed editor and guide sheet |
| Paces settings | Model, threshold/easy range, zones | Read-only easy range | 6, 8 | Add pushed editor and zone table |
| Account | Password update for email accounts | Sign out | 8 | Add password editor |
| Adapt week | Fatigue plus optional schedule editor | Fatigue, RPE, notes | 8 | Add collapsed schedule disclosure |
| Manage | Plan actions | Solid rows and new plan | 6 | Add Schedule entry; retain actions |
| Move notice | CalendarNoticeBanner, structured warnings | Generic error, no warnings | 8 | Add warning/error mapping and week window |
| Goal sheet | GoalContextView, GoalResult | Assessment without context | 8 | Add disclosure and nonempty groups |
| Generation | Real job status | Timer, resume, retry | None | Keep behavior; align hierarchy and spacing |
| Next week | Completion gate and confirmation | Existing sheet | None | Keep; align spacing |
| Weekly review | Review narrative | Existing sheet | None | Keep; align spacing |
| Empty plan | Build entry | Existing build action | None | Keep; align hierarchy |
| Workout card | Full workout facts and actions | Existing day card | Owner exception | Keep content exactly; spacing only |
| Week header | Coach review and phase brief | Existing header | Owner exception | Keep content exactly; spacing only |

## Visual baseline

Use the spec's light-only SF Pro system styles and existing UH tokens. Accent #19ce8b, accent ink #08764f, button ink #063e2b, ink #172b26, secondary #455c52, muted #5d7167, line #dce5df, surface #f8faf8 and white cards. Card radius 12; row spacing 12; section spacing 24. Titles use screenTitle, body uses body, supporting copy uses caption; coach prompts use callout in secondary. Large option rows have a minimum 44-point target, readable wrapping labels, selection tint and checkmark. The primary action uses uhPrimary and remains reachable above the safe area. Use system pickers, steppers, switches, navigation and sheets, direction-matched transitions and Reduce Motion. Later tasks follow this baseline.

## Found in the audit

#81 has a manual race-name field, not the race search the Phase 2b snippet assumes. Adaptation must use an existing backend race-search endpoint without backend changes. The removed target-time and terrain options must remain reachable through settings rather than being silently discarded.


## Task 9 visual evidence

After-shots for Tasks 2–8 are in [screenshots/phase2b](screenshots/phase2b/). Each accepted capture was inspected once. Captures use the real SwiftUI screens with recorded API responses and local preview state; warnings, empty states and checklist completion use controlled presentation state. The capture-only harness was removed before final testing.

The onboard/clarify review confirmed separate race/date, return/feeling and recovery questions, readable coach prompts, and a reachable primary action. The schedule screen was also checked at extra-extra-extra-large Dynamic Type. The polish/harden review confirmed system type hierarchy, consistent card spacing, 44-point Goal action, separate profile editors, and nonempty goal context groups. The watch guide's long native navigation title truncates; its instructional body remains readable. The adapt sheet capture shows its expanded disclosure; a separate schedule warning capture shows all editor rows and the inline warning. Workout card and week header content remain unchanged.

Manual timing: **23.8 seconds**, Welcome → Getting started → default four runs / 30 km → today's start date → visible “Build my plan”. This measures navigation and answering with defaults, excluding registration and generation. The timer used manual Simulator clicks, not XCTest.

Task 7 used a temporary second backend on localhost:8002, from this worktree, to record the current reassessment response. The app's local URL was restored to localhost:8000 and the second server stopped immediately afterward. Information-schema snapshots before and after startup were identical: init_db added no columns. No backend, prompt or schema changes; no Alembic or backend integration tests.


Final verification: `test.sh` passed 163 tests across 24 suites. `e2e.sh` passed both live-local tests: account creation/onboarding/generation and sign-in/workout completion/undo. The first E2E run failed to tap Welcome while the Simulator retained the enlarged screenshot text setting; rerunning at default Large text passed. No product-code change was needed.
