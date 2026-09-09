"""Zone 2 pace defaults: one source of truth, and a stored value always wins.

Regression cover for the production bug where a beginner on a walk-to-run plan was
shown 6:30-5:45 /km. Two mechanisms combined:

  1. the beginner default existed only inside the onboarding handler, while the pair
     "6:30"/"5:45" was hardcoded at nine other call sites; and
  2. UpdateProfileRequest declares the pace fields Optional-with-None, and
     `request.dict()` includes unset fields, so `data.get("zone2_pace_min", "6:30")`
     returned None and the writer blanked the column -- after which every reader's
     `or "6:30"` produced a trained runner's zones.

Because distance_km is recomputed as duration / zone2_pace_mid, a wrong zone here
silently falsifies every distance, pace and treadmill speed shown to the athlete.
"""

import pytest

from services.athlete_tier import BEGINNER, DEFAULT_TIER, ELITE, TIER_ORDER, TIER_PROFILES
from services.plan_generator import PlanGenerator
from services.training_rules import default_zone2_pace, pace_tier_for_goal, resolve_zone2_pace


class TestPaceTierForGoal:
    def test_start_running_is_the_beginner_tier(self):
        assert pace_tier_for_goal("start_running") == BEGINNER

    @pytest.mark.parametrize("goal", ["finish", "time", "optimal", None, ""])
    def test_everything_else_falls_back_to_the_default_tier(self, goal):
        assert pace_tier_for_goal(goal) == DEFAULT_TIER

    def test_an_explicit_tier_wins_over_the_goal(self):
        assert pace_tier_for_goal("finish", athlete_tier="elite") == ELITE

    @pytest.mark.parametrize("goal", ["return", "recovery"])
    def test_return_and_recovery_are_not_beginners(self, goal):
        """A detrained runner is not a new runner -- they usually still have usable
        zones from before, and slowing them to walk-run pace would be wrong."""
        assert pace_tier_for_goal(goal) == DEFAULT_TIER

    def test_case_insensitive(self):
        assert pace_tier_for_goal("START_RUNNING") == "beginner"


class TestDefaultZone2Pace:
    def test_zone2_defaults_get_faster_at_every_step_up_the_tiers(self):
        """KB-grounded: 12:00-15:00 /mi for a beginner down to 4:30-5:00 /mi for an elite.
        A non-monotonic table would mean some tier is prescribed a pace from another."""
        mids = [PlanGenerator.parse_pace_to_decimal(TIER_PROFILES[t].zone2_pace[0]) for t in TIER_ORDER]
        assert mids == sorted(mids, reverse=True), "each tier's Zone 2 must be faster than the one below"

    def test_every_tier_has_a_slower_and_a_faster_bound(self):
        for tier in TIER_ORDER:
            slow, fast = TIER_PROFILES[tier].zone2_pace
            assert PlanGenerator.parse_pace_to_decimal(slow) > PlanGenerator.parse_pace_to_decimal(
                fast
            ), f"{tier}: slower bound must be a larger min/km than the faster bound"

    def test_unknown_tier_falls_back_rather_than_raising(self):
        assert default_zone2_pace("nonsense") == default_zone2_pace(DEFAULT_TIER)
        assert default_zone2_pace(None) == default_zone2_pace(DEFAULT_TIER)


class TestResolveZone2Pace:
    def test_a_stored_value_beats_the_tier_default(self):
        """The athlete's own measured zones always win -- including when they happen to
        equal the general default. The old code compared against the literal "6:30" and
        treated a real measurement as 'unset'."""
        assert resolve_zone2_pace("6:30", "5:45", "start_running") == ("6:30", "5:45")

    def test_a_beginner_with_no_stored_zones_gets_the_beginner_default(self):
        assert resolve_zone2_pace(None, None, "start_running") == TIER_PROFILES[BEGINNER].zone2_pace

    def test_a_race_athlete_with_no_stored_zones_gets_the_general_default(self):
        assert resolve_zone2_pace(None, None, "finish") == TIER_PROFILES[DEFAULT_TIER].zone2_pace

    def test_each_bound_falls_back_independently(self):
        """A half-populated profile keeps the bound it does have."""
        slow, fast = resolve_zone2_pace("9:15", None, "start_running")
        assert slow == "9:15"
        assert fast == TIER_PROFILES[BEGINNER].zone2_pace[1]

    def test_empty_strings_are_treated_as_unset(self):
        assert resolve_zone2_pace("", "", "start_running") == TIER_PROFILES[BEGINNER].zone2_pace


class TestDownstreamImpact:
    """The reason this matters: distance is a pure function of duration and pace."""

    def test_the_same_session_yields_a_shorter_distance_at_beginner_pace(self):
        duration = 23.0  # the session from the reported production plan

        general = PlanGenerator.estimate_pace_zones(*resolve_zone2_pace(None, None, "finish"), 140, 172)
        beginner = PlanGenerator.estimate_pace_zones(*resolve_zone2_pace(None, None, "start_running"), 140, 172)

        _, general_km = PlanGenerator.pace_and_distance_for_zone("Zone 2", duration, general)
        _, beginner_km = PlanGenerator.pace_and_distance_for_zone("Zone 2", duration, beginner)

        # The bug showed ~3.7km for this session; the beginner tier must show meaningfully less.
        assert general_km > beginner_km
        assert beginner_km < 3.2, f"beginner distance still inflated: {beginner_km} km"


class TestResolvePaceZones:
    """One resolver, so the app and the plan cannot disagree about an athlete's zones.

    The generator used to call estimate_pace_zones with only the Zone 2 bounds, dropping
    threshold_pace and pace_zone_model even though the function accepts both and
    GET /api/auth/pace-zones passes them. An athlete with a measured threshold saw one
    set of zones in the app while their plan was built on another -- and every workout's
    target pace, distance_km and treadmill speed came from the plan's set.
    """

    def test_a_measured_threshold_pace_is_honoured(self):
        profile = {"zone2_pace_min": "6:30", "zone2_pace_max": "5:45", "aet_hr": 140, "ant_hr": 172}
        estimated = PlanGenerator.resolve_pace_zones(profile)
        measured = PlanGenerator.resolve_pace_zones({**profile, "threshold_pace": "4:30"})
        assert measured != estimated, "threshold_pace must change the resolved zones"
        assert measured["zone4_pace"] != estimated["zone4_pace"]

    def test_the_pace_zone_model_is_honoured(self):
        profile = {"zone2_pace_min": "6:30", "zone2_pace_max": "5:45", "aet_hr": 140, "ant_hr": 172}
        four = PlanGenerator.resolve_pace_zones({**profile, "threshold_pace": "4:30", "pace_zone_model": "4_zone"})
        five = PlanGenerator.resolve_pace_zones({**profile, "threshold_pace": "4:30", "pace_zone_model": "5_zone"})
        assert four.get("model") == "4_zone"
        assert five.get("model") == "5_zone"

    def test_it_always_returns_the_mid_values_the_distance_maths_needs(self):
        """pace_and_distance_for_zone indexes zoneN_pace_mid; a resolver that returned a
        display-shaped payload without them would make every distance 0."""
        for extra in ({}, {"threshold_pace": "4:30"}):
            zones = PlanGenerator.resolve_pace_zones(
                {"zone2_pace_min": "6:30", "zone2_pace_max": "5:45", "aet_hr": 140, "ant_hr": 172, **extra}
            )
            for z in range(1, 6):
                assert zones.get(f"zone{z}_pace_mid"), f"missing zone{z}_pace_mid with {extra}"

    def test_it_still_applies_the_beginner_tier_default_when_no_zones_are_stored(self):
        zones = PlanGenerator.resolve_pace_zones({"aet_hr": 140, "ant_hr": 172}, "start_running")
        general = PlanGenerator.resolve_pace_zones({"aet_hr": 140, "ant_hr": 172}, "finish")
        slow = PlanGenerator.parse_pace_to_decimal(zones["zone2_pace_mid"])
        fast = PlanGenerator.parse_pace_to_decimal(general["zone2_pace_mid"])
        assert slow > fast, "a beginner's Zone 2 must be slower than the general default"
