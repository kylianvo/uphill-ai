# Goal Determiner: GPX-Derived Real Course Profiles (sub-project 3 of 3)

## Context

`RaceEstimator.synthesize_course()` (`backend/services/race_estimator.py`)
fabricates a course from two scalars — `distance_km`, `elevation_gain_m` —
spreading gain evenly per km and setting `segment_loss_meters =
segment_gain_meters`. This has two known consequences (identified earlier
in the Goal Determiner accuracy review):

1. **Grade is always assumed uniform at `ASSUMED_HILL_GRADE = 0.10`**
   (`pacing_calculator.py:23`) inside `_segment_parts` — a course with one
   brutal 1000m climb and a long gentle descent gets smoothed into rolling
   hills, understating real climbing difficulty.
2. **Altitude never engages.** `synthesize_course` never sets
   `elevation_meters` on any checkpoint, so `cp_elev` defaults to `0.0`
   everywhere and `altitude_multiplier` (meant to activate above 1500m
   absolute elevation) is always `1.0`, regardless of the target race's
   actual altitude.

Meanwhile `GpxParser.parse()` (`backend/parsers/gpx_parser.py`) already
produces real checkpoints — `distance_meters`, `elevation_meters`,
`segment_gain_meters`, `segment_loss_meters` — from an actual `.gpx` track.
This is *already* the exact shape `PacingCalculator` consumes (it's used
today by Pace Strategy via `/api/parser/gpx`). Goal Determiner has simply
never been wired to use it.

**Timing constraint that shapes this design**: a runner's *own* race-day
GPX is often unavailable until 2-3 weeks before race day, but Goal
Determiner needs to work months out. The fix is to decouple the profile
from the individual runner: most races' *official route* GPX is published
by organizers well in advance (independent of when any one runner gets
their own copy), so the profile belongs on the race, curated once in the
KB — the same pattern `results`/`percentiles` already use — not attached
per-request by each runner.

This is sub-project 3 of 3 for Goal Determiner accuracy (sub-project 1,
percentile-based calibration, and sub-project 2, terrain difficulty
scoring, are both implemented and merged on branch
`claude/goal-determiner-algorithm-6a018f`). Independent of both — this
changes which *course shape* feeds the physics model; sub-project 2's
terrain multiplier is an orthogonal scalar applied on top regardless of
course source, and sub-project 1's percentile blend operates on the
resulting `adjusted_time_mins` as an opaque number either way.

## Goal

Let a race's `race_courses` KB entry carry a real, admin-curated elevation
profile (from an official-route GPX) per distance variant, and have
`RaceEstimator` use it instead of the synthetic uniform-grade assumption
whenever one is available — falling back to today's `synthesize_course`
behavior otherwise.

## Non-goals

- No per-runner/per-request ad-hoc GPX override for this sub-project — a
  runner's own late GPX upload has the timing problem described above; a
  future enhancement could add a request-level override, but it's not
  needed to fix the systemic "most courses have no real profile at all"
  gap this spec targets. YAGNI for now.
- No change to `GpxParser` itself — its output shape is already correct
  and unchanged.
- No change to sub-project 2's terrain scoring or sub-project 1's
  percentile blend — both remain exactly as implemented.
- No automatic GPX discovery/fetching from race websites — curation is an
  explicit admin action (upload the already-parsed checkpoints), matching
  how `results`/`percentiles` a race-results discovery IS automated
  (`discover_race_results_web`) but a course profile is not, since a GPX
  track isn't something Tavily web search can reliably locate and parse
  the way structured result tables can. A future sub-project could
  automate this; out of scope here.
- `synthesize_course` itself is not deleted or changed — it remains the
  fallback for every race without a curated profile (the overwhelming
  majority, at least initially).

## Algorithm

### 1. Storage — no new KB schema

`kb_chunks.payload` is JSONB; no `ALTER TABLE`, no Alembic migration.
Reuse the exact update mechanism `services/kb_distiller.py`'s
`save_race_results` already uses: `db.update_kb_chunk_payload(domain, kind,
title, payload)`, matched by **exact chunk title** (not fuzzy — the admin
curating this already knows/copies the race's exact KB title, same as
`save_race_results`'s `title` keys).

New payload key, keyed by the same `distance_label` string already used in
that race's `distances: [{label, distance_km, elevation_gain_m}]` array:

```json
{
  "course_profiles": {
    "70km": {
      "checkpoints": [ /* GpxParser.parse() checkpoint shape, verbatim */ ],
      "source": "gpx_upload",
      "curated_at": "2026-08-22"
    }
  }
}
```

Each checkpoint entry is exactly what `GpxParser.parse()` already produces
(`backend/parsers/gpx_parser.py`): `name`, `distance_meters`,
`elevation_meters`, `accumulated_gain_meters`, `accumulated_loss_meters`,
`segment_gain_meters`, `segment_loss_meters`, `latitude`, `longitude`. No
transformation needed — `PacingCalculator.solve_base_pace`/
`calculate_checkpoint_paces` already read exactly these keys
(`cp.get("elevation_meters")`, `cp.get("segment_gain_meters")`, etc.).

### 2. Ingestion — new admin endpoint

A curator already has (or can get) a race's official GPX file. Rather than
build a new multipart-upload-and-parse pipeline, reuse the existing
`/api/parser/gpx` endpoint the frontend's GPX tools already call: the
curator parses the GPX there first (getting back the checkpoints array in
the exact shape needed), then posts the result to a new endpoint that
attaches it to the matching KB chunk.

```python
class CourseProfileRequest(BaseModel):
    race_name: str  # exact race_courses KB chunk title
    distance_label: str  # must match an entry in that race's distances[]
    checkpoints: list[dict[str, Any]]  # GpxParser.parse()["checkpoints"], verbatim


@app.post("/api/kb/race-courses/course-profile")
def save_course_profile(request: CourseProfileRequest, user: dict[str, Any] = Depends(require_admin)):
    ...
```

Handler behavior (implemented in `services/kb_distiller.py`, mirroring
`save_race_results`'s structure):

1. Look up the chunk by exact `title == request.race_name` in
   `db.get_kb_chunks("race_courses", kind="race_profile")`. 404 if not
   found.
2. Validate `request.distance_label` appears in that chunk's
   `payload["distances"]` — 422 if not (curating a profile for a distance
   the race doesn't have is almost certainly a typo).
3. Validate `request.checkpoints` is non-empty and each entry has
   `distance_meters` present — 422 if not (catches an empty/malformed
   parse result before it corrupts a KB row).
4. Merge `{"checkpoints": request.checkpoints, "source": "gpx_upload",
   "curated_at": <today's ISO date>}` into
   `payload["course_profiles"][request.distance_label]`, **overwriting**
   any existing entry for that distance label (unlike
   `save_race_results`'s never-overwrite rule — a re-uploaded GPX for the
   same distance is a deliberate correction/update, not a duplicate to
   dedupe against).
5. Save via `db.update_kb_chunk_payload`, then re-export the seed file
   (`export_seed("race_courses", ...)`), matching `save_race_results`'s
   pattern so the curated profile flows to `kb_seed/race_courses.json` and
   is portable across environments via the existing `/api/kb/import`
   path.
6. Returns `{"race_name": ..., "distance_label": ..., "checkpoint_count": N}`.

### 3. Lookup — mirrors `race_benchmarks()`

New function in `services/race_matcher.py`:

```python
def course_profile(name: str | None, distance_label: str | None) -> list[dict[str, Any]] | None:
    """Curated GPX-derived checkpoints for a race+distance, if one has been
    uploaded. Returns None when the race is unknown, has no curated
    profile, or distance_label doesn't match a curated entry — callers
    fall back to synthesize_course()."""
```

Same fuzzy-match-then-read-payload structure as `race_benchmarks`
(`_score_chunks`, `_FUZZY_THRESHOLD` gate), reading
`payload.get("course_profiles", {}).get(distance_label, {}).get("checkpoints")`
instead of `payload.get("results")`. `distance_label` is required (not
optional like `race_benchmarks`'s `distance_km`) since profiles are always
keyed by a specific distance variant — a `None` or unresolved
`distance_label` returns `None` immediately, no lookup attempted.

### 4. `RaceEstimator` integration

`estimate()` gains a `target_checkpoints: list[dict[str, Any]] | None =
None` parameter; the existing `reference: dict | None` parameter gains an
optional `"checkpoints"` key. When present, used directly instead of
`synthesize_course(...)`:

```python
@classmethod
def estimate(cls, distance_km, elevation_gain_m, base_flat_pace_min_km=None,
             reference=None, weeks_to_race=None, terrain_tags=None,
             target_checkpoints=None) -> dict:
    ...
    if base_flat_pace_min_km is None:
        ...
        ref_checkpoints = reference.get("checkpoints")
        ref_course = ref_checkpoints if ref_checkpoints else cls.synthesize_course(
            reference["distance_km"], reference.get("elevation_gain_m") or 0.0
        )
        ref_terrain_mult = cls.terrain_multiplier(reference.get("terrain_tags"))
        base_flat_pace_min_km = cls.base_pace_from_result(
            ref_course, reference["finish_time_mins"], terrain_multiplier=ref_terrain_mult
        )

    target_terrain_mult = cls.terrain_multiplier(terrain_tags)
    course = target_checkpoints if target_checkpoints else cls.synthesize_course(distance_km, elevation_gain_m)
    predicted = cls.predict_time_mins(course, base_flat_pace_min_km, terrain_multiplier=target_terrain_mult)
    ...
    return {
        ...,  # existing fields unchanged
        "target_profile_source": "gpx" if target_checkpoints else "synthetic",
        "reference_profile_source": ("gpx" if ref_checkpoints else "synthetic") if reference else None,
    }
```

`predict_time_mins`/`base_pace_from_result` (already accepting arbitrary
checkpoint lists, since `synthesize_course`'s output was never
special-cased by them) need no changes — they already operate on whatever
checkpoint list they're handed, real or synthetic. Terrain scoring
(sub-project 2) and the improvement/A-B-C goal spread are unaffected —
they operate on the resulting `predicted`/`adjusted` scalar regardless of
which course source produced it.

### 5. Wiring into `_goal_estimate_core`

```python
    from services.race_matcher import course_profile, match_race, race_benchmarks

    target_checkpoints = (
        course_profile(request.race_name, matched_target.distance_label)
        if matched_target and matched_target.distance_label
        else None
    )
    ...
    if ref_time_mins and ref_distance:
        reference = {
            "distance_km": ref_distance,
            "elevation_gain_m": ref_gain or 0.0,
            "finish_time_mins": ref_time_mins,
            "terrain_tags": matched_ref.terrain if matched_ref else None,
            "checkpoints": (
                course_profile(request.reference_race_name, matched_ref.distance_label)
                if matched_ref and matched_ref.distance_label
                else None
            ),
        }
    ...
    estimate = RaceEstimator.estimate(
        ...,
        target_checkpoints=target_checkpoints,
    )
```

No new KB read beyond what `course_profile()` itself performs (one
`db.get_kb_chunks("race_courses", ...)` call per race name, same as
`race_benchmarks` already does today — this endpoint already makes that
call twice per request for the percentile-blend feature, so this adds at
most two more, all cache-free reads of a ~40-row table; not worth
optimizing given current KB size).

## API changes

`_goal_estimate_core` response gains:

- `target_profile_source: "gpx" | "synthetic"` — always present.
- `reference_profile_source: "gpx" | "synthetic" | None` — present only
  when a reference result was used (mirrors `terrain_multiplier_reference`
  from sub-project 2).

New admin endpoint: `POST /api/kb/race-courses/course-profile` (request/
response shape in §2 above).

## Gating / fallback

- No curated profile for the target race+distance → `target_checkpoints`
  is `None` → `synthesize_course` runs exactly as before. Byte-identical
  behavior to pre-this-feature for every race without a curated profile —
  which is every race until an admin curates one.
- Same fallback independently on the reference side.
- A race resolving via fuzzy match but the specific `distance_label`
  having no curated profile (e.g. profile exists for "100km" but the
  runner's targeting "50km") → falls back to synthetic for that course,
  same as if no profile existed at all.

## Testing

- Unit tests (`backend/tests/unit/test_race_estimator.py`):
  `estimate()` with `target_checkpoints` supplied produces a different
  (and, for a checkpoint list carrying elevation above 1500m, slower —
  altitude now engages) prediction than the same distance/elevation
  totals routed through `synthesize_course`; `target_profile_source`/
  `reference_profile_source` present/absent per the rules above; omitting
  `target_checkpoints` entirely reproduces current `TestEstimate` behavior
  unchanged (regression guard).
- Unit tests (`backend/tests/unit/test_race_matcher.py` or a new
  `test_course_profile.py`, following `test_race_benchmarks.py`'s
  patched-`db.get_kb_chunks` style): `course_profile()` returns the
  checkpoints for a matched race+distance_label; returns `None` for an
  unmatched race, a race with no `course_profiles` key, or a
  `distance_label` not present in that race's curated profiles.
- Integration tests (`backend/tests/integration/test_coach_tools.py`):
  `/api/coach/goal-estimate` returns `target_profile_source: "gpx"` and a
  measurably different `predicted_time_mins` for a KB fixture carrying a
  `course_profiles` entry with checkpoints above the 1500m altitude floor,
  versus the same distance/elevation totals with no `course_profiles` key
  (regression guard for the synthetic fallback path).
- Integration tests for the new admin endpoint
  (`backend/tests/integration/test_admin_kb.py` or similar, following
  existing admin-endpoint test conventions): non-admin gets 403; unknown
  `race_name` gets 404; `distance_label` not in the race's `distances[]`
  gets 422; empty `checkpoints` gets 422; a valid request updates the
  chunk's payload and a subsequent `course_profile()` lookup reflects it.

## Open items

This closes all three sub-projects identified in the original Goal
Determiner accuracy review (percentile calibration, terrain difficulty,
real course profiles). Remaining known gap, not part of any of the three:
the frontend (`GoalDeterminer.tsx`) doesn't yet surface any of the new
response fields (`percentile_transfer_mins`, `percentile_years_used`,
`rank_transfer_mins`, `terrain_multiplier_target`,
`terrain_multiplier_reference`, and now `target_profile_source`/
`reference_profile_source`) to the user — flagged during sub-project 1's
final review and still open. Worth a dedicated frontend pass once all
three backend pieces are stable.
