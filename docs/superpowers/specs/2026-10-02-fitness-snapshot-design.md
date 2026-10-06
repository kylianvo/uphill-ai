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
- **Tier (revised):** a composite of four dimensions (load, performance, experience,
  physiology), clamped to within one tier of the load tier. Supersedes the earlier
  "volume first, promote one step, demote on gap" rule. Physiology counts only when
  the thresholds were measured.
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
| Chronic load cap | 12-week mean of complete covered weeks (needs ≥ 8) | None (cap not applied) | Effective volume = min(4-week mean, 1.15 × 12-week mean); km and vert scaled together. A spike cannot lift the tier past what the long-term load supports; a dip still uses the lower 4-week value |
| Performance (tiering) | Faster of COROS marathon prediction and best road result as a Riegel marathon equivalent; UTMB index; VO2max, then threshold pace, as fallbacks | None | Assessment ≤ 60 days. VO2max and the other predictions are prompt context only; race results stay in the existing RACE HISTORY block and long-run ceiling |
| AeT/AnT | Typed values | None | Usable for tiering only when `threshold_source` is `lab` or `field` |
| Load and recovery | `daily_metrics`, last 14 days: load ratio, HRV trend, resting HR | None | Prompt context only, never tiering |

When the athlete overrides the pre-filled km/week in the plan form, the typed value
wins over measured volume and the snapshot says so (`reason: "athlete override"`).

## Tier rule: composite level score

The tier comes from four dimensions combined, not from volume alone. Each maps to a
continuous **level** on one scale (0 beginner, 1 novice, 2 recreational, 3 sub-elite,
4 elite, capped at 4.99), interpolated linearly between anchors. All anchors and weights
are conventional defaults, unsourced like the old volume bands, kept in one table in
`services/athlete_tier.py`.

| Dimension | Weight | Input | Level anchors (value → level) |
|---|---|---|---|
| Load | 0.45 | Effort-km = weekly km + vert/100 (vert only when measured), chronic-capped | 0→0, 15→1, 40→2, 80→3, 160→4, 320→5 |
| Performance | 0.30 | Fallback chain, first available: best of {marathon time, UTMB index}; else VO2max; else threshold pace | Marathon 7:00→0, 5:30→1, 4:15→2, 3:10→3, 2:40→4, 2:10→5 (women ×1.12). UTMB 250→1, 400→2, 550→3, 700→4, 850→5. VO2max (men) 38→1, 45→2, 55→3, 65→4, 75→5 (women ×0.9). Threshold pace (men) 6:00→1, 5:00→2, 4:15→3, 3:40→4, 3:10→5 per km (women ×1.12) |
| Experience | 0.15 | Longest proven run or imported race (km) | 0→0, 10→1, 21→2, 42→3, 80→4, 160→5 |
| Physiology | 0.10 | Only when `threshold_source` is `lab`/`field`: mean of AeT/AnT-gap level and AnT-as-%-of-max-HR level | Gap 0.50→0, 0.35→1, 0.30→2, 0.10→3, 0.07→4, 0.04→5. AnT/max 0.80→2, 0.87→3, 0.91→4, 0.94→5 |

"Marathon time" is the faster of the COROS marathon prediction (≤ 60 days old) and the
best recent road result converted with Riegel (T × (42.195 / D)^1.06; imported VBM road
results, 5–42.2 km, last 12 months, not DNF or hidden). Field percentiles are not used:
field depth differs too much between races and countries. Trail results count through
the UTMB index, which UTMB already normalises by race.

The UTMB index is read from the athlete's own claim (`race_profile_claims.meta.indexes`,
"general" entry), with the `utmb_runners` mirror as fallback. The mirror was empty on
production (2026-10), so the old mirror-only lookup returned None for every athlete.

VO2max and threshold pace are fallbacks inside Performance, never a separate dimension:
COROS derives its race predictor from them, so counting both would weight one measurement
twice. Running level, resting HR, HRV, load ratio and sleep are not tier inputs (proprietary
composite, not comparable between athletes, or readiness rather than level).

Procedure:

1. Explicit per-plan override wins. **Bug fixed alongside:** `plans.athlete_tier`
   stores the last resolved tier, and next block / adapt week passed it back as the
   explicit override, freezing every plan at its first tier. Re-plans now pass it as
   `previous_tier` and no explicit override; nothing in the product sets a real
   override today.
2. Beginner rules (goal "start running", max continuous jog under 10 min) force `beginner`.
3. Compute each available dimension's level. **Experience is lift-only**: it joins the
   mean only when its level is above the mean of the others, because a missing or short
   long run in our data (30-day COROS backfill, no imports) is not evidence of
   inexperience.
4. Score = weighted mean over the dimensions present (weights rescaled). No dimension
   at all → default tier.
5. Tier = floor(score), then **clamped to within one tier of the load tier** (the tier the
   Load level alone gives; the default tier when volume is unknown). Fast runners on low
   volume cannot get elite caps; a measured wide gap cannot drop a high-volume runner two
   tiers.
6. **Hysteresis** on re-plans: if the result is one step from `previous_tier` and the
   score is within 0.1 of the boundary between them, keep `previous_tier`.

The function returns the tier and per-dimension levels with reasons (e.g. "load 4.2 ·
performance 3.6 · physiology not used (source unknown) → 3.9 sub_elite"), stored in
`plans.fitness_snapshot` and shown to the model in the snapshot block.

Worked examples (numbers from the reference accounts, rounded):

| Athlete | Load | Performance | Experience | Physiology | Score | Tier |
|---|---|---|---|---|---|---|
| Elite reporter (~187 effort-km, predictor ~2:53, longest 50 km) | 4.2 | 3.6 | 3.2 (not above mean, unused) | unknown source, unused | 3.9 | sub_elite |
| Same, no COROS (typed 140 km) | 3.75 | — | — | — | 3.75 | sub_elite |
| Recreational owner (~73 effort-km, VO2max 57, longest 26 km) | 2.8 | 3.2 (VO2max fallback) | 2.2 unused | — | 3.0- | recreational, close to the edge |

## Consumers

`fitness_snapshot.build` replaces the raw profile fields for volume, threshold pace and
tier inputs in:

- Plan creation, self-serve and coach-created (`main.py` around the two
  `get_user_activity_ceiling` call sites, ~1014 and ~1817).
- Next block / adapt week (`main.py` ~2348, `services/week_rebuild.py`).
- Goal context (`services/goal_context.py`, which already reads VO2max; it gains the
  race predictor).
- Coach chat context (`services/coach_context.py`) and the chat route's own profile
  (`routers/coach_chat.py`): weekly km from the snapshot with its source, and the tier
  from the active plan (previously read from `users`, which has no tier column, so chat
  never saw it).
- The human-coach co-pilot block (`main.py` `_build_athlete_context_block`): one
  "Level" line from `plans.fitness_snapshot`.
- Not changed: Gear Finder / Nutrition Lab (weekly km barely affects their output) and
  analytics (`users.current_weekly_km` stays the self-reported history).

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

## Evaluation and release

- Golden set: three synthetic look-alike scheduler fixtures (an elite with high measured
  volume and unknown-source thresholds, the same athlete without COROS, a recreational
  runner with field-tested thresholds). They are shaped on two real accounts but copy no
  real values. The eval gate fails on a tier mismatch or a week-2 volume outside the
  fixture's range.
- Live signals on `plan_generation` traces: `plan_tier` and `plan_volume_fit`.
- Prompt experiment: a candidate `plan_generation` version in Langfuse (label
  `snapshot-exp`) that tells Gemini how to use the snapshot, evaluated against the
  `production` version on the golden set before any promotion.
- Release: hand deploy to staging, then production (backups, `alembic stamp head`,
  `LANGFUSE_RELEASE`), then promote the prompt label if the experiment passed.

## Out of scope

- Automatically proposing plan changes when the snapshot changes.
- COROS sync stopping after 2026-09-25 for that athlete (separate feedback item).
- Regenerating the affected athlete's existing plans (an operator action after deploy).
