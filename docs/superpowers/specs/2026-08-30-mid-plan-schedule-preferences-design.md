# Mid-Plan Schedule Preferences Design

## Problem

Runners with an active training plan cannot change their Schedule Preferences
(days per week, preferred run days, long run day, double session days, gym
access, treadmill use, training environment) without generating a brand new
plan. These preferences are stored per-plan on the `plans` table
(`preferred_run_days`, `long_run_day`, `days_per_week`, `double_session_days`,
`has_gym_access`, `use_treadmill`, `training_environment`), and every block
generation call already rebuilds `race_info` fresh from the live `plans` row
(`main.py:1954-1973`), but there is currently no UI or API path that lets a
runner update that row mid-plan — the only place these fields are edited is
the initial plan-creation form (`PlannerView.tsx`'s `planForm`, submitted via
`usePlanner.ts` to `POST /api/coach/generate-plan`).

## Goal

Let a runner update their Schedule Preferences as part of generating their
next training block, so the new preferences take effect starting with that
block — without needing to abandon or regenerate the whole plan.

## Non-goals

- Changing preferences mid-block (only takes effect for the *next* generated
  block, consistent with how blocks are already fixed 2-week windows once
  generated).
- Updating the runner's global `users` defaults (`users.days_per_week`, etc.)
  — this feature only touches the active plan's row, per user decision.
- Editing training environment/gym/treadmill fields separately from
  scheduling fields — they're bundled into the same edit step per user
  decision.
- New validation rules beyond what plan-creation already has (see below).

## Design

### Approach

Extend the existing "Generate Next Block" flow rather than adding a separate
save-then-generate step. The next-block endpoint already re-reads the
`plans` row for `race_info` on every call, so writing the updated schedule
fields to that row immediately before generation is the natural, minimal
integration point — one request, one job, no intermediate state to manage
between "edit" and "generate."

### Backend

- `_generate_next_block_for_athlete` (`backend/main.py:1762-2026`) and its
  request model gain new **optional** fields: `preferred_run_days`,
  `long_run_day`, `days_per_week`, `double_session_days`, `has_gym_access`,
  `use_treadmill`, `training_environment` — same shapes as the equivalent
  fields on `PlanGenerateRequest` (`main.py:171-197`).
- If any of these fields are present in the request, call a new
  `db.update_plan_schedule(plan_id, **fields)` (simple parameterized
  `UPDATE plans SET ... WHERE id = :plan_id`, following `db.py`'s existing
  `text()` pattern) **before** the existing block-generation logic runs.
- No schema changes — all fields already exist on `plans`
  (`c3d4e5f6a7b8_add_scheduling_fields_to_plans.py`,
  `e5f6a7b8c9d0_plan_wise_gym_treadmill_environment.py`). No new
  migration needed.
- No new cross-field validation (e.g. `days_per_week == len(preferred_run_days)`,
  `long_run_day in preferred_run_days`) — plan creation doesn't enforce this
  either (confirmed: no validators in `PlanGenerateRequest`, no checks in
  `plan_generator.py`), so the edit path stays consistent with that
  convention. The frontend constrains choices via UI only, same as creation.
- If generation subsequently fails (job error), the `plans` row already
  reflects the updated preferences — this is an accepted tradeoff (same
  implicit behavior as `race_info` today) and simply means a retry uses the
  already-updated row; no rollback/transaction spanning both steps.

### Frontend

- In `PlannerView.tsx`'s "Generate Next Block" flow, add a preferences
  section that reuses the exact same field components as `planForm` on the
  creation form: days-per-week buttons, preferred-days toggle group,
  long-run-day select, double-session-days chips (rendering constrained to
  selected preferred days, same as creation), gym/treadmill checkboxes,
  training-environment button group.
- Pre-fill from the current plan's row (already available via
  `AppContext`/`usePlanner`).
- `handleGenerateNextBlock` (`usePlanner.ts`) includes the full current form
  state (not a diff) in the existing next-block request payload.

### Data flow

1. Runner opens "Generate Next Block", sees preferences pre-filled from the
   current plan.
2. Runner edits any subset of fields, submits.
3. Backend updates the `plans` row's schedule columns, then proceeds with
   the existing block-generation pipeline (completion gate, block review,
   `block_context`, `PlanGenerator.generate_plan_workouts`, `save_workouts`)
   unchanged.
4. Frontend polls `plan-status/{job_id}` as it already does today.

### Testing

- Backend: extend/add a test around `_generate_next_block_for_athlete`
  verifying that schedule fields in the request update the `plans` row and
  are reflected in the values passed to `generate_plan_workouts`.
- Frontend: manual verification via dev server — change preferences,
  generate next block, confirm the resulting workouts reflect the new
  days/long-run-day/double-session-days.
