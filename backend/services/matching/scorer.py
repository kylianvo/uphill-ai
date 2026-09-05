"""Scores how well a session bundle satisfies a planned workout.

Only the dimensions the plan actually specifies are scored, and the total is
normalised by the weight of those present. A workout that omits distance and
pace must not be systematically out-scored by one that specifies them --
otherwise time-based sessions would never win their own match.

Every component returns 1.0 for an exact match and decays toward 0.0 with
relative error, so the total reads as "how much of what was prescribed did this
session deliver".
"""

import re
from dataclasses import dataclass, field

from services.matching.bundler import SessionBundle

# Relative weights. Duration and distance dominate because they are the most
# reliably recorded; elevation matters for a mountain-running plan; heart rate
# is the execution signal rather than the identity signal. These sum to
# exactly 1.0 already, but score_bundle renormalises by whichever subset is
# actually present on a given workout, so the sum is not load-bearing.
WEIGHTS = {"duration": 0.35, "distance": 0.30, "elevation": 0.10, "hr": 0.15, "pace": 0.10}

# Elevation carries only 0.10 weight, so rolling terrain on a nominally flat
# prescription should cost the match a little, not tank it, while 300m of
# unplanned climbing against a flat prescription is definitively not the
# session that was prescribed. Used only when the target is 0 -- see
# _elevation_score, since a target of 0 can't drive _ratio_score's
# relative-error formula (it divides by target).
FLAT_ELEVATION_SCALE_M = 300.0


@dataclass
class MatchScore:
    total: float
    components: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def _component(self, name: str) -> float | None:
        return self.components.get(name)


def parse_hr_range(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    found = re.findall(r"\d+", str(value))
    if len(found) < 2:
        return None
    low, high = int(found[0]), int(found[1])
    return (low, high) if low <= high else (high, low)


def parse_pace_to_seconds(value: str | None) -> float | None:
    """'5:30' -> 330.0; '5:30-6:30' -> 360.0 (midpoint)."""
    if not value:
        return None
    paces = re.findall(r"(\d+):(\d{2})", str(value))
    if not paces:
        return None
    seconds = [int(m) * 60 + int(s) for m, s in paces]
    return sum(seconds) / len(seconds)


def _ratio_score(actual: float, target: float) -> float:
    """1.0 at exact match, decaying linearly to 0.0 at 100% relative error."""
    if target <= 0:
        return 0.0
    return max(0.0, 1.0 - abs(actual - target) / target)


def _elevation_score(actual_elevation_m: float, target: float) -> float:
    """A target of 0 (a flat prescription) can't go through _ratio_score,
    which would divide by zero's neighbourhood and always return 0.0 --
    wrongly punishing a session that matched its flat prescription exactly.
    Score that case on absolute deviation instead: 0m -> 1.0, 100m -> 0.667,
    300m+ -> 0.0. Non-zero targets keep the normal relative-error scoring."""
    if target <= 0:
        return max(0.0, 1.0 - actual_elevation_m / FLAT_ELEVATION_SCALE_M)
    return _ratio_score(actual_elevation_m, target)


def _hr_score(avg_hr: int, target: tuple[int, int]) -> float:
    low, high = target
    if low <= avg_hr <= high:
        return 1.0
    distance = low - avg_hr if avg_hr < low else avg_hr - high
    span = max(high - low, 1)
    return max(0.0, 1.0 - distance / span)


def score_bundle(bundle: SessionBundle, workout: dict) -> MatchScore:
    components: dict[str, float] = {}
    reasons: list[str] = []

    # duration_minutes is NOT NULL with no legitimate zero, so the falsy
    # check alone already excludes "unspecified" correctly; a negative value
    # can only be corrupt data, and must not silently score as a hard 0.0.
    planned_duration = workout.get("duration_minutes")
    if planned_duration and planned_duration > 0:
        actual_minutes = bundle.duration_seconds / 60.0
        components["duration"] = _ratio_score(actual_minutes, float(planned_duration))
        reasons.append(f"duration {actual_minutes:.0f} min vs {float(planned_duration):.0f} planned")

    # distance_km is nullable with no default, so a real 0 km never occurs;
    # the falsy check is correct as-is. Guard against a corrupt negative the
    # same way as duration.
    planned_distance = workout.get("distance_km")
    if planned_distance and planned_distance > 0:
        components["distance"] = _ratio_score(bundle.distance_km, float(planned_distance))
        reasons.append(f"distance {bundle.distance_km:.2f} km vs {float(planned_distance):.2f} planned")

    # elevation_gain_m is REAL DEFAULT 0.0 (never NULL), so 0.0 is a common,
    # legitimate "flat prescription" -- not "unspecified". Presence must be
    # tested with `is None` (not falsy) so a genuine 0.0 target is always
    # scored via _elevation_score, while an absent/None key (or a corrupt
    # negative) is excluded and renormalised like every other component.
    planned_elevation = workout.get("elevation_gain_m")
    if planned_elevation is not None and planned_elevation >= 0:
        components["elevation"] = _elevation_score(bundle.elevation_gain_m, float(planned_elevation))

    hr_range = parse_hr_range(workout.get("target_hr_range"))
    if hr_range and bundle.avg_hr:
        components["hr"] = _hr_score(bundle.avg_hr, hr_range)
        reasons.append(f"avg HR {bundle.avg_hr} vs target {hr_range[0]}-{hr_range[1]}")

    planned_pace = parse_pace_to_seconds(workout.get("target_pace"))
    if planned_pace and bundle.distance_km:
        actual_pace = bundle.duration_seconds / bundle.distance_km
        components["pace"] = _ratio_score(actual_pace, planned_pace)

    available = sum(WEIGHTS[name] for name in components)
    if available <= 0:
        return MatchScore(total=0.0, components={}, reasons=["workout specifies nothing scorable"])

    total = sum(components[name] * WEIGHTS[name] for name in components) / available
    return MatchScore(total=round(total, 4), components=components, reasons=reasons)
