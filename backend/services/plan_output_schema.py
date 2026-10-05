"""Provider output shape; contextual coaching remains locally validated."""

from copy import deepcopy

from services.workout_prescription import KINDS, SETTINGS, ZONES

SEGMENT_SCHEMA = {
    "type": "object",
    "required": ["kind", "duration_minutes", "setting"],
    "properties": {
        "id": {"type": "string"},
        "kind": {"type": "string", "enum": sorted(KINDS)},
        "setting": {"type": "string", "enum": sorted(SETTINGS)},
        "role": {"type": "string", "enum": ["warmup", "main", "cooldown"]},
        "duration_minutes": {"type": "number", "minimum": 0},
        "zone": {"anyOf": [{"type": "string", "enum": sorted(ZONES)}, {"type": "null"}]},
        "pace_min_per_km": {
            "anyOf": [{"type": "number"}, {"type": "array", "items": {"type": "number"}, "minItems": 1, "maxItems": 2}]
        },
        "incline_pct": {"type": "number"},
        "elevation_gain_m": {"type": "number"},
        "stop_if_power_drops": {"type": "boolean"},
        "exercise": {
            "type": "object",
            "required": ["name", "sets", "rest_seconds", "equipment"],
            "properties": {
                "name": {"type": "string"},
                "sets": {"type": "integer", "minimum": 1},
                "reps": {"type": "integer", "minimum": 1},
                "hold_seconds": {"type": "number"},
                "rest_seconds": {"type": "number", "minimum": 0},
                "equipment": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "enum": ["bodyweight", "weights", "machine", "box", "stairs"]},
                },
            },
        },
    },
}

WORKOUT_RESPONSE_SCHEMA = {
    "type": "array",
    "minItems": 1,
    "items": {
        "type": "object",
        "required": ["week_number", "day_of_week", "phase", "title", "type"],
        "properties": {
            "week_number": {"type": "integer", "minimum": 1},
            "day_of_week": {
                "type": "string",
                "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            },
            "phase": {"type": "string", "enum": ["Base", "Build", "Peak", "Taper", "Race Week", "Recovery"]},
            "title": {"type": "string"},
            "type": {
                "type": "string",
                "enum": [
                    "Easy",
                    "Tempo",
                    "Interval",
                    "Long Run",
                    "Strength",
                    "Rest",
                    "Race",
                    "Recovery",
                    "Muscular Endurance",
                    "Walk/Run",
                ],
            },
            "segments": {"type": "array", "minItems": 1, "items": SEGMENT_SCHEMA},
            "training_method": {
                "type": "string",
                "enum": [
                    "aerobic",
                    "tempo",
                    "interval",
                    "general_strength",
                    "max_strength",
                    "muscular_endurance",
                    "power",
                    "rest",
                ],
            },
            "rationale": {"type": "string"},
            "description": {"type": "string"},
            "fueling_tip": {"type": "string"},
            "session_slot": {"type": "string", "enum": ["morning", "afternoon"]},
            "duration_minutes": {"type": "number"},
            "distance_km": {"type": "number"},
            "target_zone": {"type": "string"},
            "target_hr_range": {"type": "string"},
            "target_pace": {"type": "string"},
            "walk_interval_value": {"type": "number"},
            "interval_reps": {"type": "integer"},
            "interval_rep_value": {"type": "number"},
            "interval_rep_unit": {"type": "string", "enum": ["s", "m", "min", "km"]},
            "elevation_gain_m": {"type": "number"},
            "grade_percent": {"type": "number"},
            "treadmill_incline": {"type": "number"},
            "treadmill_speed": {"type": "number"},
        },
    },
}


STRUCTURED_PRESCRIPTION_HEADER = (
    "STRUCTURED PRESCRIPTION — authoritative over the earlier numerical description schema:"
)


def workout_response_schema(*, structured: bool, minimum_workouts: int = 1) -> dict:
    """Legacy templates retain scalar output; explicit segment contracts require it."""
    schema = deepcopy(WORKOUT_RESPONSE_SCHEMA)
    schema["minItems"] = minimum_workouts
    if structured:
        schema["items"]["required"].append("segments")
    else:
        del schema["items"]["properties"]["segments"]
    return schema


DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def expected_calendar_days(
    start_week: int, end_week: int, *, start_weekday: int, partial_first_week: bool
) -> set[tuple[int, str]]:
    """Mirror the prompt's existing first-block start-date exclusion."""
    return {
        (week, day)
        for week in range(start_week, end_week + 1)
        for index, day in enumerate(DAYS)
        if not (partial_first_week and week == 1 and index < start_weekday)
    }


def validate_calendar_coverage(workouts: list[dict], expected: set[tuple[int, str]]) -> None:
    """Reject missing/extra calendar days; multiple sessions remain valid."""
    from services.plan_checks import PrescriptionValidationError

    actual = set()
    unexpected = []
    for workout in workouts:
        week, day = workout.get("week_number"), workout.get("day_of_week")
        if type(week) is not int or not isinstance(day, str) or (week, day) not in expected:
            unexpected.append(f"week={week!r}, day={day!r}")
        else:
            actual.add((week, day))
    missing = sorted(expected - actual)
    if missing or unexpected:
        raise PrescriptionValidationError(
            "Incomplete or unexpected calendar",
            f"Return every requested calendar day, including Rest on off days. Missing days: {missing!r}; "
            f"unexpected days: {unexpected!r}. Double sessions cannot replace missing days. "
            "Remove out-of-block days; do not change trusted dose or access constraints.",
        )
