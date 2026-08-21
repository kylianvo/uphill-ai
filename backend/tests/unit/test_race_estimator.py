"""Tests for RaceEstimator — the shared goal/feasibility engine behind the
Goal Determiner (docs/pace-strategy-v2-plan.md §9). Pure math, no DB/network."""

from services.race_estimator import RaceEstimator


class TestSynthesizeCourse:
    def test_builds_per_km_checkpoints_preserving_totals(self):
        course = RaceEstimator.synthesize_course(69.5, 4000)
        assert course[0]["distance_meters"] == 0
        assert course[-1]["distance_meters"] == 69_500
        total_gain = sum(c.get("segment_gain_meters") or 0 for c in course)
        assert abs(total_gain - 4000) < 1


class TestPredict:
    def test_prediction_scales_linearly_with_base_pace(self):
        course = RaceEstimator.synthesize_course(50, 2500)
        t6 = RaceEstimator.predict_time_mins(course, base_flat_pace_min_km=6.0)
        t7 = RaceEstimator.predict_time_mins(course, base_flat_pace_min_km=7.0)
        assert abs(t7 / t6 - 7.0 / 6.0) < 0.01

    def test_mountain_course_slower_than_flat(self):
        flat = RaceEstimator.synthesize_course(50, 0)
        hilly = RaceEstimator.synthesize_course(50, 3000)
        assert RaceEstimator.predict_time_mins(hilly, 6.0) > RaceEstimator.predict_time_mins(flat, 6.0)


class TestFitnessFromReference:
    def test_reference_race_result_round_trips(self):
        # If the runner finished a 50k/2500m in X mins, the inferred base pace
        # must predict X mins on the same course.
        ref = RaceEstimator.synthesize_course(50, 2500)
        base = RaceEstimator.base_pace_from_result(ref, finish_time_mins=420.0)
        assert abs(RaceEstimator.predict_time_mins(ref, base) - 420.0) < 0.5


class TestEstimate:
    def test_goals_are_ordered_ambitious_realistic_safe(self):
        est = RaceEstimator.estimate(distance_km=70, elevation_gain_m=4000, base_flat_pace_min_km=6.5)
        goals = est["goals"]
        assert goals["ambitious"] < goals["realistic"] < goals["safe"]

    def test_weeks_to_race_improves_prediction_with_a_cap(self):
        base = RaceEstimator.estimate(distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0)
        soon = RaceEstimator.estimate(distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0, weeks_to_race=8)
        long_block = RaceEstimator.estimate(
            distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0, weeks_to_race=52
        )
        assert soon["adjusted_time_mins"] < base["adjusted_time_mins"] == base["predicted_time_mins"]
        # capped: a year of training doesn't promise more than ~5%
        assert long_block["adjusted_time_mins"] >= base["predicted_time_mins"] * 0.95 - 1

    def test_estimate_from_reference_result(self):
        est = RaceEstimator.estimate(
            distance_km=70,
            elevation_gain_m=4000,
            reference={"distance_km": 50, "elevation_gain_m": 2500, "finish_time_mins": 420.0},
        )
        assert est["predicted_time_mins"] > 420.0  # longer, hillier race takes longer
        assert est["base_flat_pace_min_km"] > 0

    def test_requires_some_fitness_input(self):
        try:
            RaceEstimator.estimate(distance_km=70, elevation_gain_m=4000)
            raised = False
        except ValueError:
            raised = True
        assert raised


class TestRankTransfer:
    def test_ultrasignup_style_rank_transfer(self):
        # runner did 12:00 where the winner ran 9:00 -> rank 0.75;
        # on a course whose winner runs 10:00 -> predicted 10:00/0.75 = 13:20
        predicted = RaceEstimator.rank_transfer_mins(
            reference_winner_mins=540.0, reference_time_mins=720.0, target_winner_mins=600.0
        )
        assert abs(predicted - 800.0) < 0.1


class TestPercentileCurve:
    def test_averages_percentiles_across_valid_years(self):
        results = [
            {
                "year": 2024,
                "percentiles": {
                    "overall": {
                        "p5": "9:30:00",
                        "p10": "10:00:00",
                        "p25": "11:00:00",
                        "p50": "13:00:00",
                        "p75": "15:00:00",
                        "p90": "17:00:00",
                    }
                },
            },
            {
                "year": 2025,
                "percentiles": {
                    "overall": {
                        "p5": "9:10:00",
                        "p10": "9:50:00",
                        "p25": "10:50:00",
                        "p50": "12:40:00",
                        "p75": "14:30:00",
                        "p90": "16:30:00",
                    }
                },
            },
        ]
        curve, years_used = RaceEstimator.percentile_curve(results)
        assert years_used == 2
        as_dict = dict(curve)
        # p5 average: (570 + 550) / 2 = 560 mins = 9:20:00
        assert abs(as_dict[5.0] - 560.0) < 0.01
        # p50 average: (780 + 760) / 2 = 770 mins = 12:50:00
        assert abs(as_dict[50.0] - 770.0) < 0.01
        assert [pt[0] for pt in curve] == [5.0, 10.0, 25.0, 50.0, 75.0, 90.0]

    def test_skips_non_monotonic_year(self):
        results = [
            {
                "year": 2024,
                "percentiles": {
                    "overall": {
                        # p50 faster than p25 -- invalid, must be skipped
                        "p5": "9:30:00",
                        "p10": "10:00:00",
                        "p25": "11:00:00",
                        "p50": "10:30:00",
                        "p75": "15:00:00",
                        "p90": "17:00:00",
                    }
                },
            },
            {
                "year": 2025,
                "percentiles": {
                    "overall": {
                        "p5": "9:10:00",
                        "p10": "9:50:00",
                        "p25": "10:50:00",
                        "p50": "12:40:00",
                        "p75": "14:30:00",
                        "p90": "16:30:00",
                    }
                },
            },
        ]
        curve, years_used = RaceEstimator.percentile_curve(results)
        assert years_used == 1
        as_dict = dict(curve)
        assert abs(as_dict[5.0] - 550.0) < 0.01  # only the 2025 year counted

    def test_returns_none_when_no_valid_years(self):
        results = [{"year": 2024, "percentiles": {}}, {"year": 2025}]
        assert RaceEstimator.percentile_curve(results) is None

    def test_returns_none_for_empty_results(self):
        assert RaceEstimator.percentile_curve([]) is None
