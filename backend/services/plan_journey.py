"""The plan's journey: phases, milestones, days to race and whether the plan keeps the athlete's preferences.

Pure and deterministic: the Today/journey strip reads this, and the coach message uses the same milestones
as facts. A milestone is `done` once its week is behind the athlete (a completed week), never from a guess.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

from db import compute_current_week
from services import plan_lint
from services.athlete_tier import TierProfile, get_profile

LONG_RUN_MILESTONE_MIN = 180  # the first long run of three hours or more
_PREFERENCE_CODES = {"LONG_RUN_DAY", "DAYS_SHORT"}


@dataclass(frozen=True)
class Phase:
    name: str
    start_week: int
    end_week: int


@dataclass(frozen=True)
class Milestone:
    key: str
    week: int
    done: bool


@dataclass(frozen=True)
class Preferences:
    long_run_day: str | None = None
    days_per_week: int | None = None


def phases(workouts: list[dict[str, Any]]) -> list[Phase]:
    by_week: dict[int, str] = {}
    for w in workouts:
        if isinstance(w.get("week_number"), int) and w.get("phase"):
            by_week.setdefault(w["week_number"], w["phase"])
    out: list[Phase] = []
    for wk in sorted(by_week):
        name = by_week[wk]
        if out and out[-1].name == name and out[-1].end_week == wk - 1:
            out[-1] = Phase(name, out[-1].start_week, wk)
        else:
            out.append(Phase(name, wk, wk))
    return out


def milestones(workouts: list[dict[str, Any]], current_week: int) -> list[Milestone]:
    weeks = plan_lint._by_week(workouts)
    found: dict[str, int] = {}
    for wk in sorted(weeks):
        ws = weeks[wk]
        phase = next((w.get("phase") for w in ws if w.get("phase")), "")
        if "long_run_3h" not in found and any(
            plan_lint._is_long(w) and plan_lint._min(w) >= LONG_RUN_MILESTONE_MIN for w in ws
        ):
            found["long_run_3h"] = wk
        if "first_recovery_week" not in found and phase not in plan_lint.DOWN_PHASES and plan_lint._is_down(weeks, wk):
            found["first_recovery_week"] = wk
        if phase == "Taper":
            found.setdefault("taper_start", wk)
        if phase == "Race Week":
            found.setdefault("race_week", wk)
    build = [wk for wk in weeks if any(w.get("phase") in ("Build", "Peak") for w in weeks[wk])]
    if build:
        found["peak_week"] = max(build, key=lambda wk: plan_lint.week_minutes(weeks[wk]))
    return sorted((Milestone(k, wk, wk < current_week) for k, wk in found.items()), key=lambda m: (m.week, m.key))


def days_to_race(race_date: str | None, today: date) -> int | None:
    if not race_date:
        return None
    try:
        return max((date.fromisoformat(str(race_date)[:10]) - today).days, 0)
    except ValueError:
        return None


def deviations(
    workouts: list[dict[str, Any]], profile: TierProfile, prefs: Preferences, current_week: int
) -> list[dict[str, Any]]:
    """Upcoming weeks (this one onward) that break the athlete's long-run day or training-day count."""
    weeks = {wk for wk in plan_lint._by_week(workouts) if wk >= current_week}
    lint_prefs = plan_lint.Prefs(long_run_day=prefs.long_run_day, days_per_week=prefs.days_per_week)
    issues = plan_lint.lint_weeks(workouts, weeks, profile, lint_prefs)
    return [{"code": i.code, "week": i.week} for i in issues if i.code in _PREFERENCE_CODES]


def journey(plan: dict[str, Any], workouts: list[dict[str, Any]], today: date) -> dict[str, Any]:
    total = int(plan.get("total_weeks") or 0)
    current = compute_current_week(plan.get("start_date"), total)
    prefs = Preferences(plan.get("long_run_day"), plan.get("days_per_week"))
    return {
        "current_week": current,
        "total_weeks": total,
        "days_to_race": days_to_race(plan.get("race_date"), today),
        "phases": [p.__dict__ for p in phases(workouts)],
        "milestones": [m.__dict__ for m in milestones(workouts, current)],
        "preferences": {
            "days_per_week": prefs.days_per_week,
            "long_run_day": prefs.long_run_day,
            "mountain": plan.get("training_mountain"),
        },
        "deviations": deviations(workouts, get_profile(plan.get("athlete_tier")), prefs, current),
    }
