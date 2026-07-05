"""Pure static-method tests for PlanGenerator's pace math.

parse_pace_to_decimal / decimal_to_pace_str / estimate_pace_zones are used
throughout onboarding and plan generation. Pace strings ("MM:SS") <-> decimal
minutes conversions are a classic off-by-format bug class, the same flavor
as the plan_start_date regression this suite exists to catch.
"""

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
        with_explicit_defaults = PlanGenerator.estimate_pace_zones("6:30", "5:45")
        with_none = PlanGenerator.estimate_pace_zones(None, None)
        assert with_none == with_explicit_defaults

    def test_missing_aet_ant_hr_falls_back_to_baseline_ratios(self):
        # scale=1.0 reproduces the original fixed ratios: Z1=1.15x, Z3=0.90x,
        # Z4=0.82x, Z5=0.73x of the Zone 2 bounds (both slow and fast ends).
        zone2_min, zone2_max = "6:30", "5:45"
        z2_min_dec = PlanGenerator.parse_pace_to_decimal(zone2_min)
        z2_max_dec = PlanGenerator.parse_pace_to_decimal(zone2_max)

        zones = PlanGenerator.estimate_pace_zones(zone2_min, zone2_max)  # no aet_hr/ant_hr
        z4_slow_str, z4_fast_str = zones["zone4_pace"].split(" - ")

        assert z4_slow_str == PlanGenerator.decimal_to_pace_str(z2_min_dec * 0.82)
        assert z4_fast_str == PlanGenerator.decimal_to_pace_str(z2_max_dec * 0.82)

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
