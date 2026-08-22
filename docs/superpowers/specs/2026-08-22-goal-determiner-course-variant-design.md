# Goal Determiner: Course Variant Awareness

## Context

`RaceEstimator` (via `race_matcher.course_profile()` and the GPX
course-profile admin endpoint, both shipped) already lets an admin curate a
real GPX-derived elevation profile per race+distance, used instead of the
synthetic uniform-grade course when available. It also has percentile-based
calibration (`RaceEstimator.percentile_curve`), which averages **every**
curated result-year's percentiles for a distance label into one field-outcome
curve.

Both assume one canonical route per distance label. Some races don't hold
that assumption — e.g. Dalat Ultra Trail changes the Langbiang climb's
direction some years while the rest of the route stays similar. For those
races:
- `course_profiles[distance_label]` currently stores a single checkpoints
  blob (`services/kb_distiller.py:734`'s `save_course_profile`, `services/
  race_matcher.py:254`'s `course_profile` lookup) — there's no way to curate
  more than one year's GPX per distance label; a re-upload overwrites the
  prior one entirely.
- `percentile_curve` has no concept of route compatibility — it would
  silently blend a rerouted year's results with unrelated years into one
  meaningless curve.

The user has GPX files from previous seasons of several major races and
wants to curate multiple years per race, associating each with that year's
results, without needing the system to geometrically detect what changed
between them (ruled out during brainstorming — hard, low-value; the curator
already knows which years share a route).

## Goal

Let an admin curate more than one year's GPX profile per race+distance,
tag a year with an optional route "variant" label, and have percentile
calibration only pool result-years that share the target year's variant —
while every race with no variant tagging (the common case) behaves exactly
as it does today.

## Non-goals

- No geometric climb-matching or track comparison between years — variant
  compatibility is entirely curator-asserted, never inferred.
- No per-runner GPX upload — curation stays admin-only, at the race level,
  reused by every runner (unchanged from the shipped design).
- No separate `variant` field on `results[]` entries. A results-year's
  compatibility is derived by cross-referencing its `year` against
  `course_profiles[distance_label]`'s variant tags — if you're curating a
  historical year's GPX specifically to associate it with that year's
  results (as described), the course-profile entry's variant *is* the tag;
  there is no second place to maintain it. A results-year with no matching
  curated course-profile year is simply not variant-filtered (see Selection
  logic).
- No required migration for existing curated profiles — the year-keying
  change is additive; a distance label with zero curated years behaves as
  "no profile," matching today's fallback.

## Data model change

`course_profiles[distance_label]` changes from a single object to a dict
keyed by year (string, e.g. `"2026"`):

```json
"course_profiles": {
  "70km": {
    "2025": {
      "checkpoints": [ /* GpxParser.parse() shape, unchanged */ ],
      "variant": null,
      "source": "gpx_upload",
      "curated_at": "2025-09-01"
    },
    "2026": {
      "checkpoints": [ /* ... */ ],
      "variant": "langbiang-reversed",
      "source": "gpx_upload",
      "curated_at": "2026-08-15"
    }
  }
}
```

`variant` is an optional free-text string (curator's choice — e.g.
`"standard"`, `"langbiang-reversed"`, `"2024-reroute"`), `null`/absent by
default. Two years with the same non-null variant string are treated as
route-compatible; a `null` variant is treated as **not asserted either
way** (see Selection logic — this is the "common case, zero extra work"
path).

## Ingestion changes

`kb_distiller.save_course_profile(race_name, distance_label, checkpoints,
year, variant=None)` — gains two parameters:
- `year: int` — required. The curator always knows which edition's GPX
  they're uploading; no auto-detection.
- `variant: str | None = None` — optional route-variant tag.

Overwrite semantics change from "overwrite by `(race_name, distance_label)`"
to "overwrite by `(race_name, distance_label, year)`" — uploading the same
year twice still overwrites (unchanged intent: a re-upload is a correction),
but uploading a *different* year now adds alongside existing years instead
of replacing them.

The 15% distance-tolerance validation (already shipped) is unchanged,
checked per upload regardless of year.

`main.py`'s `CourseProfileRequest` model gains `year: int` and
`variant: str | None = None`; `POST /api/kb/race-courses/course-profile`
passes them through.

## Lookup changes

`race_matcher.course_profile(name, distance_label, year=None) ->
dict[str, Any] | None` — signature and return type both change:
- New optional `year` parameter: when given, look up that specific curated
  year; when omitted (the common case — Goal Determiner predicting a
  future race doesn't know a "year" to ask for), select the
  **most-recently-curated year** (by `curated_at`, not by the `year` key
  itself — a newly-uploaded correction to an older edition should still
  win, since it's the most current information the curator has given us).
- Return shape changes from a bare checkpoints list to
  `{"year": int, "variant": str | None, "checkpoints": [...]}` (or `None`)
  — bundles everything a caller needs from one lookup, matching the shape
  `race_benchmarks` already returns.

New function `race_matcher.course_profile_variants(name, distance_label) ->
dict[int, str | None]` — every curated year's variant tag for a
race+distance (`{}` if none curated). Used only to cross-reference
`results[]` years for percentile filtering (see below); not used by the
`RaceEstimator` physics path.

## Selection logic — percentile filtering

In `_goal_estimate_core` (`backend/main.py`), after resolving
`target_bench`/`ref_bench` (already shipped), filter each side's `results`
list before handing it to `RaceEstimator.percentile_curve`:

```python
def _variant_filtered_results(results, variants, target_variant):
    if not target_variant:
        return results  # no assertion for this route -> pool everything, unchanged
    return [r for r in results if variants.get(r.get("year")) == target_variant]
```

- `target_variant` comes from the target/reference race's *selected*
  course-profile year's `variant` (from the `course_profile()` call already
  made to get `target_checkpoints`/`reference["checkpoints"]`).
- When the selected course-profile year has no variant (`None`) — the
  common case — every result-year is pooled, byte-identical to today's
  behavior. This is deliberate: a `null` variant is not itself a variant to
  match against; it means "no assertion," not "the null-variant route."
- When the selected year *does* have a variant, only result-years whose
  `year` maps (via `course_profile_variants`) to that same variant are
  pooled. A result-year with no curated course-profile entry at all is
  excluded once filtering is active — it's not proven either compatible or
  incompatible, so it's dropped rather than guessed at.
- This applies independently to the target and reference sides, since they
  can be different races (or the same race requested for two different
  years' fitness contexts).

No change to `RaceEstimator.percentile_curve` itself — it already just
takes whatever `results` list it's handed.

## API changes

`_goal_estimate_core` response: `target_profile_source`/
`reference_profile_source` (already shipped, `"gpx" | "synthetic"`) are
joined by `target_course_year`/`reference_course_year: int | None` — the
year of the selected course profile, for UI transparency (e.g. "using the
2026 route"). `None` when the source is `"synthetic"`.

## Testing

- Unit (`race_matcher`): `course_profile` selects the most-recently-curated
  year when `year` is omitted; selects the exact requested year when given;
  returns `None` for an unmatched race/distance/year. `course_profile_variants`
  returns the full year→variant map; `{}` for a race with no curated
  profiles.
- Unit (`kb_distiller`): `save_course_profile` stores under
  `course_profiles[distance_label][year]`; uploading a second year adds
  alongside the first (both retrievable); re-uploading the same year
  overwrites only that year, leaving other years untouched; the existing
  distance-tolerance and unknown-race/distance-label validations are
  unchanged and still enforced per upload.
- Integration (`main.py` / `_goal_estimate_core`): a race with two curated
  years, one tagged `"langbiang-reversed"` and one untagged (`None`) —
  confirm percentile pooling only includes result-years sharing the
  selected year's variant when that variant is set, and pools everything
  when the selected year's variant is `null`. A race with only one curated
  year (today's common case) behaves identically to before this change.

## Open items for later (not this sub-project)

- No UI yet for curating a specific year+variant (the admin endpoint is the
  only interface, same as the original course-profile feature).
- Frontend still doesn't surface `target_course_year`/`reference_course_year`
  to users (same open gap as the other new response fields, tracked
  separately).
- The reference race's `course_profile()` lookup always selects the
  most-recently-curated year, same as the target side — there's no way for
  a caller to say "the athlete's result was from the *2024* edition." For a
  variant-tagged race this can narrow percentile pooling on the reference
  side to a single, likely-wrong year (a real behavior change from the
  pre-this-feature unfiltered pooling). `GoalEstimateRequest` would need a
  `reference_year` field, threaded into the reference-side `course_profile`
  call, to fix this properly. Flagged during this sub-project's final
  review; deferred rather than expanding scope.
- `rank_transfer_mins` (the winner-time-only secondary estimate, from the
  percentile-calibration sub-project) still reads `results[0]` with no
  variant filtering, so it can report a cross-variant winner-time
  comparison in the same response as a correctly variant-filtered
  `percentile_transfer_mins`. Extending variant-filtering to
  `rank_transfer_mins` would need the filtered-results computation moved
  above the rank-transfer block in `_goal_estimate_core`. Flagged during
  this sub-project's final review; deferred rather than expanding scope.
