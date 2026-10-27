"""'For your race': one line per session comparing it with what the plan's race asks, from numbers only.

Computed when a plan is read (never stored), so it follows edits to the race or the session. The app shows it
under "About this session". A session it has nothing true to say about gets no line.
"""

from typing import Any

from services import goal_demands
from services.plan_generator import hm

_STEEP_RACE_M_PER_KM = 15  # flatter races: today's climbing is not the point
_RACE_STEEP_SHARE = 0.8  # a session at 80%+ of the race's climb rate is as steep as the race


def line(plan: dict[str, Any], workout: dict[str, Any], vi: bool = False) -> str | None:
    km, gain = float(plan.get("course_distance_km") or 0), float(plan.get("course_elevation_gain_m") or 0)
    if km <= 0 or workout.get("type") in (None, "Rest", "Race"):
        return None
    race = str(plan.get("race_name") or "").strip() or ("race của bạn" if vi else "your race")
    minutes = float(workout.get("duration_minutes") or 0)
    if workout.get("type") == "Long Run" and minutes >= 90:
        demands = goal_demands.compute(km, gain, plan.get("target_time_hours"), plan.get("cutoff_time_hours"))
        if demands:
            if demands.source == "target":
                return (
                    f"{hm(minutes, True)} trên chân, so với khoảng {hm(demands.time_on_feet_min, True)} bạn nhắm ở {race}."
                    if vi
                    else f"{hm(minutes)} on your feet, of the {hm(demands.time_on_feet_min)} you're aiming for at {race}."
                )
            cutoff = float(plan.get("cutoff_time_hours") or 0) * 60
            return (
                f"{hm(minutes, True)} trên chân, so với cutoff {hm(cutoff, True)} của {race}."
                if vi
                else f"{hm(minutes)} on your feet, of the {hm(cutoff)} cutoff at {race}."
            )
    steepness = gain / km
    s_gain, s_km = float(workout.get("elevation_gain_m") or 0), float(workout.get("distance_km") or 0)
    if steepness >= _STEEP_RACE_M_PER_KM and s_gain >= 100 and s_km > 0:
        rate = s_gain / s_km
        steep = rate >= _RACE_STEEP_SHARE * steepness
        if vi:
            return (
                f"{race} leo khoảng {steepness:.0f} m mỗi km. Hôm nay: {s_gain:.0f} m trên {s_km:g} km "
                f"({rate:.0f} m/km){', dốc như race' if steep else ''}."
            )
        return (
            f"{race} climbs about {steepness:.0f} m per km. Today: {s_gain:.0f} m over {s_km:g} km "
            f"({rate:.0f} m/km){', as steep as the race' if steep else ''}."
        )
    return None


def annotate(plan: dict[str, Any], workouts: list[dict[str, Any]], lang: str | None) -> list[dict[str, Any]]:
    """Adds `race_fit` (a string or None) to each workout of a plan payload."""
    vi = lang == "vi"
    for w in workouts:
        try:
            w["race_fit"] = line(plan, w, vi)
        except (TypeError, ValueError):  # a malformed row loses its line, never the plan
            w["race_fit"] = None
    return workouts
