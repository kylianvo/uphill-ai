"""The legacy /api/coach/chat profile quotes the same weekly km and tier the plan used."""

from unittest.mock import patch

from routers import coach_chat

SUMMARY = {"weekly_km": 138.0, "weekly_km_source": "coros", "athlete_tier": "sub_elite"}


def test_profile_uses_snapshot_volume_and_plan_tier():
    user = {"id": 7, "current_weekly_km": 70.0, "max_hr": 183}
    plan = {"id": 1, "athlete_tier": "sub_elite", "use_treadmill": False}
    with patch("services.fitness_snapshot.chat_summary", return_value=SUMMARY):
        profile = coach_chat._profile_for(user, plan)
    text = f"\nUser Running Profile: {profile}"
    assert "'current_weekly_km': 138.0" in text
    assert "'weekly_km_source': 'coros'" in text
    assert profile["athlete_tier"] == "sub_elite"


def test_profile_falls_back_to_the_typed_value_without_a_summary():
    user = {"id": 7, "current_weekly_km": 70.0}
    with patch("services.fitness_snapshot.chat_summary", return_value={}):
        profile = coach_chat._profile_for(user, None)
    assert profile["current_weekly_km"] == 70.0
    assert profile["weekly_km_source"] == "self_reported"
    assert profile["athlete_tier"] is None
