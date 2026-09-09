"""The assembled prompt must not contradict itself across tiers.

The tier system initially fixed only the RULES block. The SCHEMA section stayed global,
so a beginner's prompt stated "NO Muscular Endurance sessions of any kind" a few hundred
characters after handing the model the Summit Water Dump protocol, a Split Jump Squats
circuit, and 8-10g/kg race-day carb loading.

A prompt that contradicts itself is worse than one that is uniformly wrong: the model
resolves the conflict however it likes, and differently on each run. These tests assert
that each tier's prompt is internally consistent.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from services.plan_generator import PlanGenerator

BEGINNER_PROFILE = {
    "age": 34,
    "max_hr": 185,
    "resting_hr": 62,
    "current_weekly_km": 5.0,
    "max_continuous_jog_min": 3,
}
BEGINNER_RACE = {"lang": "en", "terrain": "road", "goal_type": "start_running", "name": "My Running Journey"}

ELITE_PROFILE = {"age": 29, "max_hr": 192, "resting_hr": 44, "current_weekly_km": 130.0}
ELITE_RACE = {
    "lang": "en",
    "terrain": "trail",
    "goal_type": "finish",
    "name": "UTMB",
    "course_distance_km": 170,
    "course_elevation_gain_m": 10000,
}

# Prescriptions -- not prohibitions. "NEVER prescribe a Hill Sprint" is correct in a
# beginner prompt; "Hill Bounding: 6-8 reps of 8-12s max-effort bounds" is not.
ME_AND_ULTRA_PRESCRIPTIONS = (
    "Summit Water Dump",
    "Split Jump Squats",
    "6-8 rounds",
    "Box Step-Ups at 75% kneecap height",
    "5-15% bodyweight pack",
)
ENDURANCE_FUELING_PRESCRIPTIONS = (
    "60-90g carbohydrates per hour",
    "8-10g carbohydrates per kg",
    "30-60g carbohydrates per hour",
)


def _capture_prompt(user_profile, race_info):
    response = MagicMock()
    response.text = "[]"  # falls through to rule-based; we only want the prompt
    client = MagicMock()
    client.models.generate_content.return_value = response
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=1,
                user_profile=user_profile,
                race_info=race_info,
                total_weeks=12,
                api_key="test-key",
                block_number=1,
            )
        )
    return client.models.generate_content.call_args_list[0].kwargs["contents"]


@pytest.fixture(scope="module")
def beginner_prompt():
    return _capture_prompt(BEGINNER_PROFILE, BEGINNER_RACE)


@pytest.fixture(scope="module")
def elite_prompt():
    return _capture_prompt(ELITE_PROFILE, ELITE_RACE)


class TestBeginnerPromptIsInternallyConsistent:
    @pytest.mark.parametrize("prescription", ME_AND_ULTRA_PRESCRIPTIONS)
    def test_the_schema_does_not_hand_over_me_apparatus(self, beginner_prompt, prescription):
        assert prescription not in beginner_prompt

    @pytest.mark.parametrize("prescription", ENDURANCE_FUELING_PRESCRIPTIONS)
    def test_the_schema_does_not_hand_over_endurance_fueling(self, beginner_prompt, prescription):
        assert prescription not in beginner_prompt

    def test_it_says_what_it_does_want_instead(self, beginner_prompt):
        assert "Muscular Endurance sessions of any kind" in beginner_prompt  # named to forbid
        assert "Do NOT prescribe gels" in beginner_prompt
        assert "Plain water" in beginner_prompt
        assert "run/walk intervals" in beginner_prompt

    def test_hill_sprints_appear_only_as_a_prohibition(self, beginner_prompt):
        """The equipment rule legitimately says NEVER prescribe one. What must not appear
        is the steep-incline prescription for executing them."""
        assert "NEVER prescribe a Hill Sprint" in beginner_prompt
        assert "MUST be in the 10-15% range" not in beginner_prompt
        # Guards the f-string itself: an unformatted literal would ALSO satisfy the
        # assertion above while shipping "{hill_incline_exception}" to the model.
        assert "{hill_incline_exception}" not in beginner_prompt

    def test_the_conditional_schema_slots_are_actually_interpolated(self, beginner_prompt, elite_prompt):
        for placeholder in ("{me_format_spec}", "{fueling_spec}", "{hill_incline_exception}", "{rules_block}"):
            assert placeholder not in beginner_prompt, f"unformatted placeholder: {placeholder}"
            assert placeholder not in elite_prompt, f"unformatted placeholder: {placeholder}"


class TestElitePromptKeepsTheFullApparatus:
    @pytest.mark.parametrize("prescription", ME_AND_ULTRA_PRESCRIPTIONS + ENDURANCE_FUELING_PRESCRIPTIONS)
    def test_nothing_was_removed_from_the_tier_that_needs_it(self, elite_prompt, prescription):
        assert prescription in elite_prompt

    def test_it_carries_the_high_volume_doctrine(self, elite_prompt):
        assert "Double-Threshold Days" in elite_prompt
        assert "ZONE 4 HARD CAP" in elite_prompt
        assert "daily repeatability test" in elite_prompt


def test_the_beginner_prompt_is_materially_shorter(beginner_prompt, elite_prompt):
    """Not a style preference: every extra character in a beginner's prompt was
    apparatus that contradicted the rules it sat beside."""
    assert len(beginner_prompt) < len(elite_prompt)
