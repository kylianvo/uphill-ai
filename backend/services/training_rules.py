from typing import Any


class TrainingRules:
    @staticmethod
    def calculate_heart_rate_zones(max_hr: int, resting_hr: int) -> dict[str, dict[str, int]]:
        """
        Calculates five heart rate zones using the Karvonen formula (Heart Rate Reserve).
        Zone 1: 50% - 60%
        Zone 2: 60% - 70%
        Zone 3: 70% - 80%
        Zone 4: 80% - 90%
        Zone 5: 90% - 100%
        """
        hrr = max_hr - resting_hr

        zones = {}
        thresholds = [
            ("Zone 1", 0.50, 0.60),
            ("Zone 2", 0.60, 0.70),
            ("Zone 3", 0.70, 0.80),
            ("Zone 4", 0.80, 0.90),
            ("Zone 5", 0.90, 1.00),
        ]

        for name, low_pct, high_pct in thresholds:
            zones[name] = {"min": int(resting_hr + (hrr * low_pct)), "max": int(resting_hr + (hrr * high_pct))}

        return zones

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
