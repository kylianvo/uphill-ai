"""Tier derivation and the rules block assembled from it.

The bug this exists to prevent: one rules block, written for a mountain ultrarunner,
served to every athlete. A beginner who could jog two minutes was told to keep her ME
session 48 hours clear of the weekend long run, and an elite got a novice's progression
cap. Special-casing beginners would only relocate that, so tier is a dimension.
"""

import pytest

from services.athlete_tier import (
    BEGINNER,
    DEFAULT_TIER,
    ELITE,
    NOVICE,
    RECREATIONAL,
    SUB_ELITE,
    TIER_ORDER,
    TIER_PROFILES,
    derive_tier,
    get_profile,
    resolve_tier,
)
from services.plan_rules import build_rules_block


class TestTierProfiles:
    def test_every_tier_in_the_order_has_a_profile(self):
        assert set(TIER_ORDER) == set(TIER_PROFILES)

    def test_the_volume_bands_are_contiguous_and_ascending(self):
        """A gap would leave some weekly volume unclassifiable; an overlap would make
        derivation depend on dict iteration order."""
        bands = [TIER_PROFILES[k] for k in TIER_ORDER]
        for lower, upper in zip(bands, bands[1:]):
            assert lower.weekly_km_max == upper.weekly_km_min, f"{lower.key} -> {upper.key} band mismatch"
        assert bands[0].weekly_km_min == 0.0
        assert bands[-1].weekly_km_max is None, "the top tier must be unbounded"

    def test_only_the_beginner_tier_uses_walk_run(self):
        for key, profile in TIER_PROFILES.items():
            assert profile.uses_walk_run == (key == BEGINNER)

    def test_intensity_and_me_blocks_are_withheld_from_the_lowest_tiers(self):
        assert not TIER_PROFILES[BEGINNER].allows_intensity
        assert not TIER_PROFILES[NOVICE].allows_intensity
        assert TIER_PROFILES[RECREATIONAL].allows_intensity
        assert not TIER_PROFILES[BEGINNER].allows_me_blocks
        assert TIER_PROFILES[SUB_ELITE].allows_me_blocks

    def test_weekday_session_bands_never_regress_as_the_tier_rises(self):
        lows = [TIER_PROFILES[k].weekday_minutes[0] for k in TIER_ORDER]
        assert lows == sorted(lows)

    def test_the_long_run_share_cap_tightens_as_volume_rises(self):
        """A 30% long run is a different session at 10 km/week than at 120."""
        caps = [TIER_PROFILES[k].long_run_share_cap for k in TIER_ORDER]
        assert caps == sorted(caps, reverse=True)


class TestDeriveTier:
    def test_the_start_running_goal_beats_a_stale_volume_number(self):
        """current_weekly_km defaults to 30.0, which would otherwise read as
        recreational for someone who has never run."""
        assert derive_tier(goal_type="start_running", current_weekly_km=30.0) == BEGINNER

    def test_someone_who_cannot_jog_ten_minutes_is_a_beginner_whatever_else_says(self):
        assert derive_tier(goal_type="finish", current_weekly_km=40.0, max_continuous_jog_min=4) == BEGINNER

    @pytest.mark.parametrize(
        "weekly_km,expected",
        [
            (5.0, BEGINNER),
            (14.9, BEGINNER),
            (15.0, NOVICE),
            (29.9, NOVICE),
            (30.0, RECREATIONAL),
            (59.9, RECREATIONAL),
            (60.0, SUB_ELITE),
            (99.9, SUB_ELITE),
            (100.0, ELITE),
            (180.0, ELITE),
        ],
    )
    def test_weekly_volume_selects_the_band(self, weekly_km, expected):
        assert derive_tier(current_weekly_km=weekly_km) == expected

    def test_unknown_volume_falls_back_to_the_default_rather_than_the_easiest_tier(self):
        """Defaulting everyone to beginner would hand a walk-run plan to a trained
        runner who simply hasn't filled in their profile."""
        assert derive_tier(current_weekly_km=None) == DEFAULT_TIER
        assert derive_tier(current_weekly_km=0) == DEFAULT_TIER
        assert DEFAULT_TIER != BEGINNER

    def test_a_proven_long_run_promotes_but_never_demotes(self):
        assert derive_tier(current_weekly_km=8.0, historical_max_distance_km=30.0) == NOVICE
        # It must not pull a genuine elite down toward the long run's own band.
        assert derive_tier(current_weekly_km=120.0, historical_max_distance_km=30.0) == ELITE

    def test_an_explicit_start_running_goal_outranks_a_long_run_history(self):
        assert derive_tier(goal_type="start_running", historical_max_distance_km=42.0) == BEGINNER


class TestResolveTier:
    def test_an_explicit_override_wins(self):
        assert resolve_tier(explicit_tier="elite", current_weekly_km=10.0) == ELITE

    def test_an_unrecognised_override_is_ignored_rather_than_honoured(self):
        """A typo must degrade to derivation, not silently select the default."""
        assert resolve_tier(explicit_tier="ultra-elite", current_weekly_km=8.0) == BEGINNER

    def test_no_override_derives(self):
        assert resolve_tier(explicit_tier=None, goal_type="start_running") == BEGINNER

    def test_override_is_case_and_whitespace_insensitive(self):
        assert resolve_tier(explicit_tier="  Sub_Elite  ", current_weekly_km=5.0) == SUB_ELITE


class TestGetProfile:
    def test_unknown_tier_degrades_to_the_default_profile(self):
        assert get_profile("nonsense").key == DEFAULT_TIER
        assert get_profile(None).key == DEFAULT_TIER


class TestRulesBlock:
    def test_a_beginner_gets_walk_run_rules_and_none_of_the_ultra_apparatus(self):
        rules = build_rules_block(get_profile(BEGINNER), max_continuous_jog_min=3)

        assert "run/walk intervals" in rules
        assert "longest UNBROKEN jog" in rules
        assert "3 minutes" in rules  # their actual current ability is quoted back

        # The ultrarunner apparatus that used to fire at beginners regardless. These are
        # PRESCRIPTIONS -- the bare term "Muscular Endurance" is deliberately still
        # present below, in the rule that forbids it.
        for leaked in (
            "Muscular Endurance (ME) Directives",
            "48-Hour Buffer",
            "Summit Water Dump",
            "eccentric downhill",
            "weighted pack",
            "carbohydrates per hour",
            "Peak Phase",
            "Taper Phase",
        ):
            assert leaked not in rules, f"beginner rules leaked: {leaked}"

        # ...and ME is named only to rule it out.
        assert "Muscular Endurance sessions of any kind" in rules

    def test_a_beginner_without_a_recorded_jog_time_is_told_where_to_start(self):
        rules = build_rules_block(get_profile(BEGINNER), max_continuous_jog_min=None)
        assert "not recorded yet" in rules
        # The KB's stated starting ratio, not an invented one.
        assert "1 min jog / 1 min walk" in rules

    def test_beginner_rules_forbid_intensity_explicitly(self):
        rules = build_rules_block(get_profile(BEGINNER))
        assert "NO Zone 3, 4 or 5" in rules

    def test_beginner_effort_cues_are_the_kb_field_tests_not_device_numbers(self):
        """A new runner's zones are estimates, so the KB prescribes ventilatory cues."""
        rules = build_rules_block(get_profile(BEGINNER))
        assert "COMPLETE sentences" in rules
        assert "NOSE breathing" in rules
        assert "stumblingly slow" in rules

    def test_beginner_rules_carry_the_kb_progression_ladder(self):
        rules = build_rules_block(get_profile(BEGINNER))
        assert "1 min jog / 1 min walk" in rules
        assert "10 min jog /" in rules and "3 min walk" in rules
        # Progression advances the JOG specifically -- an earlier placeholder wrongly
        # allowed any one of three variables to move.
        assert "advance the JOG duration" in rules or "advance the JOG" in rules

    def test_beginner_rules_carry_the_kb_readiness_criterion(self):
        rules = build_rules_block(get_profile(BEGINNER))
        assert "Aerobic Threshold" in rules
        assert "settle" in rules  # HR must settle within the walk break

    def test_beginner_rest_days_prescribe_non_impact_work_not_nothing(self):
        """The KB is explicit that alternate days carry non-impact aerobic volume."""
        rules = build_rules_block(get_profile(BEGINNER))
        assert "NON-IMPACT" in rules
        assert "consecutive days" in rules
        for modality in ("cycling", "elliptical", "swimming"):
            assert modality in rules

    def test_beginner_injury_guardrails_name_the_kb_warning_signs(self):
        rules = build_rules_block(get_profile(BEGINNER))
        assert "10-15 bpm" in rules
        assert "dead" in rules
        assert "A-F" in rules  # the session-grading threshold

    def test_recreational_keeps_the_muscular_endurance_framework(self):
        rules = build_rules_block(get_profile(RECREATIONAL))
        assert "Muscular Endurance (ME) Directives" in rules
        assert "48-Hour Buffer" in rules
        assert "run/walk intervals" not in rules

    def test_novice_gets_neither_walk_run_nor_me_blocks(self):
        rules = build_rules_block(get_profile(NOVICE))
        assert "run/walk intervals" not in rules
        assert "48-Hour Buffer" not in rules
        assert "do not prescribe them" in rules or "do NOT prescribe" in rules

    @pytest.mark.parametrize("tier", TIER_ORDER)
    def test_every_tier_states_who_it_is_writing_for(self, tier):
        rules = build_rules_block(get_profile(tier))
        assert "ATHLETE TIER:" in rules
        assert TIER_PROFILES[tier].label in rules

    def test_the_weekly_cap_is_uniform_but_the_annual_cap_separates_tiers(self):
        """KB-corrected. An earlier revision guessed elites progress more slowly week to
        week; the doctrine caps everyone at 7-10% weekly, and differentiates ANNUALLY --
        25%/year for a beginner against 10%/year once trained."""
        elite = build_rules_block(get_profile(ELITE))
        recreational = build_rules_block(get_profile(RECREATIONAL))
        beginner = build_rules_block(get_profile(BEGINNER))

        assert "10% week-over-week" in elite
        assert "10% week-over-week" in recreational
        assert "10% per year" in elite
        assert "15% per year" in recreational
        # The beginner block states its weekly cap in its own words.
        assert "10%" in beginner

    def test_intensity_distribution_tightens_toward_ninety_ten_at_the_top(self):
        recreational = build_rules_block(get_profile(RECREATIONAL))
        elite = build_rules_block(get_profile(ELITE))
        assert "85% of total" in recreational
        assert "90% of total" in elite
        assert "TIME IN ZONE" in elite

    def test_the_zone4_weekly_cap_applies_only_where_intensity_does(self):
        assert "ZONE 4 HARD CAP" in build_rules_block(get_profile(RECREATIONAL))
        assert "40 minutes" in build_rules_block(get_profile(ELITE))
        assert "ZONE 4 HARD CAP" not in build_rules_block(get_profile(BEGINNER))
        assert "ZONE 4 HARD CAP" not in build_rules_block(get_profile(NOVICE))

    def test_high_volume_doctrine_reaches_only_the_top_two_tiers(self):
        """Double-threshold spacing and Zone 1 substitution are meaningless below the
        volume at which they bind, and would be actively wrong advice."""
        for tier in (SUB_ELITE, ELITE):
            rules = build_rules_block(get_profile(tier))
            assert "Double-Threshold Days" in rules
            assert "8-12 hours" in rules
            assert "Zone 1 Substitution" in rules
            assert "daily repeatability test" in rules
        for tier in (BEGINNER, NOVICE, RECREATIONAL):
            rules = build_rules_block(get_profile(tier))
            assert "Double-Threshold Days" not in rules
            assert "Zone 1 Substitution" not in rules

    def test_the_weekday_band_follows_the_tier(self):
        beginner = build_rules_block(get_profile(BEGINNER))
        recreational = build_rules_block(get_profile(RECREATIONAL))
        assert "20-45 minutes" in beginner
        assert "45-75 minutes" in recreational
