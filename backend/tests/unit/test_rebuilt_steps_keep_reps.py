"""A session whose step text is rebuilt keeps its strides in the text; rep fields the text no longer describes are
cleared (prod plan 129: the app showed '5 x 15 s' as the main set of an easy run whose steps had no strides)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.plan_generator import PlanGenerator


def _session(title: str, reps: int, value: int, description: str) -> dict:
    return {
        "week_number": 1,
        "day_of_week": "Friday",
        "phase": "Base",
        "title": title,
        "type": "Easy",
        "duration_minutes": 40,
        "target_zone": "Zone 2",
        "distance_km": 6.5,
        "elevation_gain_m": 0,
        "interval_reps": reps,
        "interval_rep_value": value,
        "interval_rep_unit": "s",
        "description": description,
        "fueling_tip": "Water only.",
    }


def _generate(sessions: list[dict]) -> list[dict]:
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps(sessions), usage_metadata=None)
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=client),
    ):
        workouts, _tier = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=999999,
                user_profile={"age": 34, "max_hr": 188, "resting_hr": 52},
                race_info={"lang": "en", "terrain": "trail"},
                total_weeks=8,
                api_key="test-key",
                block_number=1,
            )
        )
    return workouts


def test_rebuilt_easy_run_keeps_its_strides():
    # steps add up to 15 of 40 min, so the text is rebuilt from the header
    [wo] = [
        w
        for w in _generate([_session("Aerobic Base Run + Strides", 5, 15, "Warm up 5 min → 5 min easy → 5 min cool")])
        if "Strides" in (w.get("title") or "")
    ]
    assert wo["interval_reps"] == 5
    assert "5 × 15 s strides" in wo["description"]


def test_rebuilt_run_drops_rep_fields_it_cannot_describe():
    [wo] = [
        w
        for w in _generate([_session("Recovery Run + Core", 3, 45, "Warm up 5 min → 5 min easy → 5 min cool")])
        if "Core" in (w.get("title") or "") or w.get("day_of_week") == "Friday"
    ]
    assert wo["interval_reps"] is None and wo["interval_rep_value"] is None
