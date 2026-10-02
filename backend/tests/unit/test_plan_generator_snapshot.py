from unittest.mock import MagicMock, patch

import pytest

from services.fitness_snapshot import FitnessSnapshot
from services.plan_generator import PlanGenerator

PROFILE = {"id": 7, "current_weekly_km": 120.0, "aet_hr": 134, "ant_hr": 163, "max_hr": 183, "resting_hr": 60}
RACE = {
    "name": "APTRC",
    "date": "2026-11-27",
    "goal_type": "race",
    "course_distance_km": 80.0,
    "course_elevation_gain_m": 4000.0,
}


def _snapshot():
    return FitnessSnapshot(
        weekly_km=134.0,
        weekly_km_source="coros",
        weekly_vert_m=5000.0,
        volume_as_of="2026-09-20",
        threshold_pace="3:53",
        threshold_pace_source="coros",
        assessment=None,
        utmb_index=None,
        threshold_source="unknown",
        gender=None,
        readiness=None,
    )


async def _generate(race_info):
    mock_resp = MagicMock()
    mock_resp.text = "invalid json to trigger fallback"
    client = MagicMock()
    client.models.generate_content.return_value = mock_resp
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        _, tier = await PlanGenerator.generate_plan_workouts(
            plan_id=1, user_profile=dict(PROFILE), race_info=race_info, total_weeks=8, api_key="fake-gemini-key"
        )
    return tier, client.models.generate_content.call_args.kwargs.get("contents", "")


@pytest.mark.asyncio
async def test_snapshot_sets_tier_volume_and_prompt_block():
    snap = _snapshot()
    tier, prompt = await _generate({**RACE, "fitness_snapshot": snap})
    assert tier == "sub_elite"
    assert snap.tier == "sub_elite" and snap.tier_reasons
    assert "ATHLETE FITNESS SNAPSHOT" in prompt
    assert "Weekly volume base: 134.0 km" in prompt


@pytest.mark.asyncio
async def test_without_snapshot_unknown_threshold_source_no_longer_demotes():
    tier, prompt = await _generate(dict(RACE))
    assert tier == "sub_elite"
    assert "ATHLETE FITNESS SNAPSHOT" not in prompt
