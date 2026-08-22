# Coach Dashboard: Roster Overview

## Context

Coach mode already exists and is not greenfield. `coach_athletes`
(`backend/db.py:129`) implements the coach→athlete roster relationship
(`status`: invited/active/paused/removed). `frontend/src/views/CoachDashboardView.tsx`
renders invite management and the active/invited athlete lists, backed by
`useCoachDashboard.ts` calling `/api/coaching/roster`,
`/api/coaching/my-invites`, `/api/coaching/invite`, etc.
(`backend/main.py:991-1120`, gated by the existing `require_coach`/
`require_athlete_access` dependencies at `main.py:464,469`). Per-athlete
detail (active plan, recent plans, workouts, profile) is already fetchable
one athlete at a time.

What's missing, and what this spec adds: a roster-wide **overview** — at-a-
glance progress/engagement per athlete, action items the coach owes
(unfinished draft plans, workouts awaiting approval), phase alerts
(peak/taper/race week), and a roster-wide workout-type breakdown. All of it
is derivable from existing tables (`plans`, `workouts`) with no new schema.

**Important finding that shapes this design**: workouts have no calendar
date column — only `week_number` (int) and `day_of_week` (TEXT weekday
name). The only place "which week is current" is resolved anywhere in the
backend is `_build_athlete_context_block` (`main.py:1197-1208`), which
trusts `plans.current_week` directly (no date-vs-`race_date` computation
exists anywhere, and `services/calendar_service.py`'s date math is a
separate, unrelated concern — mapping *all* weeks to calendar dates for iCal
export, not identifying "now"). This design follows the same trusted
convention: `plans.current_week` **is** the current week, full stop. No new
date-derivation logic is introduced.

## Goal

Add one read-only endpoint and one new frontend tab giving a coach, at a
glance, across their whole roster:

1. Per-athlete progress: plan week X of Y, 14-day workout adherence %, last
   completed workout, missed-workout streak.
2. Action items: draft plans not yet finished, workouts pending coach
   approval — counted and listed, each linking to the relevant athlete.
3. Phase alerts: athletes whose current or next plan week is tagged
   peak/taper/race.
4. Roster-wide workout-type mix: distribution of completed workout types
   over the last 14 days.

## Non-goals

- No engagement tracking beyond workout completion (no login/session
  tracking, no new `users` columns) — adherence and completion recency are
  the only engagement signal, per existing data.
- No new tables, no migration. Everything is computed from `plans` and
  `workouts` at request time.
- No caching/materialized rollups — roster sizes are small (a single
  coach's own athletes), so on-the-fly aggregation per request is
  sufficient. Revisit only if a coach's roster size or request volume makes
  this measurably slow.
- No calendar-date-based "current week" computation — `plans.current_week`
  is the sole source of truth, matching the existing convention in
  `_build_athlete_context_block`.
- No changes to the existing roster/invite management UI or endpoints —
  this is purely additive (a new tab, a new endpoint).
- Per-athlete workout-type breakdown is out of scope — the mix is
  roster-wide only (per user decision during brainstorming).

## Data model (no schema changes — query design only)

All four queries scope to the requesting coach via a `JOIN coach_athletes
ca ON ca.athlete_id = <athlete> AND ca.coach_id = :coach_id AND ca.status =
'active'` — the same scoping already used by `get_roster_for_coach`.

### 1. Per-athlete progress summary

For each active athlete, the athlete's most recent plan (`ORDER BY
created_at DESC LIMIT 1` per athlete, `plan_status = 'active'` preferred —
same "pick the current plan" convention as the per-athlete detail fetch at
`main.py:1050-1120`):

- `current_week`, `total_weeks`, `race_name`, `race_date` — straight from
  `plans`.
- `adherence_pct_14d` — over workouts in that plan with `week_number` in
  the range covering the last 14 days' worth of scheduled workouts
  (approximated as the two most recent `week_number`s ≤ `current_week`,
  since there's no calendar date to filter by precisely — see Open items):
  `COUNT(is_completed) / COUNT(*)` where `is_missed = 0 OR is_completed =
  1` (i.e., workouts that have already resolved one way or the other;
  future-scheduled workouts in the window aren't counted as either).
- `last_completed_at` — this requires a completion timestamp, which
  `workouts` does not have (`is_completed` is a bare 0/1 flag, no
  `completed_at` column). **Substituted with**: the highest `week_number` +
  `day_of_week` combination where `is_completed = 1`, rendered as "Week N,
  <Day>" rather than an absolute date/time. This is a real gap — see Open
  items for the alternative of adding `completed_at`.
- `missed_streak` — count of consecutive most-recent workouts (ordered by
  `week_number DESC, day_of_week` mapped to `DAY_OFFSETS` order) with
  `is_missed = 1`, stopping at the first `is_completed = 1`.

### 2. Phase alerts

For each athlete's current plan: distinct `workouts.phase` values where
`week_number = plans.current_week` (this week) and where `week_number =
plans.current_week + 1` (next week). If either set contains `'peak'`,
`'taper'`, or `'race'`, emit an alert `{athlete_id, name, phase, starts:
"this_week" | "next_week"}`. A plan can only be in one phase per week in
practice (workouts within a week share a phase), but the query doesn't
assume that — it takes `DISTINCT` and flags on any match.

### 3. Action items

- **Draft plans**: `SELECT id, user_id, race_name FROM plans WHERE
  plan_status = 'draft'` scoped to roster athletes.
- **Pending workout approvals**: `SELECT w.id, w.plan_id, w.title,
  p.user_id FROM workouts w JOIN plans p ON p.id = w.plan_id WHERE
  w.approved_at IS NULL` scoped to roster athletes' plans.

Both returned as lists (not just counts) so the frontend can render
clickable items; the frontend derives counts from list length.

### 4. Workout type mix

`SELECT type, COUNT(*) FROM workouts w JOIN plans p ON p.id = w.plan_id
WHERE w.is_completed = 1 AND <week_number falls in the last-14-days
approximation from #1> GROUP BY type` across all roster athletes' plans.
Returned as `[{type, count, pct}]`, `pct` computed server-side against the
total.

## API changes

New endpoint: `GET /api/coaching/overview`, gated by the existing
`require_coach` dependency (same as `/api/coaching/roster`). No request
body/params — always scoped to the authenticated coach's active roster.

Response:

```jsonc
{
  "athletes": [
    {
      "athlete_id": 42,
      "name": "Jane Runner",
      "active_plan": {
        "plan_id": 7,
        "race_name": "VMM 70km",
        "race_date": "2026-11-15",
        "current_week": 9,
        "total_weeks": 16
      },
      "adherence_pct_14d": 0.83,
      "last_completed": { "week_number": 9, "day_of_week": "Wednesday" },
      "missed_streak": 0
    }
  ],
  "action_items": {
    "draft_plans": [ { "plan_id": 12, "athlete_id": 55, "athlete_name": "...", "race_name": "..." } ],
    "pending_workout_approvals": [ { "workout_id": 301, "plan_id": 7, "athlete_id": 42, "athlete_name": "...", "title": "Long run" } ]
  },
  "phase_alerts": [
    { "athlete_id": 42, "athlete_name": "Jane Runner", "phase": "taper", "starts": "this_week" }
  ],
  "workout_type_mix": [
    { "type": "long_run", "count": 14, "pct": 0.28 },
    { "type": "tempo", "count": 9, "pct": 0.18 }
  ]
}
```

Athletes with no active plan are included in `athletes` with
`active_plan: null` and null/zero metrics (not excluded — a coach should
see who has no active plan, that's itself useful signal, distinct from an
"action item").

## Frontend

- `frontend/src/hooks/useCoachOverview.ts` — fetches `/api/coaching/overview`
  once on mount, standard `{ data, loading, error }` shape matching
  `useCoachDashboard.ts`'s existing convention.
- `CoachDashboardView.tsx` gains a new "Overview" tab alongside the
  existing roster/invites tab(s), rendered top-to-bottom:
  1. **Phase alerts** — only rendered when non-empty; one line per alert
     ("Jane Runner enters Taper this week"), clicking jumps into that
     athlete's plan view via the existing "enter athlete view" navigation
     already used elsewhere in this file.
  2. **Action items** — two counters with expandable lists ("2 draft plans
     to finish", "5 workouts pending your approval"); each list item
     clickable, same navigation pattern.
  3. **Roster progress table** — one row per athlete: race name/date, "Week
     X of Y", adherence %, last completed (Week N, Day), missed-streak
     badge if > 0.
  4. **Workout type mix** — a bar chart, roster-wide, last-14-days
     approximation window. Built per the `dataviz` skill's guidance (form,
     color, accessibility) rather than a default chart-library look, to
     stay visually consistent with the rest of the app.
- Empty states: no athletes → "No athletes yet, invite one to get
  started" (matches existing roster empty-state tone); no completed
  workouts in the window → mix chart renders a neutral empty state, not a
  crash or a zero-slice pie.

## Testing

- Backend unit tests (new, following existing `backend/tests/` patterns):
  the four query functions against a seeded test DB — adherence % with a
  known mix of completed/missed/future workouts; phase-alert detection for
  this-week vs next-week vs neither; draft-plan and pending-approval counts
  scoped correctly to the coach's roster (and *not* leaking another coach's
  athletes); workout-type mix percentages sum to 1.0 (or 0 items when
  nothing completed in window).
- Backend integration test: `GET /api/coaching/overview` as a coach with a
  mixed roster (one athlete mid-taper, one with a draft plan, one with no
  active plan) returns 200 and the expected shape; as a non-coach user,
  returns the same 403 `require_coach` already enforces elsewhere.
- Frontend: manual verification via the dev server — seed a coach with a
  few athletes in varying states (draft plan, pending workout approval,
  taper-week athlete, athlete with zero activity) and confirm the Overview
  tab renders each section correctly, including empty states.

## Open items for a future iteration (not this one)

- `workouts` has no completion timestamp, so `last_completed_at` is
  approximated as "Week N, Day" rather than an absolute date/time, and the
  "last 14 days" window used for adherence/mix is approximated by
  `week_number` proximity rather than true calendar days. A real fix (a
  `completed_at TIMESTAMPTZ` column, set when `is_completed` flips to true)
  is a schema change and reasonably deferred — not needed for this
  dashboard to be useful, but would sharpen precision if coaches find the
  week-granularity approximation too coarse in practice.
- No real-time push — the overview is fetched on tab load only; a coach
  must refresh to see new activity. Acceptable for a first version; revisit
  if coaches want live updates.
