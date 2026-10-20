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

AET_BAND = (-10, 3)  # bpm around AeT: at or just under the aerobic threshold
MIN_RUN_MINUTES = 30
MIN_RUNS = 3
MIN_WEEKS_FOR_PATH = 3  # weeks between the baseline and the latest point
A_EXTRA = 0.05  # the A goal asks for 5% more than the assumed improvement, earned across the plan
ON_TOLERANCE = 0.01  # within a percentage point of the line still counts as on it
AHEAD_MARGIN = 0.005
HIGH_CONFIDENCE_WEEKS = 8


@dataclass(frozen=True)
class WeekPoint:
    week: int
    pace_min_km: float  # grade-adjusted
    n: int


@dataclass(frozen=True)
class PathStatus:
    b: str  # ahead | on | behind
    a: str
    measured_pct: float  # how much faster than the baseline, in percent
    expected_pct: float
    weeks: int
    confidence: str  # low | medium | high


def qualifying(a: dict[str, Any], aet_hr: float) -> bool:
    hr = a.get("avg_hr")
    pace = a.get("adjusted_pace_sec_per_km")
    if not hr or not pace or "run" not in str(a.get("activity_type") or "").lower():
        return False
    if float(a.get("duration_seconds") or 0) < MIN_RUN_MINUTES * 60:
        return False
    return aet_hr + AET_BAND[0] <= hr <= aet_hr + AET_BAND[1]


def weekly_points(
    activities: list[dict[str, Any]], aet_hr: float, plan_monday: date, through_week: int
) -> list[WeekPoint]:
    by_week: dict[int, list[float]] = {}
    for a in activities:
        if not qualifying(a, aet_hr):
            continue
        start = a["start_time"]
        day = start.date() if isinstance(start, datetime) else start
        week = (day - plan_monday).days // 7 + 1
        if 1 <= week <= through_week:
            by_week.setdefault(week, []).append(float(a["adjusted_pace_sec_per_km"]) / 60)
    return [WeekPoint(w, median(v), len(v)) for w, v in sorted(by_week.items()) if len(v) >= MIN_RUNS]


def _status(measured: float, expected: float) -> str:
    if measured >= expected + AHEAD_MARGIN:
        return "ahead"
    return "on" if measured >= expected - ON_TOLERANCE else "behind"


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
    return PathStatus(
        b=_status(measured, expected),
        a=_status(measured, a_expected),
        measured_pct=round(measured * 100, 2),
        expected_pct=round(expected * 100, 2),
        weeks=weeks,
        confidence="high" if weeks >= HIGH_CONFIDENCE_WEEKS else "medium" if weeks >= 5 else "low",
    )


def plan_monday(start_date: str) -> date:
    d = date.fromisoformat(str(start_date)[:10])
    return d - timedelta(days=d.weekday())
