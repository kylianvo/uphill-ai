"""Turns a workouts row (week_number + day_of_week) into a calendar date.

Extracted from CalendarService.generate_ics_string so the matching engine and
the athlete's ICS export cannot drift apart about which day a session falls on.
The legacy race-anchored fallback exists because plans created before
plans.start_date was stored have no explicit start.
"""

from datetime import date, datetime, timedelta

DAY_OFFSETS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def workout_date(start_monday: date, week_number: int, day_of_week: str) -> date:
    """Week 1 Monday is start_monday. An unrecognised day name falls back to
    Monday rather than raising -- plan generation has emitted odd strings, and a
    bad day name must not abort a sync."""
    offset = DAY_OFFSETS.get(day_of_week, 0)
    return start_monday + timedelta(days=(int(week_number) - 1) * 7 + offset)


def plan_start_monday(plan_start_date: str | None, workouts: list[dict], race_date: date) -> date:
    """Resolves the Monday of the plan's first week.

    Prefers plans.start_date. Falls back to anchoring on the race workout for
    legacy plans, and finally to assuming the race sits in the last week.
    """
    if plan_start_date:
        try:
            parsed = datetime.strptime(plan_start_date, "%Y-%m-%d").date()
            return parsed - timedelta(days=parsed.weekday())
        except ValueError:
            pass

    race_weekday_name = race_date.strftime("%A")
    race_day_offset = DAY_OFFSETS.get(race_weekday_name, 5)
    race_week = None
    for workout in workouts:
        title = (workout.get("title") or "").upper()
        w_type = (workout.get("type") or "").upper()
        if "TARGET EVENT" in title or w_type == "RACE":
            race_week = int(workout["week_number"])
            break

    if race_week is not None:
        return race_date - timedelta(days=((race_week - 1) * 7) + race_day_offset)

    total_weeks = max((int(w["week_number"]) for w in workouts), default=12)
    return race_date - timedelta(days=((total_weeks - 1) * 7) + race_date.weekday())
