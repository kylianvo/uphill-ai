"""ME timing follows weeks left before the ME cutoff and ME already done, not plan length."""

import asyncio
from unittest.mock import MagicMock, patch

from services.athlete_tier import get_profile
from services.plan_generator import PlanGenerator
from services.plan_rules import build_rules_block, count_me_sessions, me_runway, me_status_block

REC_PROFILE = {"age": 34, "max_hr": 188, "resting_hr": 52, "current_weekly_km": 55.0, "has_gym_access": True}
NOVICE_PROFILE = {"age": 34, "max_hr": 188, "resting_hr": 60, "current_weekly_km": 25.0}
TRAIL_RACE = {"lang": "en", "terrain": "trail", "goal_type": "finish", "name": "50K", "course_distance_km": 50}


def _run(user_profile, race_info, total_weeks=17, block_number=1):
    """Returns (prompt, rule-based workouts): the mocked model answers '[]', so it falls through."""
    response = MagicMock()
    response.text = "[]"
    client = MagicMock()
    client.models.generate_content.return_value = response
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        workouts, _ = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=1,
                user_profile=user_profile,
                race_info=race_info,
                total_weeks=total_weeks,
                api_key="test-key",
                block_number=block_number,
            )
        )
    return client.models.generate_content.call_args_list[0].kwargs["contents"], workouts


def test_count_me_sessions_matches_type_and_title_before_the_week():
    workouts = [
        {"week_number": 1, "type": "Muscular Endurance", "is_completed": 1},
        {"week_number": 2, "type": "Strength", "title": "Muscular Endurance: Step-Ups", "is_completed": 0},
        {"week_number": 2, "type": "Time Trial", "title": "5K"},
        {"week_number": 3, "type": "Muscular Endurance", "is_completed": 1},
    ]
    assert count_me_sessions(workouts, 3) == {"done": 1, "scheduled": 2}


def test_me_runway_counts_weeks_to_the_cutoff_inclusive():
    assert me_runway(11, 16) == 4  # 17-week plan, race week 16, cutoff week 14
    assert me_runway(15, 16) == 0


def test_me_status_block():
    text = me_status_block(0, 0, 4, 11, tier_changed_from="novice")
    assert "0 ME sessions completed so far (0 scheduled) before week 11." in text
    assert "Weeks left before the ME cutoff (10-14 days before race day): 4." in text
    assert "moved up from novice" in text
    assert "completed so far" not in me_status_block(None, None, 15, 1)


def test_rule_4_branches_on_weeks_left():
    rules = build_rules_block(get_profile("recreational"), None)
    for branch in ("16 or more weeks left", "Fewer than 16 weeks left", "Catch-up:", "Fewer than 3 weeks left"):
        assert branch in rules
    assert "<= 10 weeks total plan" not in rules
    assert "Soft Start:" in rules


def test_catch_up_prompt_carries_me_history_and_tier_change():
    race = {**TRAIL_RACE, "me_history": {"done": 0, "scheduled": 0}, "previous_tier": "novice"}
    prompt, _ = _run(REC_PROFILE, race, block_number=11)
    assert "0 ME sessions completed so far (0 scheduled) before week 11." in prompt
    assert "Weeks left before the ME cutoff (10-14 days before race day): 4." in prompt
    assert "moved up from novice" in prompt


def test_novice_prompt_has_no_me_history():
    prompt, _ = _run(NOVICE_PROFILE, {**TRAIL_RACE, "me_history": {"done": 0, "scheduled": 0}}, block_number=11)
    assert "ME HISTORY" not in prompt


def test_fallback_first_me_sessions_are_a_reduced_dose():
    # Week 5 of a 20-week plan is Base: without the soft start it would prescribe 6 sets.
    _, workouts = _run(REC_PROFILE, {**TRAIL_RACE, "me_history": {"done": 0}}, total_weeks=20, block_number=5)
    me = [w for w in workouts if w["type"] == "Muscular Endurance"]
    assert me and "4x10" in me[0]["description"]


def test_me_decision_cutoff_overrides_short_block_and_catch_up():
    text = me_status_block(0, 0, 2, 13)
    assert "ME DECISION: Do NOT schedule ME in this block" in text
    assert "overrides" in text
    assert "ME DECISION: Start" not in text


def test_me_decision_with_short_runway_starts_now():
    assert "ME DECISION: Start" in me_status_block(0, 0, 10, 1)
    assert "ME DECISION: Start" in me_status_block(0, 0, 3, 11)
