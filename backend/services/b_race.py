"""B-races: tune-up races inside a race plan.

The rules are pure and deterministic: the level, the mini-taper and the recovery window come from here,
never from the model. Spec: docs/superpowers/specs/2026-10-26-b-race-design.md
"""

import math
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime, timedelta
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


def current_date() -> date:
    """Today, as one hook tests can pin."""
    return date.today()


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

    today = today or current_date()
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
    if verdict.level != "good":
        try:
            import db

            out["cost"] = cost({**race, "id": race_id or -1}, db.get_plan_workouts(plan["id"]), facts.plan_monday)
        except Exception:
            logger.warning("b-race cost failed", exc_info=True)
    return {"race": race, "verdict": out, "predicted": predict_band(user, race) if predict else None}


# ─── The races a plan holds (used by the routes and the plan payload) ─────────


def validate(plan: dict[str, Any], race_date: date, today: date | None = None) -> None:
    """Raises ValueError with an API code when the race can't belong to this plan."""
    from services.calendar_rules import start_monday

    if not is_race_plan(plan):
        raise ValueError("not_a_race_plan")
    today = today or current_date()
    monday = start_monday(plan.get("start_date")) or today
    if race_date < max(today, monday) or race_date >= _date(plan["race_date"]):
        raise ValueError("date_out_of_range")


def serialize(user_id: int, plan: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Planned races with a verdict recomputed now (the A-race or the athlete's fitness may have moved)."""
    out = []
    for row in rows:
        facts = facts_for_plan(user_id, plan, exclude_race_id=row["id"])
        race = _row_race(row)
        verdict = asdict(assess(race, facts))
        verdict["cost"] = None
        week, day = week_and_day(facts.plan_monday, race.race_date)
        out.append({**row, "race_date": race.race_date.isoformat(), "verdict": verdict, "week": week, "day": day})
    return out


def safe_serialize_plan(user_id: int, plan: dict[str, Any]) -> list[dict[str, Any]]:
    """The plan payload's `b_races`: never fails the plan request it rides on."""
    import db

    if not is_race_plan(plan):
        return []
    try:
        return serialize(user_id, plan, db.get_plan_races(plan["id"]))
    except Exception:
        logger.warning("b-race list failed", exc_info=True, extra={"fields": {"plan_id": plan.get("id")}})
        return []


def _store_fields(user: dict[str, Any], plan: dict[str, Any], data: dict[str, Any], race_id: int | None):
    result = evaluate(user, plan, data, race_id=race_id, predict=True)
    race, verdict = result["race"], result["verdict"]
    validate(plan, race["race_date"])
    level = verdict["level"]
    if level == "not_recommended":
        race["effort"] = "training"  # the runner may still enter it; the plan never tapers for it
    return {
        **race,
        "verdict": verdict,
        "predicted": result["predicted"],
        "kept_against": level if level in ("risky", "not_recommended") else None,
    }


def _one(user_id: int, plan: dict[str, Any], race_id: int) -> dict[str, Any]:
    import db

    return serialize(user_id, plan, [db.get_plan_race(plan["id"], race_id)])[0]


def create(user: dict[str, Any], plan: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    import db

    validate(plan, _date(data["race_date"]))
    if len(db.get_plan_races(plan["id"])) >= MAX_PLANNED:
        raise ValueError("too_many_races")
    race_id = db.insert_plan_race(plan["id"], _store_fields(user, plan, data, None))
    return _one(user["id"], plan, race_id)


def update(user: dict[str, Any], plan: dict[str, Any], race_id: int, changes: dict[str, Any]) -> dict[str, Any]:
    import db

    row = db.get_plan_race(plan["id"], race_id)
    if not row or row["status"] != "planned":
        raise ValueError("not_found")
    data = {k: row.get(k) for k in ("race_name", "race_date", "distance_km", "elevation_gain_m", "effort")}
    data.update({k: v for k, v in changes.items() if v is not None})
    db.update_plan_race(race_id, _store_fields(user, plan, data, race_id))
    return _one(user["id"], plan, race_id)


def cancel(user: dict[str, Any], plan: dict[str, Any], race_id: int) -> dict[str, Any]:
    import db

    row = db.get_plan_race(plan["id"], race_id)
    if not row or row["status"] != "planned":
        raise ValueError("not_found")
    db.update_plan_race(race_id, {"status": "cancelled", "cancelled_at": datetime.now(UTC)})
    return {**db.get_plan_race(plan["id"], race_id), "race_date": _date(row["race_date"]).isoformat()}


def save_setup_races(user: dict[str, Any], plan_id: int, races: list[dict[str, Any]]) -> int:
    """B-races given while creating the plan. A bad one is skipped and logged: the plan is already created."""
    import db

    plan = db.get_plan_by_id(plan_id)
    saved = 0
    for data in races or []:
        try:
            create(user, plan, data)
            saved += 1
        except Exception:
            logger.warning("setup b-race skipped", exc_info=True, extra={"fields": {"plan_id": plan_id}})
    return saved


# ─── The guard: race day, mini-taper and recovery window, whatever the model wrote ────

_A_RACE_PHASES = {"Taper", "Race Week", "Race"}
_EASY_TYPES = {"Easy", "Recovery", "Walk/Run"}
_TAPER_CAP_SHARE = 0.5
_TAPER_CAP_FALLBACK_MIN = 30
_RECOVERY_CAP_MIN = 60
_RECOVERY_CONVERTED_MIN = 45
_STRIDES = " + 3 × 20 s relaxed strides"


def _row_date(plan_monday: date, row: dict[str, Any]) -> date | None:
    if row.get("day_of_week") not in DAYS or not row.get("week_number"):
        return None
    return plan_monday + timedelta(days=(int(row["week_number"]) - 1) * 7 + DAYS.index(row["day_of_week"]))


def _rest(row: dict[str, Any], lang: str) -> None:
    vi = lang == "vi"
    row.update(
        type="Rest",
        title="Nghỉ ngơi và phục hồi" if vi else "Rest & Regeneration",
        description="Ngày nghỉ quanh B-race." if vi else "Rest day around your B-race.",
        duration_minutes=0.0,
        target_zone="",
        target_pace="",
        distance_km=0.0,
        elevation_gain_m=0.0,
        is_priority=False,
    )


def _easy(row: dict[str, Any], minutes: float, zone: str, lang: str, title_en: str, title_vi: str) -> None:
    if row.get("type") not in _EASY_TYPES:
        row.update(type="Easy", title=title_vi if lang == "vi" else title_en, elevation_gain_m=0.0, is_priority=False)
    row["duration_minutes"] = float(min(float(row.get("duration_minutes") or minutes), minutes))
    row["target_zone"] = zone


def _race_shape(race: dict[str, Any]) -> tuple[int, int]:
    """(taper days, recovery days) for a stored race."""
    ekm = race_effort_km(float(race["distance_km"]), race.get("elevation_gain_m"))
    effort = race.get("effort") or "race"
    taper = 0 if race.get("kept_against") == "not_recommended" else taper_days(ekm, effort)
    return taper, recovery_days(ekm, effort, kept_risky=race.get("kept_against") == "risky")


def _race_minutes(race: dict[str, Any]) -> float:
    band = race.get("predicted") or {}
    if band.get("low_sec") and band.get("high_sec"):
        return round((band["low_sec"] + band["high_sec"]) / 2 / 60)
    return round(6 * race_effort_km(float(race["distance_km"]), race.get("elevation_gain_m")))


def enforce(
    workouts: list[dict[str, Any]], races: list[dict[str, Any]], plan_monday: date, lang: str = "en"
) -> list[dict[str, Any]]:
    """Pins each B-race into `workouts` (returns the new list). Idempotent; never touches A-race taper weeks."""
    if not races:
        return workouts
    weeks = {int(w["week_number"]) for w in workouts if w.get("week_number")}
    out = list(workouts)
    shaped = []
    for race in races:
        rdate = _date(race["race_date"])
        week, day = week_and_day(plan_monday, rdate)
        if week not in weeks:
            continue
        shaped.append((race, rdate, *_race_shape(race)))
        phase = next((w.get("phase") for w in out if w.get("week_number") == week and w.get("phase")), None)
        if phase in _A_RACE_PHASES:
            continue
        out = [
            w
            for w in out
            if not (
                w.get("week_number") == week and w.get("day_of_week") == day and w.get("plan_race_id") != race["id"]
            )
        ]
        if not any(w.get("plan_race_id") == race["id"] for w in out):
            out.append(
                {
                    "week_number": week,
                    "day_of_week": day,
                    "phase": phase,
                    "type": "Race",
                    "title": race["race_name"],
                    "description": (
                        "B-race: chạy như buổi tập dài, không dốc hết sức."
                        if lang == "vi"
                        else "B-race: run it as a rehearsal, not all-out."
                    )
                    if (race.get("effort") or "race") == "training"
                    else (
                        "B-race. Tập dượt dinh dưỡng, gậy và nhịp độ."
                        if lang == "vi"
                        else "B-race. Rehearse fuel, poles and pacing."
                    ),
                    "duration_minutes": float(_race_minutes(race)),
                    "distance_km": float(race["distance_km"]),
                    "elevation_gain_m": float(race.get("elevation_gain_m") or 0),
                    "target_zone": "",
                    "is_priority": True,
                    "session_slot": "main",
                    "plan_race_id": race["id"],
                }
            )
        for w in out:  # the race replaces the week's long run
            if w.get("week_number") == week and w.get("type") == "Long Run":
                _rest(w, lang)

    def editable(w: dict[str, Any]) -> bool:
        return w.get("type") not in ("Race", "Rest") and w.get("phase") not in _A_RACE_PHASES

    for race, rdate, taper, _rec in shaped:
        taper_dates = {rdate - timedelta(days=d) for d in range(1, taper + 1)}
        week, _ = week_and_day(plan_monday, rdate)
        easy = sorted(
            float(w.get("duration_minutes") or 0)
            for w in out
            if w.get("week_number") == week
            and w.get("type") in _EASY_TYPES
            and _row_date(plan_monday, w) not in taper_dates
        )
        cap = easy[len(easy) // 2] * _TAPER_CAP_SHARE if easy else _TAPER_CAP_FALLBACK_MIN
        last = max(taper_dates) if taper_dates else None
        for w in out:
            d = _row_date(plan_monday, w)
            if d not in taper_dates or not editable(w):
                continue
            if w.get("type") not in _EASY_TYPES and w.get("type") not in ("Interval", "Tempo", "Threshold", "Long Run"):
                _rest(w, lang)  # strength and cross-training wait until after the race
                continue
            _easy(w, cap, "Zone 2", lang, "Easy Run (mini-taper)", "Chạy nhẹ (mini-taper)")
            if d == last and "strides" not in (w.get("description") or ""):
                w["description"] = (w.get("description") or "").rstrip() + _STRIDES

    for race, rdate, _taper, rec in shaped:
        window = {rdate + timedelta(days=d) for d in range(1, rec + 1)}
        for w in out:
            if _row_date(plan_monday, w) not in window or not editable(w):
                continue
            if w.get("type") in _EASY_TYPES:
                _easy(w, _RECOVERY_CAP_MIN, "Zone 1", lang, "Easy Recovery Run", "Chạy hồi phục nhẹ")
            elif w.get("type") in ("Interval", "Tempo", "Threshold", "Long Run"):
                _easy(w, _RECOVERY_CONVERTED_MIN, "Zone 1", lang, "Easy Recovery Run", "Chạy hồi phục nhẹ")
                w["duration_minutes"] = float(_RECOVERY_CONVERTED_MIN)
            else:
                _rest(w, lang)
    return out


def _by_day(workouts: list[dict[str, Any]]) -> dict[tuple[int, str], list[dict[str, Any]]]:
    out: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for w in workouts:
        out.setdefault((int(w.get("week_number") or 0), w.get("day_of_week") or ""), []).append(w)
    return out


def _peak_minutes(workouts: list[dict[str, Any]]) -> float | None:
    weeks: dict[int, float] = {}
    for w in workouts:
        if w.get("phase") == "Peak":
            weeks[int(w["week_number"])] = weeks.get(int(w["week_number"]), 0) + float(w.get("duration_minutes") or 0)
    return max(weeks.values()) if weeks else None


def cost(race: dict[str, Any], workouts: list[dict[str, Any]], plan_monday: date) -> dict[str, Any]:
    """What adding `race` would change, from a dry run of the guard on a copy of the plan."""
    import copy

    after = enforce(copy.deepcopy(workouts), [race], plan_monday)
    before_days, after_days = _by_day(workouts), _by_day(after)
    changed = []
    for key in sorted(
        set(before_days) | set(after_days), key=lambda k: (k[0], DAYS.index(k[1]) if k[1] in DAYS else 7)
    ):
        b, a = before_days.get(key, []), after_days.get(key, [])
        tb = " + ".join(w.get("title") or w.get("type") or "" for w in b if w.get("type") != "Rest") or "Rest"
        ta = " + ".join(w.get("title") or w.get("type") or "" for w in a if w.get("type") != "Rest") or "Rest"
        mb = sum(float(w.get("duration_minutes") or 0) for w in b)
        ma = sum(float(w.get("duration_minutes") or 0) for w in a)
        if (tb, mb) != (ta, ma):
            changed.append(
                {
                    "week": key[0],
                    "day": key[1],
                    "title_before": tb,
                    "title_after": ta,
                    "minutes_before": mb,
                    "minutes_after": ma,
                }  # fmt: skip
            )
    pb, pa = _peak_minutes(workouts), _peak_minutes(after)
    return {"changed": changed, "peak_week_minutes": {"before": pb, "after": pa} if pb is not None else None}


def prompt_block(races: list[dict[str, Any]], plan_monday: date) -> str:
    """The rule block the plan prompt carries: the B-races and the days around them are fixed."""
    if not races:
        return ""
    lines = ["B-RACES (fixed by the coach; the app pins these days, do not move them):"]
    for race in races:
        rdate = _date(race["race_date"])
        week, day = week_and_day(plan_monday, rdate)
        taper, rec = _race_shape(race)
        effort = "training effort, not all-out" if (race.get("effort") or "race") == "training" else "race effort"
        parts = [f"- Week {week} {day}: {race['race_name']} ({race['distance_km']:g} km), {effort}."]
        if taper:
            start = rdate - timedelta(days=taper)
            parts.append(
                f"Mini-taper {DAYS[start.weekday()][:3]}–{DAYS[(rdate - timedelta(days=1)).weekday()][:3]}: easy and short."
            )
        end = rdate + timedelta(days=rec)
        parts.append(
            f"No hard session or long run until {DAYS[end.weekday()][:3]} (week {week_and_day(plan_monday, end)[0]})."
        )
        lines.append(" ".join(parts))
    return "\n".join(lines) + "\n"


def safe_races_for_plan(plan_id: int | None) -> list[dict[str, Any]]:
    """Planned B-races for the generator; [] on any problem (a plan must always be produced)."""
    import db

    if not plan_id:
        return []
    try:
        return [r for r in db.get_plan_races(plan_id) if r.get("status") == "planned"]
    except Exception:
        logger.warning("b-race load failed", exc_info=True, extra={"fields": {"plan_id": plan_id}})
        return []


def lint_view(races: list[dict[str, Any]], plan_monday: date) -> list[dict[str, Any]]:
    """What plan_lint needs to check B-race weeks, as (week, day) pairs (plan_lint knows no dates)."""
    out = []
    for race in races:
        rdate = _date(race["race_date"])
        taper, rec = _race_shape(race)
        week, day = week_and_day(plan_monday, rdate)
        out.append(
            {
                "week": week,
                "day": day,
                "plan_race_id": race["id"],
                "taper": [week_and_day(plan_monday, rdate - timedelta(days=d)) for d in range(taper, 0, -1)],
                "recovery": [week_and_day(plan_monday, rdate + timedelta(days=d)) for d in range(1, rec + 1)],
            }
        )
    return out


def affected_weeks(race: dict[str, Any], plan_monday: date) -> set[int]:
    """Weeks the race touches: its mini-taper, the race week and the recovery window."""
    rdate = _date(race["race_date"])
    taper, rec = _race_shape(race)
    return {week_and_day(plan_monday, rdate + timedelta(days=d))[0] for d in range(-taper, rec + 1)}


def generated_weeks(workouts: list[dict[str, Any]]) -> set[int]:
    return {int(w["week_number"]) for w in workouts if w.get("week_number")}
