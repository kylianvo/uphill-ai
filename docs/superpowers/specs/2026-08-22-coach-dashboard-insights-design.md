# Coach Dashboard: Dynamic Window + Expanded Insights (sub-project 2 of 2)

## Context

The Coach Dashboard Overview currently has one insight: a roster-wide
workout-type mix, fixed to a 2-week window (`docs/superpowers/specs/2026-08-22-coach-dashboard-overview-design.md`).
This is sub-project 2 of 2 in the roster-overview follow-up — independent of
sub-project 1 (runner levels + roster search), no shared code beyond both
reading `GET /api/coaching/overview`.

**Important finding that shapes this design**: `block_reviews`
(`backend/db.py:302`) has a real `created_at TIMESTAMPTZ` column — unlike
`workouts`, which only has `week_number`/`day_of_week` and no completion
timestamp (the reason the existing feature approximates its window by
week-number proximity, not real dates). The RPE insight below uses
`block_reviews.created_at` directly with true calendar filtering; every
other insight stays on the existing week-number approximation, now
parameterized instead of hardcoded to 2 weeks.

## Goal

1. Make the insights window coach-adjustable (7/14/30/90 days) instead of a
   fixed 2 weeks, applied consistently to every window-scoped calculation.
2. Add five new roster-wide insights alongside the existing workout-type
   mix: adherence trend, missed-workout day-of-week pattern, RPE
   distribution, race-readiness distribution, roster totals, and a
   most-consistent-athletes callout.

## Non-goals

- No per-athlete insight breakdowns (matches the original spec's decision
  to keep insights roster-wide only) — these are coach-facing roster
  summaries, not athlete drill-downs.
- No new tables. `block_reviews` and `workouts` already carry everything
  needed.
- No caching/precomputation — same on-the-fly-per-request philosophy as
  the rest of this feature; roster scale doesn't yet justify it (see
  sub-project 1's latency note — not a confirmed problem).
- Race-readiness and most-consistent both reuse the *existing* per-athlete
  `adherence_pct` calculation (now window-parameterized) rather than
  introducing a second adherence formula — one definition of "adherence,"
  reused everywhere.

## Dynamic window

`GET /api/coaching/overview` gains an optional `days` query param, default
`14`:

```python
@app.get("/api/coaching/overview")
def get_coaching_overview(days: int = 14, coach: dict[str, Any] = Depends(require_coach)):
    return get_roster_overview_data(coach["id"], days=days)
```

`get_roster_overview_data(coach_id, days=14)` converts `days` to a
week-count the same way the existing window already works, just no longer
hardcoded:

```python
window_weeks = max(1, math.ceil(days / 7))
window_wos = [w for w in wos_sorted if current_week - (window_weeks - 1) <= w["week_number"] <= current_week]
```

(Replaces the existing fixed `current_week - 1 <= w["week_number"] <=
current_week`, which was the `days=14` case all along — `ceil(14/7) - 1 =
1`.) This same `window_wos`/`window_weeks` feeds adherence, workout-type
mix, missed-day pattern, and roster totals below, so every window-scoped
number in one response is computed over the same span. No validation beyond
`max(1, ...)` — an unexpected `days` value just produces a wider or
narrower window, never an error; the frontend only ever sends one of
7/14/30/90.

Frontend: a dropdown (7/14/30/90 days, default 14) above the insights
section in `CoachDashboardView.tsx`, re-fetching `useCoachOverview` with the
selected value. `useCoachOverview.fetchOverview` gains a `days?: number`
parameter, appended to the query string when present.

## New insights

All computed inside `get_roster_overview_data`, added to the response
alongside the existing `workout_type_mix`.

### 1. Adherence trend

Weekly adherence % for each week from `current_week - (window_weeks - 1)`
through `current_week`, roster-wide (not per-athlete) — i.e. across all
athletes' workouts in that single week, `completed / resolved`:

```jsonc
"adherence_trend": [
  { "week_number": 7, "adherence_pct": 0.71 },
  { "week_number": 8, "adherence_pct": 0.78 },
  { "week_number": 9, "adherence_pct": 0.83 }
]
```

Weeks with zero resolved workouts roster-wide are omitted (not zero — no
data isn't the same as bad adherence). Computed from the same
`workouts_by_plan` data already fetched for the per-athlete loop, grouped
by `week_number` across all athletes instead of per-athlete.

### 2. Missed-workout day-of-week pattern

Count of `is_missed=1` workouts in the window, grouped by `day_of_week`,
roster-wide:

```jsonc
"missed_by_day": [
  { "day_of_week": "Monday", "count": 12 },
  { "day_of_week": "Saturday", "count": 3 }
]
```

Only days with at least one miss appear (no zero-padding for unused days —
the frontend can render "Monday" through "Sunday" in fixed order and treat
absence as zero).

### 3. RPE distribution

From `block_reviews.overall_rpe`, scoped to the coach's roster via
`plans.user_id` → `coach_athletes` (same join pattern as
`action_items`), filtered by real calendar time —
`block_reviews.created_at >= NOW() - (days || ' days')::INTERVAL` — since
this table has an actual timestamp, unlike `workouts`:

```jsonc
"rpe_distribution": {
  "avg_rpe": 6.4,
  "by_value": [
    { "rpe": 5, "count": 3 },
    { "rpe": 6, "count": 7 },
    { "rpe": 7, "count": 4 }
  ]
}
```

`overall_rpe` is nullable (`backend/db.py:306`) — rows with `NULL` are
excluded from both the average and the distribution. If zero block reviews
fall in the window, `rpe_distribution` is `{"avg_rpe": null, "by_value":
[]}`.

### 4. Race-readiness distribution

Roster-wide counts of athletes bucketed by their adherence in the current
window (reusing the exact same `adherence_pct` value already computed
per-athlete for the roster list — no second formula):

```jsonc
"race_readiness": { "on_track": 14, "at_risk": 5, "behind": 2 }
```

- `on_track`: `adherence_pct >= 0.8`
- `at_risk`: `0.5 <= adherence_pct < 0.8`
- `behind`: `adherence_pct < 0.5`
- Athletes with `adherence_pct === null` (no active plan, or no resolved
  workouts in window) are excluded from all three buckets — "no data" isn't
  a readiness verdict.

### 5. Roster totals

Sum across every `is_completed=1` workout in the window, roster-wide:

```jsonc
"roster_totals": {
  "distance_km": 842.3,
  "duration_hours": 118.5,
  "elevation_gain_m": 21400,
  "workout_count": 156
}
```

`distance_km`/`elevation_gain_m` sum `workouts.distance_km`/
`elevation_gain_m` (both nullable — `COALESCE(..., 0)` so a missing value
contributes 0, not `NULL`-poisons-the-sum). `duration_hours` sums
`duration_minutes / 60`.

### 6. Most-consistent athletes

Top 3 athletes by their own `adherence_pct` in the current window (the
same per-athlete value in the `athletes[]` list), ties broken
alphabetically by name; athletes with `adherence_pct === null` are excluded
(nothing to rank):

```jsonc
"most_consistent": [
  { "athlete_id": 42, "name": "Jane Runner", "adherence_pct": 1.0 },
  { "athlete_id": 51, "name": "Alex Chen", "adherence_pct": 0.92 },
  { "athlete_id": 33, "name": "Sam Lee", "adherence_pct": 0.88 }
]
```

## API changes

`GET /api/coaching/overview?days=<7|14|30|90>` (default 14). Response gains
five top-level fields: `adherence_trend`, `missed_by_day`,
`rpe_distribution`, `race_readiness`, `roster_totals`, `most_consistent`.
All existing fields (`athletes`, `action_items`, `phase_alerts`,
`workout_type_mix`) keep their shape, now computed over the requested
window instead of a hardcoded 2 weeks.

## Frontend

New cards in the Overview tab's insights section (below the existing
workout-type mix, which stays as-is structurally, just window-parameterized):

- **Window selector**: dropdown, 7/14/30/90 days, default 14, drives a
  refetch of `useCoachOverview`.
- **Adherence trend**: a small sparkline/line chart (hand-rolled SVG,
  following `ProfileChart`'s conventions per the existing feature's
  pattern) — week on x-axis, adherence % on y-axis.
- **Missed-by-day**: a simple bar row, days of week on x-axis (fixed
  Mon–Sun order, zero-filled for absent days), count on y-axis — reuses the
  `WorkoutTypeMixChart`-style bar rendering, generalized or duplicated as a
  small sibling component (implementer's call at plan time — if the shapes
  diverge enough, a shared bar-row primitive is worth extracting; if not,
  don't force it).
- **RPE distribution**: `avg_rpe` as a stat tile, `by_value` as a compact
  bar row.
- **Race readiness**: three stat tiles (on-track / at-risk / behind) with
  distinct colors (e.g. green/amber/red), each showing a count.
- **Roster totals**: a row of stat tiles (distance, hours, elevation,
  workout count) — a "team accomplishment" summary at the top of the
  insights section.
- **Most consistent**: a short ranked list (name + %), styled as a
  positive callout distinct from the alert-toned cards elsewhere in the tab.
- Every new label is bilingual (en/vi), matching the existing convention.
- Empty states: any insight with no data for the selected window renders a
  brief "not enough data yet" message in place of an empty chart — no
  insight silently renders a blank/broken visual.

## Testing

- Backend integration tests (extending
  `backend/tests/integration/test_coach_overview.py`):
  - `days` param: `days=7` produces a narrower window than `days=30` for
    the same seeded data (fewer or equal resolved workouts counted); a
    request with no `days` param defaults to the existing 14-day/2-week
    behavior (regression guard — the existing test suite's assertions
    about the default window must still pass unmodified).
  - Adherence trend: a plan with three weeks of workouts, only some
    resolved, produces one entry per week with resolved data, omitting the
    week with none.
  - Missed-by-day: seeded misses on specific days produce exactly those
    days in `missed_by_day`, with correct counts, and no entry for days
    with zero misses.
  - RPE distribution: a `block_reviews` row inside the window counts; one
    outside the window (`created_at` older than the cutoff) is excluded; a
    `NULL overall_rpe` row is excluded from both the average and the
    distribution.
  - Race readiness: athletes with adherence at each bucket boundary
    (exactly 0.8, exactly 0.5) land in the correct bucket per the `>=`/`<`
    semantics above; an athlete with `adherence_pct = null` appears in none
    of the three counts.
  - Roster totals: seeded completed workouts with known
    distance/duration/elevation sum correctly; a `NULL` `distance_km` or
    `elevation_gain_m` on one workout doesn't zero out the whole sum.
  - Most consistent: top 3 by adherence, correct tie-break by name,
    excludes null-adherence athletes; roster with fewer than 3 eligible
    athletes returns fewer than 3 entries (no padding/error).
- Frontend tests: the window-selector's refetch-on-change behavior (via
  `useCoachOverview`), and any new pure formatting/layout helpers extracted
  for the new chart components, following the existing
  `WorkoutTypeMixChart.test.tsx` convention of testing exported pure
  functions rather than full DOM rendering.

## Open items for a future iteration (not this one)

- Per-athlete insight drill-down (e.g. clicking "at risk" to see which
  athletes) — the roster-wide counts here are a summary; linking them back
  to the filterable roster list from sub-project 1 is a natural follow-up
  once both ship.
- RPE-over-time trend (parallel to the adherence trend) — deferred since
  it wasn't in the original shortlist the roster-totals/most-consistent
  ideas came from; easy to add later using the same `block_reviews`
  windowing this spec introduces.
