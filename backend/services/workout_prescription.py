"""Pure internal workout accounting. Treadmill distance is belt-path distance.

Indoor ascent uses path * sin(arctan(grade)); it is an estimate, not GPS elevation.
Totals are rounded after summation; source segments retain their precision.
"""

from copy import deepcopy
from math import isfinite, sqrt

KINDS = {"run", "hike", "strength", "recovery", "rest"}
SETTINGS = {"flat_outdoor", "mountain", "treadmill", "indoor", "unknown"}
ZONES = {f"Zone {n}" for n in range(1, 6)}


def _number(value, *, positive=False):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a prescription quantity")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid prescription quantity") from error
    if not isfinite(result) or result < 0 or (positive and result == 0):
        raise ValueError("Prescription quantities must be finite and nonnegative")
    return result


def _pace_values(value):
    values = value if isinstance(value, list) else [value]
    if len(values) not in (1, 2):
        raise ValueError("Pace must be a value or two endpoints")
    return sorted(_number(v, positive=True) for v in values)


def resolve_prescription(segments: list[dict], *, lang: str) -> dict:
    if lang not in {"en", "vi"} or not isinstance(segments, list) or not segments:
        raise ValueError("Prescription requires segments and a supported language")
    result = dict.fromkeys(
        (
            "run_km",
            "hike_km",
            "aerobic_minutes",
            "strength_minutes",
            "passive_minutes",
            "duration_minutes",
            "estimated_indoor_ascent_m",
        ),
        0.0,
    )
    validated = []
    ids = set()
    for raw in segments:
        if not isinstance(raw, dict):
            raise ValueError("Each segment must be an object")
        segment = deepcopy(raw)
        kind, setting = segment.get("kind"), segment.get("setting")
        if kind not in KINDS or setting not in SETTINGS:
            raise ValueError("Unsupported segment kind or setting")
        if segment.get("role", "main") not in {"warmup", "main", "cooldown"}:
            raise ValueError("Unsupported segment role")
        if segment.get("id") is not None:
            identifier = segment["id"]
            if not isinstance(identifier, str) or not identifier or identifier in ids:
                raise ValueError("Segment IDs must be unique nonempty strings")
            ids.add(identifier)
        minutes = _number(segment.get("duration_minutes"))
        segment["duration_minutes"] = minutes
        if kind == "rest" and minutes != 0:
            raise ValueError("Rest has no prescribed session duration")
        grade = _number(segment.get("incline_pct", 0))
        if grade and (setting != "treadmill" or kind not in {"run", "hike"}):
            raise ValueError("Incline applies only to treadmill movement")
        if kind in {"run", "hike"}:
            if segment.get("zone") not in ZONES:
                raise ValueError("Movement requires an explicit intensity zone")
            pace = _pace_values(segment.get("pace_min_per_km"))
            distance = minutes / (sum(pace) / len(pace))
            result["run_km" if kind == "run" else "hike_km"] += distance
            result["aerobic_minutes"] += minutes
            if setting == "treadmill":
                slope = grade / 100
                result["estimated_indoor_ascent_m"] += distance * 1000 * slope / sqrt(1 + slope * slope)
        else:
            if segment.get("pace_min_per_km") is not None or segment.get("zone") is not None:
                raise ValueError("Nonmovement cannot carry running pace or intensity")
            result["strength_minutes" if kind == "strength" else "passive_minutes"] += minutes
        result["duration_minutes"] += minutes
        validated.append(segment)
    for key in result:
        result[key] = round(result[key], 0 if key == "estimated_indoor_ascent_m" else 1)
    result["segments"] = validated
    result["description"] = render_prescription(result, lang=lang)
    return result


def _pace_text(value):
    parts = []
    for pace in _pace_values(value):
        seconds = round(pace * 60)
        parts.append(f"{seconds // 60}:{seconds % 60:02d}")
    return "-".join(parts)


def render_prescription(resolved: dict, *, lang: str) -> str:
    if lang not in {"en", "vi"}:
        raise ValueError("Unsupported language")
    lines = []
    for segment in resolved["segments"]:
        kind = segment["kind"]
        role = segment.get("role", "main")
        label = {"warmup": "Warm-up", "cooldown": "Cool-down"}.get(role)
        label = (
            label
            or {"run": "Run", "hike": "Hike", "strength": "Strength", "recovery": "Recovery", "rest": "Rest"}[kind]
        )
        if kind == "rest":
            lines.append("Rest." if lang == "en" else "Nghỉ.")
            continue
        minutes = f"{segment['duration_minutes']:g}"
        line = f"{label}: {minutes} " + ("minutes" if lang == "en" else "phút")
        if kind in {"run", "hike"}:
            line += (" in " if lang == "en" else " ở ") + segment["zone"]
            line += f", pace {_pace_text(segment['pace_min_per_km'])}/km"
        if segment["setting"] == "treadmill":
            grade = _number(segment.get("incline_pct", 0))
            line += f", Treadmill {grade:g}%"
        line += "."
        if segment.get("stop_if_power_drops"):
            line += " Stop if power drops." if lang == "en" else " Dừng nếu power giảm."
        lines.append(line)
    if resolved["estimated_indoor_ascent_m"]:
        ascent = f"{resolved['estimated_indoor_ascent_m']:g}"
        lines.append(f"Indoor D+ (estimated): {ascent} m." if lang == "en" else f"D+ trong nhà (ước tính): {ascent} m.")
    return " → ".join(lines)
