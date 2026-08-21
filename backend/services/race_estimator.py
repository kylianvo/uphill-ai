"""Shared goal/feasibility engine (docs/pace-strategy-v2-plan.md §9).

One stateless estimator behind the Goal Determiner tool (and, later, the
plan-generation wizard): fitness in — either a flat base pace or a past race
result inverted through the same PacingCalculator physics — predicted finish
time and A/B/C goals out. Keeping all consumers on this single engine is what
stops Goal Determiner and Pace Strategy from disagreeing about the same
runner on the same course.
"""

from typing import Any

from services.pacing_calculator import PacingCalculator

# A structured training block plausibly yields ~0.25%/week improvement for
# trained runners, capped at ~5% (plan §9 "time-to-race adjustment").
IMPROVEMENT_PER_WEEK = 0.0025
IMPROVEMENT_CAP = 0.05

# A/B/C goal spread around the (adjusted) prediction: ambitious assumes a
# great day, safe banks margin for problems. Asymmetric on purpose — things
# go wrong more often than they go right in the mountains.
AMBITIOUS_FACTOR = 0.95
SAFE_FACTOR = 1.08

_PERCENTILE_KEYS = ("p5", "p10", "p25", "p50", "p75", "p90")
_PERCENTILE_VALUES = (5.0, 10.0, 25.0, 50.0, 75.0, 90.0)


def _parse_hms_to_mins(time_str: str | None) -> float | None:
    """Parses 'h:mm:ss' or 'h:mm' into minutes. Mirrors main.py's request-time
    parser; kept local so services/ doesn't import from main.py."""
    if not time_str:
        return None
    parts = time_str.strip().split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        return None
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    return h * 60 + m + s / 60


class RaceEstimator:
    @staticmethod
    def synthesize_course(distance_km: float, elevation_gain_m: float) -> list[dict[str, Any]]:
        """Per-km checkpoints with gain/loss spread evenly (loss = gain: races
        loop or return to the valley). Mirrors the frontend synthesizeCourse."""
        n = max(1, round(distance_km + 0.4999))  # ceil without math import
        gain_per_km = elevation_gain_m / distance_km if distance_km > 0 else 0.0
        checkpoints: list[dict[str, Any]] = [
            {"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}
        ]
        prev = 0.0
        for i in range(1, n + 1):
            dist_m = min(i * 1000.0, distance_km * 1000.0)
            frac = (dist_m - prev) / 1000.0
            checkpoints.append(
                {
                    "name": f"KM {i}",
                    "distance_meters": dist_m,
                    "segment_gain_meters": gain_per_km * frac,
                    "segment_loss_meters": gain_per_km * frac,
                }
            )
            prev = dist_m
        return checkpoints

    @staticmethod
    def predict_time_mins(checkpoints: list[dict[str, Any]], base_flat_pace_min_km: float) -> float:
        """Forward physics: course time at a given flat base pace. Time is
        linear in pace, so one unit-pace solve is exact."""
        unit_time = PacingCalculator.solve_base_pace(checkpoints, target_time_mins=1.0)
        # solve_base_pace returns pace for a 1-minute finish => unit course
        # time at 1.0 min/km base pace is 1/pace.
        return base_flat_pace_min_km / unit_time

    @classmethod
    def base_pace_from_result(cls, checkpoints: list[dict[str, Any]], finish_time_mins: float) -> float:
        """ITRA-style normalization: the flat base pace that reproduces a past
        result on that course's profile."""
        return PacingCalculator.solve_base_pace(checkpoints, target_time_mins=finish_time_mins)

    @classmethod
    def percentile_curve(cls, results: list[dict[str, Any]]) -> tuple[list[tuple[float, float]], int] | None:
        """Averages each race-year's `percentiles.overall` (p5..p90) into a
        single 6-point (percentile, minutes) curve. Years with missing or
        non-monotonic percentile data are excluded. Returns
        (curve, valid_year_count), or None if no year is usable."""
        buckets: dict[float, list[float]] = {v: [] for v in _PERCENTILE_VALUES}
        valid_years = 0
        for entry in results:
            overall = ((entry.get("percentiles") or {}).get("overall")) or {}
            parsed: list[float] = []
            ok = True
            for key in _PERCENTILE_KEYS:
                mins = _parse_hms_to_mins(overall.get(key))
                if mins is None:
                    ok = False
                    break
                parsed.append(mins)
            if not ok:
                continue
            if any(parsed[i] > parsed[i + 1] for i in range(len(parsed) - 1)):
                continue
            valid_years += 1
            for pct, mins in zip(_PERCENTILE_VALUES, parsed):
                buckets[pct].append(mins)

        if valid_years == 0:
            return None
        curve = [(pct, sum(buckets[pct]) / len(buckets[pct])) for pct in _PERCENTILE_VALUES]
        return curve, valid_years

    @staticmethod
    def interpolate_percentile(
        curve: list[tuple[float, float]],
        *,
        time_mins: float | None = None,
        percentile: float | None = None,
    ) -> float:
        """Bidirectional piecewise-linear lookup on a (percentile, minutes)
        curve. Extrapolates past the ends using the nearest segment's slope
        instead of clamping, so an elite reference time still projects a
        meaningfully fast rank rather than pinning to p5."""
        if (time_mins is None) == (percentile is None):
            raise ValueError("Provide exactly one of time_mins or percentile")

        if time_mins is not None:
            xs = [pt[1] for pt in curve]  # minutes, ascending
            ys = [pt[0] for pt in curve]  # percentile, ascending
            query = time_mins
        else:
            xs = [pt[0] for pt in curve]  # percentile, ascending
            ys = [pt[1] for pt in curve]  # minutes, ascending
            query = percentile

        n = len(xs)
        if query <= xs[0]:
            slope = (ys[1] - ys[0]) / (xs[1] - xs[0])
            return ys[0] + slope * (query - xs[0])
        if query >= xs[-1]:
            slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
            return ys[-1] + slope * (query - xs[-1])
        for i in range(n - 1):
            if xs[i] <= query <= xs[i + 1]:
                frac = (query - xs[i]) / (xs[i + 1] - xs[i])
                return ys[i] + frac * (ys[i + 1] - ys[i])
        raise ValueError("Unreachable: query not bracketed by curve bounds")

    @classmethod
    def percentile_transfer_mins(
        cls,
        reference_curve: list[tuple[float, float]],
        reference_time_mins: float,
        target_curve: list[tuple[float, float]],
    ) -> float:
        """Finds the runner's percentile rank on the reference race's curve,
        then maps that rank onto the target race's curve."""
        rank = cls.interpolate_percentile(reference_curve, time_mins=reference_time_mins)
        return cls.interpolate_percentile(target_curve, percentile=rank)

    @staticmethod
    def rank_transfer_mins(
        reference_winner_mins: float, reference_time_mins: float, target_winner_mins: float
    ) -> float:
        """UltraSignup-style rank transfer: rank = winner/you on the reference
        race; predicted target time = target winner time / rank."""
        rank = reference_winner_mins / reference_time_mins
        return target_winner_mins / rank

    @classmethod
    def estimate(
        cls,
        distance_km: float,
        elevation_gain_m: float,
        base_flat_pace_min_km: float | None = None,
        reference: dict[str, Any] | None = None,
        weeks_to_race: float | None = None,
    ) -> dict[str, Any]:
        """Predicted finish time + A/B/C goals for a target course.

        Fitness comes from ``base_flat_pace_min_km`` or from ``reference``
        ({distance_km, elevation_gain_m, finish_time_mins}) — a past result
        inverted through the same physics. Raises ValueError without either.
        """
        if base_flat_pace_min_km is None:
            if not reference or not reference.get("finish_time_mins"):
                raise ValueError("Provide base_flat_pace_min_km or a reference race result")
            ref_course = cls.synthesize_course(reference["distance_km"], reference.get("elevation_gain_m") or 0.0)
            base_flat_pace_min_km = cls.base_pace_from_result(ref_course, reference["finish_time_mins"])

        course = cls.synthesize_course(distance_km, elevation_gain_m)
        predicted = cls.predict_time_mins(course, base_flat_pace_min_km)

        improvement = 0.0
        if weeks_to_race:
            improvement = min(IMPROVEMENT_CAP, max(0.0, weeks_to_race) * IMPROVEMENT_PER_WEEK)
        adjusted = predicted * (1.0 - improvement)

        return {
            "base_flat_pace_min_km": round(base_flat_pace_min_km, 3),
            "predicted_time_mins": round(predicted, 1),
            "adjusted_time_mins": round(adjusted, 1),
            "improvement_pct": round(improvement * 100, 1),
            "goals": {
                "ambitious": round(adjusted * AMBITIOUS_FACTOR, 1),
                "realistic": round(adjusted, 1),
                "safe": round(adjusted * SAFE_FACTOR, 1),
            },
        }
