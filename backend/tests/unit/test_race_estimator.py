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


class TestInterpolatePercentile:
    CURVE = [(5.0, 550.0), (10.0, 580.0), (25.0, 650.0), (50.0, 770.0), (75.0, 870.0), (90.0, 990.0)]

    def test_exact_point_lookup_time_to_percentile(self):
        assert abs(RaceEstimator.interpolate_percentile(self.CURVE, time_mins=770.0) - 50.0) < 0.01

    def test_exact_point_lookup_percentile_to_time(self):
        assert abs(RaceEstimator.interpolate_percentile(self.CURVE, percentile=50.0) - 770.0) < 0.01

    def test_midpoint_interpolation_time_to_percentile(self):
        # halfway between p25 (650) and p50 (770) in time -> halfway in percentile
        mid_time = (650.0 + 770.0) / 2.0
        rank = RaceEstimator.interpolate_percentile(self.CURVE, time_mins=mid_time)
        assert abs(rank - 37.5) < 0.01

    def test_midpoint_interpolation_percentile_to_time(self):
        mid_pct = (25.0 + 50.0) / 2.0
        time_mins = RaceEstimator.interpolate_percentile(self.CURVE, percentile=mid_pct)
        assert abs(time_mins - 710.0) < 0.01

    def test_extrapolates_faster_than_p5(self):
        # elite time faster than p5 -- must extrapolate below 5, not clamp to 5
        rank = RaceEstimator.interpolate_percentile(self.CURVE, time_mins=520.0)
        assert rank < 5.0

    def test_extrapolates_slower_than_p90(self):
        time_mins = RaceEstimator.interpolate_percentile(self.CURVE, percentile=95.0)
        assert time_mins > 990.0

    def test_extrapolation_survives_a_tied_low_end_bucket(self):
        # p5 == p10 in minutes (small field / coarse rounding) -- the low-end
        # extrapolation segment has zero width and must not divide by zero.
        curve = [(5.0, 550.0), (10.0, 550.0), (25.0, 650.0), (50.0, 770.0), (75.0, 870.0), (90.0, 990.0)]
        rank = RaceEstimator.interpolate_percentile(curve, time_mins=500.0)
        assert rank == rank  # finite, not NaN
        assert isinstance(rank, float)

    def test_extrapolation_survives_a_tied_high_end_bucket(self):
        # p75 == p90 in minutes -- the high-end extrapolation segment has
        # zero width and must not divide by zero.
        curve = [(5.0, 550.0), (10.0, 580.0), (25.0, 650.0), (50.0, 770.0), (75.0, 990.0), (90.0, 990.0)]
        time_mins = RaceEstimator.interpolate_percentile(curve, percentile=95.0)
        assert time_mins == time_mins  # finite, not NaN
        assert isinstance(time_mins, float)

    def test_requires_exactly_one_of_time_or_percentile(self):
        raised = False
        try:
            RaceEstimator.interpolate_percentile(self.CURVE)
        except ValueError:
            raised = True
        assert raised

        raised = False
        try:
            RaceEstimator.interpolate_percentile(self.CURVE, time_mins=600.0, percentile=50.0)
        except ValueError:
            raised = True
        assert raised


class TestPercentileTransfer:
    def test_transfers_rank_from_reference_to_target_curve(self):
        reference_curve = [(5.0, 550.0), (10.0, 580.0), (25.0, 650.0), (50.0, 770.0), (75.0, 870.0), (90.0, 990.0)]
        target_curve = [(5.0, 600.0), (10.0, 640.0), (25.0, 720.0), (50.0, 860.0), (75.0, 980.0), (90.0, 1120.0)]
        # runner ran exactly the reference p50 (770 mins) -> should land near target p50 (860 mins)
        predicted = RaceEstimator.percentile_transfer_mins(reference_curve, 770.0, target_curve)
        assert abs(predicted - 860.0) < 0.01

    def test_faster_reference_time_transfers_to_faster_target_time(self):
        reference_curve = [(5.0, 550.0), (10.0, 580.0), (25.0, 650.0), (50.0, 770.0), (75.0, 870.0), (90.0, 990.0)]
        target_curve = [(5.0, 600.0), (10.0, 640.0), (25.0, 720.0), (50.0, 860.0), (75.0, 980.0), (90.0, 1120.0)]
        fast = RaceEstimator.percentile_transfer_mins(reference_curve, 600.0, target_curve)
        slow = RaceEstimator.percentile_transfer_mins(reference_curve, 950.0, target_curve)
        assert fast < slow


class TestTerrainInPaceConversion:
    def test_predict_time_scales_multiplicatively_with_terrain(self):
        course = RaceEstimator.synthesize_course(50, 2500)
        base = RaceEstimator.predict_time_mins(course, base_flat_pace_min_km=6.0)
        with_terrain = RaceEstimator.predict_time_mins(course, base_flat_pace_min_km=6.0, terrain_multiplier=1.2)
        assert abs(with_terrain - base * 1.2) < 0.01

    def test_predict_time_default_terrain_multiplier_is_noop(self):
        course = RaceEstimator.synthesize_course(50, 2500)
        base = RaceEstimator.predict_time_mins(course, base_flat_pace_min_km=6.0)
        explicit = RaceEstimator.predict_time_mins(course, base_flat_pace_min_km=6.0, terrain_multiplier=1.0)
        assert abs(base - explicit) < 1e-9

    def test_base_pace_from_result_is_faster_with_terrain_multiplier(self):
        course = RaceEstimator.synthesize_course(50, 2500)
        base = RaceEstimator.base_pace_from_result(course, finish_time_mins=420.0)
        with_terrain = RaceEstimator.base_pace_from_result(course, finish_time_mins=420.0, terrain_multiplier=1.2)
        # a technical-course result implies stronger underlying (faster, lower min/km) fitness
        assert with_terrain < base

    def test_terrain_round_trips_through_predict_and_base_pace(self):
        course = RaceEstimator.synthesize_course(50, 2500)
        pace = RaceEstimator.base_pace_from_result(course, finish_time_mins=420.0, terrain_multiplier=1.2)
        predicted = RaceEstimator.predict_time_mins(course, pace, terrain_multiplier=1.2)
        assert abs(predicted - 420.0) < 0.5


class TestTerrainMultiplier:
    def test_no_tags_returns_one(self):
        assert RaceEstimator.terrain_multiplier(None) == 1.0
        assert RaceEstimator.terrain_multiplier([]) == 1.0

    def test_pure_landmark_tags_return_one(self):
        # place names / landmarks with no difficulty keyword should not match
        tags = ["dragon bridge", "marina bay sands", "national stadium"]
        assert RaceEstimator.terrain_multiplier(tags) == 1.0

    def test_single_keyword_match(self):
        mult = RaceEstimator.terrain_multiplier(["muddy rainy-season terrain"])
        assert abs(mult - 1.05) < 0.001

    def test_multiple_keywords_sum(self):
        # "technical hand-and-knees scrambles on final climbs" -> technical (0.07) + scramb (0.08)
        mult = RaceEstimator.terrain_multiplier(["technical hand-and-knees scrambles on final climbs"])
        assert abs(mult - 1.15) < 0.001

    def test_repeated_keyword_across_tags_counts_once(self):
        # "steep" appears in both tags but must only be counted once
        tags = ["steep rolling hills", "steep climb to the summit"]
        assert abs(RaceEstimator.terrain_multiplier(tags) - 1.04) < 0.001

    def test_vmm_worked_example_from_spec(self):
        tags = [
            "technical hand-and-knees scrambles on final climbs",
            "continuously slippery, dark single trail deep in the jungle",
        ]
        # technical (0.07) + scramb (0.08) + slippery (0.06) + jungle (0.02) = 0.23
        assert abs(RaceEstimator.terrain_multiplier(tags) - 1.23) < 0.001

    def test_cap_never_exceeded(self):
        # every keyword at once would sum well past 0.30 without the cap;
        # equality (not <=) proves the cap is actually being exercised
        tags = [
            "technical scrambling scree slippery muddy rocky river crossing steep "
            "volcanic karst exposed root staircase singletrack single track sand steps jungle"
        ]
        assert abs(RaceEstimator.terrain_multiplier(tags) - 1.30) < 1e-9

    def test_plural_river_crossings_still_matches(self):
        mult = RaceEstimator.terrain_multiplier(["river crossings"])
        assert abs(mult - 1.05) < 0.001

    def test_plural_staircases_still_matches(self):
        mult = RaceEstimator.terrain_multiplier(["long staircases (spit to manly, north head)"])
        assert abs(mult - 1.03) < 0.001

    def test_sand_plural_still_excluded(self):
        # "Marina Bay Sands" is a landmark, not a terrain signal -- must not match even with the s? fix elsewhere
        assert RaceEstimator.terrain_multiplier(["marina bay sands"]) == 1.0


class TestEstimateTerrain:
    def test_target_terrain_slows_prediction_and_is_reported(self):
        base = RaceEstimator.estimate(distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0)
        technical = RaceEstimator.estimate(
            distance_km=50,
            elevation_gain_m=2000,
            base_flat_pace_min_km=6.0,
            terrain_tags=["technical hand-and-knees scrambles"],
        )
        assert base["terrain_multiplier_target"] == 1.0
        assert technical["terrain_multiplier_target"] > 1.0
        assert technical["predicted_time_mins"] > base["predicted_time_mins"]

    def test_reference_terrain_multiplier_reported_when_reference_used(self):
        est = RaceEstimator.estimate(
            distance_km=70,
            elevation_gain_m=4000,
            reference={
                "distance_km": 50,
                "elevation_gain_m": 2500,
                "finish_time_mins": 420.0,
                "terrain_tags": ["muddy rainy-season terrain"],
            },
        )
        assert est["terrain_multiplier_reference"] is not None
        assert est["terrain_multiplier_reference"] > 1.0

    def test_reference_terrain_multiplier_none_without_reference(self):
        est = RaceEstimator.estimate(distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0)
        assert est["terrain_multiplier_reference"] is None

    def test_no_terrain_tags_matches_pre_terrain_behavior(self):
        # regression guard: identical to calling estimate() with no terrain_tags at all
        with_none = RaceEstimator.estimate(distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0)
        explicit_none = RaceEstimator.estimate(
            distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0, terrain_tags=None
        )
        assert with_none == explicit_none


class TestEstimateGpxProfile:
    def test_target_checkpoints_used_instead_of_synthetic(self):
        checkpoints = [
            {
                "name": "Start",
                "distance_meters": 0,
                "elevation_meters": 1500.0,
                "segment_gain_meters": 0.0,
                "segment_loss_meters": 0.0,
            },
            {
                "name": "KM 10",
                "distance_meters": 10000.0,
                "elevation_meters": 3000.0,
                "segment_gain_meters": 1500.0,
                "segment_loss_meters": 0.0,
            },
            {
                "name": "KM 20",
                "distance_meters": 20000.0,
                "elevation_meters": 3000.0,
                "segment_gain_meters": 0.0,
                "segment_loss_meters": 0.0,
            },
        ]
        with_gpx = RaceEstimator.estimate(
            distance_km=20, elevation_gain_m=1500, base_flat_pace_min_km=6.0, target_checkpoints=checkpoints
        )
        synthetic = RaceEstimator.estimate(distance_km=20, elevation_gain_m=1500, base_flat_pace_min_km=6.0)
        assert with_gpx["target_profile_source"] == "gpx"
        assert synthetic["target_profile_source"] == "synthetic"
        # the real profile concentrates gain into one steep 10km climb (vs.
        # synthetic's evenly-spread grade) AND carries elevation above the
        # 1500m altitude floor -- both push predicted time up
        assert with_gpx["predicted_time_mins"] > synthetic["predicted_time_mins"]

    def test_reference_checkpoints_used_and_reported(self):
        checkpoints = [
            {
                "name": "Start",
                "distance_meters": 0,
                "elevation_meters": 1500.0,
                "segment_gain_meters": 0.0,
                "segment_loss_meters": 0.0,
            },
            {
                "name": "Finish",
                "distance_meters": 10000.0,
                "elevation_meters": 2000.0,
                "segment_gain_meters": 500.0,
                "segment_loss_meters": 0.0,
            },
        ]
        est = RaceEstimator.estimate(
            distance_km=50,
            elevation_gain_m=2000,
            reference={
                "distance_km": 10,
                "elevation_gain_m": 500,
                "finish_time_mins": 60.0,
                "checkpoints": checkpoints,
            },
        )
        assert est["reference_profile_source"] == "gpx"
        assert est["target_profile_source"] == "synthetic"

    def test_no_reference_gives_none_reference_profile_source(self):
        est = RaceEstimator.estimate(distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0)
        assert est["reference_profile_source"] is None

    def test_omitting_target_checkpoints_matches_pre_gpx_behavior(self):
        with_none = RaceEstimator.estimate(distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0)
        explicit_none = RaceEstimator.estimate(
            distance_km=50, elevation_gain_m=2000, base_flat_pace_min_km=6.0, target_checkpoints=None
        )
        assert with_none == explicit_none
