# Fitness snapshot: measured signals drive tier and plan baseline

Date: 2026-10-02
Status: approved design, pending implementation plan

## Problem

An elite trail runner on prod (user feedback, 2026-09) got plans of 37–59 km/week while running
125–163 km/week (COROS activities, 4 complete weeks to 2026-09-20).

Cause, in `services/athlete_tier.py:derive_tier`:

1. The typed 120 km/week put him in `sub_elite` (80–160 km band).
2. The stored AeT 134 / AnT 163 give a 17.8% gap. `sub_elite` allows at most 10%, so
   the gap rule demoted him to `recreational` (40–80 km band), and the plan followed
   that profile's caps.

The gap rule assumes the stored thresholds were measured. Nothing records whether
they were, and these values sit next to the DB defaults (135/165).

More generally, plan generation ignores almost everything COROS gives us:

| Data | COROS tool | Stored today | Used by plan generation |
|---|---|---|---|
| Activities (distance, vert, HR, load) | `querySportRecords` | `activities` | Only max-ever distance (`get_user_activity_ceiling`) |
| Resting HR, HRV, training load | daily-metric tools | `daily_metrics` | No |
| VO2max, running level, threshold pace | `queryFitnessAssessmentOverview` | `users` columns, overwritten | Threshold pace only (pace zones) |
| Race predictor 5k/10k/HM/M | same tool | Parsed, returned once, discarded | No |

The fitness overview only refreshes when the athlete presses "sync fitness".

## Decisions

- **Scope (C):** the measured signals drive the tier, replace the volume baseline, and
  go into the prompt as an athlete snapshot.
- **Changes over time (B):** new plans and the existing re-plan points (next block,
  adapt week, weekly goal re-assessment) read the fresh snapshot. No automatic plan
  rewrites or proposals.
- **Tier conflicts (A):** measured volume sets the base tier; performance may promote
  one step; the AeT/AnT gap may demote only when the thresholds were measured.
- **Threshold provenance (A):** ask the athlete how the AeT/AnT values were obtained.
  Existing users default to `unknown`, which disables the gap demotion for them.
- **Storage (approach 1):** assemble the snapshot on read from existing tables, plus an
  append-only history table for COROS fitness assessments.

## Data model

New table `fitness_assessments` (append-only):

| Column | Type | Notes |
|---|---|---|
| id | serial PK | |
| user_id | int FK users ON DELETE CASCADE | |
| source | text | `coros` for now |
| vo2max | real | |
| running_level | real | |
| threshold_pace | text | `m:ss` |
| pred_5k_sec, pred_10k_sec, pred_hm_sec, pred_marathon_sec | real | race predictor |
| measured_at | timestamptz | time of the pull |

Index `(user_id, measured_at DESC)`. A row is inserted only when any value differs
from the user's latest row, so repeated syncs do not create duplicates.
`delete_provider_data` (COROS disconnect) also deletes this user's `coros` rows.

New column `users.threshold_source TEXT NOT NULL DEFAULT 'unknown'`, one of
`lab | field | estimated | unknown`. It describes the stored AeT/AnT pair.

New column `plans.fitness_snapshot JSONB`: the snapshot summary used when the plan was
generated or last re-planned, so the tier decision can be audited later.

The existing `users.threshold_pace / coros_vo2max / coros_running_level` columns stay,
kept in sync with the latest assessment, so current readers keep working.

All schema changes go in both `db.py:init_db()` and an Alembic migration.

## Refresh

- `coros_sync.sync_user` (activity sync) also calls `queryFitnessAssessmentOverview`
  and records the assessment. A failure there is logged and does not fail the
  activity sync.
- `sync_fitness` (the existing button) writes to `fitness_assessments` too.
- Before building a snapshot for a plan, if the athlete has an active COROS connection
  and the latest assessment is older than 7 days, pull one on demand. Any failure falls
  back to stored data and never blocks the plan.

## Snapshot

`services/fitness_snapshot.py`, `build(user_id, typed_weekly_km=None) -> FitnessSnapshot`.

Each signal carries `value`, `source` (`coros | race_history | self_reported`),
`as_of`, `used` (bool) and `reason` (why it was or was not used).

| Signal | First choice | Fallback | Rule |
|---|---|---|---|
| Weekly volume (km, vert) | Mean of the last 4 complete Mon–Sun weeks of running activities | Typed km/week | A week counts only if it ended before `last_sync_at`; at least 3 counted weeks required. Running = the activity types `get_user_activity_ceiling` treats as running, excluding duplicates |
| Threshold pace | Latest assessment | Typed `users.threshold_pace` | Assessment ≤ 60 days old |
| Performance (tiering) | Marathon prediction (latest assessment); UTMB index | None | Assessment ≤ 60 days. VO2max and the other predictions are prompt context only; race results stay in the existing RACE HISTORY block and long-run ceiling |
| AeT/AnT | Typed values | None | Usable for tiering only when `threshold_source` is `lab` or `field` |
| Load and recovery | `daily_metrics`, last 14 days: load ratio, HRV trend, resting HR | None | Prompt context only, never tiering |

When the athlete overrides the pre-filled km/week in the plan form, the typed value
wins over measured volume and the snapshot says so (`reason: "athlete override"`).

## Tier rule

Replaces the current `derive_tier` ordering. Order:

1. Explicit per-plan `athlete_tier` override wins (unchanged).
2. Beginner rules (goal type, max continuous jog under 10 min) unchanged.
3. Base tier = volume band of the snapshot's weekly volume (measured or typed).
4. Long-run promotion out of `beginner` unchanged.
5. **Promote at most one step** when the best performance signal maps to a higher tier.
   New `perf_bands` in `TIER_PROFILES`, conventional defaults marked unsourced like the
   volume bands:
   - Marathon prediction (men): elite ≤ 2:40, sub-elite ≤ 3:10, recreational ≤ 4:15.
     Women: thresholds 12% slower. Unknown gender: men's thresholds (conservative).
   - UTMB index: elite ≥ 700, sub-elite ≥ 550, recreational ≥ 400.
   - Best (highest) mapped tier across available signals is used.
6. **Demote** on the AeT/AnT gap only when `threshold_source in ("lab", "field")`. The
   existing limits and the stop-at-`recreational` behaviour stay.

The function returns the tier plus a short list of reasons, stored in
`plans.fitness_snapshot`.

Regression case (that athlete): measured ~140 km → `sub_elite`; `threshold_source = unknown` →
no gap demotion; possible one-step promotion from the predictor. Never `recreational`.

## Consumers

`fitness_snapshot.build` replaces the raw profile fields for volume, threshold pace and
tier inputs in:

- Plan creation, self-serve and coach-created (`main.py` around the two
  `get_user_activity_ceiling` call sites, ~1014 and ~1817).
- Next block / adapt week (`main.py` ~2348, `services/week_rebuild.py`).
- Goal context (`services/goal_context.py`, which already reads VO2max; it gains the
  race predictor).
- Coach chat context (`services/coach_context.py`).

`PlanGenerator` receives the snapshot's weekly volume as `current_weekly_km`, so the
existing baseline math (`base_weekly_minutes`, the prompt's "Weekly volume base") uses
it unchanged.

## Prompt block

An `ATHLETE FITNESS SNAPSHOT` section beside the existing `RACE HISTORY` block, listing
only signals with `used = true`, each with source and date. Example:

```
ATHLETE FITNESS SNAPSHOT
- Volume: 141 km/week, 5,800 m vert (4-week avg to 2026-09-20, COROS)
- Marathon prediction 2:52, half 1:21 (COROS, 2026-09-25)
- VO2max 61, threshold pace 3:53/km (COROS, 2026-09-25)
- Load ratio 1.1, HRV stable (COROS, last 14 days)
- Level: sub_elite (volume band; AeT/AnT source unknown, not used)
```

The tier profile still sets caps; the block is calibration context for the model.
The block is English, like the rest of the scheduler prompt; the plan `lang` already controls the output language.

## UI

- Profile settings and onboarding: a "How did you get these?" select next to AeT/AnT
  (lab test / field test / estimated / don't know), EN and VI.
- Plan creation: km/week pre-fills with the measured average when available, with a
  hint "From your COROS: 141 km/wk (last 4 weeks)". Editing it is an override.
- Needs screenshot evidence per the `ui-screenshot-evidence` skill.

## Failure handling

- COROS call or parse failure: use stored assessments and typed values; log; never block
  a plan.
- No COROS connection: typed volume, typed thresholds, race history.
- Not enough covered weeks: measured volume unused, `reason` says why.

## Testing

- Unit: snapshot priority (covered-week rule, partial week excluded, < 3 weeks falls
  back, freshness windows, athlete override).
- Unit: tier rule (one-step promotion cap, gap demotes only for lab/field, the affected athlete's
  numbers as a regression case, existing beginner cases still pass).
- Unit: assessment persistence (insert on change only; predictions stored).
- Integration (scratch DB only, the suite truncates tables): plan creation stores
  `fitness_snapshot` and uses measured volume.
- `python scripts/golden_eval.py compare --service scheduler` to check plan drift for
  other users before deploy.

## Out of scope

- Automatically proposing plan changes when the snapshot changes.
- COROS sync stopping after 2026-09-25 for that athlete (separate feedback item).
- Regenerating the affected athlete's existing plans (an operator action after deploy).
