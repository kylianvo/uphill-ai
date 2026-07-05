"""Pure static-method tests for PlanGenerator's pace math.

parse_pace_to_decimal / decimal_to_pace_str / estimate_pace_zones are used
throughout onboarding and plan generation. Pace strings ("MM:SS") <-> decimal
minutes conversions are a classic off-by-format bug class, the same flavor
as the plan_start_date regression this suite exists to catch.
"""

import re

import pytest

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
    """Regression tests: the rule-based fallback generator (used when
    NotebookLM/Gemini are both unavailable) used to hardcode Process minutes
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
        # Force the rule-based fallback deterministically and without any
        # network calls -- don't rely on the environment's real NotebookLM/
        # Gemini config (whatever it happens to be) to land here.
        from config import settings

        monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "")
        monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", "")

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

        # 8 weeks in one block: Base(1-2)/Build(3-4)/Peak(5)/Taper(6)/Race Week(7)/Recovery(8)
        # -- week 5 (odd) exercises the Tempo branch, week 6 (even) exercises
        # both the Interval branch and the Sunday Taper "Active Recovery Walk".
        workouts = await PlanGenerator.generate_plan_workouts(
            plan_id=1,
            user_profile=user_profile,
            race_info=race_info,
            total_weeks=8,
            api_key=None,  # no Gemini key either -- guarantees the rule-based path
            block_number=1,
            weeks_per_block=8,
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
    async def test_vietnamese_translation_keeps_the_dynamic_minutes_consistent(self, monkeypatch):
        from config import settings

        monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "")
        monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", "")

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

        workouts = await PlanGenerator.generate_plan_workouts(
            plan_id=1,
            user_profile=user_profile,
            race_info=race_info,
            total_weeks=8,
            api_key=None,
            block_number=1,
            weeks_per_block=8,
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
