"""Race-name -> curated course enrichment, shared by plan generation (main.py)
and week rebuilds (services/week_rebuild.py)."""


def resolve_course_match(
    race_name: str | None, course_distance_km: float | None, course_elevation_gain_m: float | None
) -> tuple[float | None, float | None, str | None]:
    """Fuzzy-matches race_name against the curated race_courses KB. Returns
    (resolved_distance_km, resolved_elevation_gain_m, course_context) —
    numeric fields are backfilled only when the caller passed None; manual
    entry and GPX-derived values are never overwritten. course_context
    (qualitative terrain/climate prose) is always returned when there's a
    match, regardless of whether the numeric fields needed backfilling.
    Never raises: race matching is enrichment, never allowed to break plan
    creation or generation, even if the hand-edited KB has malformed data
    or the matcher's dependencies aren't installed."""
    try:
        from services.race_matcher import match_race

        matched = match_race(race_name, distance_km=course_distance_km)
    except Exception as e:
        print(f"[CourseMatch] match_race failed unexpectedly: {e}")
        matched = None
    if not matched:
        return course_distance_km, course_elevation_gain_m, None
    resolved_distance_km = course_distance_km if course_distance_km is not None else matched.distance_km
    resolved_elevation_gain_m = (
        course_elevation_gain_m if course_elevation_gain_m is not None else matched.elevation_gain_m
    )
    return resolved_distance_km, resolved_elevation_gain_m, matched.course_context
