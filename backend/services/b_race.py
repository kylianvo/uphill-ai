"""B-races: tune-up races inside a race plan.

The rules are pure and deterministic: the level, the mini-taper and the recovery window come from here,
never from the model. Spec: docs/superpowers/specs/2026-10-26-b-race-design.md
"""

import math
from dataclasses import asdict, dataclass, replace
from datetime import date, timedelta
from typing import Any, Literal

from log_utils import get_logger
from services.athlete_tier import effort_km

logger = get_logger(__name__)

Effort = Literal["race", "training"]
Level = Literal["good", "conditions", "risky", "not_recommended"]

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
NOT_RECOMMENDED_DAYS = 14  # doctrine: never within the final 10-14 days before the A-race
CLOSE_DAYS = 28
STACK_DAYS, STACK_DAYS_LONG, LONG_EKM = 21, 28, 42
LOAD_RISKY, LOAD_CONDITIONS = 1.5, 1.2
BASE_SIZE_RATIO = 0.6

# (max effort-km, taper days, recovery days); beyond the last row: 4 / 10.
_TAPER_RECOVERY = ((21, 2, 3), (42, 3, 5), (70, 3, 7))


@dataclass(frozen=True)
class BRace:
    race_date: date
    distance_km: float
    elevation_gain_m: float | None
    effort: Effort
    options_km: tuple[float, ...] = ()


@dataclass(frozen=True)
class PlanFacts:
    a_date: date
    a_distance_km: float
    a_gain_m: float | None
    plan_monday: date
    total_weeks: int
    longest_recent_km: float | None
    longest_recent_min: float | None
    other_races: tuple[BRace, ...] = ()


@dataclass(frozen=True)
class Verdict:
    level: Level
    reasons: tuple[str, ...]
    numbers: dict[str, float | int | None]
    taper_days: int
    recovery_days: int
    suggestion: dict[str, Any] | None


def race_effort_km(distance_km: float, gain_m: float | None) -> float:
    return effort_km(distance_km, gain_m) or 0.0


def taper_days(ekm: float, effort: Effort) -> int:
    days = next((t for limit, t, _ in _TAPER_RECOVERY if ekm <= limit), 4)
    return max(1, days - 1) if effort == "training" else days


def recovery_days(ekm: float, effort: Effort, kept_risky: bool = False) -> int:
    days = next((r for limit, _, r in _TAPER_RECOVERY if ekm <= limit), 10)
    if effort == "training":
        days = math.ceil(days / 2)
    return days + (2 if kept_risky else 0)


def week_and_day(plan_monday: date, race_date: date) -> tuple[int, str]:
    return (race_date - plan_monday).days // 7 + 1, DAYS[race_date.weekday()]


def _phase(facts: PlanFacts, day: date) -> str:
    from services.plan_generator import PlanGenerator

    week, _ = week_and_day(facts.plan_monday, day)
    return PlanGenerator.phase_for_week(week, facts.total_weeks)


def _ekm(race: BRace) -> float:
    return race_effort_km(race.distance_km, race.elevation_gain_m)


def _verdict(race: BRace, facts: PlanFacts) -> Verdict:
    """The level without a suggestion."""
    ekm = _ekm(race)
    a_ekm = race_effort_km(facts.a_distance_km, facts.a_gain_m) or None
    days_before_a = (facts.a_date - race.race_date).days
    load_ratio = round(ekm / facts.longest_recent_km, 2) if facts.longest_recent_km else None
    size_ratio = round(ekm / a_ekm, 2) if a_ekm else None
    rec = recovery_days(ekm, race.effort)
    numbers = {
        "effort_km": round(ekm, 1),
        "days_before_a": days_before_a,
        "load_ratio": load_ratio,
        "size_ratio": size_ratio,
        "longest_recent_km": facts.longest_recent_km,
    }
    racing = race.effort == "race"

    def done(level: Level, reasons: list[str]) -> Verdict:
        return Verdict(level, tuple(reasons), numbers, taper_days(ekm, race.effort), rec, None)

    if days_before_a < NOT_RECOMMENDED_DAYS:
        return done("not_recommended", ["too_close"])

    risky: list[str] = []
    window = [race.race_date + timedelta(days=d) for d in range(rec + 1)]
    phases = {_phase(facts, d) for d in window}
    if phases & {"Taper", "Race Week"}:
        risky.append("overlaps_taper")
    if "Peak" in phases:
        risky.append("overlaps_peak")
    if racing:
        for other in facts.other_races:
            if other.effort != "race":
                continue
            limit = STACK_DAYS_LONG if max(ekm, _ekm(other)) >= LONG_EKM else STACK_DAYS
            if abs((other.race_date - race.race_date).days) < limit:
                risky.append("stacked")
                break
        if load_ratio is not None and load_ratio > LOAD_RISKY:
            risky.append("longer_than_trained")
    if risky:
        return done("risky", risky)

    conditions: list[str] = []
    if racing and load_ratio is not None and load_ratio > LOAD_CONDITIONS:
        conditions.append("longer_than_trained")
    if racing and days_before_a < CLOSE_DAYS:
        conditions.append("too_close")
    if _phase(facts, race.race_date) == "Base" and size_ratio is not None and size_ratio > BASE_SIZE_RATIO:
        conditions.append("base_phase")
    if conditions:
        return done("conditions", conditions)
    return done("good", [])


def _candidates(race: BRace) -> list[BRace]:
    shorter = sorted((o for o in race.options_km if o < race.distance_km), reverse=True)

    def at(km: float, effort: Effort) -> BRace:
        gain = race.elevation_gain_m * km / race.distance_km if race.elevation_gain_m and race.distance_km else None
        return replace(race, distance_km=km, elevation_gain_m=gain, effort=effort)

    return (
        [at(km, "race") for km in shorter]
        + ([replace(race, effort="training")] if race.effort == "race" else [])
        + [at(km, "training") for km in shorter]
    )


def suggest(race: BRace, facts: PlanFacts) -> dict[str, Any] | None:
    """The first safer version that scores `good`; none, the shortest one at training effort."""
    candidates = _candidates(race)
    if not candidates:
        return None
    pick = next((c for c in candidates if _verdict(c, facts).level == "good"), candidates[-1])
    return {"distance_km": pick.distance_km, "effort": pick.effort}


def assess(race: BRace, facts: PlanFacts) -> Verdict:
    v = _verdict(race, facts)
    return v if v.level == "good" else replace(v, suggestion=suggest(race, facts))


# ─── Plan facts, course lookup and prediction (impure) ───────────────────────

LEVELS = ("good", "conditions", "risky", "not_recommended")
ELIGIBLE_GOALS = ("finish", "time", "optimal")
MAX_PLANNED = 3
LONGEST_RUN_WINDOW_DAYS = 42


def is_race_plan(plan: dict[str, Any]) -> bool:
    return plan.get("goal_type") in ELIGIBLE_GOALS


def _date(v: Any) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def _row_race(row: dict[str, Any]) -> BRace:
    return BRace(
        _date(row["race_date"]),
        float(row["distance_km"]),
        row.get("elevation_gain_m"),
        row.get("effort") or "race",
        tuple(row.get("options_km") or ()),
    )


def facts_for_plan(
    user_id: int, plan: dict[str, Any], exclude_race_id: int | None = None, today: date | None = None
) -> PlanFacts:
    import db
    from services.calendar_rules import start_monday

    today = today or date.today()
    km, minutes = db.longest_recent_run(user_id, today - timedelta(days=LONGEST_RUN_WINDOW_DAYS))
    others = tuple(_row_race(r) for r in db.get_plan_races(plan["id"]) if r["id"] != exclude_race_id)
    return PlanFacts(
        a_date=_date(plan["race_date"]),
        a_distance_km=float(plan.get("course_distance_km") or 0),
        a_gain_m=plan.get("course_elevation_gain_m"),
        plan_monday=start_monday(plan.get("start_date")) or today - timedelta(days=today.weekday()),
        total_weeks=int(plan.get("total_weeks") or 1),
        longest_recent_km=km,
        longest_recent_min=minutes,
        other_races=others,
    )


def resolve_input(data: dict[str, Any]) -> dict[str, Any]:
    """The race as stored: the race list fills distance, climb and the distance options. Raises
    ValueError("distance_required") when neither the runner nor the race list gives a distance."""
    from services import course_match, race_matcher

    name = (data.get("race_name") or "").strip()
    distance, gain, _ = course_match.resolve_course_match(name, data.get("distance_km"), data.get("elevation_gain_m"))
    if not distance or distance <= 0:
        raise ValueError("distance_required")
    options = sorted({float(d["distance_km"]) for d in race_matcher.race_distances(name) if d.get("distance_km")})
    matched = race_matcher.match_race(name, distance_km=distance)
    return {
        "race_name": name,
        "course_ref": getattr(matched, "race_name", None),
        "race_date": _date(data["race_date"]),
        "distance_km": float(distance),
        "elevation_gain_m": float(gain) if gain is not None else None,
        "options_km": [int(o) if o.is_integer() else o for o in options],
        "effort": data.get("effort") or "race",
    }


def predict_band(user: dict[str, Any], race: dict[str, Any]) -> dict[str, int] | None:
    """The finish band from the goal engine, or None. Run without the plan, so the B-race assessment never
    becomes the plan's latest one (which the A-race Goal pill reads)."""
    from services import goal_service

    try:
        out = goal_service.run(
            user=user,
            race_name=race.get("course_ref") or race["race_name"],
            distance_km=race["distance_km"],
            elevation_gain_m=race.get("elevation_gain_m"),
            race_date=str(race["race_date"]),
            plan=None,
            trigger="b_race",
        )
        goals = out.get("goals") or {}
        return {"low_sec": int(goals["a"] * 60), "high_sec": int(goals["c"] * 60)}
    except Exception:
        logger.warning("b-race prediction failed", exc_info=True)
        return None


def evaluate(
    user: dict[str, Any],
    plan: dict[str, Any],
    data: dict[str, Any],
    race_id: int | None = None,
    predict: bool = False,
    today: date | None = None,
) -> dict[str, Any]:
    """Resolve, assess and (when asked) predict one race against the plan. The live assess skips the
    prediction: it can reach the model and runs on every change of distance or effort."""
    race = resolve_input(data)
    facts = facts_for_plan(user["id"], plan, exclude_race_id=race_id, today=today)
    verdict = assess(_row_race(race), facts)
    out = asdict(verdict)
    out["cost"] = None
    return {"race": race, "verdict": out, "predicted": predict_band(user, race) if predict else None}
