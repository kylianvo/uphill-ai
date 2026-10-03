import dataclasses
from unittest.mock import MagicMock, patch

import pytest

from services.fitness_snapshot import FitnessSnapshot
from services.plan_generator import PlanGenerator

PROFILE = {"id": 7, "current_weekly_km": 112.0, "aet_hr": 138, "ant_hr": 168, "max_hr": 188, "resting_hr": 60}
RACE = {
    "name": "APTRC",
    "date": "2026-11-27",
    "goal_type": "race",
    "course_distance_km": 80.0,
    "course_elevation_gain_m": 4000.0,
}


def _snapshot():
    return FitnessSnapshot(
        weekly_km=138.0,
        weekly_km_source="coros",
        weekly_vert_m=4600.0,
        volume_as_of="2026-08-23",
        threshold_pace="3:57",
        threshold_pace_source="coros",
        assessment=None,
        utmb_index=None,
        threshold_source="unknown",
        gender=None,
        readiness=None,
    )


async def _generate(race_info, profile=None):
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
            plan_id=1,
            user_profile={**PROFILE, **(profile or {})},
            race_info=race_info,
            total_weeks=8,
            api_key="fake-gemini-key",
        )
    return tier, client.models.generate_content.call_args.kwargs.get("contents", "")


@pytest.mark.asyncio
async def test_snapshot_sets_tier_volume_and_prompt_block():
    snap = _snapshot()
    tier, prompt = await _generate({**RACE, "fitness_snapshot": snap})
    # load 184 effort-km -> 4.150; pace 237 s -> 3.514; weighted score 3.896
    assert tier == "sub_elite"
    assert snap.tier == "sub_elite" and snap.tier_reasons
    assert "ATHLETE FITNESS SNAPSHOT" in prompt
    assert "Weekly volume base: 138.0 km" in prompt


@pytest.mark.asyncio
async def test_without_snapshot_unknown_threshold_source_no_longer_demotes():
    tier, prompt = await _generate(dict(RACE))
    assert tier == "sub_elite"
    assert "ATHLETE FITNESS SNAPSHOT" not in prompt


@pytest.mark.asyncio
async def test_snapshot_path_passes_max_hr_to_the_physiology_level():
    snap = dataclasses.replace(_snapshot(), threshold_source="lab")
    await _generate({**RACE, "fitness_snapshot": snap})
    # gap 30/168 -> 2.607; AnT/max 168/188 -> 3.590; mean 3.099. Without
    # max_hr only the gap level (2.607) would be present.
    assert snap.tier_levels["physiology"] == pytest.approx(3.099, abs=0.01)


@pytest.mark.asyncio
async def test_previous_tier_reaches_the_hysteresis():
    # 84 km typed, no snapshot: load 3.05 alone, within 0.1 of the recreational boundary.
    tier, _ = await _generate({**RACE, "previous_tier": "recreational"}, profile={"current_weekly_km": 84.0})
    assert tier == "recreational"
    tier, _ = await _generate(dict(RACE), profile={"current_weekly_km": 84.0})
    assert tier == "sub_elite"
