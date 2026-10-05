# Fitness snapshot UI evidence

Captured 2026-10-02 from the PR worktree's running Next.js app at
`http://127.0.0.1:3052/app/`, with its FastAPI backend at `127.0.0.1:8012`.
The backend used the local scratch database `uphill_ai_test`; no integration
suite or table truncation was run for these screenshots.

- [Profile source select, English](profile-source-en.png)
- [Profile source select, Vietnamese](profile-source-vi.png)
- [Onboarding source select, race path](onboarding-source-race-en.png)
- [Onboarding source select, return path](onboarding-source-return-en.png)
- [Planner weekly-km prefill](planner-weekly-km-prefill-en.png)

All accounts and activities were synthetic. Four complete weeks contained
72.6, 76.2, 69.8 and 74.2 km, with 660, 810, 570 and 730 m of ascent.
The snapshot endpoint returned 73.2 km/week with source `coros`; the planner
rounded this to 73, displayed the COROS hint, and prefilled the input with 73.
Profile captures show `field`; the two onboarding captures show `field` and
`estimated` respectively. The options retain `lab`, `field`, `estimated`,
and `unknown` in both languages.

The app workspace is `/app/` on this branch. Session restore and email login
do not open the onboarding wizard; registration does, so a local synthetic
registration was used to reach both threshold steps. The long English option
is clipped by the narrow native select on the race onboarding screen. No
frontend code was changed for this evidence task.

The temporary accounts and their seeded data were removed after capture,
and the two temporary dev servers were stopped.
