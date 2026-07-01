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
