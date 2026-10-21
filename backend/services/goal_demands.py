"""What a goal physically demands of the athlete, derived from the course and the target time.

Pure: no I/O. Feeds the generation prompt, the specificity lint and the feasibility verdict, so a
plan is built from the race's demands instead of one goal sentence.
"""

from dataclasses import dataclass
from typing import Any

from services.athlete_tier import ELITE_ULTRA_KM, ELITE_ULTRA_SESSION_MIN, MAX_SESSION_MIN, taper_shift
from services.pacing_calculator import PacingCalculator
from services.race_estimator import RaceEstimator
from services.race_readiness import race_class

MIN_ULTRA_KM = 48.0  # the book benchmarks start at the 50K; shorter races get no demand block
CUTOFF_SAFE_SHARE = 0.85  # a finish goal targets 85% of the cutoff (same rule as the plan prompt)
LONGEST_SESSION_SHARE = 0.40  # my call: the longest training session reaches ~40% of race time


@dataclass(frozen=True)
class Demands:
    target_time_min: float
    source: str  # target | cutoff_safe
    distance_km: float
    gain_m: float
    required_flat_pace_min_km: float
    climb_rate_m_per_h: float
    steepness_m_per_km: float
    time_on_feet_min: float
    longest_session_min: float
    peak_week_km_lo: float
    peak_week_km_hi: float
    race_class: str
    venue_climb_rate: float | None = None  # m D+/km the athlete's training mountain offers


def compute(
    distance_km: float | None,
    gain_m: float | None,
    target_time_h: float | None,
    cutoff_h: float | None,
    checkpoints: list[dict[str, Any]] | None = None,
    venue_climb_rate: float | None = None,
) -> Demands | None:
    if not distance_km or float(distance_km) < MIN_ULTRA_KM:
        return None
    if target_time_h:
        minutes, source = float(target_time_h) * 60, "target"
    elif cutoff_h:
        minutes, source = float(cutoff_h) * 60 * CUTOFF_SAFE_SHARE, "cutoff_safe"
    else:
        return None
    distance, gain = float(distance_km), float(gain_m or 0)
    course = checkpoints or RaceEstimator.synthesize_course(distance, gain)
    label, _avg, lo, hi = race_class(distance)
    return Demands(
        target_time_min=minutes,
        source=source,
        distance_km=distance,
        gain_m=gain,
        required_flat_pace_min_km=PacingCalculator.solve_base_pace(course, minutes),
        climb_rate_m_per_h=gain / (minutes / 60),
        steepness_m_per_km=gain / distance,
        time_on_feet_min=minutes,
        longest_session_min=min(
            ELITE_ULTRA_SESSION_MIN if distance >= ELITE_ULTRA_KM else MAX_SESSION_MIN, LONGEST_SESSION_SHARE * minutes
        ),
        peak_week_km_lo=lo,
        peak_week_km_hi=hi,
        race_class=label,
        venue_climb_rate=venue_climb_rate,
    )


def _pace(p: float) -> str:
    return f"{int(p)}:{round((p - int(p)) * 60):02d}"


def prompt_block(d: Demands, lang: str) -> str:
    """Short lines for the generator. Technical terms stay in English in Vietnamese."""
    h, m = divmod(round(d.target_time_min), 60)
    longest = round(d.longest_session_min)
    if lang == "vi":
        lines = [
            f"Yêu cầu của mục tiêu ({d.source}: {h}h{m:02d}): giữ khoảng {_pace(d.required_flat_pace_min_km)} min/km quy đổi đường bằng.",
            f"Cung đường leo {round(d.gain_m)} m D+ ({round(d.steepness_m_per_km)} m D+/km), tốc độ leo cần có khoảng {round(d.climb_rate_m_per_h)} m D+/h.",
            f"Peak week mục tiêu {round(d.peak_week_km_lo)}-{round(d.peak_week_km_hi)} km quy đổi; buổi dài nhất cần đạt khoảng {longest} phút.",
        ]
    else:
        lines = [
            f"Goal demands ({d.source}, {h}h{m:02d}): hold about {_pace(d.required_flat_pace_min_km)} min/km flat-equivalent.",
            f"The course climbs {round(d.gain_m)} m D+ ({round(d.steepness_m_per_km)} m D+/km), needing about {round(d.climb_rate_m_per_h)} m D+/h.",
            f"Peak-week target {round(d.peak_week_km_lo)}-{round(d.peak_week_km_hi)} flat-equivalent km; the longest session should reach about {longest} min.",
        ]
    if d.venue_climb_rate:
        lines.append(
            f"Training mountain offers {round(d.venue_climb_rate)} m D+/km on long runs."
            if lang != "vi"
            else f"Núi tập cho {round(d.venue_climb_rate)} m D+/km ở buổi Long Run."
        )
    return "\n".join(lines)


LONG_RUN_WEEKLY_GROWTH = 1.20  # ask for at most +20% on last week's long run (the lint allows 25%)


def long_run_ask(
    workouts: list[dict[str, Any]], week: int, total_weeks: int, demands: Demands, profile_long_cap_min: float
) -> tuple[float, float, int] | None:
    """(ask, recent, last_build): how long this week's long run should be so the longest session reaches the
    goal's time on feet by the last build week instead of staying where it started."""
    last_build = total_weeks - 3 - taper_shift(total_weeks)
    if week > last_build:
        return None
    prior = [
        float(w.get("duration_minutes") or 0)
        for w in workouts
        if (w.get("week_number") or 0) < week and str(w.get("type") or "").lower() == "long run"
    ]
    if not prior:
        return None
    recent = max(prior[-2:])  # a recovery week's short long run is not the base
    target = min(demands.longest_session_min, profile_long_cap_min)
    remaining = max(last_build - week + 1, 1)
    needed = recent * (target / recent) ** (1 / remaining) if target > recent else recent
    return min(max(needed, recent), recent * LONG_RUN_WEEKLY_GROWTH, target), recent, last_build


def long_run_line(
    workouts: list[dict[str, Any]], week: int, total_weeks: int, demands: Demands, profile_long_cap_min: float
) -> str | None:
    """A context line telling the generator how long this week's long run should be."""
    asked = long_run_ask(workouts, week, total_weeks, demands, profile_long_cap_min)
    if asked is None:
        return None
    ask, recent, last_build = asked
    target = min(demands.longest_session_min, profile_long_cap_min)
    return (
        f"LONG RUN TARGET: the goal needs the longest session to reach about {target:.0f} min by week {last_build}; "
        f"this week's Long Run should be at least {ask:.0f} min (last week's was {recent:.0f})."
    )


ULTRA_KM = 80
B2B_WINDOW = (6, 3)  # last four pre-taper weeks
B2B_DAYS = 5


def back_to_back_line(
    workouts: list[dict[str, Any]], week: int, total_weeks: int, demands: Demands, days_per_week: int | None
) -> str | None:
    """Ask for a back-to-back weekend in the first two weeks of the ultra window (total-5 and total-4)."""
    if demands.distance_km < ULTRA_KM or (days_per_week or B2B_DAYS) < B2B_DAYS or not total_weeks:
        return None
    lo, _hi = B2B_WINDOW
    shift = taper_shift(total_weeks)
    if week not in (total_weeks - lo + 1 - shift, total_weeks - lo + 2 - shift, total_weeks - lo + 3 - shift):
        return None
    from services.plan_lint import b2b_targets

    sat, sun = b2b_targets(workouts, week, demands.longest_session_min)
    return (
        f"BACK-TO-BACK WEEKEND (ultra specificity): if this is not a recovery week, make Saturday about {sat} min and "
        f"Sunday's Long Run about {sun} min, both Zone 2 (on trail or with climbing where you can), practising race "
        f"fueling and the race pack; keep Friday easy and shorten the midweek easy runs so the week total stays "
        f"within the weekly cap."
    )


def climb_line(week: int, total_weeks: int, demands: Demands, flat_only: bool) -> str | None:
    """Ask for climbing-specific Muscular Endurance when the course is steep and the athlete has no hills."""
    if not flat_only or demands.steepness_m_per_km < 25 or week < 3 or week > total_weeks - 3:
        return None
    return (
        f"CLIMB SPECIFICITY: the course climbs {demands.gain_m:.0f} m D+ ({demands.steepness_m_per_km:.0f} m D+/km) "
        f"and the athlete has no hills: make this week's Muscular Endurance session the outdoor weighted carries, "
        f"stair or incline-treadmill format (climbing laps of 5+ min with a 5-15% bodyweight pack), not gym straight "
        f"sets, and finish with eccentric step-downs."
    )
