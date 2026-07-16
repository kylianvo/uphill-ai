"""Tests for TrainingRules.calculate_heart_rate_zones — threshold-anchored HR zones.

Formula matches the Uphill Athlete training zone calculator:
https://uphillathlete.com/aerobic-training/uphill-athlete-training-zones-heart-rate-calculator/
"""

from services.training_rules import TrainingRules


class TestCalculateHeartRateZones:
    def test_zones_anchored_on_explicit_aet_and_ant(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=190, resting_hr=50, aet_hr=140, ant_hr=165)

        z1_min = int(140 * 0.8)  # 112
        z1_max = int(140 * 0.9)  # 126
        z4_z5_split = int(165 + 0.5 * (190 - 165))  # 177

        assert zones["Zone 1"] == {"min": z1_min, "max": z1_max}
        assert zones["Zone 2"] == {"min": z1_max, "max": 140}
        assert zones["Zone 3"] == {"min": 140, "max": 165}
        assert zones["Zone 4"] == {"min": 165, "max": z4_z5_split}
        assert zones["Zone 5"] == {"min": z4_z5_split, "max": 190}

    def test_zones_are_contiguous_and_increasing(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=185, resting_hr=60, aet_hr=135, ant_hr=165)

        ordered = [zones[f"Zone {i}"] for i in range(1, 6)]
        for zone in ordered:
            assert zone["min"] <= zone["max"]
        for prev, nxt in zip(ordered, ordered[1:]):
            assert prev["max"] == nxt["min"]
        assert ordered[0]["min"] == int(135 * 0.8)
        assert ordered[-1]["max"] == 185

    def test_auto_derives_aet_and_ant_from_max_hr_when_not_supplied(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=200, resting_hr=55)

        expected_aet = round(200 * 0.73)  # 146
        expected_ant = round(200 * 0.89)  # 178

        assert zones["Zone 2"]["max"] == expected_aet
        assert zones["Zone 3"]["min"] == expected_aet
        assert zones["Zone 3"]["max"] == expected_ant
        assert zones["Zone 4"]["min"] == expected_ant

    def test_auto_derives_only_the_missing_threshold(self):
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=200, resting_hr=55, aet_hr=140)

        expected_ant = round(200 * 0.89)  # 178
        assert zones["Zone 3"]["min"] == 140
        assert zones["Zone 4"]["min"] == expected_ant

    def test_matches_uphill_athlete_calculator_example(self):
        """AeT=159, AnT=179, Max=197 — from the site's own worked example."""
        zones = TrainingRules.calculate_heart_rate_zones(max_hr=197, resting_hr=49, aet_hr=159, ant_hr=179)

        assert zones["Zone 1"] == {"min": 127, "max": 143}
        assert zones["Zone 2"] == {"min": 143, "max": 159}
        assert zones["Zone 3"] == {"min": 159, "max": 179}
        assert zones["Zone 4"] == {"min": 179, "max": 188}
        assert zones["Zone 5"] == {"min": 188, "max": 197}
