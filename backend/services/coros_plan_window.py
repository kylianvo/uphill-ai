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
from services.coros_workouts import SPORT_REST, build_day, rest_course, validate_course, workout_kind

WINDOW_WEEKS = 4
MIN_PLAN_WEEKS = 4
MAX_PLAN_WEEKS = 16
MAX_START_DELAY_DAYS = 14  # COROS: planStartDate within [today, today + 14]
RACE_GOALS = frozenset({"finish", "time", "optimal"})
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
    "race_placeholder",
    "race_name",
    "course_distance_km",
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
    return day_hashes_for(by_date, _dates(start, end))


def day_hashes_for(by_date: dict[dt.date, list[dict[str, Any]]], dates: list[dt.date]) -> dict[str, str]:
    return {d.isoformat(): _day_hash(by_date.get(d, [])) for d in dates}


def _as_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def race_date_of(plan: dict[str, Any]) -> dt.date | None:
    return _as_date(plan.get("race_date"))


def is_race_goal(plan: dict[str, Any]) -> bool:
    """A real race to anchor a COROS plan on. Non-race goals store a synthetic
    race_date at the plan's end, which must not become a "Race day"."""
    return str(plan.get("goal_type") or "").lower() in RACE_GOALS and race_date_of(plan) is not None


def with_race_day(
    plan: dict[str, Any], by_date: dict[dt.date, list[dict[str, Any]]]
) -> dict[dt.date, list[dict[str, Any]]]:
    """by_date plus a race-day placeholder row when the race day has no generated run.
    The row carries race name/distance so the day hash follows race edits."""
    race = race_date_of(plan)
    if not is_race_goal(plan) or race is None:
        return by_date
    if any(workout_kind(r) == "run" for r in by_date.get(race, [])):
        return by_date
    placeholder = {
        "id": None,
        "race_placeholder": True,
        "race_name": plan.get("race_name"),
        "course_distance_km": plan.get("course_distance_km"),
        "type": "Race",
        "approved_at": "race",
        "session_slot": "main",
    }
    return {**by_date, race: [*by_date.get(race, []), placeholder]}


def last_generated_date(by_date: dict[dt.date, list[dict[str, Any]]]) -> dt.date | None:
    return max(by_date) if by_date else None


def last_run_date(by_date: dict[dt.date, list[dict[str, Any]]]) -> dt.date | None:
    runs = [d for d, rows in by_date.items() if any(workout_kind(r) == "run" for r in rows)]
    return max(runs) if runs else None


class GeometryRefusal(Exception):
    def __init__(self, code: str, params: dict[str, Any]) -> None:
        super().__init__(code)
        self.code = code
        self.params = params


@dataclass(frozen=True)
class PlanGeometry:
    start: dt.date
    end: dt.date  # Sunday of the final week
    weeks: int


def plan_geometry(race: dt.date, last_run: dt.date | None, today: dt.date) -> PlanGeometry:
    """A new COROS plan anchored on race day: it starts today, or later (up to
    14 days, the COROS limit) so a far race still fits in 16 weeks; it ends on
    race week, or on a later generated run's week, capped at 16 weeks."""
    race_monday = monday_of(race)
    earliest = race_monday - dt.timedelta(weeks=MAX_PLAN_WEEKS - 1)
    start = max(today, earliest)
    if start > today + dt.timedelta(days=MAX_START_DELAY_DAYS):
        opens_on = earliest - dt.timedelta(days=MAX_START_DELAY_DAYS)
        raise GeometryRefusal("RACE_too_far", {"opens_on": opens_on.isoformat()})
    end_monday = max(race_monday, monday_of(last_run)) if last_run else race_monday
    end_monday = min(end_monday, monday_of(start) + dt.timedelta(weeks=MAX_PLAN_WEEKS - 1))
    end = end_monday + dt.timedelta(days=6)
    weeks = natural_weeks(start, end)
    if weeks < MIN_PLAN_WEEKS:
        raise GeometryRefusal("RACE_too_close", {"weeks": natural_weeks(today, race)})
    return PlanGeometry(start=start, end=end, weeks=weeks)


def send_dates(frm: dt.date, last_generated: dt.date | None, race: dt.date | None) -> list[dt.date]:
    """Every date from `frm` through the last generated date, plus race day.
    Ungenerated days are not sent, so COROS shows them empty rather than "Rest"."""
    dates = _dates(frm, last_generated) if last_generated and last_generated >= frm else []
    if race and race >= frm and race not in dates:
        dates.append(race)
    return sorted(dates)


def clear_dates(stored: dict[str, str], sent: list[dt.date], frm: dt.date, until: dt.date) -> list[dt.date]:
    """Days sent before that aren't sent now (a moved workout, a moved race):
    a rest entry clears them. Only within [frm, until] -- COROS can't edit the past
    or days beyond the plan's end."""
    sent_set = set(sent)
    out = []
    for key in stored:
        d = _as_date(key)
        if d and frm <= d <= until and d not in sent_set:
            out.append(d)
    return sorted(out)


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


def build_window(
    by_date: dict[dt.date, list[dict[str, Any]]],
    start: dt.date,
    end: dt.date,
    lang: str,
    *,
    dates: list[dt.date] | None = None,
    clear: list[dt.date] | None = None,
) -> PushWindow:
    """One DayPush per date in `dates` (default: every date in [start, end]),
    plus a rest entry for each `clear` date. Locked days (a completed or matched
    Uphill workout) are omitted so COROS keeps what it has."""
    window = PushWindow(start=start, end=end)
    wanted = _dates(start, end) if dates is None else list(dates)
    for d in sorted({*wanted, *(clear or [])}):
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


def standalone_window(
    by_date: dict[dt.date, list[dict[str, Any]]], start: dt.date, end: dt.date, lang: str
) -> PushWindow:
    """Standalone COROS workouts can only be runs: rest days are skipped and
    strength sessions (a rest-type placeholder in plan mode) stay in Uphill."""
    full = build_window(by_date, start, end, lang)
    window = PushWindow(start=start, end=end, locked_dates=full.locked_dates, invalid=full.invalid)
    for day in full.days:
        rows = [r for r in by_date.get(day.date, []) if r.get("approved_at") is not None]
        runs = [c for c in day.courses if c["sportType"] != SPORT_REST]
        window.left_in_uphill += sum(1 for r in rows if workout_kind(r) == "other")
        if runs:
            window.days.append(DayPush(day.date, runs))
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
