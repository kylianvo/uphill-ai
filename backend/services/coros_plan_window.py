"""Pure date/window logic for pushing an Uphill plan to a COROS training plan.

No I/O. Weeks are natural Monday-Sunday weeks on both sides: Uphill's week 1
starts on the Monday on or before plans.start_date (calendar_rules), and COROS
plans cover whole natural weeks with dayNo 0 = the COROS plan start date.
"""

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from services.calendar_rules import DAYS, start_monday, workout_date
from services.coach_tools.base import json_safe
from services.coros_workouts import SPORT_REST, build_day, rest_course, validate_course

WINDOW_WEEKS = 4
MAX_PLAN_WEEKS = 16
DEFAULT_PHASE = 1  # COROS "preparation"
PHASE_TYPES = {
    "base": 2,
    "build": 3,
    "peak": 4,
    "taper": 5,
    "race week": 5,
    "race": 5,
    "recovery": 6,
    "transition": 6,
}
HASH_FIELDS = (
    "id",
    "week_number",
    "day_of_week",
    "title",
    "type",
    "duration_minutes",
    "target_zone",
    "target_hr_range",
    "interval_reps",
    "interval_rep_value",
    "interval_rep_unit",
    "walk_interval_value",
    "elevation_gain_m",
    "description",
    "fueling_tip",
    "session_slot",
    "is_completed",
    "matched_activity_id",
    "approved_at",
)


def monday_of(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def window_end(start: dt.date, weeks: int = WINDOW_WEEKS) -> dt.date:
    """Sunday of the `weeks`-th natural week, counting start's own week as week 1."""
    return monday_of(start) + dt.timedelta(days=7 * weeks - 1)


def natural_weeks(start: dt.date, end: dt.date) -> int:
    return (monday_of(end) - monday_of(start)).days // 7 + 1


def ymd(d: dt.date) -> int:
    return int(d.strftime("%Y%m%d"))


def _dates(start: dt.date, end: dt.date) -> list[dt.date]:
    return [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]


def rows_by_date(plan: dict[str, Any], rows: list[dict[str, Any]]) -> dict[dt.date, list[dict[str, Any]]]:
    monday = start_monday(plan.get("start_date"))
    if monday is None:
        return {}
    out: dict[dt.date, list[dict[str, Any]]] = {}
    for r in rows:
        if r.get("day_of_week") not in DAYS or not r.get("week_number"):
            continue
        out.setdefault(workout_date(monday, int(r["week_number"]), r["day_of_week"]), []).append(r)
    return out


def _day_hash(rows: list[dict[str, Any]]) -> str:
    payload = sorted(({f: json_safe(r.get(f)) for f in HASH_FIELDS} for r in rows), key=lambda x: str(x.get("id")))
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def day_hashes(by_date: dict[dt.date, list[dict[str, Any]]], start: dt.date, end: dt.date) -> dict[str, str]:
    return {d.isoformat(): _day_hash(by_date.get(d, [])) for d in _dates(start, end)}


@dataclass
class DayPush:
    date: dt.date
    courses: list[dict[str, Any]]


@dataclass
class PushWindow:
    start: dt.date
    end: dt.date
    days: list[DayPush] = field(default_factory=list)
    locked_dates: list[dt.date] = field(default_factory=list)
    left_in_uphill: int = 0
    invalid: int = 0


def build_window(by_date: dict[dt.date, list[dict[str, Any]]], start: dt.date, end: dt.date, lang: str) -> PushWindow:
    """One DayPush per date in [start, end], except locked days (a completed or
    matched Uphill workout) which are omitted so COROS keeps what it has."""
    window = PushWindow(start=start, end=end)
    for d in _dates(start, end):
        rows = by_date.get(d, [])
        if any(r.get("is_completed") or r.get("matched_activity_id") for r in rows):
            window.locked_dates.append(d)
            continue
        courses, left = build_day(rows, lang)
        valid = [c for c in courses if not validate_course(c)]
        window.invalid += len(courses) - len(valid)
        window.left_in_uphill += left
        window.days.append(DayPush(d, valid or [rest_course(lang)]))
    return window


def course_list(window: PushWindow, anchor: dt.date) -> list[dict[str, Any]]:
    return [{**c, "dayNo": (day.date - anchor).days} for day in window.days for c in day.courses]


def has_run(window: PushWindow, start: dt.date, end: dt.date) -> bool:
    return any(c["sportType"] != SPORT_REST for day in window.days if start <= day.date <= end for c in day.courses)


def _week_phase(by_date: dict[dt.date, list[dict[str, Any]]], monday: dt.date) -> int | None:
    for d in _dates(monday, monday + dt.timedelta(days=6)):
        for r in by_date.get(d, []):
            phase = str(r.get("phase") or "").strip().lower()
            if phase:
                return PHASE_TYPES.get(phase, DEFAULT_PHASE)
    return None


def periodization(
    by_date: dict[dt.date, list[dict[str, Any]]], anchor: dt.date, total_weeks: int
) -> list[dict[str, int]]:
    """COROS phase table: contiguous natural weeks from `anchor`, first phase
    starting on `anchor`, later ones on Mondays, all ending on Sundays. A week
    without Uphill rows inherits the previous week's phase."""
    first_monday = monday_of(anchor)
    weekly: list[int] = []
    for i in range(total_weeks):
        phase = _week_phase(by_date, first_monday + dt.timedelta(weeks=i))
        weekly.append(phase if phase is not None else (weekly[-1] if weekly else DEFAULT_PHASE))
    phases: list[dict[str, int]] = []
    for i, phase_type in enumerate(weekly):
        week_start = anchor if i == 0 else first_monday + dt.timedelta(weeks=i)
        week_end = first_monday + dt.timedelta(weeks=i, days=6)
        if phases and phases[-1]["phaseType"] == phase_type:
            phases[-1]["endDate"] = ymd(week_end)
            phases[-1]["durationWeeks"] += 1
        else:
            phases.append(
                {"phaseType": phase_type, "startDate": ymd(week_start), "endDate": ymd(week_end), "durationWeeks": 1}
            )
    return phases
