# UI revamp browser evidence

Verified locally on 2026-10-01 against commit `0d3089a` with a dedicated seeded athlete and coach in the local development database. The athlete has an active 10-week plan, three rest days, and two priority workouts in week 1.

| Check | Browser result |
| --- | --- |
| 375 × 812 plan | Today's priority workout is visible without manual scrolling; no horizontal page overflow. |
| Rest rows | Monday, Wednesday, and Friday each measure 46 px high. |
| Manage sheet | Panel background is `rgb(255, 255, 255)` with computed opacity `1` at 375 × 812 and 1280 × 800. |
| Desktop plan | `.content-panel-inner--plan-v2` measures 720 px wide at 1280 × 800. |
| Coach deep link | A fresh 375 × 812 load of `/app?ui=v2&tab=athletes` preserves `tab=athletes` and renders the coach roster. |

Screenshots: [mobile plan at today's workout](mobile-plan-375.png), [mobile plan top](mobile-plan-top-375.png), [mobile Manage sheet](mobile-manage-sheet-375.png), [desktop plan at today's workout](desktop-plan-1280.png), [desktop plan top](desktop-plan-top-1280.png), [desktop Manage sheet](desktop-manage-sheet-1280.png), and [coach athletes cold load](coach-athletes-cold-load-375.png).

Frontend validation: `npm test` passed (61 files, 488 tests). `npm run lint` exited 0 with 132 warnings. `npx tsc --noEmit` fails in three test files unchanged by this branch: `ConnectedAccounts.test.tsx`, `PlanCalendarView.test.tsx`, and `useMatching.test.ts`. No backend integration tests were run against `uphill_ai`.
