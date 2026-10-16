# Trail session content and plan-flow gap fixes

Date: 2026-10-16. Source: beta feedback from quangtranultra (plan 108, Aptrc 80km) and a
brainstorm with Viet. Builds on PR #142, which is **held** (Viet's decision): its iOS
sprint-step parser fix and treadmill flat-pace fix stay; its km-effort pace logic is
reworked to the B2 formula on the same branch before anything merges.

## Why

Vietnamese city runners (HCMC, Hanoi) train on flat roads all week and travel to a
mountain on weekends. HCMC runners take a bus to Núi Dinh (~1.5 h each way, on site
~7:00–14:00). A mountain day is the key session of the week, and the plan currently
gets it wrong in three ways:

1. Trail runs show road pace. Plan 108's 130 min long run showed 4:54–4:30 /km and
   27.7 km for 850 m D+. Viet's real Núi Dinh runs are ~60 m D+/km at ~4.8 km/h in Zone 2.
2. Climbing is far below the real mountain: the plan gives 19–31 m/km, Núi Dinh is ~60.
3. Sessions are too short for the trip: 80–85 min on the mountain after 3 h on a bus.

Plus display gaps: hill sprints vanish or show a meaningless pace, and coach edits can
jump an athlete's pace to app defaults.

Success: Quang (and any HCMC/Hanoi runner) opens a mountain-day session and the time,
km, D+ and pace all look like what he would actually run there.

## Goals

- Mountain-day sessions are sized by **time**, with estimated km, D+, zone and **trail
  pace** shown with equal weight.
- D+ and pace come from the athlete's chosen training mountain, not the race and not
  a road pace.
- Generated mountain-day sessions are long enough to justify the trip.
- Coaches can set a trail session by km + D+ instead.
- Interval/sprint structure is shown on web and iOS whatever way the AI wrote it.

## Non-goals

- Learning each runner's own trail speed from their activity history (not enough data
  yet).
- Grade-by-grade route modelling or GPX loops for training mountains.
- Changing plan 108's existing rows (handled separately, by hand, after this ships).
- Distance-based track reps beyond displaying them correctly (none exist on prod yet).

## Anti-goals

- A mountain day that asks for climbing the mountain can't deliver (e.g. sizing a 3 h
  long run from Bà Đen's 176 m/km).
- Treadmill speeds slowed twice (flat pace must stay the treadmill input; fixed in #142).
- Numbers on the card that disagree with each other (km, D+, pace, time must come from
  one formula).

## Part A — Plan-flow gap fixes (small, ship first)

A1. **Coach zone edit uses the wrong pace source.** `main.py` (`_pace_and_hr_for_zone`,
    ~line 585) builds paces from the profile's Zone 2 fields via `estimate_pace_zones`;
    the plan uses `PlanGenerator.resolve_pace_zones` (threshold-based). Quang's Zone 2
    fields are still the 6:30–5:45 defaults, so one zone edit jumps his pace ~1:00/km.
    Fix: use `resolve_pace_zones`, same as `_generate_single_workout`.

A2. **iOS rep detection** (`WorkoutStepParser.swift`):
    - `detectReps` only matches `N x M min`, and only on `parts.main.first`. Must also
      match seconds (`8 x 12s`, `12-second`, `N reps of 10s`), distance (`5 x 400m`,
      `4 x 1 km`) and Vietnamese (`phút`, `giây`), scanning every main step.
    - Rep values render with `Int(val)`: 0.4 km → "0 km", 1.5 min → "1 min". Format like
      web's `fmtRepValue`.
    - Max-effort sprints (Hill Sprint/Strides titles, Zone 5) show no pace after the reps.

A3. **Backend fills rep fields from the description** (my call): when a run's Process
    text contains one clean rep block and the AI left `interval_reps/value/unit` empty,
    `resolve_interval_summary` parses it, for any run type (today: Interval and Walk/Run
    only). Prod: 98 of 133 Interval rows and 73 Easy rows (strides/sprints) have reps only
    in text. Web's chip (`WorkoutCard.tsx`) then shows them too; widen its type gate to
    any row with rep fields.

A4. **Web parser has no Vietnamese warm-up/cool-down cues**
    (`frontend/src/utils/workoutDescription.ts`): add "khởi động" (warm-up) and
    leading "thả lỏng"/"hạ nhiệt" (cool-down), with the same lead-of-step rule as iOS.

## Part B — Trail session content

### B1. Training mountains

A curated list in code (my call: a constant next to `services/training_venues.py`, not
the KB — it is small and changes rarely):

| Area | Mountain | D+ per km | Use |
|---|---|---|---|
| HCMC | Núi Dinh (default) | 60 | long runs, repeats |
| HCMC | Núi Chứa Chan | 85 | long runs |
| HCMC | Núi Bà Đen | 176 | hill repeats only |
| Hanoi | Núi Hàm Lợn (default) | 45 | long runs, repeats |
| Dalat | Dalat trails (avg Lâm Đồng Trail + Vietnam Highlands Trail) | 47 | all |
| Sapa | Sapa trails (VMM) | 56 | all |
| — | Other / none | race course D+/km, else today's behaviour | |

Sources: Viet's 4 Núi Dinh COROS runs (57.8–60.6 m/km), Viet's Chứa Chan 59 km/5000 m,
Bà Đen 5 km/881 m, Hàm Lợn ~22 km/1000 m, `kb_seed/race_courses.json` for Dalat and VMM
(long distances; DUT left out — most of its distances have no D+).

A "repeats only" mountain never sizes a long run; on such a mountain day the long run
uses the area's default long-run mountain rate (my call).

The athlete picks one training mountain in Schedule Preferences, next to the existing
`mountain_days` field (web `TrainingVenueFields`, iOS `TrainingVenueSection`). New plan
column, both in `init_db()` and an Alembic migration (db-migration skill).

### B2. One formula for time, km, D+ and pace

From Quang: "flat 5:00 at HR 150 → trail 8:00/km at 50 m D+/km, same HR".

    trail_pace = flat_zone_pace × (1 + 0.012 × climb_rate)     # climb_rate = m D+ per km
    km         = minutes / trail_pace
    D+         = km × climb_rate

Applies to Easy and Long Run sessions on a mountain day (or any trail session when the
plan has no mountain days but trail terrain). Tempo/Interval keep zone paces. Treadmill
settings keep using the flat pace.

This **replaces PR #142's km-effort rule** (100 m = 1 km, 60% distance floor); the floor
is no longer needed because D+ is derived from km. The AI's own `elevation_gain_m` is
ignored for these sessions (same backstop pattern as treadmill settings).

Example, Quang (flat Z2 4:54–4:30), Núi Dinh, 3.5 h: pace ~8:25–7:45, ~26 km, ~1550 m.

### B3. Mountain-day duration

- Generated sessions on a mountain day last at least the athlete's mountain minimum.
  Default 3 h for HCMC and Hanoi mountains, none for Dalat/Sapa (my call for Hanoi and
  for making it editable next to the mountain picker).
- The ceiling follows the trip window (HCMC bus ~7:00–14:00 → ~4.5–5 h moving).
- When the phase wants a short weekend session, the **plan decides first**:
  - recovery week or early taper → "chill": keep the minimum time, Zone 1, mostly
    power-hiking;
  - final taper days or beginner tier → "skip": short road/treadmill session in the city.
- The **athlete can switch** chill ↔ skip on that workout without the rest of the week
  being rearranged.
- These are prompt rules → LLM change process (Langfuse prompt version, golden eval,
  staging → production label), plus a post-processing backstop that enforces the
  minimum.

### B4. Coach km + D+ mode

A coach (coach role on the athlete's plan) can set a trail session by km + D+. Time is
then derived backwards with the same formula and the coach's numbers are never
recalculated. The mountain minimum does not apply to coach-set sessions. Watch push
targets time for generated sessions, distance for coach-set ones (my guess, confirm in
plan review).

### B5. Card content (web + iOS)

Duration, est. km, est. D+, zone (+ HR range), trail pace — equal weight. Pace label says
it is a trail pace for this mountain. No new visual design; reuse the existing workout
card/detail layout.

## Constraints

- Prompt changes follow `.claude/skills/llm-change-process/SKILL.md`.
- Schema changes go in `db.py:init_db()` and Alembic.
- UI changes need local screenshots (`ui-screenshot-evidence`).
- iOS ships via TestFlight; backend deploy by hand (see prod deploy notes).

## Left to the builder

- Exact regexes for rep detection and the shared test corpus (use real prod
  descriptions).
- Where the mountain constant lives and its exact shape.
- How "chill/skip" is stored on the workout and shown as a toggle.
- Order: Part A first (independent), then B1 → B2 → B3/B4 → B5.
