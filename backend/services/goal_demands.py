"""What a goal physically demands of the athlete, derived from the course and the target time.

Pure: no I/O. Feeds the generation prompt, the specificity lint and the feasibility verdict, so a
plan is built from the race's demands instead of one goal sentence.
"""

from dataclasses import dataclass
from typing import Any

from services.athlete_tier import MAX_SESSION_MIN
from services.pacing_calculator import PacingCalculator
from services.race_estimator import RaceEstimator
from services.race_readiness import race_class

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
    if not distance_km or float(distance_km) <= 0:
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
        longest_session_min=min(MAX_SESSION_MIN, LONGEST_SESSION_SHARE * minutes),
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
