from typing import Any


class PacingCalculator:
    """Pace Strategy v2 engine.

    Per-segment pace = base_pace × grade × altitude × fatigue × weather × split_bias,
    where the grade factor comes from the Minetti (2002) metabolic cost curve with
    descent damping and a hike cap on steep climbs. Solving base pace from a target
    finish time is exact because every multiplier is independent of pace.
    """

    # Minetti (2002) polynomial C(i) in J/kg/m, i = gradient fraction, coefficients i^5..i^0
    MINETTI_COEFFS = (155.4, -30.4, -43.3, 46.3, 19.5, 3.6)
    FLAT_COST = 3.6  # C(0)
    GRADE_CLAMP = 0.45  # validity range of the polynomial
    # Runners can't convert the full downhill energy savings into pace (braking, impact).
    DESCENT_EFFICIENCY = 0.4
    HIKE_GRADE = 0.20  # segments steeper than this are labeled "hike"
    CLIMB_CAP_GRADE = 0.30  # climb multiplier stops growing here (hiking economy)
    # Characteristic grade used to split a checkpoint segment into up/down/flat parts
    # when only total gain/loss is known (rolling terrain costs more than net grade).
    ASSUMED_HILL_GRADE = 0.10
    ALTITUDE_FLOOR_M = 1500.0
    ALTITUDE_PENALTY_PER_100M = 0.015
    FATIGUE_FREE_KM = 15.0  # flat-equivalent km before durability decay starts
    FATIGUE_PER_KM = 0.0015
    HEAT_FLOOR_C = 15.0
    HEAT_PENALTY_PER_C = 0.003
    SPLIT_BIAS_MAX = 0.05  # ±5% pace swing between start and finish at |bias| = 1
    DEFAULT_WEIGHT_KG = 68.0
    JOULES_PER_KCAL = 4184.0

    @classmethod
    def _minetti_cost(cls, grade: float) -> float:
        i = max(-cls.GRADE_CLAMP, min(cls.GRADE_CLAMP, grade))
        a5, a4, a3, a2, a1, a0 = cls.MINETTI_COEFFS
        return a5 * i**5 + a4 * i**4 + a3 * i**3 + a2 * i**2 + a1 * i + a0

    @classmethod
    def grade_pace_multiplier(cls, grade: float) -> float:
        """Pace multiplier vs flat for a gradient given as a fraction (0.10 = 10%)."""
        if grade > cls.CLIMB_CAP_GRADE:
            grade = cls.CLIMB_CAP_GRADE
        ratio = cls._minetti_cost(grade) / cls.FLAT_COST
        if grade < 0:
            return 1.0 + (ratio - 1.0) * cls.DESCENT_EFFICIENCY
        return ratio

    @classmethod
    def _segment_parts(cls, dist_m: float, gain_m: float, loss_m: float) -> list[tuple[float, float]]:
        """Split a segment into (distance_m, grade) parts: climb, descent, flat."""
        if dist_m <= 0:
            return []
        d_up = gain_m / cls.ASSUMED_HILL_GRADE if gain_m > 0 else 0.0
        d_down = loss_m / cls.ASSUMED_HILL_GRADE if loss_m > 0 else 0.0
        total_hill = d_up + d_down
        if total_hill > dist_m:
            scale = dist_m / total_hill
            d_up *= scale
            d_down *= scale
        parts = []
        if d_up > 0:
            parts.append((d_up, gain_m / d_up))
        if d_down > 0:
            parts.append((d_down, -loss_m / d_down))
        d_flat = dist_m - d_up - d_down
        if d_flat > 0:
            parts.append((d_flat, 0.0))
        return parts

    @classmethod
    def _segment_grade_multiplier(cls, dist_m: float, gain_m: float, loss_m: float) -> float:
        parts = cls._segment_parts(dist_m, gain_m, loss_m)
        if not parts:
            return 1.0
        return sum(d * cls.grade_pace_multiplier(g) for d, g in parts) / dist_m

    @classmethod
    def _segment_energy_kcal(cls, dist_m: float, gain_m: float, loss_m: float, weight_kg: float) -> float:
        """Metabolic energy for a segment from the raw Minetti cost (J/kg/m).
        Uses the undamped curve: descents still save energy even though they
        don't yield proportional pace."""
        parts = cls._segment_parts(dist_m, gain_m, loss_m)
        joules = sum(d * cls._minetti_cost(g) * weight_kg for d, g in parts)
        return joules / cls.JOULES_PER_KCAL

    @classmethod
    def altitude_multiplier(cls, elevation_m: float) -> float:
        excess = max(0.0, elevation_m - cls.ALTITUDE_FLOOR_M)
        return 1.0 + cls.ALTITUDE_PENALTY_PER_100M * excess / 100.0

    @classmethod
    def fatigue_multiplier(cls, cumulative_flat_eq_km: float) -> float:
        return 1.0 + cls.FATIGUE_PER_KM * max(0.0, cumulative_flat_eq_km - cls.FATIGUE_FREE_KM)

    @classmethod
    def weather_multiplier(cls, temp_c: float | None) -> float:
        if temp_c is None:
            return 1.0
        return 1.0 + cls.HEAT_PENALTY_PER_C * max(0.0, temp_c - cls.HEAT_FLOOR_C)

    @classmethod
    def split_bias_multiplier(cls, split_bias: float, progress: float) -> float:
        """split_bias in [-1, 1]; positive = negative split (start easier, finish faster).

        progress is the segment midpoint as a fraction of total course distance, so
        the redistribution is symmetric and the total time is preserved.
        """
        bias = max(-1.0, min(1.0, split_bias))
        return 1.0 + bias * cls.SPLIT_BIAS_MAX * (1.0 - 2.0 * progress)

    @classmethod
    def calculate_checkpoint_paces(
        cls,
        checkpoints: list[dict[str, Any]],
        target_flat_pace_min_km: float,
        climb_coef: float | None = None,  # legacy flat-equivalent params, ignored by v2
        descent_coef: float | None = None,
        split_bias: float = 0.0,
        runner_weight_kg: float | None = None,
    ) -> list[dict[str, Any]]:
        """Calculates paced checkpoint splits from a base flat pace.

        Checkpoints may carry an optional per-segment forecast temperature under
        "temp_c"; heat above 15°C slows that segment (~0.3%/°C).
        """
        paced_checkpoints = []
        prev_dist = 0.0
        cumulative_time_mins = 0.0
        cumulative_flat_eq_km = 0.0
        cumulative_kcal = 0.0
        weight_kg = runner_weight_kg or cls.DEFAULT_WEIGHT_KG
        total_dist_m = max((cp["distance_meters"] for cp in checkpoints), default=0.0)

        for idx, cp in enumerate(checkpoints):
            cp_dist = cp["distance_meters"]
            cp_elev = cp.get("elevation_meters") or 0.0

            seg_dist_m = cp_dist - prev_dist
            seg_gain_m = cp.get("segment_gain_meters") or 0.0
            seg_loss_m = cp.get("segment_loss_meters") or 0.0

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
                        "effort": "run",
                        "temp_c": cp.get("temp_c"),
                        "after_sunset": bool(cp.get("after_sunset")),
                        "energy_kcal": 0,
                    }
                )
                prev_dist = cp_dist
                continue

            grade_mult = cls._segment_grade_multiplier(seg_dist_m, seg_gain_m, seg_loss_m)
            flat_eq_km = (seg_dist_m / 1000.0) * grade_mult

            grade_pct = ((seg_gain_m - seg_loss_m) / seg_dist_m) * 100.0 if seg_dist_m > 0 else 0.0
            climb_grade = (seg_gain_m / seg_dist_m) if seg_dist_m > 0 else 0.0
            effort = "hike" if climb_grade >= cls.HIKE_GRADE else "run"

            progress = (prev_dist + seg_dist_m / 2.0) / total_dist_m if total_dist_m > 0 else 0.5

            multiplier = (
                grade_mult
                * cls.altitude_multiplier(cp_elev)
                * cls.fatigue_multiplier(cumulative_flat_eq_km)
                * cls.weather_multiplier(cp.get("temp_c"))
                * cls.split_bias_multiplier(split_bias, progress)
            )
            adjusted_pace_decimal = target_flat_pace_min_km * multiplier

            seg_duration_mins = (seg_dist_m / 1000.0) * adjusted_pace_decimal
            cumulative_time_mins += seg_duration_mins
            cumulative_flat_eq_km += flat_eq_km
            cumulative_kcal += cls._segment_energy_kcal(seg_dist_m, seg_gain_m, seg_loss_m, weight_kg)

            total_secs = round(adjusted_pace_decimal * 60)
            formatted_pace = f"{total_secs // 60}:{total_secs % 60:02d}"

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
                    "flat_equivalent_km": round(flat_eq_km, 2),
                    "grade_pct": round(grade_pct, 1),
                    "effort": effort,
                    "temp_c": cp.get("temp_c"),
                    "after_sunset": bool(cp.get("after_sunset")),
                    "energy_kcal": round(cumulative_kcal),
                }
            )

            prev_dist = cp_dist

        return paced_checkpoints

    @classmethod
    def solve_base_pace(
        cls,
        checkpoints: list[dict[str, Any]],
        target_time_mins: float,
        split_bias: float = 0.0,
    ) -> float:
        """Inverse solve: the base flat pace (min/km) that finishes in target_time_mins.

        Total time is linear in base pace (no multiplier depends on pace), so the
        solve is a single division by the course time at 1.0 min/km.
        """
        unit_time = 0.0
        prev_dist = 0.0
        cumulative_flat_eq_km = 0.0
        total_dist_m = max((cp["distance_meters"] for cp in checkpoints), default=0.0)

        for idx, cp in enumerate(checkpoints):
            cp_dist = cp["distance_meters"]
            seg_dist_m = cp_dist - prev_dist
            if seg_dist_m <= 0:
                prev_dist = cp_dist
                continue
            seg_gain_m = cp.get("segment_gain_meters") or 0.0
            seg_loss_m = cp.get("segment_loss_meters") or 0.0
            cp_elev = cp.get("elevation_meters") or 0.0

            grade_mult = cls._segment_grade_multiplier(seg_dist_m, seg_gain_m, seg_loss_m)
            progress = (prev_dist + seg_dist_m / 2.0) / total_dist_m if total_dist_m > 0 else 0.5
            multiplier = (
                grade_mult
                * cls.altitude_multiplier(cp_elev)
                * cls.fatigue_multiplier(cumulative_flat_eq_km)
                * cls.weather_multiplier(cp.get("temp_c"))
                * cls.split_bias_multiplier(split_bias, progress)
            )
            unit_time += (seg_dist_m / 1000.0) * multiplier
            cumulative_flat_eq_km += (seg_dist_m / 1000.0) * grade_mult
            prev_dist = cp_dist

        if unit_time <= 0:
            raise ValueError("Course has no distance to pace")
        return target_time_mins / unit_time
