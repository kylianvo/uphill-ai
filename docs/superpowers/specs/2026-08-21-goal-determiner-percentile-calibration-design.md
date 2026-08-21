# Goal Determiner: Percentile-Based Calibration (sub-project 1 of 3)

## Context

The Goal Determiner (`RaceEstimator` + `_goal_estimate_core` in `backend/main.py`)
currently predicts a runner's finish time using only a physics model
(`PacingCalculator`) applied to a *synthesized* course profile built from two
scalars: total distance and total elevation gain. This ignores real-world
race outcomes entirely, even though the `race_courses` KB already curates
rich per-year results data (`services/kb_distiller.py`'s `RaceResultEntry`):
`finishers`, `winner_time`, and `percentiles.overall/men/women` (p5/p10/p25/
p50/p75/p90 finish times).

Today only `results[0].winner_time` is used, for an optional secondary
`rank_transfer_mins` field (`main.py`, `_goal_estimate_core`). Percentile data
is fetched and returned to the frontend as `benchmarks` for display, but never
used to adjust the estimate. Winner-time-only rank transfer is noisy — a
single elite outlier result — and users report the tool over-rates them,
particularly against real field outcomes.

This is sub-project 1 of 3 identified for improving Goal Determiner accuracy
(the other two — terrain difficulty scoring, and GPX-derived real course
profiles — are separate, larger changes requiring new KB schema/ingestion and
are out of scope here). This sub-project uses data that already exists in the
KB, so it ships independently and immediately.

## Goal

Use the curated `percentiles` data to pull the physics-only prediction toward
real field outcomes on the target course, when both the target race and the
runner's reference race have curated results in the KB.

## Non-goals

- No new KB schema or ingestion — uses existing `RaceResultEntry.percentiles`.
- No gender-specific transfer — no gender field exists on the user profile
  today, so only the `overall` percentile group is used.
- No change to the A/B/C spread factors (`AMBITIOUS_FACTOR`/`SAFE_FACTOR`) or
  the `weeks_to_race` improvement adjustment — those are separate concerns.
- No change to `rank_transfer_mins` — it stays as-is, reported alongside the
  new field for comparison/backward compatibility.

## Algorithm

### 1. Build an averaged percentile curve per race

For a given race name and distance, reuse `race_matcher.race_benchmarks()`'s
existing distance filter (curated result years within ~15% of the target
distance). For each matching year, parse `percentiles.overall`
(`p5, p10, p25, p50, p75, p90`, each an `"h:mm:ss"` string) into minutes.

Average each percentile bucket independently across all matching years that
have it present, producing a single 6-point curve:

```
points = [(5, avg_p5), (10, avg_p10), (25, avg_p25), (50, avg_p50), (75, avg_p75), (90, avg_p90)]
```

**Validation**: a year's percentile set is skipped (not included in the
average) if its parsed times are not monotonically non-decreasing from p5 to
p90 (guards against bad KB data). If fewer than 1 valid year remains, the
curve is unavailable.

### 2. Find the runner's percentile rank on the reference race

Given the reference race's curve and the runner's `reference_time` (minutes),
find the percentile rank via piecewise-linear interpolation over the 6
points, treating `(percentile, time)` pairs as an increasing function of
percentile.

- If `reference_time` falls between two known points, linearly interpolate
  the percentile.
- If faster than `p5` or slower than `p90`, extrapolate linearly using the
  nearest segment's slope (do not hard-clamp to 5 or 90 — an elite reference
  time should still project a meaningfully fast rank, not just "top 5%").

### 3. Map that rank onto the target race's curve

Apply the same interpolation in reverse on the target race's curve: given the
percentile rank found in step 2, solve for the corresponding time
(`percentile_transfer_mins`). Same extrapolation rule at the ends.

### 4. Blend into the primary estimate

```
adjusted_time_mins =
    (physics_adjusted_time_mins + percentile_transfer_mins) / 2
    if percentile_transfer_mins is available
    else physics_adjusted_time_mins  # unchanged from today
```

`physics_adjusted_time_mins` is the existing `RaceEstimator.estimate()`
output (post `weeks_to_race` improvement). The blend is a simple 50/50
average — no confidence weighting.

### 5. A/B/C goals

Computed from the blended `adjusted_time_mins` exactly as today:
`ambitious = adjusted * 0.95`, `realistic = adjusted`, `safe = adjusted *
1.08`.

## API changes

`_goal_estimate_core` response gains two fields (both `None`/absent when
percentile data isn't available for both races):

- `percentile_transfer_mins: float | None` — the step-3 result, pre-blend.
- `percentile_years_used: {"target": int, "reference": int} | None` — count
  of curated years that fed each race's averaged curve, for UI transparency
  (e.g. "based on 3 years of results").

`predicted_time_mins` (the pure physics number, pre-blend) is unchanged and
still returned — so the raw physics prediction remains inspectable even when
blending occurs. `adjusted_time_mins` and `goals` reflect the blended value
per §4 above.

`rank_transfer_mins` (existing field) is unchanged and still computed
independently.

## Gating / fallback

Percentile blending only activates when **all** of the following hold, same
spirit as the existing `rank_transfer_mins` gate:

- `request.race_name` resolves to a KB entry with a curated `results` block
  containing valid percentile data (per §1's validation) for the target
  distance.
- `request.reference_race_name` similarly resolves with valid percentile
  data.
- `request.reference_time` and `ref_time_mins` are present (as required
  today for any reference-based estimate).

If any of these are missing, behavior is identical to today: physics-only
`adjusted_time_mins`, `percentile_transfer_mins`/`percentile_years_used`
omitted from the response.

## Implementation location

- `backend/services/race_estimator.py`:
  - New `RaceEstimator.percentile_curve(results: list[dict], distance_km:
    float) -> list[tuple[float, float]] | None` — builds/averages/validates
    the 6-point curve from a race's curated `results` (mirrors the existing
    distance-filter logic in `race_matcher.race_benchmarks`).
  - New `RaceEstimator.interpolate_percentile(curve, *, time_mins=None,
    percentile=None) -> float` — bidirectional piecewise-linear lookup with
    slope extrapolation at the ends (used both directions in steps 2 and 3).
  - New `RaceEstimator.percentile_transfer_mins(reference_curve,
    reference_time_mins, target_curve) -> float` — composes steps 2+3.
- `backend/main.py`, `_goal_estimate_core`: after the existing
  `rank_transfer_mins` block, build both races' curves from `target_bench`/
  `ref_bench` (already fetched there), call `percentile_transfer_mins`, and
  recompute `adjusted_time_mins`/`goals` via the blend when available.

## Testing

- Unit tests (`backend/services/race_estimator.py`'s test module):
  - `percentile_curve`: multi-year averaging, skip of non-monotonic year,
    `None` when zero valid years.
  - `interpolate_percentile`: exact point lookup, midpoint interpolation
    (both directions: time→percentile and percentile→time), extrapolation
    beyond p5 and beyond p90.
  - `percentile_transfer_mins`: end-to-end on a synthetic pair of curves with
    a known expected transfer time.
- Integration test on `_goal_estimate_core`:
  - Both races have curated percentile data → `adjusted_time_mins` reflects
    the 50/50 blend; `percentile_transfer_mins`/`percentile_years_used`
    present.
  - One or both races missing curated data → response identical to current
    behavior (regression guard), new fields absent.

## Open items for a future sub-project (not this one)

- Terrain/technicality scoring (needs new KB schema + scoring source).
- GPX-derived real course profiles feeding `synthesize_course` (needs a
  curated-profile field on `race_courses` KB entries and an ingestion path,
  independent of a given runner's own late GPX upload).
