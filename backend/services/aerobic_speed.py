"""Is the athlete getting fitter on the path to their B and A goals? Measured from training, not asked.

The signal is aerobic speed: the grade-adjusted pace of steady runs held at aerobic-threshold heart rate.
It is passive (any synced run counts) and robust (a weekly median of at least three runs). The goals
credit the training improvement the plan engine assumes (services/plan_adequacy.py); this compares what
the athlete actually gained with that line, and with the A line, which adds the A goal's extra 5% over the plan.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import median
from typing import Any

from services.plan_adequacy import _improvement

AET_BAND = (-16, 3)  # bpm around AeT: easy aerobic running, most of it well under the threshold
MIN_RUN_MINUTES = 30
MIN_RUNS = 3  # qualifying runs needed in a window
WINDOW_WEEKS = 3  # each weekly point pools this many trailing weeks (sparse weeks are normal)
FLAT_MAX_GAIN_M_PER_KM = 15  # without a grade-adjusted pace, only flat runs may use their average pace
_HARD_WORKOUTS = {"interval", "tempo", "threshold", "race"}  # structured hard sessions are not steady runs
MIN_WEEKS_FOR_PATH = 3  # weeks between the baseline and the latest point
A_EXTRA = 0.05  # the A goal asks for 5% more than the assumed improvement, earned across the plan
ON_TOLERANCE = 0.01  # within a percentage point of the line still counts as on it
AHEAD_MARGIN = 0.005
NOISE_SIGMAS = 2.0
HIGH_CONFIDENCE_WEEKS = 8


@dataclass(frozen=True)
class WeekPoint:
    week: int
    pace_min_km: float  # the pace this athlete would hold at AeT heart rate (grade-adjusted, HR-normalised)
    n: int
    rel_se: float = 0.0  # standard error of the window's median efficiency, relative


@dataclass(frozen=True)
class PathStatus:
    b: str  # ahead | on | behind
    a: str
    measured_pct: float  # how much faster than the baseline, in percent
    expected_pct: float
    weeks: int
    confidence: str  # low | medium | high


def _pace_s(a: dict[str, Any]) -> float | None:
    """Grade-adjusted pace in s/km; the average pace for a flat run that has no adjusted one."""
    if a.get("adjusted_pace_sec_per_km"):
        return float(a["adjusted_pace_sec_per_km"])
    avg, dist = a.get("avg_pace_sec_per_km"), float(a.get("distance_km") or 0)
    if avg and dist > 0 and float(a.get("elevation_gain_m") or 0) / dist <= FLAT_MAX_GAIN_M_PER_KM:
        return float(avg)
    return None


def efficiency(a: dict[str, Any]) -> float:
    """Metres per second per heartbeat: comparable across runs at different heart rates in the band."""
    return (1000 / _pace_s(a)) / float(a["avg_hr"])


def qualifying(a: dict[str, Any], aet_hr: float) -> bool:
    hr = a.get("avg_hr")
    if not hr or not _pace_s(a) or "run" not in str(a.get("activity_type") or "").lower():
        return False
    if str(a.get("workout_type") or "").lower() in _HARD_WORKOUTS:
        return False
    if float(a.get("duration_seconds") or 0) < MIN_RUN_MINUTES * 60:
        return False
    return aet_hr + AET_BAND[0] <= hr <= aet_hr + AET_BAND[1]


def weekly_points(
    activities: list[dict[str, Any]], aet_hr: float, plan_monday: date, through_week: int
) -> list[WeekPoint]:
    """One point per week that has enough steady runs in its trailing window: the pace the athlete would hold
    at AeT heart rate, from the window's median efficiency."""
    by_week: dict[int, list[float]] = {}
    for a in activities:
        if not qualifying(a, aet_hr):
            continue
        start = a["start_time"]
        day = start.date() if isinstance(start, datetime) else start
        week = (day - plan_monday).days // 7 + 1
        if 1 <= week <= through_week:
            by_week.setdefault(week, []).append(efficiency(a))
    points: list[WeekPoint] = []
    for week in range(1, through_week + 1):
        window = [e for w in range(max(1, week - WINDOW_WEEKS + 1), week + 1) for e in by_week.get(w, [])]
        if len(window) >= MIN_RUNS and week in by_week:
            speed_at_aet = median(window) * aet_hr  # m/s
            mid = median(window)
            spread = 1.4826 * median(abs(e - mid) for e in window) / mid  # robust relative spread
            points.append(WeekPoint(week, 1000 / speed_at_aet / 60, len(window), spread / len(window) ** 0.5))
    return points


def _status(measured: float, expected: float, tol: float = 0.01) -> str:
    if measured >= expected + max(AHEAD_MARGIN, tol):
        return "ahead"
    return "on" if measured >= expected - tol else "behind"


def path(points: list[WeekPoint], total_weeks: int) -> PathStatus | None:
    """B and A status from the weekly series, or None until there is enough history."""
    if len(points) < 2:
        return None
    first, last = points[0], points[-1]
    weeks = last.week - first.week
    if weeks < MIN_WEEKS_FOR_PATH:
        return None
    baseline = median(p.pace_min_km for p in points[:2])
    latest = median(p.pace_min_km for p in points[-2:])
    measured = baseline / latest - 1  # a lower pace is faster
    expected = _improvement(weeks)
    a_expected = expected + A_EXTRA * weeks / max(total_weeks, 1)
    # Week-to-week medians are noisy (heat, terrain, sleep): the gap must clear what the data itself cannot tell.
    tol = max(ON_TOLERANCE, NOISE_SIGMAS * (points[0].rel_se ** 2 + points[-1].rel_se ** 2) ** 0.5)
    return PathStatus(
        b=_status(measured, expected, tol),
        a=_status(measured, a_expected, tol),
        measured_pct=round(measured * 100, 2),
        expected_pct=round(expected * 100, 2),
        weeks=weeks,
        confidence="high" if weeks >= HIGH_CONFIDENCE_WEEKS else "medium" if weeks >= 5 else "low",
    )


def plan_monday(start_date: str) -> date:
    d = date.fromisoformat(str(start_date)[:10])
    return d - timedelta(days=d.weekday())
