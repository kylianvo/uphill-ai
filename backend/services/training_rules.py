from typing import Any

# ─── Zone 2 pace defaults ─────────────────────────────────────────────────────
# The per-tier values live in services/athlete_tier.py's TIER_PROFILES, so the tier
# table is the single place a coach corrects any of this. These wrappers exist because
# the pace defaults are consumed from call sites that know a goal but not a tier.
#
# Before this existed the pair "6:30"/"5:45" was hardcoded at nine call sites, so a
# beginner who lost her stored zones silently read as a trained runner: every derived
# number -- target pace, distance_km, treadmill speed -- inherited the error.
from services.athlete_tier import BEGINNER, DEFAULT_TIER, get_profile

# Goals that imply an athlete who cannot yet sustain continuous running. "return" and
# "recovery" are deliberately absent: a runner coming back from a break or a race is
# detrained, not a beginner, and usually still has usable zones from before.
BEGINNER_GOAL_TYPES = ("start_running",)


def pace_tier_for_goal(goal_type: str | None, athlete_tier: str | None = None) -> str:
    """Which tier's pace defaults apply. An explicit athlete tier wins over the goal,
    since it is derived from more signals."""
    if athlete_tier:
        return athlete_tier.strip().lower()
    return BEGINNER if (goal_type or "").lower() in BEGINNER_GOAL_TYPES else DEFAULT_TIER


def default_zone2_pace(tier: str | None = None) -> tuple[str, str]:
    """(slower, faster) Zone 2 bounds in min/km for a tier. Unknown tiers fall back to
    the default profile rather than raising -- a plan with slightly wrong paces beats no
    plan, and the caller has no better answer to substitute."""
    return get_profile(tier).zone2_pace


def resolve_zone2_pace(
    stored_min: str | None,
    stored_max: str | None,
    goal_type: str | None = None,
    athlete_tier: str | None = None,
) -> tuple[str, str]:
    """The athlete's own zones when they have them, otherwise the tier default.
    Each bound falls back independently, so a half-populated profile doesn't lose the
    bound it does have."""
    tier_min, tier_max = default_zone2_pace(pace_tier_for_goal(goal_type, athlete_tier))
    return (stored_min or tier_min, stored_max or tier_max)


class TrainingRules:
    @staticmethod
    def calculate_heart_rate_zones(
        max_hr: int, resting_hr: int, aet_hr: int | None = None, ant_hr: int | None = None
    ) -> dict[str, dict[str, int]]:
        """
        Calculates five heart rate zones anchored on aerobic (AeT) and anaerobic (AnT)
        threshold heart rates, per the Uphill Athlete training zone calculator
        (https://uphillathlete.com/aerobic-training/uphill-athlete-training-zones-heart-rate-calculator/):
        Zone 1 (Recovery):            AeT - 20% -> AeT - 10%
        Zone 2 (Aerobic):             AeT - 10% -> AeT
        Zone 3 (Tempo):               AeT -> AnT
        Zone 4 (Threshold/Anaerobic): AnT -> midpoint(AnT, max_hr)
        Zone 5 (VO2max):              midpoint(AnT, max_hr) -> max_hr
        The site describes Zone 5 only loosely as "the top portion of Zone 4, near
        max HR" without a fixed formula; the midpoint of AnT and max_hr is used
        here to split Zone 4/Zone 5 into non-overlapping display ranges.

        resting_hr is accepted for API compatibility but not used in this model.

        If aet_hr/ant_hr are not supplied, they are estimated from max_hr using the
        same ratios used elsewhere for auto-derivation (73% / 89% of max_hr).
        """
        if aet_hr is None:
            aet_hr = round(max_hr * 0.73)
        if ant_hr is None:
            ant_hr = round(max_hr * 0.89)

        z1_min = aet_hr * 0.8
        z1_max = aet_hr * 0.9
        z4_z5_split = ant_hr + 0.5 * (max_hr - ant_hr)

        bounds = [
            ("Zone 1", z1_min, z1_max),
            ("Zone 2", z1_max, aet_hr),
            ("Zone 3", aet_hr, ant_hr),
            ("Zone 4", ant_hr, z4_z5_split),
            ("Zone 5", z4_z5_split, max_hr),
        ]

        return {name: {"min": int(low), "max": int(high)} for name, low, high in bounds}

    @staticmethod
    def audit_80_20(weekly_workouts: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Audits a week of workouts to ensure intensity compliance.
        Low Intensity (Zone 1-2) duration should be >= 80% of total training duration.
        High Intensity (Zone 3-5) duration should be <= 20% of total training duration.
        """
        total_duration = 0.0
        low_intensity_duration = 0.0
        high_intensity_duration = 0.0

        for workout in weekly_workouts:
            duration = float(workout.get("duration_minutes", 0.0))
            zone = workout.get("target_zone", "Zone 2")
            total_duration += duration

            # Group into low/high intensity buckets
            if zone in ("Zone 1", "Zone 2"):
                low_intensity_duration += duration
            else:
                high_intensity_duration += duration

        if total_duration == 0.0:
            return {"compliant": True, "low_intensity_pct": 100.0, "high_intensity_pct": 0.0}

        low_pct = (low_intensity_duration / total_duration) * 100
        high_pct = (high_intensity_duration / total_duration) * 100

        # We allow a small tolerance buffer (e.g. 78% / 22% splits)
        compliant = low_pct >= 78.0 and high_pct <= 22.0

        return {
            "compliant": compliant,
            "low_intensity_pct": round(low_pct, 1),
            "high_intensity_pct": round(high_pct, 1),
            "total_minutes": total_duration,
        }

    @staticmethod
    def calculate_treadmill_settings(flat_pace_min_per_km: float, grade_percentage: float) -> dict[str, float]:
        """
        Converts a target flat pace (min/km) to treadmill settings (speed in kph, incline in %)
        using a physiological grade-adjusted model.
        Speed (kph) = 60 / flat_pace (min/km)
        Then adjusts speed down as incline increases to match equivalent metabolic effort.
        """
        if flat_pace_min_per_km <= 0:
            return {"speed_kph": 0.0, "incline_percentage": grade_percentage}

        flat_speed_kph = 60.0 / flat_pace_min_per_km

        # Grade metabolic factor: each 1% incline increases effort by roughly 4-5%
        # Thus, to maintain the same effort, actual speed must be adjusted downwards.
        # Adjusted speed = flat_speed / (1 + 0.045 * grade)
        if grade_percentage > 0:
            adjusted_speed_kph = flat_speed_kph / (1.0 + (0.045 * grade_percentage))
        else:
            adjusted_speed_kph = flat_speed_kph

        return {"speed_kph": round(adjusted_speed_kph, 1), "incline_percentage": round(grade_percentage, 1)}
