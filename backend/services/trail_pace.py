"""Consistent trail pace, distance and climbing from a flat-ground zone pace."""

import re

from services.plan_generator import PlanGenerator

TRAIL_CLIMB_FACTOR = 0.012


_PACE_TOKEN = re.compile(r"(?<![\d:])(\d{1,2}):([0-5]\d)(?![\d:])")


def scale_step_paces(text: str, band: tuple[float, float], climb_rate: float) -> str:
    """The step text of a trail session quotes paces too. Any pace inside the athlete's flat easy-to-tempo band
    (`band` = fastest, slowest in min/km) is scaled by the same climb factor as the header pace, so the steps
    never ask for road pace on a climb. Sprint-speed paces fall outside the band and stay."""
    factor = 1 + TRAIL_CLIMB_FACTOR * climb_rate
    fast, slow = band

    def _scale(m: re.Match[str]) -> str:
        value = int(m.group(1)) + int(m.group(2)) / 60
        if not fast <= value <= slow:
            return m.group(0)
        return PlanGenerator.decimal_to_pace_str(value * factor)

    return _PACE_TOKEN.sub(_scale, text)


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
