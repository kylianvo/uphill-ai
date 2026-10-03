"""The snapshot fixtures resolve the expected tier through golden_eval's runner."""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import scripts.golden_eval as golden_eval

NAMES = [
    "fixture_snapshot_elite_unmeasured_thresholds.json",
    "fixture_snapshot_recreational_field_thresholds.json",
    "fixture_snapshot_elite_no_coros.json",
    "fixture_vietnam_urban_recreational_no_gym.json",
    "fixture_vietnam_urban_recreational_treadmill.json",
    "fixture_vietnam_urban_sub_elite_no_gym.json",
    "fixture_vietnam_urban_sub_elite_treadmill.json",
]


@pytest.mark.parametrize("name", NAMES)
def test_fixture_is_synthetic_and_resolves_expected_tier(name, monkeypatch):
    with open(os.path.join(golden_eval.GOLDEN_DIR, "scheduler", name), encoding="utf-8") as f:
        fixture = json.load(f)
    assert fixture["synthetic"] is True and fixture["provenance"] == "scheduler"

    resp = MagicMock()
    resp.text = "invalid json to trigger fallback"
    client = MagicMock()
    client.models.generate_content.return_value = resp
    monkeypatch.setattr(golden_eval.settings, "GEMINI_API_KEY", "fake-gemini-key")
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        workouts, _engine = asyncio.run(golden_eval._run_scheduler(fixture))

    assert workouts
    assert fixture.pop("_resolved_tier") == fixture["expect"]["tier"]


def test_gate_fails_on_tier_mismatch_and_volume_out_of_range():
    items = [{"id": "a", "input": {}}, {"id": "b", "input": {}}]
    scores = [
        {"engine": "gemini", "tier_match": False, "week2_in_range": True},
        {"engine": "gemini", "tier_match": True, "week2_in_range": False},
    ]
    failures = golden_eval.gate_failures("scheduler", items, scores)
    assert any("a" in f and "tier" in f for f in failures)
    assert any("b" in f and "week-2" in f for f in failures)


def test_week_km_sums_one_week():
    workouts = [
        {"week_number": 2, "distance_km": 10.0},
        {"week_number": 2, "distance_km": None},
        {"week_number": 3, "distance_km": 99.0},
    ]
    assert golden_eval._week_km(workouts, 2) == 10.0


@pytest.mark.parametrize("expect,block_weeks", [({"week2_km": [110, 145]}, 2), ({}, 1)])
def test_week2_gate_requests_a_block_that_contains_week2(expect, block_weeks, monkeypatch):
    from services.plan_generator import PlanGenerator

    monkeypatch.setattr(golden_eval.settings, "WEEKS_PER_BLOCK", 1)
    generate = AsyncMock(return_value=([], "sub_elite"))
    monkeypatch.setattr(PlanGenerator, "generate_plan_workouts", generate)
    fixture = {"user_profile": {}, "race_info": {}, "expect": expect}
    asyncio.run(golden_eval._run_scheduler(fixture))
    assert generate.call_args.kwargs["weeks_per_block"] == block_weeks


def test_vietnam_urban_cases_cover_both_tiers_and_access_conditions():
    cases = []
    for name in NAMES:
        if not name.startswith("fixture_vietnam_urban_"):
            continue
        with open(os.path.join(golden_eval.GOLDEN_DIR, "scheduler", name), encoding="utf-8") as f:
            fixture = json.load(f)
        race = fixture["race_info"]
        gym = fixture["user_profile"]["has_gym_access"]
        assert race["lang"] == "vi"
        assert race["training_environment"] == "mixed"
        assert race["has_gym_access"] is gym and race["use_treadmill"] is gym
        assert race["long_run_day"] == "Sunday"
        assert "Weekday outdoor runs must be flat" in race["athlete_notes"]
        assert "Mountains are available only on Saturday and Sunday" in race["athlete_notes"]
        cases.append((fixture["expect"]["tier"], gym))
    assert set(cases) == {("recreational", False), ("recreational", True), ("sub_elite", False), ("sub_elite", True)}
