import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.gear_planner as gp
from config import settings
from services.gear_planner import GearParams

GEAR_JSON = json.dumps(
    {
        "recommendations": [
            {
                "model": "Speedgoat 7",
                "brand": "Hoka",
                "foam_material": "CMEVA (EVA)",
                "outsole_compound": "Vibram Megagrip",
                "lug_depth": "5mm",
                "drop": "4mm",
                "stack": "40mm/36mm",
                "weight": "10.3 oz / 292 g",
                "price": "$155",
                "pros": "Grippy and plush; great for long technical trail days.",
                "cons": "On the heavy side.",
            }
        ],
        "tips": ["Size up half a size."],
    }
)


@pytest.fixture(autouse=True)
def clear_cache():
    gp._GEAR_CACHE.clear()
    yield
    gp._GEAR_CACHE.clear()


def _mock_gemini_model(response_text):
    fake_response = MagicMock()
    fake_response.text = response_text
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response
    return fake_model


def test_gemini_engine_primary_uses_kb_catalog(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_model = _mock_gemini_model(GEAR_JSON)
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka", "price": "$155"}}]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    assert result["recommendations"][0]["model"] == "Speedgoat 7"
    prompt_sent = fake_model.generate_content.call_args[0][0]
    assert "KNOWLEDGE BASE" in prompt_sent  # catalog context was injected
    assert "Speedgoat 7" in prompt_sent
    assert "BRAND CONSTRAINT" in prompt_sent  # constraint wording preserved
    # Result was cached
    assert len(gp._GEAR_CACHE) == 1


def test_gemini_refuses_on_empty_kb_and_falls_back_to_notebooklm(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    monkeypatch.setattr(settings, "NOTEBOOKLM_GEAR_ID", "nb-gear")
    with (
        patch("db.get_kb_chunks", return_value=[]),
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            return_value=GEAR_JSON,
        ) as nlm,
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    nlm.assert_called_once()
    assert result["recommendations"][0]["brand"] == "Hoka"


def test_default_flag_keeps_notebooklm_primary(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "notebooklm")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    monkeypatch.setattr(settings, "NOTEBOOKLM_GEAR_ID", "nb-gear")
    with patch(
        "services.notebooklm_service.NotebookLmService.query_notebook",
        new_callable=AsyncMock,
        return_value=GEAR_JSON,
    ) as nlm:
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="road")))
    nlm.assert_called_once()
    assert result["tips"] == ["Size up half a size."]


def test_gear_recommendation_schema_includes_weight():
    assert "weight" in gp.GearRecommendation.model_fields


def test_gemini_prompt_includes_weight_field_guidance(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_model = _mock_gemini_model(GEAR_JSON)
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka", "weight": "9.6 oz / 272 g"}}]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
    ):
        asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    prompt_sent = fake_model.generate_content.call_args[0][0]
    assert '"weight"' in prompt_sent  # field guidance mentions weight
    assert "9.6 oz / 272 g" in prompt_sent  # catalog's own weight value was injected


def test_notebooklm_schema_includes_weight_field_guidance(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "notebooklm")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    monkeypatch.setattr(settings, "NOTEBOOKLM_GEAR_ID", "nb-gear")
    with patch(
        "services.notebooklm_service.NotebookLmService.query_notebook",
        new_callable=AsyncMock,
        return_value=GEAR_JSON,
    ) as nlm:
        asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="road")))
    query_sent = nlm.call_args.kwargs["query"]
    assert '"weight"' in query_sent  # schema block mentions weight guidance


def test_gear_params_accepts_race_name():
    assert "race_name" in GearParams.model_fields


def test_gemini_engine_injects_course_context_and_echoes_matched_race(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_model = _mock_gemini_model(GEAR_JSON)
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka", "price": "$155"}}]
    from services.race_matcher import MatchedRace

    matched = MatchedRace(
        race_name="Vietnam Mountain Marathon",
        distance_label="50km",
        distance_km=46.7,
        elevation_gain_m=2800,
        terrain=["rice terraces"],
        course_context="Highly technical hand-and-knees scrambles on the final climbs.",
        confidence=100.0,
    )
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("services.race_matcher.match_race", return_value=matched),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail", race_name="VMM")))
    prompt_sent = fake_model.generate_content.call_args[0][0]
    assert "hand-and-knees scrambles" in prompt_sent
    assert result["matched_race"]["race_name"] == "Vietnam Mountain Marathon"
    assert result["matched_race"]["elevation_gain_m"] == 2800


def test_no_race_name_means_no_matched_race_in_response(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_model = _mock_gemini_model(GEAR_JSON)
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka"}}]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    assert result["matched_race"] is None
