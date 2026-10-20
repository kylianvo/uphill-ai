"""Is the plan's training load on a path that can reach the book's race benchmark?

Source: the scheduler KB chunk "Training Volume, Terrain Specificity, and Session Structure"
(Uphill Athlete): a 50K averages 50 km/week with a peak week of 80-88 km, a 100K 75 km with a
peak of 120-130 km, a 100-mile 100 km with a peak of 145-160 km. Weekly increases are capped
at 7-10% (the tier profile's max_weekly_progression), with a recovery week after three build
weeks, and the plan tapers for about two weeks before the race.

This cannot promise a finish time. It checks the one thing arithmetic can: whether, from where
the plan is now, the load can still reach the benchmark peak by the taper without breaking the
progression and recovery rules, and what this week must total to stay on that path.
"""

from dataclasses import dataclass
from typing import Any

from services.coros_workouts import NON_RUN_TYPES
from services.plan_lint import Issue, _by_week, _is_down

TAPER_WEEKS = 2
RECOVERY_FACTOR = 0.85  # a recovery week is about 70-85% of the base; use the generous end
BUILDS_BEFORE_RECOVERY = 3
PATH_TOLERANCE = 0.97  # km are estimates; do not nag over a few percent

# (largest race distance in km for the class, label, average km/week, peak-week low, peak-week high)
RACE_CLASSES = (
    (75.0, "50K", 50.0, 80.0, 88.0),
    (135.0, "100K", 75.0, 120.0, 130.0),
    (float("inf"), "100 miles", 100.0, 145.0, 160.0),
)


@dataclass(frozen=True)
class Readiness:
    status: str  # on_track | behind | at_risk
    race_class: str
    peak_lo: float
    peak_hi: float
    base_km: float
    floor_km: float  # what this week must total to stay on the path (0 when already on track)
    cap_km: float  # the most this week may total under the progression cap
    reachable_km: float  # best peak reachable at the cap
    peak_week: int
    message: str


def race_class(distance_km: float) -> tuple[str, float, float, float]:
    for limit, label, avg, lo, hi in RACE_CLASSES:
        if distance_km <= limit:
            return label, avg, lo, hi
    raise ValueError("unreachable")


def weekly_km(ws: list[dict[str, Any]], flat_pace_min_km: float | None = None) -> float:
    """Weekly running volume in km. With the athlete's flat Zone 2 pace it is flat-equivalent km
    (run minutes / pace), so a slow mountain pace does not make a hard plan read as light against
    the book's km benchmarks; without it, the plan's own distance_km."""
    if not flat_pace_min_km:
        return sum(float(w.get("distance_km") or 0) for w in ws if w.get("type") != "Rest")
    run_minutes = sum(
        float(w.get("duration_minutes") or 0)
        for w in ws
        if w.get("type") != "Rest" and (w.get("type") or "").strip().lower() not in NON_RUN_TYPES
    )
    return run_minutes / flat_pace_min_km


def max_reachable(v: float, steps: int, builds_so_far: int, max_prog: float) -> float:
    """Highest weekly km reachable `steps` weeks after a week of `v` km (which is build week
    `builds_so_far` of the current run), growing at the cap with a recovery week after 3 builds."""
    peak = base = v
    c = builds_so_far
    for _ in range(max(steps, 0)):
        if c >= BUILDS_BEFORE_RECOVERY:
            c = 0  # recovery week: volume dips, the base is unchanged
            continue
        base *= 1 + max_prog
        c += 1
        peak = max(peak, base)
    return peak


def _builds_through(weeks: dict[int, list[dict[str, Any]]], week: int) -> int:
    n, wk = 1, week - 1
    while wk >= 1 and weeks.get(wk) and not _is_down(weeks, wk):
        n += 1
        wk -= 1
    return n


def assess_week(
    workouts: list[dict[str, Any]],
    week: int,
    *,
    total_weeks: int,
    distance_km: float | None,
    max_prog: float,
    flat_pace_min_km: float | None = None,
) -> Readiness | None:
    """Readiness for generating `week`, from the weeks before it. None when there is nothing
    to judge (no race distance, no earlier week, or the week is already in the taper)."""
    if not distance_km or total_weeks < 4:
        return None
    weeks = _by_week(workouts)
    prior = [wk for wk in sorted(weeks) if wk < week and weekly_km(weeks[wk], flat_pace_min_km) > 0]
    peak_week = total_weeks - TAPER_WEEKS
    if not prior or week >= peak_week:
        return None
    base_wk = next((wk for wk in reversed(prior) if not _is_down(weeks, wk)), prior[-1])
    base = weekly_km(weeks[base_wk], flat_pace_min_km)
    label, _avg, lo, hi = race_class(distance_km)
    cap = base * (1 + max_prog)
    steps = peak_week - week
    builds = _builds_through(weeks, week)
    if builds > BUILDS_BEFORE_RECOVERY:
        # This week is the recovery week (3 builds : 1 recovery): no floor, or the two rules would fight.
        # An unreachable timeline is still reported: a recovery week does not make the peak reachable.
        reach = max_reachable(cap, steps, 0, max_prog)
        if reach < lo:
            msg = (
                f"The timeline cannot reach the {label} benchmark peak week ({lo:.0f}-{hi:.0f} km) within the "
                f"{max_prog * 100:.0f}% weekly cap: the best reachable peak is about {reach:.0f} km by week "
                f"{peak_week}. Build as fast as the cap allows."
            )
            return Readiness("at_risk", label, lo, hi, base, 0.0, cap, reach, peak_week, msg)
        return Readiness("on_track", label, lo, hi, base, 0.0, cap, reach, peak_week, "")
    reach_at_cap = max_reachable(cap, steps, builds, max_prog)
    if max_reachable(base, steps, builds, max_prog) >= lo:
        return Readiness("on_track", label, lo, hi, base, 0.0, cap, reach_at_cap, peak_week, "")
    if reach_at_cap < lo:
        msg = (
            f"The timeline cannot reach the {label} benchmark peak week ({lo:.0f}-{hi:.0f} km) within the "
            f"{max_prog * 100:.0f}% weekly cap: the best reachable peak is about {reach_at_cap:.0f} km by week "
            f"{peak_week}. Build as fast as the cap allows."
        )
        return Readiness("at_risk", label, lo, hi, base, cap, cap, reach_at_cap, peak_week, msg)
    low, high = base, cap  # minimal week-`week` volume that can still reach the benchmark
    for _ in range(40):
        mid = (low + high) / 2
        low, high = (mid, high) if max_reachable(mid, steps, builds, max_prog) < lo else (low, mid)
    msg = (
        f"To reach the {label} benchmark peak week ({lo:.0f}-{hi:.0f} km) by week {peak_week} within the "
        f"{max_prog * 100:.0f}% weekly cap, this week should total at least {high:.0f} km "
        f"(at most {cap:.0f} km)."
    )
    return Readiness("behind", label, lo, hi, base, high, cap, reach_at_cap, peak_week, msg)


def readiness_issue(
    r: Readiness | None,
    week: int,
    week_km: float,
    capacity_km: float | None = None,
    push_at_risk: bool = True,
) -> Issue | None:
    """A lint issue when a generated week sits under the floor. On a reachable path the floor is what keeps the
    benchmark reachable; when the benchmark is out of reach it is the cap itself (best feasible build), so a
    flat plan is still pushed upward (`push_at_risk`). `capacity_km` is what the athlete's days can hold: never
    ask for more."""
    if r and (r.status == "behind" or (push_at_risk and r.status == "at_risk")) and r.floor_km:
        floor = min(r.floor_km, capacity_km) if capacity_km else r.floor_km
        if week_km >= floor * PATH_TOLERANCE:
            return None
        return Issue(
            "READINESS_BEHIND",
            week,
            f"Week {week}: planned distance {week_km:.0f} km is below the path to the {r.race_class} peak-week "
            f"benchmark. {r.message}",
        )
    return None


def target_vs_cutoff_issue(target_h: float | None, cutoff_h: float | None, week: int) -> Issue | None:
    if target_h and cutoff_h and target_h > cutoff_h:
        return Issue(
            "TARGET_PAST_CUTOFF",
            week,
            f"The target time ({target_h:.1f} h) is past the race cutoff ({cutoff_h:.1f} h): the goal itself "
            f"would not be a finish. Re-run the Goal Determiner.",
        )
    return None


_QUALITY = {"tempo", "interval", "threshold", "race"}


def suggest_minutes(
    ws: list[dict[str, Any]], target_run_minutes: float, weekday_max: float, long_share_cap: float
) -> str:
    """Concrete durations that bring a week's running up to `target_run_minutes`: easy and long runs are scaled
    up in proportion, each inside the tier's weekday maximum and the long run inside its share of the week.
    Quality sessions, strength and Muscular Endurance are left as drafted. "" when nothing can be scaled."""
    runs = [
        w
        for w in ws
        if w.get("type") != "Rest" and (w.get("type") or "").strip().lower() not in NON_RUN_TYPES | _QUALITY
    ]
    if not runs:
        return ""
    current = sum(
        float(w.get("duration_minutes") or 0)
        for w in ws
        if (w.get("type") or "").strip().lower() not in NON_RUN_TYPES and w.get("type") != "Rest"
    )
    minutes = {id(w): float(w.get("duration_minutes") or 0) for w in runs}
    is_long = lambda w: (w.get("type") or "").strip().lower() == "long run"  # noqa: E731
    cap = lambda w: min(300.0, long_share_cap * target_run_minutes) if is_long(w) else weekday_max  # noqa: E731
    need = target_run_minutes - current
    for _ in range(4):  # redistribute what the caps refuse
        room = [w for w in runs if minutes[id(w)] < cap(w)]
        base = sum(minutes[id(w)] for w in room)
        if need <= 0.5 or not room or not base:
            break
        for w in room:
            add = need * minutes[id(w)] / base
            minutes[id(w)] = min(cap(w), minutes[id(w)] + add)
        need = target_run_minutes - (
            current + sum(minutes[id(w)] - float(w.get("duration_minutes") or 0) for w in runs)
        )
    parts = [
        f"{w.get('day_of_week')} {w.get('type')} {int(round(minutes[id(w)] / 5) * 5)} min"
        for w in runs
        if abs(minutes[id(w)] - float(w.get("duration_minutes") or 0)) >= 2.5
    ]
    return ("Set these sessions to " + ", ".join(parts) + ".") if parts else ""


def completed_weekly_km(
    ws: list[dict[str, Any]], before_week: int, flat_pace_min_km: float | None, weeks: int = 2
) -> float | None:
    """Flat-equivalent km per week over the last `weeks` weeks before `before_week`, counting only sessions the
    athlete ticked complete: what they really trained, which is what their level should follow."""
    if not flat_pace_min_km:
        return None
    by_week = _by_week([w for w in ws if w.get("is_completed") == 1 and (w.get("week_number") or 0) < before_week])
    recent = sorted(by_week)[-weeks:]
    if not recent:
        return None
    return sum(weekly_km(by_week[wk], flat_pace_min_km) for wk in recent) / len(recent)
