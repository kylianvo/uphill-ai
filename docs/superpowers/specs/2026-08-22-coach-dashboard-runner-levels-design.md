# Coach Dashboard: Runner Levels + Scalable Roster (sub-project 1 of 2)

## Context

The Coach Dashboard Overview (`docs/superpowers/specs/2026-08-22-coach-dashboard-overview-design.md`,
implemented on this branch) gives a coach a single-screen roster view: progress,
action items, phase alerts, and a workout-type mix. It works well for a
handful of athletes, but a coach with ~100 runners has two problems: the
roster list has no way to search or narrow it down, and there is no concept
of grouping runners by training level — coaching a beginner and an elite
athlete calls for different attention and different expectations, but today
every athlete renders identically in one flat list.

This is sub-project 1 of 2 in the roster-overview follow-up (sub-project 2,
dynamic insights window + expanded insights, is a separate spec — independent
of this one, no shared code beyond both reading the same `GET
/api/coaching/overview` response).

**Latency note**: the user reported feeling latency while viewing the
dashboard, but that observation came from an ad-hoc verification setup (a
dev server pointed at a database over a slower network path, right after a
cold restart) — not a properly running environment. This spec does not treat
it as a confirmed performance requirement. At the data volumes in play (a
coach's own roster — dozens to low hundreds of athletes, each with at most a
few hundred workout rows), the existing single-query aggregation in
`get_roster_overview_data` remains cheap; the real risk at 100 athletes is
an unfiltered, unsearchable UI list, which is what this spec addresses.

## Goal

1. Classify each athlete into a runner level (Beginner/Intermediate/Advanced/Elite),
   computed from data already collected — no new coach workflow required.
2. Add a `needs_attention` signal per athlete so a coach can immediately see
   who needs them, without reading every row.
3. Let a coach search and filter their roster by name, level, "needs
   attention," and race/goal — entirely client-side, no new endpoint.

## Non-goals

- No manual level override UI in this pass — level is fully derived; a
  coach cannot hand-set it. (If this turns out to matter in practice, it's
  a small follow-up: one column + one edit control, deferred until there's
  a real case for overriding the computed value.)
- No server-side pagination or virtualization — YAGNI at current roster
  scale. Revisit only if a coach's actual roster size or measured render
  cost crosses a few hundred athletes.
- No backend-side search/filter endpoint — the existing `GET
  /api/coaching/overview` payload already carries everything a client-side
  filter needs; adding query params for this would just be moving work
  that's already cheap client-side onto the server for no benefit.
- Does not touch the workout-type mix, adherence math, phase alerts, or
  action items logic already implemented — additive only.

## Runner level classification

Computed from `users.current_weekly_km` (`backend/db.py:59`, already
collected at onboarding, `REAL DEFAULT 30.0`) — no new column, no new
collection step. Thresholds (weekly km, approximating recreational →
elite trail/road running volume):

```python
def runner_level(current_weekly_km: float | None) -> str:
    km = current_weekly_km if current_weekly_km is not None else 30.0
    if km < 20:
        return "beginner"
    if km < 50:
        return "intermediate"
    if km < 90:
        return "advanced"
    return "elite"
```

This is a pure function of one already-fetched field — computed in Python
alongside the rest of `get_roster_overview_data`'s per-athlete assembly, no
new query. `users.current_weekly_km` is nullable-in-practice only via the
same `30.0` default every other read in this codebase already assumes
(`backend/db.py:1144`), so the `None` fallback here matches existing
convention, not a new assumption.

## `needs_attention` signal

`True` when any of the following hold for that athlete, `False` otherwise:

- They appear in `phase_alerts` (this week or next week)
- They have an entry in `action_items.draft_plans` (their own draft plan)
- They have an entry in `action_items.pending_workout_approvals`
- Their `missed_streak > 0`

Computed in the same per-athlete loop in `get_roster_overview_data` that
already builds `phase_alerts` and knows `missed_streak` — the draft-plan and
pending-approval checks need a per-athlete lookup into the
`action_items` lists already being assembled (a small `set` of athlete ids
touched by each, built once, checked per athlete — O(1) per lookup, no new
query).

## API changes

`GET /api/coaching/overview`'s existing `athletes[]` entries gain two
fields (no other response shape changes):

```jsonc
{
  "athlete_id": 42,
  "name": "Jane Runner",
  "runner_level": "advanced",              // NEW: "beginner" | "intermediate" | "advanced" | "elite"
  "needs_attention": true,                 // NEW
  "active_plan": { ... },                  // unchanged
  "adherence_pct_14d": 0.83,               // unchanged
  "last_completed": { ... },               // unchanged
  "missed_streak": 0                       // unchanged
}
```

## Frontend

All new UI lives in the existing "Overview" tab's Roster-progress card
(`frontend/src/views/CoachDashboardView.tsx`), operating entirely on the
already-fetched `overview.athletes` array — no new fetch, no new hook.

- **Search box**: free-text, matches `name` (case-insensitive substring).
  Matches the existing invite-form input styling (`className="chat-input"`)
  for visual consistency with the Roster tab.
- **Level filter**: a row of toggle chips — All / Beginner / Intermediate /
  Advanced / Elite — single-select, "All" is the default.
- **"Needs attention" toggle**: a single checkbox/switch that, when on,
  shows only `needs_attention === true` athletes.
- **Race/goal search**: a second free-text input matching
  `active_plan.race_name` (case-insensitive substring); athletes with no
  active plan are excluded when this filter has a value, included when it's
  empty.
- Filters compose with AND (name match AND level match AND
  needs-attention-if-on AND race match).
- Each athlete row gains a small level badge (e.g. a colored pill next to
  the name) — bilingual labels for all four levels, matching the existing
  `lang === "en" ? ... : ...` convention.
- Empty-filtered-result state: a small "No runners match your filters" message
  distinct from the existing "No athletes yet" empty-roster state (the
  latter means zero athletes total; the former means filters excluded all
  of them).

## Testing

- Backend unit/integration tests (extending
  `backend/tests/integration/test_coach_overview.py`):
  - `runner_level`: boundary values at 20/50/90 km (each boundary belongs
    to the *higher* bracket, e.g. exactly 20.0 → intermediate, not
    beginner), `None`/default (30.0) → intermediate, very high value (e.g.
    200) → elite.
  - `needs_attention`: an athlete with only a phase alert → `true`; only a
    draft plan → `true`; only a pending approval → `true`; only a nonzero
    `missed_streak` → `true`; an athlete with none of the four → `false`;
    an athlete with an active plan, zero missed streak, no alerts, no
    pending items → `false` (regression guard against a signal firing on
    everything).
  - Response shape: `GET /api/coaching/overview` includes `runner_level`
    and `needs_attention` on every athlete entry, including the
    no-active-plan case.
- Frontend tests: a pure filter-predicate helper function (e.g.
  `matchesFilters(athlete, filters)`) extracted and exported from the view
  (or a small new `frontend/src/utils/`/`frontend/src/hooks/` module,
  implementer's call at plan time) so it's unit-testable without rendering
  — covering each filter dimension alone and combined (AND semantics), plus
  the case-insensitivity of both search fields.

## Open items for a future iteration (not this one)

- Manual level override, if coaches disagree with the computed
  classification in practice.
- Revisit `current_weekly_km`'s staleness: it's a point-in-time onboarding
  value, never updated from actual training data. A future version could
  derive level from recent real workout volume instead — deferred since it
  would need a new aggregation, not a one-line threshold function.
