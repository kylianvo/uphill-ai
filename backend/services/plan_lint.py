"""Deterministic structural lint of generated training weeks (no LLM).

The generation prompt already states these rules; this checks the result, because under
constraints (few training days, gym access, a mountain minimum) the model breaks them.
Each Issue.message is an imperative instruction, written to be pasted into a corrective
retry prompt. Caps come from the athlete's tier profile, not from one-size numbers.
"""

from dataclasses import dataclass
from typing import Any

from services.athlete_tier import TierProfile

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DOWN_PHASES = {"Recovery", "Taper", "Race Week"}
HARD_TYPES = {"Tempo", "Threshold", "Interval"}
HARD_ZONES = {"Zone 3", "Zone 4", "Zone 5"}
LONG_SHARE_TOLERANCE = 0.02  # planned minutes are rounded
# Planned D+ is a noisy estimate (it moves with which session lands on a mountain day), so
# the vertical check only catches gross spikes; the doctrine's 7-10% cap is applied to time.
MAX_VERT_GROWTH = 0.25
MIN_VERT_STEP_M = 300  # ignore growth on tiny bases
BACK_TO_BACK_SHARE = 0.50  # two consecutive big days may hold at most half the week
MAX_SESSION_MIN = 300  # KB: the longest single session is capped at four to five hours
BUILD_WEEKS_BEFORE_RECOVERY = 3  # 3 build : 1 recovery


@dataclass(frozen=True)
class Issue:
    code: str
    week: int
    message: str


def _min(w: dict[str, Any]) -> float:
    try:
        return max(float(w.get("duration_minutes") or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _active(ws: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [w for w in ws if w.get("type") != "Rest"]


def _day(w: dict[str, Any]) -> int | None:
    return DAYS.index(w["day_of_week"]) if w.get("day_of_week") in DAYS else None


def is_hard(w: dict[str, Any]) -> bool:
    return w.get("type") in HARD_TYPES or w.get("target_zone") in HARD_ZONES


def _is_long(w: dict[str, Any]) -> bool:
    return (w.get("type") or "").strip().lower() == "long run"


def _is_me(w: dict[str, Any]) -> bool:
    return (w.get("type") or "").strip().lower() == "muscular endurance"


def week_minutes(ws: list[dict[str, Any]]) -> float:
    return sum(_min(w) for w in _active(ws))


def _vert(ws: list[dict[str, Any]]) -> float:
    return sum(float(w.get("elevation_gain_m") or 0) for w in _active(ws))


def _label(w: dict[str, Any]) -> str:
    return f"{w.get('title') or w.get('type')} ({DAYS[_day(w)]})"


def _by_week(workouts: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for w in workouts:
        if isinstance(w.get("week_number"), int):
            out.setdefault(w["week_number"], []).append(w)
    return out


def _is_down(weeks: dict[int, list[dict[str, Any]]], wk: int) -> bool:
    """A planned down week: a down phase, or at least 10% under the week before."""
    ws = weeks.get(wk) or []
    if any((w.get("phase") or "") in DOWN_PHASES for w in ws):
        return True
    prev = week_minutes(weeks.get(wk - 1) or [])
    return bool(prev) and week_minutes(ws) <= prev * 0.9


def lint_week(workouts: list[dict[str, Any]], week: int, profile: TierProfile) -> list[Issue]:
    """Issues in `week`, judged against the weeks before it in `workouts`."""
    weeks = _by_week(workouts)
    ws = _active(weeks.get(week) or [])
    if not ws:
        return []
    total = week_minutes(ws)
    prev_ws = weeks.get(week - 1) or []
    prev_total = week_minutes(prev_ws)
    issues: list[Issue] = []

    # Strength needs 48 h clear of the long run and of hard sessions (DOMS peaks ~48 h).
    for me in (w for w in ws if _is_me(w) and _day(w) is not None):
        for other in ws:
            if other is me or _day(other) is None or not (_is_long(other) or is_hard(other)):
                continue
            gap = abs(_day(other) - _day(me)) * 24
            if 0 < gap < 48:
                issues.append(
                    Issue(
                        "ME_SPACING",
                        week,
                        f"Week {week}: the Muscular Endurance session {_label(me)} is only {gap} h from "
                        f"{_label(other)}. Keep ME at least 48 hours from the long run and from any Zone 3+ or "
                        f"interval session: move it to another day.",
                    )
                )

    hard_days = sorted({_day(w) for w in ws if is_hard(w) and _day(w) is not None})
    for a, b in zip(hard_days, hard_days[1:]):
        if b - a == 1:
            issues.append(
                Issue(
                    "HARD_ADJACENT",
                    week,
                    f"Week {week}: hard sessions on consecutive days ({DAYS[a]} and {DAYS[b]}). "
                    f"Put an easy or rest day between them.",
                )
            )

    cap = profile.max_weekly_progression
    if prev_total and not _is_down(weeks, week - 1) and total > prev_total * (1 + cap) + 1:
        issues.append(
            Issue(
                "VOLUME_JUMP",
                week,
                f"Week {week}: total time {total:.0f} min is {(total / prev_total - 1) * 100:.0f}% above week "
                f"{week - 1} ({prev_total:.0f} min). Cap the increase at {cap * 100:.0f}% "
                f"(at most {prev_total * (1 + cap):.0f} min).",
            )
        )

    prev_vert = _vert(prev_ws)
    if prev_vert and _vert(ws) > prev_vert * (1 + MAX_VERT_GROWTH) and _vert(ws) - prev_vert > MIN_VERT_STEP_M:
        issues.append(
            Issue(
                "VERT_JUMP",
                week,
                f"Week {week}: planned climbing {_vert(ws):.0f} m D+ is {(_vert(ws) / prev_vert - 1) * 100:.0f}% "
                f"above week {week - 1} ({prev_vert:.0f} m). Keep vertical progression gradual "
                f"(at most about +{MAX_VERT_GROWTH * 100:.0f}%).",
            )
        )

    longest = max((_min(w) for w in ws if _is_long(w)), default=0.0)
    if longest and longest / total > profile.long_run_share_cap + LONG_SHARE_TOLERANCE:
        issues.append(
            Issue(
                "LONG_SHARE",
                week,
                f"Week {week}: the long run is {longest / total * 100:.0f}% of weekly time; the cap for this "
                f"athlete is {profile.long_run_share_cap * 100:.0f}%. Shorten the long run or lengthen the "
                f"other sessions.",
            )
        )

    day_min: dict[int, float] = {}
    for w in ws:
        if _day(w) is not None:
            day_min[_day(w)] = day_min.get(_day(w), 0.0) + _min(w)
    for d in sorted(day_min):
        if d + 1 in day_min and len(ws) >= 3:
            pair = day_min[d] + day_min[d + 1]
            if pair > total * BACK_TO_BACK_SHARE and min(day_min[d], day_min[d + 1]) >= 0.2 * total:
                issues.append(
                    Issue(
                        "BACK_TO_BACK",
                        week,
                        f"Week {week}: {DAYS[d]} and {DAYS[d + 1]} hold {pair / total * 100:.0f}% of the week. "
                        f"Back-to-back long days are only an occasional overreach block and must stay under "
                        f"{BACK_TO_BACK_SHARE * 100:.0f}% of weekly volume.",
                    )
                )
                break

    for w in ws:
        if _min(w) > MAX_SESSION_MIN:
            issues.append(
                Issue(
                    "SESSION_TOO_LONG",
                    week,
                    f"Week {week}: {_label(w)} is {_min(w):.0f} min. No single session may exceed "
                    f"{MAX_SESSION_MIN // 60} hours.",
                )
            )

    if not _is_down(weeks, week):
        builds, wk = 1, week - 1
        while wk >= 1 and weeks.get(wk) and not _is_down(weeks, wk):
            builds += 1
            wk -= 1
        if builds > BUILD_WEEKS_BEFORE_RECOVERY:
            issues.append(
                Issue(
                    "RECOVERY_DUE",
                    week,
                    f"Week {week} is build week {builds} in a row. Make it a recovery week at about 70-85% of "
                    f"week {week - 1}'s time before building again (3 build weeks : 1 recovery week).",
                )
            )
    return issues


def lint_weeks(workouts: list[dict[str, Any]], weeks: set[int], profile: TierProfile) -> list[Issue]:
    return [i for wk in sorted(weeks) for i in lint_week(workouts, wk, profile)]
