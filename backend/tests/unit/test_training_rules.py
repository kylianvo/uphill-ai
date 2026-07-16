"""Tests for TrainingRules.calculate_heart_rate_zones — threshold-anchored HR zones."""

from services.training_rules import TrainingRules


class TestCalculateHeartRateZones:
    def test_zones_anchored_on_explicit_aet_and_ant(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=190, resting_hr=50, aet_hr=140, ant_hr=165)

        mid1 = 50 + 0.5 * (140 - 50)  # 95
        mid2 = 140 + 0.5 * (165 - 140)  # 152

        assert zones["Zone 1"] == {"min": 50, "max": int(mid1)}
        assert zones["Zone 2"] == {"min": int(mid1), "max": 140}
        assert zones["Zone 3"] == {"min": 140, "max": int(mid2)}
        assert zones["Zone 4"] == {"min": int(mid2), "max": 165}
        assert zones["Zone 5"] == {"min": 165, "max": 190}

    def test_zones_are_contiguous_and_increasing(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=185, resting_hr=60, aet_hr=135, ant_hr=165)

        ordered = [zones[f"Zone {i}"] for i in range(1, 6)]
        for zone in ordered:
            assert zone["min"] <= zone["max"]
        for prev, nxt in zip(ordered, ordered[1:]):
            assert prev["max"] == nxt["min"]
        assert ordered[0]["min"] == 60
        assert ordered[-1]["max"] == 185

    def test_auto_derives_aet_and_ant_from_max_hr_when_not_supplied(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=200, resting_hr=55)

        expected_aet = round(200 * 0.73)  # 146
        expected_ant = round(200 * 0.89)  # 178

        assert zones["Zone 2"]["max"] == expected_aet
        assert zones["Zone 3"]["min"] == expected_aet
        assert zones["Zone 4"]["max"] == expected_ant
        assert zones["Zone 5"]["min"] == expected_ant

    def test_auto_derives_only_the_missing_threshold(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=200, resting_hr=55, aet_hr=140)

        expected_ant = round(200 * 0.89)  # 178
        assert zones["Zone 3"]["min"] == 140
        assert zones["Zone 5"]["min"] == expected_ant
