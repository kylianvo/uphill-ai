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
