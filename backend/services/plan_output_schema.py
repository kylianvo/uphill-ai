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


def workout_response_schema(*, structured: bool) -> dict:
    """Legacy templates retain scalar output; explicit segment contracts require it."""
    schema = deepcopy(WORKOUT_RESPONSE_SCHEMA)
    if structured:
        schema["items"]["required"].append("segments")
    return schema
