"""Tests for PacingCalculator.calculate_checkpoint_paces — pure math, no
DB/network, but used by the public /api/coach/calculate-pacing endpoint."""

from services.pacing_calculator import PacingCalculator


def make_checkpoint(name, distance_m, elevation_m=0.0, gain_m=0.0, loss_m=0.0):
    return {
        "name": name,
        "distance_meters": distance_m,
        "elevation_meters": elevation_m,
        "segment_gain_meters": gain_m,
        "segment_loss_meters": loss_m,
    }


class TestCalculateCheckpointPaces:
    def test_first_checkpoint_is_zeroed_start_point(self):
        checkpoints = [make_checkpoint("Start", 0)]
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        assert result[0]["distance_km"] == 0.0
        assert result[0]["cumulative_time_mins"] == 0.0
        assert result[0]["split_time"] == "0:00:00"

    def test_flat_segment_uses_target_pace_directly(self):
        checkpoints = [
            make_checkpoint("Start", 0),
            make_checkpoint("KM 5", 5000, gain_m=0.0, loss_m=0.0),
        ]
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        second = result[1]
        assert second["target_pace"] == "6:00"
        assert second["flat_equivalent_km"] == 5.0
        assert second["cumulative_time_mins"] == 30.0  # 5km @ 6:00/km
        assert second["split_time"] == "00:30:00"

    def test_climbing_segment_is_slower_than_flat_segment(self):
        flat = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000)]
        climb = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000, gain_m=500.0)]

        flat_result = PacingCalculator.calculate_checkpoint_paces(flat, target_flat_pace_min_km=6.0)
        climb_result = PacingCalculator.calculate_checkpoint_paces(climb, target_flat_pace_min_km=6.0)

        assert climb_result[1]["cumulative_time_mins"] > flat_result[1]["cumulative_time_mins"]

    def test_altitude_above_1500m_applies_oxygen_penalty(self):
        low_altitude = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000, elevation_m=1000.0)]
        high_altitude = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000, elevation_m=2500.0)]

        low_result = PacingCalculator.calculate_checkpoint_paces(low_altitude, target_flat_pace_min_km=6.0)
        high_result = PacingCalculator.calculate_checkpoint_paces(high_altitude, target_flat_pace_min_km=6.0)

        assert high_result[1]["cumulative_time_mins"] > low_result[1]["cumulative_time_mins"]

    def test_steep_grade_over_15_percent_applies_hike_penalty(self):
        # 5000m segment with 1000m gain = 20% grade, well over the 15% threshold.
        checkpoints = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000, gain_m=1000.0)]
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        assert result[1]["grade_pct"] == 20.0


class TestGradePaceMultiplier:
    """Minetti (2002) grade-adjusted pace multipliers with descent damping."""

    def test_flat_grade_is_neutral(self):
        assert PacingCalculator.grade_pace_multiplier(0.0) == 1.0

    def test_ten_percent_climb_costs_more_than_half_again(self):
        assert PacingCalculator.grade_pace_multiplier(0.10) > 1.5

    def test_moderate_descent_helps_but_less_than_energy_savings(self):
        mult = PacingCalculator.grade_pace_multiplier(-0.10)
        assert 0.80 <= mult <= 0.95

    def test_descent_benefit_is_u_shaped(self):
        # Minetti energy minimum ~ -20%; steeper descents cost pace again.
        assert PacingCalculator.grade_pace_multiplier(-0.20) < PacingCalculator.grade_pace_multiplier(-0.30)

    def test_climb_multiplier_is_capped_at_hike_grades(self):
        assert PacingCalculator.grade_pace_multiplier(0.35) == PacingCalculator.grade_pace_multiplier(0.30)

    def test_up_down_asymmetry(self):
        up_penalty = PacingCalculator.grade_pace_multiplier(0.10) - 1.0
        down_benefit = 1.0 - PacingCalculator.grade_pace_multiplier(-0.10)
        assert up_penalty > 2 * down_benefit


class TestSegmentEffects:
    def test_rolling_segment_is_slower_than_flat(self):
        flat = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000)]
        rolling = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000, gain_m=150.0, loss_m=150.0)]
        flat_r = PacingCalculator.calculate_checkpoint_paces(flat, target_flat_pace_min_km=6.0)
        roll_r = PacingCalculator.calculate_checkpoint_paces(rolling, target_flat_pace_min_km=6.0)
        assert roll_r[1]["cumulative_time_mins"] > flat_r[1]["cumulative_time_mins"]

    def test_steep_climb_segment_is_labeled_hike(self):
        checkpoints = [make_checkpoint("Start", 0), make_checkpoint("Wall", 2000, gain_m=500.0)]
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        assert result[1]["effort"] == "hike"

    def test_flat_segment_is_labeled_run(self):
        checkpoints = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000)]
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        assert result[1]["effort"] == "run"

    def test_fatigue_slows_late_segments_on_long_courses(self):
        # 60 identical flat kms: the last split must take longer than the first.
        checkpoints = [make_checkpoint("Start", 0)]
        for km in range(1, 61):
            checkpoints.append(make_checkpoint(f"KM {km}", km * 1000))
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        first_split = result[1]["cumulative_time_mins"]
        last_split = result[60]["cumulative_time_mins"] - result[59]["cumulative_time_mins"]
        assert last_split > first_split

    def test_no_fatigue_on_short_courses(self):
        # 5km flat stays exactly at target pace (fatigue starts beyond 15 flat-eq km).
        checkpoints = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000)]
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        assert result[1]["cumulative_time_mins"] == 30.0


class TestSplitBias:
    def make_flat_course(self):
        cps = [make_checkpoint("Start", 0)]
        for km in range(1, 11):
            cps.append(make_checkpoint(f"KM {km}", km * 1000))
        return cps

    def test_negative_split_bias_starts_slower_finishes_faster(self):
        even = PacingCalculator.calculate_checkpoint_paces(self.make_flat_course(), target_flat_pace_min_km=6.0)
        biased = PacingCalculator.calculate_checkpoint_paces(
            self.make_flat_course(), target_flat_pace_min_km=6.0, split_bias=1.0
        )
        even_first = even[1]["cumulative_time_mins"]
        biased_first = biased[1]["cumulative_time_mins"]
        even_last = even[10]["cumulative_time_mins"] - even[9]["cumulative_time_mins"]
        biased_last = biased[10]["cumulative_time_mins"] - biased[9]["cumulative_time_mins"]
        assert biased_first > even_first
        assert biased_last < even_last

    def test_split_bias_preserves_total_time(self):
        even = PacingCalculator.calculate_checkpoint_paces(self.make_flat_course(), target_flat_pace_min_km=6.0)
        biased = PacingCalculator.calculate_checkpoint_paces(
            self.make_flat_course(), target_flat_pace_min_km=6.0, split_bias=1.0
        )
        assert abs(biased[10]["cumulative_time_mins"] - even[10]["cumulative_time_mins"]) < 0.5


class TestWeather:
    def test_heat_slows_segment(self):
        cool = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000)]
        hot = [make_checkpoint("Start", 0), {**make_checkpoint("KM 5", 5000), "temp_c": 32.0}]
        cool_r = PacingCalculator.calculate_checkpoint_paces(cool, target_flat_pace_min_km=6.0)
        hot_r = PacingCalculator.calculate_checkpoint_paces(hot, target_flat_pace_min_km=6.0)
        assert hot_r[1]["cumulative_time_mins"] > cool_r[1]["cumulative_time_mins"]

    def test_weather_fields_pass_through_to_output(self):
        checkpoints = [
            make_checkpoint("Start", 0),
            {**make_checkpoint("KM 5", 5000), "temp_c": 31.5, "after_sunset": True},
        ]
        result = PacingCalculator.calculate_checkpoint_paces(checkpoints, target_flat_pace_min_km=6.0)
        assert result[1]["temp_c"] == 31.5
        assert result[1]["after_sunset"] is True
        assert result[0]["temp_c"] is None
        assert result[0]["after_sunset"] is False

    def test_cool_temperature_is_not_a_bonus(self):
        plain = [make_checkpoint("Start", 0), make_checkpoint("KM 5", 5000)]
        cold = [make_checkpoint("Start", 0), {**make_checkpoint("KM 5", 5000), "temp_c": 5.0}]
        plain_r = PacingCalculator.calculate_checkpoint_paces(plain, target_flat_pace_min_km=6.0)
        cold_r = PacingCalculator.calculate_checkpoint_paces(cold, target_flat_pace_min_km=6.0)
        assert cold_r[1]["cumulative_time_mins"] == plain_r[1]["cumulative_time_mins"]


class TestSolveBasePace:
    def make_hilly_course(self):
        cps = [make_checkpoint("Start", 0)]
        for km in range(1, 31):
            cps.append(make_checkpoint(f"KM {km}", km * 1000, elevation_m=1600.0, gain_m=80.0, loss_m=30.0))
        return cps

    def test_solved_pace_round_trips_to_target_time(self):
        course = self.make_hilly_course()
        target_mins = 300.0
        pace = PacingCalculator.solve_base_pace(course, target_time_mins=target_mins)
        result = PacingCalculator.calculate_checkpoint_paces(course, target_flat_pace_min_km=pace)
        assert abs(result[-1]["cumulative_time_mins"] - target_mins) < 1.0

    def test_faster_target_needs_faster_base_pace(self):
        course = self.make_hilly_course()
        fast = PacingCalculator.solve_base_pace(course, target_time_mins=240.0)
        slow = PacingCalculator.solve_base_pace(course, target_time_mins=360.0)
        assert fast < slow
