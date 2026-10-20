"""Consistent trail pace, distance and climbing from a flat-ground zone pace."""

from services.plan_generator import PlanGenerator

TRAIL_CLIMB_FACTOR = 0.012


def trail_pace_range(flat_pace: str, climb_rate: float) -> str:
    slower, faster = PlanGenerator.parse_pace_range(flat_pace)
    factor = 1 + TRAIL_CLIMB_FACTOR * climb_rate
    slow = PlanGenerator.decimal_to_pace_str(slower * factor)
    fast = PlanGenerator.decimal_to_pace_str(faster * factor)
    return f"{slow} /km" if slower == faster else f"{slow} - {fast} /km"


def trail_session(flat_pace: str, minutes: float, climb_rate: float) -> tuple[str, float, float]:
    pace = trail_pace_range(flat_pace, climb_rate)
    slower, faster = PlanGenerator.parse_pace_range(pace)
    km = round(minutes / ((slower + faster) / 2), 1)
    return pace, km, round(km * climb_rate)


def trail_minutes(flat_pace: str, distance_km: float, elevation_gain_m: float) -> float:
    slower, faster = PlanGenerator.parse_pace_range(flat_pace)
    return ((slower + faster) / 2) * (distance_km + TRAIL_CLIMB_FACTOR * elevation_gain_m)
