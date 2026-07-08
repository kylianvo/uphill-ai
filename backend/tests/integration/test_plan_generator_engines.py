"""RAG_ENGINE ordering inside PlanGenerator.generate_plan_workouts."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from config import settings
from services.plan_generator import PlanGenerator

WORKOUT_JSON = json.dumps(
    [
        {
            "week_number": 1,
            "day_of_week": "Tue",
            "phase": "Base",
            "title": "Easy Aerobic Run",
            "type": "Easy",
            "duration_minutes": 45,
            "target_zone": "Zone 2",
            "target_hr_range": "125-140 bpm",
            "target_pace": "6:30 /km",
            "distance_km": 7.0,
            "elevation_gain_m": 0,
            "grade_percent": 0,
            "description": "Warm up 10min → run 30min Zone 2 → cool down 5min. Overall: aerobic base.",
            "fueling_tip": "Water only.",
        }
    ]
)

USER_PROFILE = {"age": 34, "max_hr": 188, "resting_hr": 52}
RACE_INFO = {"lang": "en", "terrain": "trail"}


def _fake_gemini_model():
    fake_response = MagicMock()
    fake_response.text = WORKOUT_JSON
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response
    return fake_model


async def _generate():
    return await PlanGenerator.generate_plan_workouts(
        plan_id=999999,
        user_profile=USER_PROFILE,
        race_info=RACE_INFO,
        total_weeks=8,
        api_key="test-key",
        block_number=1,
    )


def test_gemini_flag_makes_gemini_primary_with_kb_context(monkeypatch):
    import asyncio

    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "nb-sched")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    fake_model = _fake_gemini_model()
    chunks = [{"title": "ME circuits", "content": "One pass per exercise, 6-8 rounds, short rests."}]
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=chunks),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
        patch("services.notebooklm_service.NotebookLmService.query_notebook", new_callable=AsyncMock) as nlm,
    ):
        workouts = asyncio.run(_generate())

    nlm.assert_not_called()  # Gemini succeeded first — NotebookLM never hit
    assert workouts and workouts[0]["title"] == "Easy Aerobic Run"
    prompt_sent = fake_model.generate_content.call_args[0][0]
    assert "UPHILL ATHLETE PHILOSOPHY" in prompt_sent
    assert "6-8 rounds" in prompt_sent


def test_default_flag_keeps_notebooklm_primary(monkeypatch):
    import asyncio

    monkeypatch.setattr(settings, "RAG_ENGINE", "notebooklm")
    monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "nb-sched")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    with patch(
        "services.notebooklm_service.NotebookLmService.query_notebook",
        new_callable=AsyncMock,
        return_value=WORKOUT_JSON,
    ) as nlm:
        workouts = asyncio.run(_generate())
    nlm.assert_called_once()
    assert workouts and workouts[0]["type"] == "Easy"


def _used_count(engine: str) -> float:
    from prometheus_client import REGISTRY

    return (
        REGISTRY.get_sample_value(
            "rag_attempts_total", {"service": "plan_generator", "engine": engine, "status": "used"}
        )
        or 0.0
    )


def test_used_counter_attributes_returned_plan_to_its_engine(monkeypatch):
    """A NotebookLM answer that fails JSON parsing must NOT count as "used" —
    only the engine whose parsed output is actually returned increments it
    (golden_eval.py relies on this for engine attribution)."""
    import asyncio

    monkeypatch.setattr(settings, "RAG_ENGINE", "notebooklm")
    monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "nb-sched")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    before = {"gemini": _used_count("gemini"), "notebooklm": _used_count("notebooklm")}
    fake_model = _fake_gemini_model()
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            return_value="Sorry, I could not find that in your sources.",  # unparsable → discarded
        ),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
    ):
        workouts = asyncio.run(_generate())
    assert workouts and workouts[0]["title"] == "Easy Aerobic Run"  # Gemini's output won
    assert _used_count("notebooklm") == before["notebooklm"]  # parse-failed answer never "used"
    assert _used_count("gemini") == before["gemini"] + 1


def test_gemini_failure_falls_back_to_notebooklm(monkeypatch):
    import asyncio

    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "nb-sched")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    fake_model = MagicMock()
    fake_model.generate_content.side_effect = Exception("Gemini down")
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            return_value=WORKOUT_JSON,
        ) as nlm,
    ):
        workouts = asyncio.run(_generate())
    nlm.assert_called_once()
    assert workouts and workouts[0]["week_number"] == 1
