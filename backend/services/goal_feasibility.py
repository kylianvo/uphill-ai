"""Can this athlete's week hold what the goal demands? A verdict before they start training.

Pure. Capacity comes from the tier's own caps (weekday run maximum, long-run share of the week, the
300-minute session limit) and the number of training days, so it is the ceiling a doctrine-following
plan can reach, not a guess about the athlete.
"""

from dataclasses import dataclass

from services import ultra_rules
from services.athlete_tier import (
    DEFAULT_TRAINING_DAYS,
    TierProfile,
    for_race,
    get_profile,
    session_cap_minutes,
    tier_for_weekly_km,
    week_capacity_parts,
)
from services.goal_demands import Demands
from services.race_readiness import TAPER_WEEKS, max_reachable

STRETCH_MARGIN = 0.20  # my call: double sessions can add about this much, so up to 20% over is a stretch
FINISH_PEAK_SHARE = 0.80  # my call: a finish goal needs 80% of the book's peak-week benchmark
VENUE_SHARE = 0.60  # a training mountain below 60% of the course steepness cannot rehearse it
FLAT_COURSE_M_PER_KM = 25.0  # below this a course needs no mountain access
MAX_WEEKS_SEARCHED = 104


@dataclass(frozen=True)
class Feasibility:
    verdict: str  # supported | stretch | unsupported
    capacity_h: float
    needed_h: float
    weeks_needed: int | None
    levers: tuple[str, ...]
    confidence: str  # measured | estimated


def week_capacity_minutes(
    profile: TierProfile, days_per_week: int | None, race_km: float | None = None, mountain_day: bool = False
) -> float:
    ultra = mountain_day and ultra_rules.band_for(race_km) is not None
    cap = session_cap_minutes(profile, race_km, mountain_day)
    return sum(week_capacity_parts(profile, days_per_week, cap, strength_day=not ultra))


def _weeks_needed(current_km: float, peak_km: float, max_prog: float) -> int | None:
    for n in range(MAX_WEEKS_SEARCHED + 1):
        if max_reachable(max(current_km, 1.0), n, 0, max_prog) >= peak_km:
            return n
    return None


def assess(
    demands: Demands | None,
    profile: TierProfile,
    days_per_week: int | None,
    flat_pace_min_km: float,
    current_weekly_km: float,
    weeks_to_race: float | None,
    pace_is_estimated: bool,
    mountain_min_minutes: int | None = None,
    flat_only: bool = False,
    mountain_day: bool = False,
) -> Feasibility | None:
    if demands is None:
        return None
    profile = for_race(profile, demands.distance_km, mountain_day)
    peak_km = demands.peak_week_km_lo * (FINISH_PEAK_SHARE if demands.source == "cutoff_safe" else 1.0)
    # An athlete who builds toward the peak graduates to the caps of the tier that volume belongs to.
    peak_profile = get_profile(tier_for_weekly_km(peak_km))
    capacity_min = max(
        week_capacity_minutes(profile, days_per_week, demands.distance_km, mountain_day),
        week_capacity_minutes(
            for_race(peak_profile, demands.distance_km, mountain_day), days_per_week, demands.distance_km, mountain_day
        ),
    )
    needed_h = peak_km * flat_pace_min_km / 60
    capacity_h = capacity_min / 60
    weeks_needed = _weeks_needed(current_weekly_km, peak_km, profile.max_weekly_progression)
    runway = None if weeks_to_race is None else weeks_to_race - TAPER_WEEKS
    short_runway = runway is not None and (weeks_needed is None or weeks_needed > runway)
    over_capacity = needed_h > capacity_h
    levers: list[str] = []
    if over_capacity and (days_per_week or DEFAULT_TRAINING_DAYS) < 6:
        levers.append("more_days")
    if over_capacity:
        levers.append("double_sessions")
    if short_runway:
        levers.append("more_weeks")
    if over_capacity or short_runway:
        levers.append("shorter_race")
        if demands.source == "target":
            levers.append("finish_only")
    soft = False
    # The mountain Long Run minimum applies from week one: it has to fit the share of the week the athlete trains
    # now (with one week's growth), not only the week they will reach later.
    start_min = current_weekly_km * flat_pace_min_km * (1 + profile.max_weekly_progression)
    if mountain_min_minutes and mountain_min_minutes / profile.long_run_share_cap > min(
        week_capacity_minutes(profile, days_per_week), max(start_min, 1.0)
    ):
        levers.append("fewer_mountain_minimum")
        soft = True
    if demands.venue_climb_rate and demands.venue_climb_rate < VENUE_SHARE * demands.steepness_m_per_km:
        levers.append("steeper_venue")
        soft = True
    if flat_only and demands.steepness_m_per_km > FLAT_COURSE_M_PER_KM:
        levers.append("mountain_access")
        soft = True
    if needed_h > capacity_h * (1 + STRETCH_MARGIN) or short_runway:
        verdict = "unsupported"
    elif over_capacity or soft:
        verdict = "stretch"
    else:
        verdict = "supported"
    return Feasibility(
        verdict=verdict,
        capacity_h=capacity_h,
        needed_h=needed_h,
        weeks_needed=weeks_needed,
        levers=tuple(levers),
        confidence="estimated" if pace_is_estimated else "measured",
    )


_LEVER_WORDS = {
    "more_days": "more training days",
    "double_sessions": "double sessions",
    "more_weeks": "more weeks before the race",
    "shorter_race": "a shorter race",
    "finish_only": "a finish-only goal",
    "fewer_mountain_minimum": "a shorter minimum mountain day",
    "steeper_venue": "a steeper training mountain",
    "mountain_access": "access to hills or a mountain",
}


def brief_line(feasibility: dict | None) -> str | None:
    """A fact for the week brief when the goal is a stretch or unsupported (goal_service.feasibility_for), so the
    athlete hears it in the plan as well as on the Goal screen. None when supported."""
    if not feasibility or feasibility.get("verdict") not in ("stretch", "unsupported"):
        return None
    levers = [_LEVER_WORDS[k] for k in feasibility.get("levers") or [] if k in _LEVER_WORDS]
    line = (
        f"Goal check: {feasibility['verdict']}. The goal needs about {feasibility['needed_h']} h of running in the "
        f"peak week; this athlete's week holds about {feasibility['capacity_h']} h."
    )
    if feasibility.get("weeks_needed"):
        line += f" Building there takes about {feasibility['weeks_needed']} weeks."
    return line + (f" What would help: {', '.join(levers[:3])}." if levers else "")
