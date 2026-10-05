"""Pure internal workout accounting. Treadmill distance is belt-path distance.

Indoor ascent uses path * sin(arctan(grade)); it is an estimate, not GPS elevation.
Totals are rounded after summation; source segments retain their precision.
"""

import re
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
            "estimated_outdoor_ascent_m",
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
        if segment.get("exercise") is not None:
            exercise = segment["exercise"]
            if (
                kind != "strength"
                or not isinstance(exercise, dict)
                or not isinstance(exercise.get("name"), str)
                or not exercise["name"].strip()
            ):
                raise ValueError("Exercise requires a named strength segment")
            sets = _number(exercise.get("sets"), positive=True)
            if not sets.is_integer():
                raise ValueError("Exercise sets must be integers")
            exercise["sets"] = int(sets)
            has_hold = exercise.get("hold_seconds") is not None
            has_reps = exercise.get("reps") is not None
            if has_hold == has_reps:
                raise ValueError("Exercise requires exactly one of reps or hold_seconds")
            if not has_hold and re.search(
                r"\b(?:plank(?: hold)?|wall[ -]?sit(?: hold)?|hollow(?: body)? hold)(?:\s*\([^)]*\))?$",
                exercise["name"].strip(),
                re.IGNORECASE,
            ):
                raise ValueError("Static hold requires explicit hold_seconds")
            if has_hold:
                exercise["hold_seconds"] = _number(exercise["hold_seconds"], positive=True)
            else:
                reps = _number(exercise["reps"], positive=True)
                if not reps.is_integer():
                    raise ValueError("Exercise reps must be integers")
                exercise["reps"] = int(reps)
            exercise["rest_seconds"] = _number(exercise.get("rest_seconds", 0))
            equipment = exercise.get("equipment")
            if (
                not isinstance(equipment, list)
                or not equipment
                or any(
                    not isinstance(item, str) or item not in {"bodyweight", "weights", "machine", "box", "stairs"}
                    for item in equipment
                )
            ):
                raise ValueError("Exercise requires explicit supported equipment")
            if has_hold and re.search(r"\b(each side|both sides|per side)\b", exercise["name"], re.I):
                raise ValueError("Use separate explicitly targeted left and right hold segments")
            if has_hold:
                minimum_seconds = sets * exercise["hold_seconds"] + (sets - 1) * exercise["rest_seconds"]
                if minimum_seconds > _number(segment.get("duration_minutes")) * 60:
                    raise ValueError("Hold targets and rests exceed segment duration")
        minutes = _number(segment.get("duration_minutes"))
        segment["duration_minutes"] = minutes
        if kind == "rest" and minutes != 0:
            raise ValueError("Rest has no prescribed session duration")
        ascent = _number(segment.get("elevation_gain_m", 0))
        if ascent and (setting != "mountain" or kind not in {"run", "hike"}):
            raise ValueError("Outdoor ascent requires explicit mountain movement")
        result["estimated_outdoor_ascent_m"] += ascent
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
        result[key] = round(result[key], 0 if key in {"estimated_indoor_ascent_m", "estimated_outdoor_ascent_m"} else 1)
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
        if segment.get("elevation_gain_m"):
            ascent = _number(segment["elevation_gain_m"])
            line += f", D+ {ascent:g} m " + ("(estimated)" if lang == "en" else "(ước tính)")
        if segment["setting"] == "treadmill":
            grade = _number(segment.get("incline_pct", 0))
            line += f", Treadmill {grade:g}%"
        if segment.get("exercise"):
            exercise = segment["exercise"]
            rest = "rest between sets" if lang == "en" else "nghỉ giữa các set"
            target = (
                f"{exercise['hold_seconds']:g} s " + ("hold" if lang == "en" else "giữ")
                if exercise.get("hold_seconds") is not None
                else str(exercise["reps"])
            )
            line += f", {exercise['name']}: {exercise['sets']} x {target}, {exercise['rest_seconds']:g} s {rest}"
        line += "."
        if segment.get("stop_if_power_drops"):
            line += " Stop if power drops." if lang == "en" else " Dừng nếu power giảm."
        lines.append(line)
    if resolved["estimated_indoor_ascent_m"]:
        ascent = f"{resolved['estimated_indoor_ascent_m']:g}"
        lines.append(f"Indoor D+ (estimated): {ascent} m." if lang == "en" else f"D+ trong nhà (ước tính): {ascent} m.")
    return " → ".join(lines)


def render_fueling_tip(minutes: float, *, lang: str) -> str:
    """Existing app duration bands, not a new physiological threshold or dose.

    Event-specific race advice stays with the existing generator policy.
    """
    if minutes == 0:
        return ""
    if minutes < 75:
        return (
            f"For this {minutes:g}-minute session: water; optional 200-400 mg Sodium. No Carbs are needed during the session."
            if lang == "en"
            else f"Buổi tập {minutes:g} phút: nước lọc; có thể thêm 200-400 mg Sodium. Không cần Carbs trong buổi tập."
        )
    carbs, sodium, water = ("30-60", "300-500", "400-600") if minutes <= 150 else ("60-90", "500-800", "500-750")
    return (
        f"For this {minutes:g}-minute session: {carbs} g Carbs/h; {sodium} mg Sodium/h; {water} ml water/h."
        if lang == "en"
        else f"Buổi tập {minutes:g} phút: {carbs} g Carbs/giờ; {sodium} mg Sodium/giờ; {water} ml nước/giờ."
    )


def apply_prescription(workout: dict, *, lang: str) -> None:
    """Resolve newly structured output; callers validate context before storage.

    Public distance is total locomotion distance. Component accounting remains
    ephemeral because the existing schema stores totals and complete instructions.
    Legacy output without segments never enters this helper.
    """
    import re

    resolved = resolve_prescription(workout["segments"], lang=lang)
    if workout.get("type") in {"Strength", "Muscular Endurance"}:
        for segment in resolved["segments"]:
            if segment["kind"] == "strength" and not segment.get("exercise"):
                raise ValueError("Strength requires a named exercise prescription")
    rationale = workout.get("rationale") or ""
    if not isinstance(rationale, str) or re.search(r"\d", rationale):
        raise ValueError("Rationale must not supply a second numerical prescription")
    if lang == "vi":
        titles = {
            "Easy": "Easy Run",
            "Recovery": "Recovery Run",
            "Long Run": "Long Run",
            "Tempo": "Tempo",
            "Interval": "Interval",
            "Strength": "Strength",
            "Muscular Endurance": "ME",
            "Walk/Run": "Walk/Run",
            "Race": "Race",
            "Rest": "Rest",
        }
        if workout.get("type") in titles:
            workout["title"] = titles[workout["type"]]
    workout["segments"] = resolved["segments"]
    workout["prescription"] = resolved
    workout["duration_minutes"] = resolved["duration_minutes"]
    workout["distance_km"] = round(resolved["run_km"] + resolved["hike_km"], 1)
    workout["description"] = resolved["description"] + (" Reason: " + rationale if rationale else "")
    if workout.get("type") != "Race":
        workout["fueling_tip"] = render_fueling_tip(resolved["duration_minutes"], lang=lang)
    moving = [s for s in resolved["segments"] if s["kind"] in {"run", "hike"}]
    main = next((s for s in moving if s.get("role", "main") == "main"), moving[0] if moving else None)
    workout["target_pace"] = f"{_pace_text(main['pace_min_per_km'])} /km" if main else ""
    workout["target_zone"] = main["zone"] if main else "Zone 1"
    indoor = [s for s in moving if s["setting"] == "treadmill"]
    if indoor:
        grades = [_number(s.get("incline_pct", 0)) for s in indoor]
        speeds = [60 / p for s in indoor for p in _pace_values(s["pace_min_per_km"])]

        def band(values):
            low, high = round(min(values), 1), round(max(values), 1)
            return f"{low:g}" if low == high else f"{low:g}-{high:g}"

        workout["treadmill_incline"] = band(grades)
        workout["treadmill_speed"] = band(speeds)
    else:
        workout["treadmill_incline"] = workout["treadmill_speed"] = "0"
    # No generic course-based climb is invented for a flat weekday or Strength.
    workout["elevation_gain_m"] = resolved["estimated_indoor_ascent_m"] + resolved["estimated_outdoor_ascent_m"]
    distance = workout["distance_km"]
    workout["grade_percent"] = round(workout["elevation_gain_m"] / (distance * 10), 1) if distance else 0
