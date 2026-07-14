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
