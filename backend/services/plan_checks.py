"""Deterministic quality checks on a generated training block (no LLM).

Each check returns True/False, or None when it doesn't apply to this block. The
`plan_checks` score is the share of applicable checks that pass.
"""

from collections import defaultdict
from typing import Any

RUN_TYPES = {"Easy", "Tempo", "Interval", "Long Run", "Recovery", "Walk/Run", "Race"}
EASY_ZONES = {"Zone 1", "Zone 2"}
MIN_EASY_SHARE = 0.70  # 80/20 with slack: at least 70% of run minutes in Zone 1-2
MAX_WEEKLY_GROWTH = 1.15  # week-over-week run minutes may grow at most 15%
_DOWN_PHASES = {"Recovery", "Taper", "Race Week"}


def _minutes(w: dict[str, Any]) -> float:
    try:
        return max(float(w.get("duration_minutes") or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def check_easy_share(workouts: list[dict[str, Any]]) -> bool | None:
    runs = [w for w in workouts if w.get("type") in RUN_TYPES and w.get("type") != "Race"]
    total = sum(_minutes(w) for w in runs)
    if not total:
        return None
    easy = sum(_minutes(w) for w in runs if w.get("target_zone") in EASY_ZONES)
    return easy / total >= MIN_EASY_SHARE


def check_progression(workouts: list[dict[str, Any]]) -> bool | None:
    weekly: dict[int, float] = defaultdict(float)
    phases: dict[int, str] = {}
    for w in workouts:
        week = w.get("week_number")
        if isinstance(week, int) and w.get("type") in RUN_TYPES:
            weekly[week] += _minutes(w)
            phases.setdefault(week, w.get("phase") or "")
    weeks = sorted(weekly)
    if len(weeks) < 2:
        return None
    for prev, cur in zip(weeks, weeks[1:]):
        # Coming back from a planned down week is not a spike.
        if phases.get(prev) in _DOWN_PHASES or not weekly[prev]:
            continue
        if weekly[cur] > weekly[prev] * MAX_WEEKLY_GROWTH:
            return False
    return True


def check_complete_sessions(workouts: list[dict[str, Any]]) -> bool | None:
    if not workouts:
        return False
    return all(w.get("title") and w.get("type") and (w.get("type") == "Rest" or _minutes(w) > 0) for w in workouts)


CHECKS = {
    "easy_share": check_easy_share,
    "progression": check_progression,
    "complete_sessions": check_complete_sessions,
}


def run_checks(workouts: list[dict[str, Any]]) -> dict[str, bool]:
    return {name: result for name, fn in CHECKS.items() if (result := fn(workouts)) is not None}


def pass_share(results: dict[str, bool]) -> float | None:
    return sum(results.values()) / len(results) if results else None


def run_context_checks(workouts: list[dict[str, Any]], *, context: dict) -> dict[str, bool | None]:
    """Check resolved output; missing precision remains explicitly unavailable.

    Calendar coverage, access and phases come from context/fields, never titles.
    Existing percentage constants are app policy, not universal book rules.
    """
    from math import isfinite

    from services.workout_prescription import apply_prescription, resolve_prescription

    results = dict.fromkeys(("arithmetic", "access", "intensity_accounting", "progression"))
    if not workouts:
        results["arithmetic"] = False
        return results
    resolved = []
    missing_precision = False
    for workout in workouts:
        try:
            values = [float(workout.get(key) or 0) for key in ("duration_minutes", "distance_km")]
            if any(not isfinite(value) or value < 0 for value in values):
                raise ValueError("Invalid totals")
        except (TypeError, ValueError):
            results["arithmetic"] = False
            return results
        if "segments" not in workout:
            missing_precision = True
            continue
        try:
            prescription = resolve_prescription(workout["segments"], lang="en")
            actual_time = float(workout.get("duration_minutes", 0))
            actual_distance = float(workout.get("distance_km", 0))
            distance = round(prescription["run_km"] + prescription["hike_km"], 1)
            if (
                not isfinite(actual_time)
                or not isfinite(actual_distance)
                or abs(actual_time - prescription["duration_minutes"]) > 0.1
                or abs(actual_distance - distance) > 0.1
            ):
                results["arithmetic"] = False
                return results
            expected = {**workout}
            apply_prescription(expected, lang="en")
            for key in ("treadmill_incline", "treadmill_speed"):
                if str(workout.get(key, "0")) != expected[key]:
                    results["arithmetic"] = False
                    return results
            resolved.append((workout, prescription))
        except (ValueError, TypeError):
            results["arithmetic"] = False
            return results
    if missing_precision:
        return results
    results["arithmetic"] = True
    access_unknown = False
    access_failed = False
    run_total = easy_total = 0.0
    weekly = defaultdict(float)
    phases = {}
    for workout, prescription in resolved:
        week = workout.get("week_number")
        phases[week] = workout.get("phase")
        permission = context.get("day_access", {}).get(workout.get("day_of_week"))
        for segment in prescription["segments"]:
            kind = segment["kind"]
            if kind == "rest":
                continue
            if permission is None or segment["setting"] == "unknown":
                access_unknown = True
            elif segment["setting"] not in permission.get("settings", []):
                access_failed = True
            elif segment["setting"] == "treadmill":
                maximum = permission.get("max_incline_pct")
                if maximum is None:
                    access_unknown = True
                elif float(segment.get("incline_pct", 0)) > maximum:
                    access_failed = True
            exercise = segment.get("exercise")
            if exercise:
                needed = exercise.get("equipment")
                available = permission.get("equipment") if permission else None
                if needed is None or available is None:
                    access_unknown = True
                elif not set(needed).issubset(available):
                    access_failed = True
            if kind in {"run", "hike"} and workout.get("type") != "Race":
                minutes = segment["duration_minutes"]
                run_total += minutes
                weekly[week] += minutes
                if segment["zone"] in EASY_ZONES:
                    easy_total += minutes
    results["access"] = False if access_failed else (None if access_unknown else True)
    results["intensity_accounting"] = easy_total / run_total >= MIN_EASY_SHARE if run_total else None
    coverage = context.get("week_coverage", {})
    compared = False
    growth_failed = False
    weeks = sorted(w for w in weekly if isinstance(w, int))
    for prev, current in zip(weeks, weeks[1:]):
        if current != prev + 1 or coverage.get(prev) != 7 or coverage.get(current) != 7:
            continue
        baseline = prev
        if phases.get(prev) in _DOWN_PHASES:
            # Rebound needs the preceding healthy full week; no unlimited exemption.
            baseline = next(
                (w for w in reversed(weeks) if w < prev and coverage.get(w) == 7 and phases.get(w) not in _DOWN_PHASES),
                None,
            )
            if baseline is None or any(coverage.get(w) != 7 for w in range(baseline, current + 1)):
                continue
        if weekly[baseline] <= 0:
            continue
        compared = True
        if weekly[current] > weekly[baseline] * MAX_WEEKLY_GROWTH:
            growth_failed = True
    results["progression"] = not growth_failed if compared else None
    return results


def generation_context(race_info: dict, workouts: list[dict]) -> dict:
    """Use explicit validation context; do not infer day availability from titles.

    Global flat access can establish flat outdoor availability. Day constraints
    and machine capabilities need explicit context; free-form notes remain input
    to the coach, not proof of independently validated access.
    """
    from datetime import date

    supplied = race_info.get("validation_context") or {}
    context = {**supplied}
    if "week_coverage" not in context:
        try:
            start = date.fromisoformat(str(race_info.get("plan_start_date"))[:10])
        except ValueError:
            start = None
        context["week_coverage"] = {
            w["week_number"]: (7 - start.weekday() if w["week_number"] == 1 else 7)
            for w in workouts
            if start is not None and isinstance(w.get("week_number"), int)
        }
    if "day_access" not in context and race_info.get("training_environment", "flat") == "flat":
        context["day_access"] = {
            day: {"settings": ["flat_outdoor", "indoor"], "equipment": ["bodyweight"]}
            for day in {w.get("day_of_week") for w in workouts}
        }
    return context


def validate_generated_workouts(workouts: list[dict], *, context: dict) -> dict[str, bool | None]:
    """Bounded generator attempts call this before any workout can be stored."""
    results = run_context_checks(workouts, context=context)
    failed = [name for name in ("arithmetic", "access") if results[name] is False]
    if failed:
        raise ValueError("Invalid generated prescription: " + ", ".join(failed))
    return results
