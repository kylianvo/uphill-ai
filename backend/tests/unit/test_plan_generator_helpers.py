"""Pure static-method tests for PlanGenerator's pace math.

parse_pace_to_decimal / decimal_to_pace_str / estimate_pace_zones are used
throughout onboarding and plan generation. Pace strings ("MM:SS") <-> decimal
minutes conversions are a classic off-by-format bug class, the same flavor
as the plan_start_date regression this suite exists to catch.
"""

import asyncio
import re
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from config import settings
from services.plan_generator import PlanGenerator


class TestParsePaceToDecimal:
    def test_parses_mm_ss_format(self):
        assert PlanGenerator.parse_pace_to_decimal("6:30") == 6.5

    def test_parses_plain_decimal_string(self):
        assert PlanGenerator.parse_pace_to_decimal("6.5") == 6.5

    def test_returns_default_for_empty_input(self):
        assert PlanGenerator.parse_pace_to_decimal("") == 6.0
        assert PlanGenerator.parse_pace_to_decimal(None) == 6.0

    def test_returns_default_for_garbage_input(self):
        assert PlanGenerator.parse_pace_to_decimal("not-a-pace") == 6.0


class TestDecimalToPaceStr:
    def test_converts_whole_minutes(self):
        assert PlanGenerator.decimal_to_pace_str(6.0) == "6:00"

    def test_converts_fractional_minutes(self):
        assert PlanGenerator.decimal_to_pace_str(6.5) == "6:30"

    def test_rounds_seconds_overflow_into_next_minute(self):
        # 6.999 minutes -> 6m + 59.94s, rounds to 60s -> carries to 7:00
        assert PlanGenerator.decimal_to_pace_str(6.999) == "7:00"

    def test_round_trip_with_parse_pace_to_decimal(self):
        original = "5:45"
        decimal = PlanGenerator.parse_pace_to_decimal(original)
        assert PlanGenerator.decimal_to_pace_str(decimal) == original


class TestEstimatePaceZones:
    def test_returns_all_five_zone_ranges_and_midpoints(self):
        zones = PlanGenerator.estimate_pace_zones("6:30", "5:45")
        assert set(zones.keys()) == {
            "zone1_pace",
            "zone1_pace_mid",
            "zone2_pace",
            "zone2_pace_mid",
            "zone3_pace",
            "zone3_pace_mid",
            "zone4_pace",
            "zone4_pace_mid",
            "zone5_pace",
            "zone5_pace_mid",
        }

    def test_zone2_pace_echoes_input_bounds(self):
        zones = PlanGenerator.estimate_pace_zones("6:30", "5:45")
        assert zones["zone2_pace"] == "6:30 - 5:45"

    def test_every_zone_is_a_slow_dash_fast_range(self):
        zones = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=140, ant_hr=161)
        for key in ("zone1_pace", "zone3_pace", "zone4_pace", "zone5_pace"):
            slow_str, fast_str = zones[key].split(" - ")
            slow = PlanGenerator.parse_pace_to_decimal(slow_str)
            fast = PlanGenerator.parse_pace_to_decimal(fast_str)
            assert slow > fast, f"{key} slow bound must be a larger (slower) decimal than its fast bound"

    def test_faster_zones_have_faster_pace_than_slower_zones(self):
        # "faster pace" == smaller decimal minutes-per-km. Zone 5's fast bound
        # must be numerically faster than Zone 1's slow bound.
        zones = PlanGenerator.estimate_pace_zones("6:30", "5:45")
        z1_slow = PlanGenerator.parse_pace_to_decimal(zones["zone1_pace"].split(" - ")[0])
        z5_fast = PlanGenerator.parse_pace_to_decimal(zones["zone5_pace"].split(" - ")[1])
        assert z5_fast < z1_slow

    def test_defaults_apply_when_bounds_missing(self):
        """The inner fallback now comes from the tier table rather than a hardcoded
        "6:30"/"5:45", so this asserts the two agree rather than naming a literal --
        pinning the literal here would silently drift from the tier the app actually
        uses. Callers should never reach this branch: they resolve zones through
        training_rules.resolve_zone2_pace first."""
        from services.training_rules import default_zone2_pace

        with_explicit_defaults = PlanGenerator.estimate_pace_zones(*default_zone2_pace())
        with_none = PlanGenerator.estimate_pace_zones(None, None)
        assert with_none == with_explicit_defaults

    def test_missing_aet_ant_hr_falls_back_to_baseline_ratios(self):
        # scale=1.0 reproduces the original fixed ratios: Z1=1.15x, Z3=0.90x,
        # Z4=0.82x, Z5=0.73x. Zones are chained (each one's slow bound is the
        # adjacent zone's fast bound), anchored on Zone 2's own bounds: Zone 1
        # touches Zone 2 at zone2_min; Zones 3/4/5 chain outward from zone2_max.
        zone2_min, zone2_max = "6:30", "5:45"
        z2_min_dec = PlanGenerator.parse_pace_to_decimal(zone2_min)
        z2_max_dec = PlanGenerator.parse_pace_to_decimal(zone2_max)

        zones = PlanGenerator.estimate_pace_zones(zone2_min, zone2_max)  # no aet_hr/ant_hr

        z1_slow_str, z1_fast_str = zones["zone1_pace"].split(" - ")
        assert z1_slow_str == PlanGenerator.decimal_to_pace_str(z2_min_dec * 1.15)
        assert z1_fast_str == PlanGenerator.decimal_to_pace_str(z2_min_dec)

        z3_slow_str, z3_fast_str = zones["zone3_pace"].split(" - ")
        assert z3_slow_str == PlanGenerator.decimal_to_pace_str(z2_max_dec)
        assert z3_fast_str == PlanGenerator.decimal_to_pace_str(z2_max_dec * 0.90)

        z4_slow_str, z4_fast_str = zones["zone4_pace"].split(" - ")
        assert z4_slow_str == PlanGenerator.decimal_to_pace_str(z2_max_dec * 0.90)
        assert z4_fast_str == PlanGenerator.decimal_to_pace_str(z2_max_dec * 0.82)

        z5_slow_str, z5_fast_str = zones["zone5_pace"].split(" - ")
        assert z5_slow_str == PlanGenerator.decimal_to_pace_str(z2_max_dec * 0.82)
        assert z5_fast_str == PlanGenerator.decimal_to_pace_str(z2_max_dec * 0.73)

    def test_adjacent_zones_are_contiguous_with_no_overlap(self):
        # Regression test: independently scaling both ends of every zone by
        # its own ratio (the original approach) could make adjacent zones
        # overlap whenever the athlete's own Zone 2 range was proportionally
        # wider than the gap between zone ratios. Zones must instead chain
        # together -- each one's boundary is exactly the next zone's boundary,
        # for both a narrow and a wide Zone 2 range, and across the clamp.
        for zone2_min, zone2_max, aet_hr, ant_hr in [
            ("6:30", "5:45", None, None),
            ("6:22", "5:14", 142, 168),  # wide Zone 2 range that triggered the original bug
            ("6:30", "5:45", 100, 200),  # clamped at the 1.4 scale ceiling
            ("6:30", "5:45", 150, 100),  # clamped at the 0.7 scale floor
        ]:
            zones = PlanGenerator.estimate_pace_zones(zone2_min, zone2_max, aet_hr, ant_hr)
            z1_fast = zones["zone1_pace"].split(" - ")[1]
            z2_slow, z2_fast = zones["zone2_pace"].split(" - ")
            z3_slow, z3_fast = zones["zone3_pace"].split(" - ")
            z4_slow, z4_fast = zones["zone4_pace"].split(" - ")
            z5_slow, _ = zones["zone5_pace"].split(" - ")

            assert z1_fast == z2_slow, "Zone 1's fast bound must equal Zone 2's slow bound"
            assert z2_fast == z3_slow, "Zone 2's fast bound must equal Zone 3's slow bound"
            assert z3_fast == z4_slow, "Zone 3's fast bound must equal Zone 4's slow bound"
            assert z4_fast == z5_slow, "Zone 4's fast bound must equal Zone 5's slow bound"

    def test_scale_factor_is_clamped_to_0_7_min(self):
        # ant_hr below aet_hr (unusual/bad data) pushes gap_ratio well under
        # 1.0, which would push scale far below 0.7; the clamp must hold it
        # at the floor.
        zones_extreme = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=150, ant_hr=100)
        # gap_ratio = 161/200 = 0.805 -> scale = 0.805/1.15 = 0.7 exactly, unclamped.
        zones_at_floor = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=200, ant_hr=161)
        assert zones_extreme["zone4_pace"] == zones_at_floor["zone4_pace"]

    def test_scale_factor_is_clamped_to_1_4_max(self):
        # A very wide AeT-AnT gap would otherwise push scale far above 1.4;
        # the clamp must hold it at the ceiling.
        zones_extreme = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=100, ant_hr=200)
        zones_at_ceiling = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=100, ant_hr=100 * 1.4 * 1.15)
        assert zones_extreme["zone4_pace"] == zones_at_ceiling["zone4_pace"]

    def test_wider_gap_pulls_zone4_further_from_zone2_than_narrower_gap(self):
        narrow_gap = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=140, ant_hr=154)  # gap_ratio=1.10
        wide_gap = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=140, ant_hr=168)  # gap_ratio=1.20
        narrow_z4_fast = PlanGenerator.parse_pace_to_decimal(narrow_gap["zone4_pace"].split(" - ")[1])
        wide_z4_fast = PlanGenerator.parse_pace_to_decimal(wide_gap["zone4_pace"].split(" - ")[1])
        # Zone 4 is faster than Zone 2, so a wider gap must push it to an
        # even smaller (faster) decimal.
        assert wide_z4_fast < narrow_z4_fast


class TestPaceAndDistanceForZone:
    def test_maps_a_named_zone_to_its_range_pace_and_computed_distance(self):
        est_zones = PlanGenerator.estimate_pace_zones("6:30", "5:45", aet_hr=140, ant_hr=161)
        pace, distance = PlanGenerator.pace_and_distance_for_zone("Zone 4", 40.0, est_zones)

        assert pace == f"{est_zones['zone4_pace']} /km"
        expected_dec = PlanGenerator.parse_pace_to_decimal(est_zones["zone4_pace_mid"])
        assert distance == round(40.0 / expected_dec, 1)

    def test_defaults_to_zone_2_for_unrecognized_zone_labels(self):
        est_zones = PlanGenerator.estimate_pace_zones("6:30", "5:45")
        pace, _ = PlanGenerator.pace_and_distance_for_zone("Some Weird Zone", 30.0, est_zones)
        assert pace == f"{est_zones['zone2_pace']} /km"

    def test_zero_duration_yields_zero_distance(self):
        est_zones = PlanGenerator.estimate_pace_zones("6:30", "5:45")
        _, distance = PlanGenerator.pace_and_distance_for_zone("Zone 3", 0.0, est_zones)
        assert distance == 0.0

    def test_is_case_insensitive_on_the_zone_label(self):
        est_zones = PlanGenerator.estimate_pace_zones("6:30", "5:45")
        pace, _ = PlanGenerator.pace_and_distance_for_zone("zone 5", 20.0, est_zones)
        assert pace == f"{est_zones['zone5_pace']} /km"


class TestCalculatePaceZonesFromThreshold:
    def test_computes_5_zone_model_from_threshold_pace(self):
        zones = PlanGenerator.calculate_pace_zones_from_threshold("4:34", model="5_zone")
        assert zones["model"] == "5_zone"
        assert zones["threshold_pace"] == "4:34"
        assert "zone1_pace" in zones
        assert "zone2_pace" in zones
        assert "zone3_pace" in zones
        assert "zone4_pace" in zones
        assert "zone5_pace" in zones
        assert "4:47" in zones["zone4_pace"] or "4:48" in zones["zone4_pace"]

    def test_computes_4_zone_model_from_threshold_pace(self):
        zones = PlanGenerator.calculate_pace_zones_from_threshold("4:34", model="4_zone")
        assert zones["model"] == "4_zone"
        assert zones["threshold_pace"] == "4:34"
        assert "zone1_pace" in zones
        assert "zone2_pace" in zones
        assert "zone3_pace" in zones
        assert "zone4_pace" in zones
        assert "zone5_pace" not in zones
        assert "AeT" in zones["zone_labels"]["Zone 1"]

    def test_estimate_pace_zones_delegates_when_threshold_pace_given(self):
        zones = PlanGenerator.estimate_pace_zones(threshold_pace="4:34", model="4_zone")
        assert zones["model"] == "4_zone"
        assert zones["threshold_pace"] == "4:34"


class TestWarmupCooldownMinutes:
    def test_clamps_to_a_3_to_10_minute_range(self):
        # 20% of 10 = 2, clamped up to the 3-minute floor.
        assert PlanGenerator._warmup_cooldown_minutes(10) == (3, 3)
        # 20% of 100 = 20, clamped down to the 10-minute ceiling.
        assert PlanGenerator._warmup_cooldown_minutes(100) == (10, 10)

    def test_scales_proportionally_within_the_clamp_range(self):
        # 20% of 30 = 6, within [3, 10].
        assert PlanGenerator._warmup_cooldown_minutes(30) == (6, 6)


class TestRuleBasedFallbackDescriptionConsistency:
    """Regression tests: the rule-based fallback generator (used when Gemini is
    unavailable or its retry also fails) used to hardcode Process minutes
    that never matched the day's actual computed duration_minutes -- e.g. a
    Tempo day always said "20-30 minutes" regardless of whether that day's
    duration_minutes was 18 or 50. Now the stated minutes must always sum
    exactly to duration_minutes.
    """

    TEMPO_RE = re.compile(
        r"Warmup (\d+)m\. Run at moderate tempo pace \(Zone 3\) for (\d+) minutes\. Cooldown (\d+)m\."
    )
    INTERVAL_RE = re.compile(
        r"Warmup (\d+)m\. Repeat (\d+)x(\d+) minutes at Zone 4 effort\. "
        r"Recover with (\d+) minutes light jog between\. Cooldown (\d+)m\."
    )
    TAPER_WALK_RE = re.compile(r"Restorative (\d+)-minute light walk or hike on soft trail\.")

    @pytest.mark.asyncio
    async def test_wednesday_and_sunday_descriptions_sum_to_duration_minutes(self, monkeypatch):
        # api_key=None below forces the rule-based fallback deterministically and
        # without any network calls.
        user_profile = {
            "age": 30,
            "max_hr": 185,
            "resting_hr": 60,
            "aet_hr": 135,
            "ant_hr": 165,
            "current_weekly_km": 40.0,
            "zone2_pace_min": "6:30",
            "zone2_pace_max": "5:45",
        }
        race_info = {"name": "Test Race", "goal_type": "finish", "terrain": "trail"}

        # 10 weeks in one block: Peak weeks (6-7) exercise the Interval (even) and Tempo (odd) branches; the
        # taper week (8) adds no hard work any more but still has the Sunday "Active Recovery Walk".
        workouts, _tier = await PlanGenerator.generate_plan_workouts(
            plan_id=1,
            user_profile=user_profile,
            race_info=race_info,
            total_weeks=10,
            api_key=None,  # no Gemini key either -- guarantees the rule-based path
            block_number=1,
            weeks_per_block=10,
        )

        checked = {"tempo": 0, "interval": 0, "taper_walk": 0}
        for wo in workouts:
            desc = wo.get("description") or ""
            duration = wo["duration_minutes"]

            m = self.TEMPO_RE.match(desc)
            if m:
                warmup, main, cooldown = (int(g) for g in m.groups())
                assert warmup + main + cooldown == duration, f"Tempo desc {desc!r} != duration {duration}"
                checked["tempo"] += 1
                continue

            m = self.INTERVAL_RE.match(desc)
            if m:
                warmup, reps, work_per_rep, recovery, cooldown = (int(g) for g in m.groups())
                total = warmup + reps * work_per_rep + (reps - 1) * recovery + cooldown
                assert total == duration, f"Interval desc {desc!r} != duration {duration}"
                checked["interval"] += 1
                continue

            m = self.TAPER_WALK_RE.match(desc)
            if m:
                assert int(m.group(1)) == duration, f"Taper walk desc {desc!r} != duration {duration}"
                checked["taper_walk"] += 1

        assert checked["tempo"] > 0, "no Tempo-session description matched the expected format"
        assert checked["interval"] > 0, "no Interval-session description matched the expected format"
        assert checked["taper_walk"] > 0, "no Taper Active-Recovery-Walk description matched the expected format"

    VI_TEMPO_RE = re.compile(
        r"Khởi động (\d+) phút\. Chạy ở tốc độ tempo vừa phải \(Zone 3\) trong (\d+) phút\. Thả lỏng (\d+) phút\."
    )
    VI_INTERVAL_RE = re.compile(
        r"Khởi động (\d+) phút\. Lặp lại (\d+) lần (\d+) phút ở mức nỗ lực Zone 4\. "
        r"Đi bộ hoặc chạy nhẹ phục hồi (\d+) phút giữa các tổ\. Thả lỏng (\d+) phút\."
    )
    VI_TAPER_WALK_RE = re.compile(r"Đi bộ phục hồi nhẹ nhàng (\d+) phút trên đường trail mềm\.")

    @pytest.mark.asyncio
    async def test_vietnamese_translation_keeps_the_dynamic_minutes_consistent(self):
        # api_key=None below forces the rule-based fallback — no external call.
        user_profile = {
            "age": 30,
            "max_hr": 185,
            "resting_hr": 60,
            "aet_hr": 135,
            "ant_hr": 165,
            "current_weekly_km": 40.0,
            "zone2_pace_min": "6:30",
            "zone2_pace_max": "5:45",
        }
        race_info = {"name": "Test Race", "goal_type": "finish", "terrain": "trail", "lang": "vi"}

        workouts, _tier = await PlanGenerator.generate_plan_workouts(
            plan_id=1,
            user_profile=user_profile,
            race_info=race_info,
            total_weeks=10,
            api_key=None,
            block_number=1,
            weeks_per_block=10,
        )

        checked = {"tempo": 0, "interval": 0, "taper_walk": 0}
        for wo in workouts:
            desc = wo.get("description") or ""
            duration = wo["duration_minutes"]

            m = self.VI_TEMPO_RE.match(desc)
            if m:
                warmup, main, cooldown = (int(g) for g in m.groups())
                assert warmup + main + cooldown == duration, f"vi Tempo desc {desc!r} != duration {duration}"
                checked["tempo"] += 1
                continue

            m = self.VI_INTERVAL_RE.match(desc)
            if m:
                warmup, reps, work_per_rep, recovery, cooldown = (int(g) for g in m.groups())
                total = warmup + reps * work_per_rep + (reps - 1) * recovery + cooldown
                assert total == duration, f"vi Interval desc {desc!r} != duration {duration}"
                checked["interval"] += 1
                continue

            m = self.VI_TAPER_WALK_RE.match(desc)
            if m:
                assert int(m.group(1)) == duration, f"vi Taper walk desc {desc!r} != duration {duration}"
                checked["taper_walk"] += 1

        assert checked["tempo"] > 0, "no Vietnamese Tempo-session description matched the expected format"
        assert checked["interval"] > 0, "no Vietnamese Interval-session description matched the expected format"
        assert (
            checked["taper_walk"] > 0
        ), "no Vietnamese Taper Active-Recovery-Walk description matched the expected format"


class TestResolveElevationAndGrade:
    def test_non_qualifying_type_returns_zero(self):
        result = PlanGenerator.resolve_elevation_and_grade(
            wo={},
            w_type="Strength",
            terrain="trail",
            distance_km=10.0,
            course_elevation_gain_m=1000.0,
            course_distance_km=50.0,
        )
        assert result == (0.0, 0.0)

    def test_non_trail_terrain_returns_zero(self):
        result = PlanGenerator.resolve_elevation_and_grade(
            wo={},
            w_type="Long Run",
            terrain="road",
            distance_km=10.0,
            course_elevation_gain_m=1000.0,
            course_distance_km=50.0,
        )
        assert result == (0.0, 0.0)

    def test_keeps_ai_supplied_values_when_present(self):
        wo = {"elevation_gain_m": 320.0, "grade_percent": 4.2}
        result = PlanGenerator.resolve_elevation_and_grade(
            wo=wo,
            w_type="Long Run",
            terrain="trail",
            distance_km=10.0,
            course_elevation_gain_m=1000.0,
            course_distance_km=50.0,
        )
        assert result == (320.0, 4.2)

    def test_derives_elevation_from_course_ratio_when_ai_omits_it(self):
        # course grade = 1000m / 50km = 20 m/km; distance 10km -> 200m
        result = PlanGenerator.resolve_elevation_and_grade(
            wo={},
            w_type="Easy",
            terrain="trail",
            distance_km=10.0,
            course_elevation_gain_m=1000.0,
            course_distance_km=50.0,
        )
        assert result[0] == 200.0

    def test_derives_grade_from_resolved_elevation_not_course_ratio(self):
        # AI supplies its own elevation_gain_m but not grade_percent: grade must
        # come from THIS elevation_gain_m / distance_km, not the course ratio.
        wo = {"elevation_gain_m": 500.0}
        result = PlanGenerator.resolve_elevation_and_grade(
            wo=wo,
            w_type="Long Run",
            terrain="trail",
            distance_km=10.0,
            course_elevation_gain_m=1000.0,
            course_distance_km=50.0,
        )
        elevation_gain_m, grade_percent = result
        assert elevation_gain_m == 500.0
        assert grade_percent == 5.0  # 500 / (10 * 10)

    def test_returns_zero_when_course_data_missing_and_ai_omits_values(self):
        result = PlanGenerator.resolve_elevation_and_grade(
            wo={},
            w_type="Long Run",
            terrain="trail",
            distance_km=10.0,
            course_elevation_gain_m=None,
            course_distance_km=None,
        )
        assert result == (0.0, 0.0)

    def test_ignores_unparseable_ai_values_and_falls_back(self):
        wo = {"elevation_gain_m": "not-a-number", "grade_percent": None}
        result = PlanGenerator.resolve_elevation_and_grade(
            wo=wo,
            w_type="Easy",
            terrain="trail",
            distance_km=10.0,
            course_elevation_gain_m=1000.0,
            course_distance_km=50.0,
        )
        assert result == (200.0, 2.0)  # 200 / (10*10) = 2.0

    def test_zero_distance_never_divides_by_zero(self):
        result = PlanGenerator.resolve_elevation_and_grade(
            wo={},
            w_type="Easy",
            terrain="trail",
            distance_km=0.0,
            course_elevation_gain_m=1000.0,
            course_distance_km=50.0,
        )
        assert result == (0.0, 0.0)


class TestResolveIntervalSummary:
    def test_tempo_with_explicit_rep_fields_keeps_them(self):
        wo = {"interval_reps": 8, "interval_rep_value": 12, "interval_rep_unit": "s"}
        result = PlanGenerator.resolve_interval_summary(wo, w_type="Tempo")
        assert result == (8, 12.0, "s")

    def test_clean_single_block_seconds(self):
        wo = {"interval_reps": 8, "interval_rep_value": 12, "interval_rep_unit": "s"}
        result = PlanGenerator.resolve_interval_summary(wo, w_type="Interval")
        assert result == (8, 12.0, "s")

    def test_clean_single_block_meters(self):
        wo = {"interval_reps": 5, "interval_rep_value": 400, "interval_rep_unit": "m"}
        result = PlanGenerator.resolve_interval_summary(wo, w_type="Interval")
        assert result == (5, 400.0, "m")

    def test_missing_fields_return_all_none(self):
        wo = {"interval_reps": 8}
        result = PlanGenerator.resolve_interval_summary(wo, w_type="Interval")
        assert result == (None, None, None)

    def test_invalid_unit_returns_all_none(self):
        wo = {"interval_reps": 8, "interval_rep_value": 12, "interval_rep_unit": "laps"}
        result = PlanGenerator.resolve_interval_summary(wo, w_type="Interval")
        assert result == (None, None, None)

    def test_non_numeric_reps_returns_all_none(self):
        wo = {"interval_reps": "several", "interval_rep_value": 12, "interval_rep_unit": "s"}
        result = PlanGenerator.resolve_interval_summary(wo, w_type="Interval")
        assert result == (None, None, None)

    def test_zero_or_negative_values_return_all_none(self):
        wo = {"interval_reps": 0, "interval_rep_value": 12, "interval_rep_unit": "s"}
        result = PlanGenerator.resolve_interval_summary(wo, w_type="Interval")
        assert result == (None, None, None)


class TestParsePaceRange:
    def test_range_string(self):
        assert PlanGenerator.parse_pace_range("6:30 - 5:45 /km") == (6.5, 5.75)

    def test_single_value(self):
        assert PlanGenerator.parse_pace_range("6:00 /km") == (6.0, 6.0)

    def test_empty_is_none(self):
        assert PlanGenerator.parse_pace_range("") is None
        assert PlanGenerator.parse_pace_range(None) is None


class TestResolveTreadmillSettings:
    def test_not_treadmill_relevant_returns_zero_strings(self):
        wo = {"title": "Aerobic Tempo Session"}
        assert PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km") == ("0", "0")

    def test_speed_derived_from_pace_range_not_ai_number(self):
        # The reported bug: pace 6:30-5:45/km but AI said 8.2 kph flat — speed
        # must be recomputed from the pace range at the incline band midpoint.
        wo = {"title": "Tempo on Treadmill", "treadmill_incline": 3.0, "treadmill_speed": 8.2}
        incline, speed = PlanGenerator.resolve_treadmill_settings(wo, "6:30 - 5:45 /km")
        assert incline == "2-4"  # ±1% band around the AI's 3%
        assert speed == "8.1-9.2"  # 60/6.5 and 60/5.75 kph, effort-adjusted at 3%

    def test_incline_band_falls_back_to_outdoor_grade(self):
        wo = {"title": "Trail Long Run", "treadmill_speed": 9.0, "grade_percent": 8.3}
        incline, speed = PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km")
        assert incline == "7.3-9.3"
        assert speed == "7.3"  # single pace → single speed, adjusted at 8.3%

    def test_default_one_percent_rule_when_no_grade_known(self):
        wo = {"title": "Easy Run", "treadmill_speed": 9.0}
        incline, _ = PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km")
        assert incline == "1-2"

    def test_hill_sprint_gets_the_15_percent_ceiling(self):
        wo = {"title": "Hill Sprint Repeats", "treadmill_incline": 1.0}
        incline, speed = PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km")
        assert incline == "15"
        assert speed == "6"  # 10 kph flat, effort-adjusted at 15%

    def test_hill_bound_keyword_matches(self):
        # A Hill Bound session is the same steep-hill power effort as Hill Sprint/Hill
        # Repeat, so it must get the same 15% backstop rather than falling through unmatched.
        wo = {"title": "Hill Bounds", "treadmill_incline": 999.0}
        incline, _ = PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km")
        assert incline == "15"

    def test_no_pace_keeps_ai_speed_but_never_invents_one(self):
        wo = {"title": "Gym Session", "treadmill_incline": 5.0, "treadmill_speed": 7.5}
        incline, speed = PlanGenerator.resolve_treadmill_settings(wo, "")
        assert incline == "4-6"
        assert speed == "7.5"
        wo_no_speed = {"title": "Gym Session", "treadmill_incline": 5.0}
        assert PlanGenerator.resolve_treadmill_settings(wo_no_speed, "")[1] == "0"

    def test_incline_clamped_to_commercial_gym_15_percent_max(self):
        # Commercial gym treadmills max out at 15% grade. If AI emits 25%, it must clamp.
        wo = {"title": "Incline Treadmill Muscular Endurance Session", "treadmill_incline": 25.0}
        incline, _ = PlanGenerator.resolve_treadmill_settings(wo, "6:00 /km")
        assert incline == "14-15"


class TestPostProcessWorkoutsElevation:
    def _run_rule_based(
        self,
        monkeypatch,
        terrain: str,
        course_distance_km: float,
        course_elevation_gain_m: float,
        block_number: int = 1,
    ):
        # Force the rule-based path: generate_plan_workouts gates the Gemini attempt
        # (and its retry) on `_ai_prompt and api_key`, so the api_key=None passed below
        # is what guarantees no external call regardless of this machine's backend/.env.
        user_profile = {
            "current_weekly_km": 30.0,
            "max_hr": 185,
            "resting_hr": 60,
            "aet_hr": 135,
            "ant_hr": 165,
            "zone2_pace_min": "6:30",
            "zone2_pace_max": "5:45",
            "use_treadmill": False,
        }
        race_info = {
            "terrain": terrain,
            "course_distance_km": course_distance_km,
            "course_elevation_gain_m": course_elevation_gain_m,
            "name": "Test Race",
            "date": "2026-12-01",
            "goal_type": "finish",
            "training_environment": "hilly",  # these tests are about the elevation formula; no-venue athletes are below
        }
        # api_key=None additionally skips the Gemini path (plan_generator.py:677:
        # `if _ai_prompt and api_key:`), so together with the monkeypatch above,
        # this call is guaranteed to fall through to the rule-based generator.
        #
        # total_weeks=12 (not a short toy value like 2): get_phase_for_week
        # (plan_generator.py:715-727) always makes the FINAL week "Recovery"
        # (Saturday -> type "Recovery", not "Long Run") and can make earlier
        # weeks "Race Week"/"Taper" depending on W = total_weeks - 1. With
        # total_weeks=12: W=11, num_peak_weeks=2, remaining_weeks=8,
        # num_build_weeks=4, num_base_weeks=4 -- weeks 1-4 are "Base", so
        # requesting block_number=1 (weeks 1-2) reliably lands in Base phase,
        # where Saturday always produces a "Long Run" workout
        # (plan_generator.py:945-959, the `else` branch after the
        # Recovery/Race-Week checks).
        workouts, _tier = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=1,
                user_profile=user_profile,
                race_info=race_info,
                total_weeks=12,
                api_key=None,
                block_number=block_number,
                weeks_per_block=2,
            )
        )
        return workouts

    def test_trail_long_run_gets_nonzero_elevation_and_grade(self, monkeypatch):
        workouts = self._run_rule_based(
            monkeypatch, terrain="trail", course_distance_km=50.0, course_elevation_gain_m=2000.0
        )
        long_runs = [w for w in workouts if w["type"] == "Long Run"]
        assert long_runs, "expected at least one Long Run workout"
        assert all(w["elevation_gain_m"] > 0 for w in long_runs)
        assert all(w["grade_percent"] > 0 for w in long_runs)

    def test_road_terrain_gets_zero_elevation(self, monkeypatch):
        workouts = self._run_rule_based(
            monkeypatch, terrain="road", course_distance_km=50.0, course_elevation_gain_m=2000.0
        )
        long_runs = [w for w in workouts if w["type"] == "Long Run"]
        assert long_runs
        assert all(w["elevation_gain_m"] == 0.0 for w in long_runs)
        assert all(w["grade_percent"] == 0.0 for w in long_runs)

    def test_rest_and_strength_always_zero_even_on_trail(self, monkeypatch):
        workouts = self._run_rule_based(
            monkeypatch, terrain="trail", course_distance_km=50.0, course_elevation_gain_m=2000.0
        )
        non_run_types = [w for w in workouts if w["type"] in ("Rest", "Strength", "Muscular Endurance")]
        assert non_run_types
        assert all(w["elevation_gain_m"] == 0.0 for w in non_run_types)
        assert all(w["grade_percent"] == 0.0 for w in non_run_types)


class TestPostProcessWorkoutsIntervalFields:
    def test_interval_workout_gets_populated_reps_fields(self, monkeypatch):
        # Block 3 = weeks 5-6 of a 12-week plan = Build phase: the base phase is aerobic (no intervals).
        workouts = TestPostProcessWorkoutsElevation()._run_rule_based(
            monkeypatch, terrain="trail", course_distance_km=50.0, course_elevation_gain_m=2000.0, block_number=3
        )
        # the Zone 4 aerobic power intervals carry reps; the Build-phase hill sprints are an unstructured set
        intervals = [w for w in workouts if w["type"] == "Interval" and w["target_zone"] == "Zone 4"]
        assert intervals, "expected at least one Zone 4 Interval workout in a Build-phase block"
        for w in intervals:
            assert isinstance(w["interval_reps"], int) and w["interval_reps"] > 0
            assert isinstance(w["interval_rep_value"], float) and w["interval_rep_value"] > 0
            assert w["interval_rep_unit"] == "min"

    def test_base_phase_has_no_zone_3_or_4_work_in_the_rule_based_schedule(self, monkeypatch):
        workouts = TestPostProcessWorkoutsElevation()._run_rule_based(
            monkeypatch, terrain="trail", course_distance_km=50.0, course_elevation_gain_m=2000.0
        )
        assert {w["phase"] for w in workouts} == {"Base"}
        assert not [
            w for w in workouts if w["type"] in ("Interval", "Tempo") or w["target_zone"] in ("Zone 3", "Zone 4")
        ]

    def test_non_interval_workouts_get_none_interval_fields(self, monkeypatch):
        workouts = TestPostProcessWorkoutsElevation()._run_rule_based(
            monkeypatch, terrain="trail", course_distance_km=50.0, course_elevation_gain_m=2000.0
        )
        non_intervals = [w for w in workouts if w["type"] != "Interval"]
        assert non_intervals
        assert all(w["interval_reps"] is None for w in non_intervals)
        assert all(w["interval_rep_value"] is None for w in non_intervals)
        assert all(w["interval_rep_unit"] is None for w in non_intervals)


class TestGenerateSingleWorkout:
    """Coach co-creation (Phase 6 feedback): duration is main-set-only,
    warm-up/cool-down are added on top; an explicit target_zone or
    target_pace from the coach must never be overridden by the AI; interval
    fields pass straight through untouched. No api_key is passed in these
    tests -- deterministic path only, no network."""

    _PROFILE = {
        "age": 30,
        "max_hr": 190,
        "resting_hr": 50,
        "aet_hr": 150,
        "ant_hr": 172,
        "zone2_pace_min": "6:30",
        "zone2_pace_max": "5:45",
    }

    @pytest.mark.asyncio
    async def test_duration_excludes_warmup_and_cooldown_for_run_types(self):
        wo = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Tempo",
            duration_minutes=30,
            day_of_week="Wednesday",
            week_number=1,
        )
        # main (30) + wu + cd, each clamped [3, 10] -> proportional wu/cd = round(30*0.15) = round(4.5) = 4 each.
        assert wo["duration_minutes"] == 30 + 4 + 4

    @pytest.mark.asyncio
    async def test_strength_and_rest_types_get_no_warmup_cooldown_added(self):
        wo = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Strength",
            duration_minutes=45,
            day_of_week="Sunday",
            week_number=1,
        )
        assert wo["duration_minutes"] == 45
        assert wo["target_pace"] is None
        assert wo["target_hr_range"] is None

    @pytest.mark.asyncio
    async def test_deterministic_fallback_zone_default_is_type_aware(self):
        """No api_key -> deterministic path. An Interval/Tempo session
        defaulting to Zone 2 (an easy-run zone) would look wrong to a coach
        even though nothing downstream is technically broken."""
        interval = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Interval",
            duration_minutes=20,
            day_of_week="Thursday",
            week_number=1,
        )
        assert interval["target_zone"] == "Zone 4"

        tempo = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Tempo",
            duration_minutes=30,
            day_of_week="Wednesday",
            week_number=1,
        )
        assert tempo["target_zone"] == "Zone 3"

        easy = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Easy",
            duration_minutes=30,
            day_of_week="Monday",
            week_number=1,
        )
        assert easy["target_zone"] == "Zone 2"

    @pytest.mark.asyncio
    async def test_coach_supplied_zone_is_never_overridden(self):
        wo = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Easy",
            duration_minutes=40,
            day_of_week="Monday",
            week_number=1,
            target_zone="Zone 4",
        )
        assert wo["target_zone"] == "Zone 4"

    @pytest.mark.asyncio
    async def test_coach_supplied_pace_is_used_verbatim(self):
        wo = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Tempo",
            duration_minutes=30,
            day_of_week="Wednesday",
            week_number=1,
            target_pace="5:00 - 4:50",
        )
        assert wo["target_pace"] == "5:00 - 4:50"

    @pytest.mark.asyncio
    async def test_interval_fields_pass_through_and_are_null_for_other_types(self):
        wo = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Interval",
            duration_minutes=20,
            day_of_week="Thursday",
            week_number=1,
            interval_reps=8,
            interval_rep_value=400.0,
            interval_rep_unit="m",
        )
        assert (wo["interval_reps"], wo["interval_rep_value"], wo["interval_rep_unit"]) == (8, 400.0, "m")

        non_interval = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Easy",
            duration_minutes=20,
            day_of_week="Thursday",
            week_number=1,
            interval_reps=8,
            interval_rep_value=400.0,
            interval_rep_unit="m",
        )
        assert (
            non_interval["interval_reps"],
            non_interval["interval_rep_value"],
            non_interval["interval_rep_unit"],
        ) == (
            None,
            None,
            None,
        )

    @pytest.mark.asyncio
    async def test_details_is_used_verbatim_as_description_when_supplied(self):
        wo = await PlanGenerator.generate_single_workout(
            user_profile=self._PROFILE,
            workout_type="Strength",
            duration_minutes=45,
            day_of_week="Sunday",
            week_number=1,
            details="3x12 lunges, 3x12 step-ups.",
        )
        assert wo["description"] == "3x12 lunges, 3x12 step-ups."


class TestPromptCarriesPerAthleteContext:
    """Every fact that cannot be inferred or regenerated -- the athlete's own profile,
    their scheduling preferences, and the race details -- must reach the model alongside
    the schema. Successor to TestNotebookLmCompactPromptContent, which asserted the same
    invariants against the deleted NotebookLM prompt: the bug it was written for (the
    generic schema pushing per-athlete context off the end of a truncated prompt) is
    exactly the kind that returns quietly, so the assertions now capture the Gemini
    prompt instead of dying with the engine.
    """

    def _capture_prompt(
        self, monkeypatch, user_profile: dict, race_info: dict, block_context: str | None = None
    ) -> str:
        fake_response = MagicMock()
        fake_response.text = "[]"  # empty list -> falls through to rule-based, no real network call
        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = fake_response

        with (
            patch("google.genai.Client", return_value=fake_client),
            patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        ):
            asyncio.run(
                PlanGenerator.generate_plan_workouts(
                    plan_id=1,
                    user_profile=user_profile,
                    race_info=race_info,
                    total_weeks=race_info.get("total_weeks", 16),
                    api_key="test-key",
                    block_number=race_info.get("block_number", 1),
                    weeks_per_block=2,
                    block_context=block_context,
                )
            )
        calls = fake_client.models.generate_content.call_args_list
        assert calls, "Gemini was never called"
        return calls[0].kwargs["contents"]

    def _base_profile_and_race(self) -> tuple[dict, dict]:
        user_profile = {
            "age": 32,
            "current_weekly_km": 40.0,
            "max_hr": 188,
            "resting_hr": 55,
            "aet_hr": 140,
            "ant_hr": 172,
            "use_treadmill": False,
            "zone2_pace_min": "6:15",
            "zone2_pace_max": "5:30",
            "double_session_days": '["Tuesday"]',
            "injury_history": "Mild right knee IT band tightness",
        }
        race_info = {
            "name": "SUM 42km",
            "date": "2026-11-15",
            "terrain": "trail",
            "course_distance_km": 42.0,
            "course_elevation_gain_m": 1800.0,
            "goal_type": "time",
            "target_time_hours": 6.5,
            "preferred_days": '["Monday", "Wednesday", "Friday", "Saturday"]',
            "long_run_day": "Saturday",
            "days_per_week": 4,
            "lang": "en",
        }
        return user_profile, race_info

    def test_schedule_preferences_fully_present_not_truncated(self, monkeypatch):
        user_profile, race_info = self._base_profile_and_race()
        prompt = self._capture_prompt(monkeypatch, user_profile, race_info)

        assert "Scheduling Preferences" in prompt
        assert "Preferred training days: Monday, Wednesday, Friday, Saturday" in prompt
        assert "Rest/off days (assign Rest workouts):" in prompt
        assert "Preferred long run day: Saturday" in prompt
        assert "Double-session days: Tuesday" in prompt
        assert "Injury history: Mild right knee IT band tightness" in prompt

    def test_race_and_date_context_fully_present(self, monkeypatch):
        user_profile, race_info = self._base_profile_and_race()
        prompt = self._capture_prompt(monkeypatch, user_profile, race_info)

        assert "Race Details" in prompt
        assert "SUM 42km" in prompt
        assert "1800.0 m" in prompt
        assert "Target Race Date" in prompt
        assert "Full Plan Length: 16 weeks." in prompt

    def test_schema_fields_still_present_alongside_athlete_context(self, monkeypatch):
        # Guards against fixing the truncation bug by simply dropping schema content —
        # the schema (including fields near its end) must survive too.
        user_profile, race_info = self._base_profile_and_race()
        prompt = self._capture_prompt(monkeypatch, user_profile, race_info)

        assert "OUTPUT CONTRACT" in prompt
        assert "`elevation_gain_m` and `grade_percent`" in prompt
        assert "`treadmill_incline`" in prompt and "`treadmill_speed`" in prompt
        assert "`session_slot`" in prompt  # last field in the schema — the one truncation eats first

    def test_survives_even_with_long_feedback_and_verbose_profile(self, monkeypatch):
        user_profile, race_info = self._base_profile_and_race()
        user_profile["double_session_days"] = '["Tuesday", "Thursday"]'
        user_profile["injury_history"] = (
            "Mild right knee IT band tightness in 2025, also occasional lower back "
            "stiffness after long runs on consecutive weekends"
        )
        race_info["name"] = "Ultra Trail Mont Something Very Long Name 100 Miler"
        race_info["course_distance_km"] = 160.0
        race_info["course_elevation_gain_m"] = 9800.0
        race_info["total_weeks"] = 24
        race_info["block_number"] = 2
        long_feedback = "Athlete reported RPE 8 last week and mentioned right knee pain during downhill sections. " * 20

        prompt = self._capture_prompt(monkeypatch, user_profile, race_info, block_context=long_feedback)

        assert "Preferred long run day: Saturday" in prompt
        assert "Double-session days: Tuesday, Thursday" in prompt
        assert "9800.0 m" in prompt
        assert "session_slot" in prompt
        assert "ATHLETE FEEDBACK FROM PREVIOUS BLOCKS" in prompt


class TestZoneFallbackConsistency:
    """The numeric fallback and the display fallback inside estimate_pace_zones were
    separate literals. A missing Zone 2 bound therefore produced a DISPLAY range of
    6:30-5:45 while the distance maths used the tier default -- the athlete was shown one
    pace and given workouts computed from another."""

    def test_the_displayed_zone2_range_matches_the_pace_the_maths_used(self):
        from services.training_rules import default_zone2_pace

        explicit = PlanGenerator.estimate_pace_zones(*default_zone2_pace())
        implicit = PlanGenerator.estimate_pace_zones(None, None)
        assert implicit == explicit

    def test_the_displayed_range_reflects_the_tier_default_not_a_literal(self):
        slow, fast = None, None
        from services.training_rules import default_zone2_pace

        slow, fast = default_zone2_pace()
        zones = PlanGenerator.estimate_pace_zones(None, None)
        assert zones["zone2_pace"] == f"{slow} - {fast}"


class TestMountainDaySessions:
    def _generate(
        self,
        *,
        mountain="nui_dinh",
        day="Saturday",
        elevation=850,
        use_treadmill=False,
        phase="Build",
        tier=None,
        workout_type="Long Run",
    ):
        import json

        response = MagicMock()
        response.text = json.dumps(
            [
                {
                    "week_number": 1,
                    "day_of_week": day,
                    "phase": phase,
                    "type": workout_type,
                    "title": workout_type,
                    "duration_minutes": 130,
                    "target_zone": "Zone 2",
                    "elevation_gain_m": elevation,
                }
            ]
        )
        client = MagicMock()
        client.models.generate_content.return_value = response
        with (
            patch("google.genai.Client", return_value=client),
            patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        ):
            workouts, _ = asyncio.run(
                PlanGenerator.generate_plan_workouts(
                    plan_id=1,
                    user_profile={"threshold_pace": "3:55", "aet_hr": 134, "ant_hr": 163, "current_weekly_km": 60},
                    race_info={
                        "training_mountain": mountain,
                        "athlete_tier": tier,
                        "mountain_days": ["Saturday"],
                        "terrain": "trail",
                        "use_treadmill": use_treadmill,
                        "plan_start_date": "2026-10-12",
                    },
                    total_weeks=12,
                    api_key="test-key",
                    weeks_per_block=2,
                )
            )
        assert client.models.generate_content.called
        return workouts[0]

    def test_weekday_city_easy_run_keeps_flat_pace(self):
        # Tuesday is not a mountain day: the athlete runs in the city, not on Núi Dinh.
        wo = self._generate(day="Tuesday", workout_type="Easy", elevation=0)
        slower, _ = PlanGenerator.parse_pace_range(wo["target_pace"])
        assert slower < 6.0
        assert wo["elevation_gain_m"] == 0

    def test_nui_dinh_long_run_uses_minimum_and_mountain_rate(self):
        wo = self._generate()
        assert wo["duration_minutes"] == 180
        assert wo["mountain_mode"] == "mountain"
        assert wo["target_pace"] == "8:26 - 7:44 /km"
        assert abs(wo["elevation_gain_m"] - wo["distance_km"] * 60) < 1

    def test_no_mountain_or_course_uses_ai_climb_rate(self):
        wo = self._generate(mountain=None)
        assert PlanGenerator.parse_pace_range(wo["target_pace"])[0] > 4.9
        assert wo["elevation_gain_m"] > 0

    def test_other_day_keeps_duration(self):
        assert self._generate(day="Tuesday")["duration_minutes"] == 130

    def test_treadmill_uses_flat_pace(self):
        wo = self._generate(use_treadmill=True)
        _, expected_speed = PlanGenerator.resolve_treadmill_settings(wo, "4:54 - 4:30 /km", True, max_incline=15)
        assert wo["treadmill_speed"] == expected_speed

    def test_climb_rate_fallback_order(self):
        from services.training_venues import Venues

        assert PlanGenerator.resolve_climb_rate(Venues(training_mountain="nui_dinh"), 2000, 50, 850, 27.7) == 60
        assert PlanGenerator.resolve_climb_rate(Venues(), 2000, 50, 850, 27.7) == 40
        assert PlanGenerator.resolve_climb_rate(Venues(), None, None, 850, 25) == 34
        assert PlanGenerator.resolve_climb_rate(Venues(), None, None, None, 25) is None

    def test_taper_chills_at_zone1_and_is_exempt_from_the_trip_minimum(self):
        wo = self._generate(phase="Taper")
        assert wo["mountain_mode"] == "chill"
        assert wo["target_zone"] == "Zone 1"
        assert wo["duration_minutes"] == 130  # the taper session as planned, not raised to the 180 min minimum
        assert wo["target_hr_range"]

    def test_race_week_skips_to_flat_city_session(self):
        wo = self._generate(phase="Race Week")
        assert wo["mountain_mode"] == "skip"
        assert wo["duration_minutes"] == 60
        assert wo["elevation_gain_m"] == wo["grade_percent"] == 0
        assert wo["target_pace"] == "4:54 - 4:30 /km"

    def test_beginner_build_week_skips(self):
        assert self._generate(tier="beginner")["mountain_mode"] == "skip"

    def test_dalat_chill_preserves_generated_duration(self):
        assert self._generate(mountain="dalat", phase="Taper")["duration_minutes"] == 130

    def test_generated_mountain_keeps_original_rate(self):
        assert self._generate(mountain=None)["mountain_climb_rate"] > 0


class TestRuleBasedFallbackFollowsDoctrine:
    """The fallback is the safety net when Gemini is down: it must keep the lint's hard rules
    (spacing, hard-day adjacency, share, session length, the athlete's long-run day and day count)
    across preference sets, tiers and race lengths. Progression/back-to-back codes are left out:
    a 3-day athlete cannot avoid a weekend pair, and capacity-bound weeks cannot ramp."""

    HARD_RULES = {"ME_SPACING", "HARD_ADJACENT", "LONG_SHARE", "SESSION_TOO_LONG", "LONG_RUN_DAY", "DAYS_SHORT"}
    ATHLETES = [
        (65, ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "Sunday", 6),
        (40, ["Tuesday", "Thursday", "Saturday", "Sunday"], "Sunday", 4),
        (25, ["Tuesday", "Saturday", "Sunday"], "Sunday", 3),
        (100, None, None, 5),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("weekly_km,days,long_day,dpw", ATHLETES)
    @pytest.mark.parametrize("distance,gain,weeks", [(56.4, 2946, 12), (104.2, 5533, 13)])
    async def test_no_hard_rule_is_broken(self, weekly_km, days, long_day, dpw, distance, gain, weeks):
        from services import plan_lint
        from services.athlete_tier import get_profile

        profile = {
            "max_hr": 185,
            "resting_hr": 55,
            "aet_hr": 145,
            "ant_hr": 168,
            "zone2_pace_min": "6:30",
            "zone2_pace_max": "5:45",
            "current_weekly_km": float(weekly_km),
        }
        race = {
            "terrain": "trail",
            "course_distance_km": distance,
            "course_elevation_gain_m": gain,
            "name": "Race",
            "date": (date(2026, 10, 19) + timedelta(weeks=weeks - 2, days=5)).isoformat(),
            "plan_start_date": "2026-10-19",  # a Monday: the fallback's week 1 depends on the start weekday
            "goal_type": "finish",
            "preferred_days": days,
            "long_run_day": long_day,
            "days_per_week": dpw,
        }
        workouts, tier = await PlanGenerator.generate_plan_workouts(
            plan_id=1,
            user_profile=profile,
            race_info=race,
            total_weeks=weeks,
            api_key=None,
            block_number=1,
            weeks_per_block=weeks,
        )
        found = plan_lint.lint_weeks(
            workouts,
            {w["week_number"] for w in workouts},
            get_profile(tier),
            plan_lint.Prefs(long_run_day=long_day, days_per_week=dpw),
        )
        assert {i.code for i in found} & self.HARD_RULES == set(), [(i.week, i.code) for i in found]
        base = [w for w in workouts if w["phase"] == "Base"]
        assert not [w for w in base if w["target_zone"] in ("Zone 3", "Zone 4")]


class TestGoalDemandsShapeGeneration:
    """The goal's demands (pace, climbing, time on feet) reach the generator instead of one goal sentence."""

    PROFILE = {
        "max_hr": 185,
        "resting_hr": 55,
        "aet_hr": 145,
        "ant_hr": 168,
        "zone2_pace_min": "6:30",
        "zone2_pace_max": "5:45",
        "current_weekly_km": 65.0,
    }
    RACE = {
        "name": "VHT 100K",
        "date": "2027-01-09",
        "terrain": "trail",
        "course_distance_km": 104.2,
        "course_elevation_gain_m": 5533,
        "goal_type": "time",
        "target_time_hours": 14.67,
        "lang": "en",
    }

    def _prompt(self, race_info, cutoff=29.0):
        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = MagicMock(text="[]")
        with (
            patch("google.genai.Client", return_value=fake_client),
            patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        ):
            asyncio.run(
                PlanGenerator.generate_plan_workouts(
                    plan_id=1,
                    user_profile=self.PROFILE,
                    race_info=race_info,
                    total_weeks=12,
                    api_key="test-key",
                    cutoff_time_hours=cutoff,
                    block_number=1,
                    weeks_per_block=2,
                )
            )
        return fake_client.models.generate_content.call_args_list[0].kwargs["contents"]

    def test_prompt_carries_the_demand_block_and_a_time_target_beats_the_cutoff_sentence(self, monkeypatch):
        monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
        prompt = self._prompt(self.RACE)
        assert "Goal demands (target, 14h40)" in prompt
        assert "needing about 377 m D+/h" in prompt
        assert "the longest session should reach about 300 min" in prompt
        assert "Just to Finish" not in prompt

    def test_a_finish_goal_keeps_the_cutoff_sentence_and_adds_the_demands(self, monkeypatch):
        monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
        prompt = self._prompt({**self.RACE, "goal_type": "finish", "target_time_hours": None})
        assert "Just to Finish" in prompt and "Goal demands (cutoff_safe" in prompt

    def test_training_mountain_reaches_the_prompt(self, monkeypatch):
        monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
        prompt = self._prompt({**self.RACE, "training_mountain": "chau_thoi", "training_environment": "flat"})
        assert "Training mountain offers 28 m D+/km" in prompt

    def test_flag_off_keeps_the_old_sentence(self, monkeypatch):
        monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", False)
        prompt = self._prompt({**self.RACE, "goal_type": "time"})
        assert "Goal demands" not in prompt

    def test_no_course_means_no_block(self, monkeypatch):
        monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
        prompt = self._prompt({**self.RACE, "course_distance_km": None})
        assert "Goal demands" not in prompt

    @pytest.mark.asyncio
    async def test_fallback_ramps_volume_toward_the_demand_and_reaches_the_long_run_target(self, monkeypatch):
        from services import goal_demands, plan_lint
        from services.athlete_tier import get_profile

        monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
        race = {**self.RACE, "preferred_days": None, "long_run_day": "Saturday", "days_per_week": 6, "lang": "en"}
        workouts, tier = await PlanGenerator.generate_plan_workouts(
            plan_id=1,
            user_profile={**self.PROFILE, "current_weekly_km": 100.0},
            race_info=race,
            total_weeks=26,
            api_key=None,
            cutoff_time_hours=29.0,
            block_number=1,
            weeks_per_block=26,
        )
        d = goal_demands.compute(104.2, 5533, 14.67, 29)
        issues = plan_lint.lint_weeks(
            workouts,
            {w["week_number"] for w in workouts},
            get_profile(tier),
            plan_lint.Prefs(long_run_day="Saturday", days_per_week=6, demands=d, flat_only=True),
        )
        assert {i.code for i in issues} & {"TIME_ON_FEET", "SPECIFICITY_LATE", "ME_SPACING", "HARD_ADJACENT"} == set()


class TestNoInventedClimbing:
    """An athlete with no hills, mountain days or mountain declared gets no invented climbing on outdoor runs."""

    PROFILE = {"max_hr": 185, "resting_hr": 55, "aet_hr": 145, "ant_hr": 168, "zone2_pace_min": "6:30",
               "zone2_pace_max": "5:45", "current_weekly_km": 50.0}  # fmt: skip

    def _plan(self, **venue):
        race = {"name": "Steep 100K", "date": "2027-03-27", "plan_start_date": "2026-10-19", "terrain": "trail",
                "course_distance_km": 104.2, "course_elevation_gain_m": 5533, "goal_type": "finish",
                "training_environment": "flat", "days_per_week": 6, **venue}  # fmt: skip
        workouts, _ = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=1,
                user_profile=self.PROFILE,
                race_info=race,
                total_weeks=20,
                api_key=None,
                block_number=1,
                weeks_per_block=20,
            )  # fmt: skip
        )
        return [w for w in workouts if w["type"] in ("Easy", "Long Run", "Aerobic Capacity", "Tempo")]

    def test_flat_with_nothing_declared_has_zero_gain_and_grade_outdoors(self):
        runs = self._plan()
        assert runs and all(not w["elevation_gain_m"] and not w["grade_percent"] for w in runs)

    def test_a_declared_mountain_keeps_its_climbing(self):
        runs = self._plan(training_mountain="nui_dinh", mountain_days='["Saturday", "Sunday"]')
        assert any(w["elevation_gain_m"] > 0 for w in runs if w["type"] == "Long Run")

    def test_hills_nearby_keep_their_climbing(self):
        runs = self._plan(training_environment="hilly")
        assert any(w["elevation_gain_m"] > 0 for w in runs)

    def test_the_prompt_says_there_is_no_outdoor_climbing(self):
        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = MagicMock(text="[]")
        with (
            patch("google.genai.Client", return_value=fake_client),
            patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        ):
            asyncio.run(
                PlanGenerator.generate_plan_workouts(
                    plan_id=1,
                    user_profile=self.PROFILE,
                    race_info={
                        "name": "Steep 100K",
                        "date": "2027-03-27",
                        "plan_start_date": "2026-10-19",
                        "terrain": "trail",
                        "course_distance_km": 104.2,
                        "course_elevation_gain_m": 5533,
                        "goal_type": "finish",
                        "training_environment": "flat",
                        "days_per_week": 6,
                    },
                    total_weeks=20,
                    api_key="k",
                    block_number=1,
                    weeks_per_block=1,
                )  # fmt: skip
            )
        prompt = fake_client.models.generate_content.call_args_list[0].kwargs["contents"]
        assert "NO OUTDOOR CLIMBING" in prompt


class TestPersonaFindings:
    def test_vietnamese_sanitizer_replaces_banned_words_but_keeps_stroke_volume(self):
        from services.plan_generator import sanitize_vi

        text = "Tăng thể tích hiếu khí, tối ưu hóa mỡ, chạy nước rút bứt phá, giáo án chuyên sâu; thể tích tâm thu."
        out = sanitize_vi(text)
        assert "khối lượng hiếu khí" in out and "cải thiện mỡ" in out and "tăng tốc" in out
        assert "lịch tập chuyên biệt" in out and "thể tích tâm thu" in out
        assert not any(b in out for b in ("tối ưu hóa", "bứt phá", "chuyên sâu", "giáo án"))

    def test_phase_labels_are_structural(self):
        phases = [PlanGenerator.phase_for_week(w, 12) for w in range(1, 13)]
        assert phases[-1] == "Recovery" and phases[-2] == "Race Week" and phases[-3] == "Taper"
        assert phases[0] == "Base" and "Build" in phases and phases.count("Taper") == 2  # 12+ weeks: two-step taper
        short = [PlanGenerator.phase_for_week(w, 8) for w in range(1, 9)]
        assert short.count("Taper") == 1 and short[0] == "Base"

    def test_a_hard_session_in_a_recovery_week_becomes_an_easy_run_and_the_models_phase_label_is_overwritten(self):
        import json

        prior = [
            {"week_number": 1, "day_of_week": d, "type": "Easy", "duration_minutes": 100.0, "phase": "Base"}
            for d in ("Tuesday", "Thursday", "Saturday")
        ]
        reply = [
            {"week_number": 2, "day_of_week": "Tuesday", "title": "Easy", "type": "Easy", "duration_minutes": 50, "target_zone": "Zone 2", "phase": "Taper", "description": "x"},
            {"week_number": 2, "day_of_week": "Thursday", "title": "Sub-Threshold Tempo", "type": "Tempo", "duration_minutes": 50, "target_zone": "Zone 3", "phase": "Taper", "description": "x"},
            {"week_number": 2, "day_of_week": "Saturday", "title": "Long", "type": "Long Run", "duration_minutes": 80, "target_zone": "Zone 2", "phase": "Taper", "description": "x"},
        ]  # fmt: skip
        client = MagicMock()
        client.models.generate_content.return_value = MagicMock(text=json.dumps(reply))
        profile = {
            "max_hr": 185,
            "resting_hr": 55,
            "aet_hr": 145,
            "ant_hr": 168,
            "zone2_pace_min": "6:30",
            "zone2_pace_max": "5:45",
            "current_weekly_km": 40.0,
        }
        with (
            patch("google.genai.Client", return_value=client),
            patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
            patch("services.plan_generator.get_plan_workouts", return_value=prior),
        ):
            workouts, _ = asyncio.run(
                PlanGenerator.generate_plan_workouts(
                    plan_id=5,
                    user_profile=profile,
                    race_info={
                        "name": "R",
                        "date": "2027-03-27",
                        "plan_start_date": "2026-10-19",
                        "terrain": "road",
                        "goal_type": "finish",
                        "days_per_week": 3,
                    },
                    total_weeks=12,
                    api_key="k",
                    block_number=2,
                    weeks_per_block=1,
                )  # fmt: skip
            )
        thursday = next(w for w in workouts if w["day_of_week"] == "Thursday")
        assert (
            thursday["type"] == "Easy" and thursday["target_zone"] == "Zone 2" and "recovery week" in thursday["title"]
        )
        assert {w["phase"] for w in workouts} == {"Base"}  # the model's "Taper" label is not trusted


class TestLanguageDetection:
    def test_place_names_do_not_switch_an_english_plan_to_vietnamese(self):
        from services.plan_generator import has_vietnamese_text, narrative_lang_instruction

        info = {"lang": "en", "name": "Vietnam Highlands Trail by UTMB"}
        block = "Week 3: Long Run at Núi Dinh (Núi Chứa Chan next), coach evaluation: on track."
        assert not has_vietnamese_text(block, info)
        assert narrative_lang_instruction(info, block) == "Respond in English."
        assert (
            narrative_lang_instruction({"lang": "en", "name": "Đà Lạt Ultra"}, "race Đà Lạt Ultra long run")
            == "Respond in English."
        )

    def test_vietnamese_prose_still_switches_the_language(self):
        from services.plan_generator import has_vietnamese_text

        assert has_vietnamese_text("Tuần này tôi mệt, đau gối nhẹ", {"name": "x"})
        assert has_vietnamese_text("Chạy Núi Dinh nhưng tôi bận việc", {})  # prose around a place name still counts
