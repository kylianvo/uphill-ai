# Goal Determiner: Terrain Difficulty Scoring (sub-project 2 of 3)

## Context

The Goal Determiner (`RaceEstimator` in `backend/services/race_estimator.py`,
wired through `_goal_estimate_core` in `backend/main.py`) predicts finish
time from distance, elevation gain, and a physics model
(`PacingCalculator`). It has no concept of terrain technicality: a race
described as `"muddy rainy-season terrain", "technical hand-and-knees
scrambles on final climbs", "river crossings"` and a race described as
`"flat urban road"` at the same distance/elevation predict identically.

The `race_courses` KB already curates a `terrain: list[str]` field per race
(`services/kb_distiller.py:65`), already surfaced to `RaceEstimator`'s
caller for free via `MatchedRace.terrain` (`services/race_matcher.py:35`,
populated in `_to_matched_race`) whenever a race name resolves. No new KB
field or fetch is needed.

**Important finding that shapes this design**: the `terrain` field is *not*
a controlled vocabulary. Inspecting the actual curated data
(`backend/kb_seed/race_courses.json`, 37 races) shows it's mostly free-text
scene descriptions and landmarks — `"dragon bridge"`, `"marina bay sands"`,
`"karst sandstone pillar formations ('avatar mountains')"` — mixed with
genuine difficulty signals — `"technical hand-and-knees scrambles on final
climbs"`, `"muddy rainy-season terrain"`, `"river crossings"`,
`"exposed tree roots"`. A fixed tag-equality lookup table (viable if the
field were an enum like `["muddy", "technical", "rocky", "runnable",
"road"]`, as the schema comment optimistically suggests) would only match a
small fraction of real entries. This spec instead scans for
difficulty-signal keywords matched on **whole-word boundaries** (with an
optional trailing plural `s`) anywhere in the tag text.

Plain substring matching was tried first and rejected: against the actual
curated corpus, the `"sand"` keyword matched inside the landmark tag
`"Marina Bay Sands"`, wrongly scoring a race that has no sand terrain at
all. Switching to strict word-boundary matching (`\bsand\b`) fixes that,
but a naive word-boundary implementation requiring an exact trailing
boundary on every keyword then silently stopped matching genuine plural
forms already present in the KB — `"river crossings"` and `"long
staircases"` — since the keywords are singular (`river crossing`,
`staircase`). The corrected approach is word-boundary matching with an
optional plural suffix (`s?`) on every keyword except `"sand"`, which stays
exact-boundary-only so it doesn't re-match "Sands".

This is sub-project 2 of 3 for Goal Determiner accuracy (sub-project 1,
percentile-based calibration, is implemented and on branch
`claude/goal-determiner-algorithm-6a018f`; sub-project 3, GPX-derived real
course profiles, is not yet designed). Independent of both — no shared
code with sub-project 1's percentile blend.

## Goal

Penalize the physics-only prediction for courses whose curated terrain
description signals genuine technical difficulty (mud, scrambling, loose
footing, river crossings, steep pitches, etc.), using only data already in
the KB — no new ingestion, no new schema.

## Non-goals

- No new KB schema or curation pass — reuses the existing `terrain: list[str]`.
- No per-checkpoint/per-segment terrain variation — until sub-project 3
  (real GPX profiles) exists, every course is a uniform synthesized
  profile, so a single whole-course multiplier is the only meaningful
  granularity.
- No "flat"/"runnable" discount — a flat course is already captured by
  `elevation_gain_m = 0`; stacking a second discount for descriptive terms
  like "flat urban road" would double-count. This is one-directional:
  only confirmed difficulty signals add time.
- No change to `PacingCalculator` (`grade`/`altitude`/`fatigue`/`weather`/
  `split_bias` multipliers) — the terrain multiplier is algebraically
  folded into `RaceEstimator`'s existing pace/time conversions instead (see
  Algorithm), so `services/pacing_calculator.py` is untouched and Pace
  Strategy's real-GPX callers are unaffected.
- No change to sub-project 1's percentile blend — terrain scoring only
  touches `predicted_time_mins`/`base_flat_pace_min_km` derivation, which
  sub-project 1 already treats as an opaque input to blend against.

## Algorithm

### 1. Keyword table and scoring

`RaceEstimator.terrain_multiplier(terrain_tags: list[str] | None) -> float`:

- Join all tags into one lowercase string (space-separated).
- For each keyword below present as a whole word anywhere in that joined
  string — matched on word boundaries, with an optional trailing plural
  `s` (except `"sand"`, which requires an exact trailing boundary so it
  doesn't match "Sands"), and `"scramb"` as a deliberate prefix-only
  exception with no trailing boundary at all (so it covers scramble/
  scrambling/scrambles) — add its weight once (regardless of how many tags
  or how many times it appears).
- Sum the matched weights, cap the sum at `TERRAIN_CAP = 0.30`, return
  `1.0 + capped_sum`.
- Empty/`None` input returns `1.0` (no-op).

```
_TERRAIN_KEYWORDS: dict[str, float] = {
    "technical": 0.07,
    "scramb": 0.08,          # scramble / scrambling / scrambles
    "scree": 0.06,
    "slippery": 0.06,
    "muddy": 0.05,
    "rocky": 0.05,
    "river crossing": 0.05,
    "steep": 0.04,
    "volcanic": 0.05,        # volcanic ash / volcanic sand / volcanic terrain
    "karst": 0.03,
    "exposed root": 0.03,
    "staircase": 0.03,
    "singletrack": 0.02,
    "single track": 0.02,
    "sand": 0.02,
    "steps": 0.02,
    "jungle": 0.02,
}
TERRAIN_CAP = 0.30
```

Worked example: VMM 70km's curated terrain includes `"technical
hand-and-knees scrambles on final climbs"` and `"continuously slippery,
dark single trail deep in the jungle"` → matches `technical` (0.07),
`scramb` (0.08), `slippery` (0.06), `single track`... (only if the exact
substring `"single track"` appears — `"single trail"` does not match either
`singletrack` or `single track`, which is correct: it's a distinct phrase
not covered by either keyword, so it contributes 0 — a known, accepted gap,
not a bug) and `jungle` (0.02) → sum `0.23` → multiplier `1.23`.

### 2. Where it applies — algebraically folded into pace/time conversion

No changes to `PacingCalculator`. Instead, `RaceEstimator`'s two pace/time
conversion functions each gain a `terrain_multiplier: float = 1.0`
parameter (default is a no-op, so existing callers — e.g. Pace Strategy's
real-checkpoint path via `PacingCalculator` directly — are unaffected):

**Target course (slows the forward prediction):**
```python
@staticmethod
def predict_time_mins(checkpoints, base_flat_pace_min_km, terrain_multiplier: float = 1.0) -> float:
    unit_time = PacingCalculator.solve_base_pace(checkpoints, target_time_mins=1.0)
    return (base_flat_pace_min_km / unit_time) * terrain_multiplier
```
The physics-only predicted time is scaled up directly by the target
course's terrain multiplier.

**Reference course (extracts a faster underlying base pace from a result
run on a harder course):**
```python
@classmethod
def base_pace_from_result(cls, checkpoints, finish_time_mins, terrain_multiplier: float = 1.0) -> float:
    return PacingCalculator.solve_base_pace(checkpoints, target_time_mins=finish_time_mins / terrain_multiplier)
```
Since `solve_base_pace(checkpoints, X)` is linear in `X`
(`X / physics_unit_time`), dividing the target finish time by
`terrain_multiplier` before the solve is algebraically equivalent to
inflating the course's physics unit-time by that multiplier — i.e. "this
runner's result on a technical course implies more raw fitness than the
same result on a physics-only-equivalent course would," extracting a
*faster* (lower-minutes-per-km) base pace than the untouched physics model
would. This is symmetric with how the target side works: the same
multiplier, applied on whichever side of the equation the technical course
sits.

### 3. Wiring into `RaceEstimator.estimate()` and `_goal_estimate_core`

`estimate()` gains a `terrain_tags: list[str] | None = None` parameter for
the target course; the existing `reference: dict | None` parameter gains an
optional `terrain_tags` key.

```python
@classmethod
def estimate(cls, distance_km, elevation_gain_m, base_flat_pace_min_km=None,
             reference=None, weeks_to_race=None, terrain_tags=None) -> dict:
    target_terrain_mult = cls.terrain_multiplier(terrain_tags)
    ref_terrain_mult = None
    if base_flat_pace_min_km is None:
        ...
        ref_terrain_mult = cls.terrain_multiplier(reference.get("terrain_tags"))
        base_flat_pace_min_km = cls.base_pace_from_result(
            ref_course, reference["finish_time_mins"], terrain_multiplier=ref_terrain_mult
        )
    course = cls.synthesize_course(distance_km, elevation_gain_m)
    predicted = cls.predict_time_mins(course, base_flat_pace_min_km, terrain_multiplier=target_terrain_mult)
    ...
    return {
        ...,  # existing fields unchanged
        "terrain_multiplier_target": round(target_terrain_mult, 3),
        "terrain_multiplier_reference": round(ref_terrain_mult, 3) if ref_terrain_mult is not None else None,
    }
```

In `backend/main.py`'s `_goal_estimate_core`, pass the already-resolved
`MatchedRace.terrain` through (no new KB read — `matched_target`/
`matched_ref` are already fetched today for distance/elevation backfill):

```python
    estimate = RaceEstimator.estimate(
        distance_km=distance_km,
        elevation_gain_m=elevation_gain_m,
        base_flat_pace_min_km=request.flat_pace_min_km,
        reference={**reference, "terrain_tags": matched_ref.terrain} if reference and matched_ref else reference,
        weeks_to_race=request.weeks_to_race,
        terrain_tags=matched_target.terrain if matched_target else None,
    )
```

(Exact reference-dict construction is an implementation detail for the
plan; the requirement is: `terrain_tags` flows from `matched_target`/
`matched_ref` into `estimate()` whenever a KB match resolved, and is absent/
`None` otherwise — manually-entered distance/elevation with no race-name
match gets `terrain_multiplier_target = 1.0`, unchanged from today.)

## API changes

`_goal_estimate_core` response gains two fields via the `estimate` dict
spread (`**estimate` in the response, same mechanism sub-project 1 uses):

- `terrain_multiplier_target: float` — always present, `1.0` when no
  terrain signal matched or no KB match resolved.
- `terrain_multiplier_reference: float | None` — present when a reference
  result was used to derive `base_flat_pace_min_km`; `None` when
  `flat_pace_min_km` was supplied directly (no reference course to score).

No existing field changes shape or meaning. `predicted_time_mins` and
`adjusted_time_mins` now implicitly include the terrain adjustment (same
way they already implicitly include elevation/altitude/fatigue) — there is
no separate "pre-terrain" physics number, matching how every other
`PacingCalculator` multiplier already works today (elevation, altitude,
fatigue are never reported as a separate "before" value either).

## Interaction with sub-project 1 (percentile blend)

None required. Sub-project 1's blend operates on `adjusted_time_mins`
(post-terrain, post-`weeks_to_race`) as one opaque number and averages it
with `percentile_transfer_mins`. Terrain scoring changes what
`adjusted_time_mins` *is* before that blend runs, same as it would for any
other physics input — no interface change on either side.

## Testing

- Unit tests (`backend/tests/unit/test_race_estimator.py`):
  - `terrain_multiplier`: no tags → `1.0`; single keyword match; multiple
    non-overlapping keywords sum correctly; repeated keyword across
    multiple tags counts once; cap kicks in when many keywords match
    (verify result never exceeds `1.3`); the VMM worked example above as a
    named regression case; a tag list of pure landmarks/place-names (no
    keyword matches) returns exactly `1.0`.
  - `predict_time_mins` with `terrain_multiplier > 1.0`: result is exactly
    `terrain_multiplier` times the `terrain_multiplier=1.0` result on the
    same course/pace (multiplicative, no other side effect).
  - `base_pace_from_result` with `terrain_multiplier > 1.0`: extracted base
    pace is faster (lower minutes/km) than the `terrain_multiplier=1.0`
    extraction for the same course/finish time; round-trip check —
    `predict_time_mins(course, base_pace_from_result(course, T,
    terrain_multiplier=m), terrain_multiplier=m) ≈ T` for some `m > 1.0`
    (confirms the algebraic inverse relationship holds).
  - `estimate()`: `terrain_multiplier_target`/`terrain_multiplier_reference`
    present/absent per the rules above; a target-only technical course
    (no reference terrain) produces a slower `predicted_time_mins` than the
    same call with `terrain_tags=None`, all else equal.
- Integration test (`backend/tests/integration/test_coach_tools.py`):
  regression guard confirming `_goal_estimate_core` still returns 200 and
  identical `adjusted_time_mins` for a request with no `race_name` (no KB
  match, no terrain data) versus the pre-change baseline; a new test with a
  `race_name` matching a KB entry whose terrain includes a difficulty
  keyword, confirming `terrain_multiplier_target > 1.0` is present in the
  response and `adjusted_time_mins` is slower than the same request against
  a KB entry with no matching keywords.

## Open items for a future sub-project (not this one)

- GPX-derived real course profiles (sub-project 3): would let terrain
  difficulty eventually vary per-segment instead of as a single
  whole-course multiplier, once real elevation/route data exists to anchor
  segments to.
