"""Day layout for the rule-based fallback schedule.

The fallback template used fixed weekdays (long run Saturday, strength Sunday, a Zone 3/4 session on
Wednesday), ignoring the athlete's training days and long-run day and putting strength 24 h before the
long run. This places the template's sessions on days that honour the athlete's schedule and keep the
doctrine's spacing, by a small exhaustive search (at most 7P6 placements). It drops strength rather than
break a rule (backfilling with an easy run so the athlete still trains the days they asked for), and it
treats Sunday as adjacent to the next Monday, because every week repeats the same layout.
"""

from itertools import permutations
from typing import Any

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# The template's origin day identifies the session's role.
_ROLE_BY_ORIGIN_DAY = {
    "Tuesday": "recovery",
    "Wednesday": "quality",
    "Thursday": "aerobic",
    "Saturday": "long",
    "Sunday": "power",  # strength / ME / hill sprints
}
# Roles in the order they are kept when the athlete trains fewer days than the template has sessions.
_PRIORITY = ("long", "quality", "power", "aerobic", "recovery", "aerobic2")
MIN_GAP_DAYS = 2  # 48 h between strength and the long run / a hard session
_HARD_TYPES = {"Interval", "Tempo", "Threshold"}
_HARD_ZONES = {"Zone 3", "Zone 4", "Zone 5"}


def _gap(a: int, b: int) -> int:
    d = abs(a - b)
    return min(d, 7 - d)  # around the week: Sunday is next to the following Monday


def _is_hard(row: dict[str, Any]) -> bool:
    return row.get("type") in _HARD_TYPES or row.get("target_zone") in _HARD_ZONES


def _rest_row(week: int, phase: str, day: str) -> dict[str, Any]:
    return {
        "week_number": week,
        "day_of_week": day,
        "phase": phase,
        "title": "Rest & Regeneration",
        "type": "Rest",
        "duration_minutes": 0.0,
        "target_zone": "Zone 1",
        "description": "Rest day. Prioritize sleep, light stretching, and muscular recovery.",
        "fueling_tip": "Focus on standard hydration. Balanced baseline meals.",
    }


def _score(
    assignment: dict[str, int], long_day: int | None, origin: dict[str, int], hard_roles: set[str]
) -> float | None:
    """None when a hard rule is broken; otherwise higher is better."""
    long = assignment.get("long")
    if long_day is not None and long != long_day:
        return None
    if "power" in assignment:  # strength keeps 48 h from the long run and from every hard session
        for other in ("long", *hard_roles):
            if other in assignment and other != "power" and _gap(assignment["power"], assignment[other]) < MIN_GAP_DAYS:
                return None
    for hard in hard_roles - {"power"}:  # a hard session keeps off the long run's neighbouring days
        if hard in assignment and long is not None and _gap(assignment[hard], long) < MIN_GAP_DAYS:
            return None
    score = 0.0
    if "recovery" in assignment and long is not None and assignment["recovery"] == (long + 1) % 7:
        score += 2  # a recovery run the day after the long run
    if (
        "recovery" in assignment
        and "quality" in assignment
        and assignment["recovery"] == (assignment["quality"] + 1) % 7
    ):
        score += 1
    # Stay close to the template's days: fewer surprises for the athlete.
    score -= sum(abs(day - origin[role]) for role, day in assignment.items()) * 0.1
    return score


def _drop_orders(keep: list[str], wanted: int, available_roles: list[str]) -> list[list[str]]:
    """The full set first; then with strength dropped and an easy run put back so the athlete still
    trains `wanted` days; then with each further role dropped."""
    orders = [list(keep)]
    dropped: list[str] = []
    for drop in ("power", "recovery", "aerobic2", "aerobic", "quality"):
        if drop not in orders[-1]:
            continue
        dropped.append(drop)
        roles = [r for r in orders[-1] if r != drop]
        for extra in ("aerobic", "aerobic2", "recovery"):  # backfill with easy runs only
            if len(roles) < wanted and extra in available_roles and extra not in roles and extra not in dropped:
                roles.append(extra)
        if roles and roles != orders[-1]:
            orders.append(roles)
    return orders


RECOVERY_FACTOR = 0.8  # a recovery week is 80% of the week before it
ADJACENT_TO_LONG_SHARE = 0.20  # the run next to the long run stays small (no back-to-back long days)
MAX_LONG_RUN_MIN = 300


def _compose(
    placed: dict[str, dict[str, Any]],
    days: dict[str, int],
    total: float,
    share_cap: float,
    weekday_max: float,
    recovery: bool = False,
) -> None:
    """Set the week's durations so they add up to `total`: the long run takes at most `share_cap` of it,
    strength keeps its fixed length, the remaining minutes go to the easy runs (each within the tier's
    weekday maximum), and the run next to the long run stays small. A quality session keeps its
    length because its description spells out the minutes. Mutates the rows."""
    long = placed.get("long")
    # A week cannot hold more than its sessions allow (weekday maximum per run, long run at its share), so
    # a recovery week dips from what the week can actually hold, not from the target it never reached.
    others_max = sum(
        float(r["duration_minutes"])
        if role == "power" or (role == "quality" and r.get("type") != "Aerobic Capacity")
        else weekday_max
        for role, r in placed.items()
        if role != "long"
    )
    capacity = others_max + (min(MAX_LONG_RUN_MIN, share_cap / (1 - share_cap) * others_max) if long else 0.0)
    total = min(total, capacity)
    fixed = [
        r
        for role, r in placed.items()
        if role == "power" or (role == "quality" and r.get("type") != "Aerobic Capacity")
    ]
    scalable = {role: r for role, r in placed.items() if role not in ("long", "power") and r not in fixed}
    fixed_min = sum(float(r["duration_minutes"]) for r in fixed)
    if long:
        long["duration_minutes"] = round(min(float(long["duration_minutes"]), share_cap * total, MAX_LONG_RUN_MIN))
    remaining = total - fixed_min - (float(long["duration_minutes"]) if long else 0.0)
    base = sum(float(r["duration_minutes"]) for r in scalable.values())
    if scalable and base > 0 and remaining > 0:
        scale = remaining / base
        for r in scalable.values():
            r["duration_minutes"] = round(min(float(r["duration_minutes"]) * scale, weekday_max))
    if long and "long" in days:
        near = [r for role, r in scalable.items() if _gap(days[role], days["long"]) == 1]
        far = [r for role, r in scalable.items() if _gap(days[role], days["long"]) != 1]
        excess = 0.0
        for _ in range(3):  # the cap is a share of the week as composed, which the trim itself changes
            actual = sum(float(r["duration_minutes"]) for r in placed.values())
            for r in near:
                cap = ADJACENT_TO_LONG_SHARE * actual
                if float(r["duration_minutes"]) > cap:
                    excess += float(r["duration_minutes"]) - cap
                    r["duration_minutes"] = round(cap)
        for r in far:  # give the trimmed minutes to the runs away from the long run
            room = weekday_max - float(r["duration_minutes"])
            give = min(room, excess / max(1, len(far)))
            r["duration_minutes"] = round(float(r["duration_minutes"]) + give)
        others = sum(float(r["duration_minutes"]) for r in placed.values() if r is not long)
        if others and 0 < share_cap < 1:  # the long run still takes at most its share of what remains
            long["duration_minutes"] = round(min(float(long["duration_minutes"]), share_cap / (1 - share_cap) * others))


def _scale_for_recovery(placed: dict[str, dict[str, Any]]) -> None:
    """A recovery week: the easy runs and long run are 80% of the build week. Strength and a quality
    session keep their length (a quality description spells out its minutes)."""
    for role, r in placed.items():
        if role not in ("power", "quality") or r.get("type") == "Aerobic Capacity":
            r["duration_minutes"] = round(float(r["duration_minutes"]) * RECOVERY_FACTOR)


def layout_week(
    rows: list[dict[str, Any]],
    *,
    week: int,
    phase: str,
    preferred_days: list[str] | None,
    long_run_day: str | None,
    days_per_week: int | None,
    week_minutes: float | None = None,
    long_run_share_cap: float | None = None,
    weekday_max_minutes: float | None = None,
    recovery: bool = False,
) -> list[dict[str, Any]]:
    """The week's 7 rows with sessions moved onto the athlete's days. Rest rows are rebuilt."""
    sessions = {
        _ROLE_BY_ORIGIN_DAY[r["day_of_week"]]: r
        for r in rows
        if r.get("day_of_week") in _ROLE_BY_ORIGIN_DAY and r.get("type") != "Rest"
    }
    if not sessions:
        return rows
    origin = {role: DAYS.index(day) for day, role in _ROLE_BY_ORIGIN_DAY.items()}
    if "aerobic" in sessions:  # a sixth day is an extra easy aerobic run
        sessions["aerobic2"] = {
            **sessions["aerobic"],
            "duration_minutes": round(sessions["aerobic"]["duration_minutes"] * 0.85),
        }
        origin["aerobic2"] = origin["aerobic"]
    available = [DAYS.index(d) for d in (preferred_days or []) if d in DAYS] or list(range(7))
    long_day = DAYS.index(long_run_day) if long_run_day in DAYS else None
    if "long" in sessions and long_day is None:
        long_day = origin["long"] if origin["long"] in available else available[-1]  # the template's Saturday
    if long_day is not None and long_day not in available:
        available = sorted(set(available) | {long_day})  # an explicit long-run day always wins
    wanted = max(2, min(days_per_week or 5, len(sessions), len(available)))
    hard_roles = {role for role, r in sessions.items() if _is_hard(r)}
    keep = [role for role in _PRIORITY if role in sessions][:wanted]

    best: tuple[float, dict[str, int]] | None = None
    for roles in _drop_orders(keep, wanted, list(sessions)):
        for days in permutations(available, len(roles)):
            assignment = dict(zip(roles, days))
            score = _score(assignment, long_day if "long" in assignment else None, origin, hard_roles)
            if score is not None and (best is None or score > best[0]):
                best = (score, assignment)
        if best:
            break
    placed = best[1] if best else {}
    by_role = {role: {**sessions[role], "day_of_week": DAYS[day]} for role, day in placed.items()}
    if week_minutes and long_run_share_cap and weekday_max_minutes:
        _compose(by_role, placed, week_minutes, long_run_share_cap, weekday_max_minutes)
        if recovery:
            _scale_for_recovery(by_role)
    out = list(by_role.values())
    taken = set(placed.values())
    out += [_rest_row(week, phase, DAYS[d]) for d in range(7) if d not in taken]
    return sorted(out, key=lambda r: DAYS.index(r["day_of_week"]))


def fit_race_week(
    rows: list[dict[str, Any]], *, week: int, phase: str, race_weekday: str | None
) -> list[dict[str, Any]]:
    """Race Week: the race on its real weekday (not always Saturday), nothing after it, rest elsewhere."""
    race = next((r for r in rows if r.get("type") == "Race"), None)
    if not race or race_weekday not in DAYS:
        return rows
    race_idx = DAYS.index(race_weekday)
    kept = [r for r in rows if r.get("type") not in ("Race", "Rest") and DAYS.index(r["day_of_week"]) < race_idx]
    out = kept + [{**race, "day_of_week": race_weekday}]
    taken = {r["day_of_week"] for r in out}
    out += [_rest_row(week, phase, d) for d in DAYS if d not in taken]
    return sorted(out, key=lambda r: DAYS.index(r["day_of_week"]))
