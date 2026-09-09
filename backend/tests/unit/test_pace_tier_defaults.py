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

from services.plan_generator import PlanGenerator
from services.training_rules import (
    ZONE2_PACE_DEFAULTS,
    default_zone2_pace,
    pace_tier_for_goal,
    resolve_zone2_pace,
)


class TestPaceTierForGoal:
    def test_start_running_is_the_beginner_tier(self):
        assert pace_tier_for_goal("start_running") == "beginner"

    @pytest.mark.parametrize("goal", ["finish", "time", "optimal", None, ""])
    def test_everything_else_is_the_general_tier(self, goal):
        assert pace_tier_for_goal(goal) == "general"

    @pytest.mark.parametrize("goal", ["return", "recovery"])
    def test_return_and_recovery_are_not_beginners(self, goal):
        """A detrained runner is not a new runner -- they usually still have usable
        zones from before, and slowing them to walk-run pace would be wrong."""
        assert pace_tier_for_goal(goal) == "general"

    def test_case_insensitive(self):
        assert pace_tier_for_goal("START_RUNNING") == "beginner"


class TestDefaultZone2Pace:
    def test_beginner_is_slower_than_general_on_both_bounds(self):
        b_slow, b_fast = default_zone2_pace("beginner")
        g_slow, g_fast = default_zone2_pace("general")
        assert PlanGenerator.parse_pace_to_decimal(b_slow) > PlanGenerator.parse_pace_to_decimal(g_slow)
        assert PlanGenerator.parse_pace_to_decimal(b_fast) > PlanGenerator.parse_pace_to_decimal(g_fast)

    def test_every_defined_tier_has_a_slower_and_a_faster_bound(self):
        for tier, (slow, fast) in ZONE2_PACE_DEFAULTS.items():
            slow_d = PlanGenerator.parse_pace_to_decimal(slow)
            fast_d = PlanGenerator.parse_pace_to_decimal(fast)
            assert slow_d > fast_d, f"{tier}: slower bound must be a larger min/km than the faster bound"

    def test_unknown_tier_falls_back_rather_than_raising(self):
        assert default_zone2_pace("elite") == default_zone2_pace("general")
        assert default_zone2_pace(None) == default_zone2_pace("general")


class TestResolveZone2Pace:
    def test_a_stored_value_beats_the_tier_default(self):
        """The athlete's own measured zones always win -- including when they happen to
        equal the general default. The old code compared against the literal "6:30" and
        treated a real measurement as 'unset'."""
        assert resolve_zone2_pace("6:30", "5:45", "start_running") == ("6:30", "5:45")

    def test_a_beginner_with_no_stored_zones_gets_the_beginner_default(self):
        assert resolve_zone2_pace(None, None, "start_running") == ZONE2_PACE_DEFAULTS["beginner"]

    def test_a_race_athlete_with_no_stored_zones_gets_the_general_default(self):
        assert resolve_zone2_pace(None, None, "finish") == ZONE2_PACE_DEFAULTS["general"]

    def test_each_bound_falls_back_independently(self):
        """A half-populated profile keeps the bound it does have."""
        slow, fast = resolve_zone2_pace("9:15", None, "start_running")
        assert slow == "9:15"
        assert fast == ZONE2_PACE_DEFAULTS["beginner"][1]

    def test_empty_strings_are_treated_as_unset(self):
        assert resolve_zone2_pace("", "", "start_running") == ZONE2_PACE_DEFAULTS["beginner"]


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
