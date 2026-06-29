from typing import Any


class PacingCalculator:
    @staticmethod
    def calculate_checkpoint_paces(
        checkpoints: list[dict[str, Any]],
        target_flat_pace_min_km: float,
        climb_coef: float = 10.0,  # 100m gain = 1000m flat
        descent_coef: float = 2.0,  # 100m loss = 200m flat
    ) -> list[dict[str, Any]]:
        """
        Parses GPX checkpoints and calculates paced checkpoint splits using Uphill AI pacing math:
        - Calculates flat-equivalent distances.
        - Applies altitude oxygen adjustments (1% slower for every 100m above 1500m).
        - Applies steepness hikes penalty (20% slower on grades >= 15%).
        """
        paced_checkpoints = []
        prev_dist = 0.0
        cumulative_time_mins = 0.0

        for idx, cp in enumerate(checkpoints):
            cp_dist = cp["distance_meters"]
            cp_elev = cp.get("elevation_meters") or 0.0

            # Segment metrics
            seg_dist_m = cp_dist - prev_dist
            seg_gain_m = cp.get("segment_gain_meters") or 0.0
            seg_loss_m = cp.get("segment_loss_meters") or 0.0

            # Handle starting point
            if idx == 0 and seg_dist_m == 0:
                paced_checkpoints.append(
                    {
                        "name": cp["name"],
                        "distance_km": 0.0,
                        "elevation_m": round(cp_elev),
                        "target_pace": "0:00",
                        "split_time": "0:00:00",
                        "cumulative_time_mins": 0.0,
                        "flat_equivalent_km": 0.0,
                        "grade_pct": 0.0,
                    }
                )
                prev_dist = cp_dist
                continue

            # 1. Flat equivalent calculations (Kilian Jornet pacing conversion)
            # Distance in meters -> convert vertical offsets
            flat_eq_m = seg_dist_m + (climb_coef * seg_gain_m) - (descent_coef * seg_loss_m)
            if flat_eq_m < 0:
                flat_eq_m = seg_dist_m  # floor at horizontal distance

            # 2. Oxygen Altitude Adjustment
            # 1% slower for every 100m above 1500m elevation
            altitude_multiplier = 1.0
            if cp_elev > 1500.0:
                excess_elev_m = cp_elev - 1500.0
                altitude_multiplier = 1.0 + (0.01 * (excess_elev_m / 100.0))

            # 3. Steepness Hike Penalty
            # Slope/Grade check
            grade_pct = 0.0
            slope_multiplier = 1.0
            if seg_dist_m > 0:
                grade_pct = (seg_gain_m / seg_dist_m) * 100.0
                if grade_pct >= 15.0:
                    slope_multiplier = 1.2  # 20% pace penalty for steep climbs

            # 4. Target Pace Calculation
            # Decimal minutes per km
            adjusted_pace_decimal = target_flat_pace_min_km * altitude_multiplier * slope_multiplier

            # Duration in minutes for this segment = flat_eq_km * adjusted_pace
            seg_duration_mins = (flat_eq_m / 1000.0) * adjusted_pace_decimal
            cumulative_time_mins += seg_duration_mins

            # Format outputs
            total_secs = round(adjusted_pace_decimal * 60)
            min_part = total_secs // 60
            sec_part = total_secs % 60
            formatted_pace = f"{min_part}:{sec_part:02d}"

            # Format Split Time (HH:MM:SS)
            total_split_secs = round(cumulative_time_mins * 60)
            hrs = total_split_secs // 3600
            mins = (total_split_secs % 3600) // 60
            secs = total_split_secs % 60
            formatted_split = f"{hrs:02d}:{mins:02d}:{secs:02d}"

            paced_checkpoints.append(
                {
                    "name": cp["name"],
                    "distance_km": round(cp_dist / 1000.0, 2),
                    "elevation_m": round(cp_elev),
                    "target_pace": formatted_pace,
                    "split_time": formatted_split,
                    "cumulative_time_mins": round(cumulative_time_mins, 1),
                    "flat_equivalent_km": round(flat_eq_m / 1000.0, 2),
                    "grade_pct": round(grade_pct, 1),
                }
            )

            prev_dist = cp_dist

        return paced_checkpoints
