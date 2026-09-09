import asyncio
import json
from unittest.mock import MagicMock, patch

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


def _mock_gemini_client(response_text):
    fake_response = MagicMock()
    fake_response.text = response_text
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response
    return fake_client


def test_gemini_engine_primary_uses_kb_catalog(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_client = _mock_gemini_client(GEAR_JSON)
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka", "price": "$155"}}]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.genai.Client", return_value=fake_client),
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    assert result["recommendations"][0]["model"] == "Speedgoat 7"
    prompt_sent = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert "KNOWLEDGE BASE" in prompt_sent  # catalog context was injected
    assert "Speedgoat 7" in prompt_sent
    assert "BRAND CONSTRAINT" in prompt_sent  # constraint wording preserved
    # Result was cached
    assert len(gp._GEAR_CACHE) == 1


def test_gemini_refuses_on_empty_kb_rather_than_answering_ungrounded(monkeypatch):
    """With no catalog to ground on there is no second engine to fall back to, so the
    only safe outcome is an empty result that explains itself -- never invented shoes."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_client = _mock_gemini_client(GEAR_JSON)
    with (
        patch("db.get_kb_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake_client),
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    assert result["recommendations"] == []
    assert result["tips"], "an empty result must say why"


def test_gear_recommendation_schema_includes_weight():
    assert "weight" in gp.GearRecommendation.model_fields


def test_gemini_prompt_includes_weight_field_guidance(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_client = _mock_gemini_client(GEAR_JSON)
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka", "weight": "9.6 oz / 272 g"}}]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.genai.Client", return_value=fake_client),
    ):
        asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    prompt_sent = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert '"weight"' in prompt_sent  # field guidance mentions weight
    assert "9.6 oz / 272 g" in prompt_sent  # catalog's own weight value was injected


def test_gear_params_accepts_race_name():
    assert "race_name" in GearParams.model_fields


def test_gemini_engine_injects_course_context_and_echoes_matched_race(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_client = _mock_gemini_client(GEAR_JSON)
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
        patch("google.genai.Client", return_value=fake_client),
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail", race_name="VMM")))
    prompt_sent = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert "hand-and-knees scrambles" in prompt_sent
    assert result["matched_race"]["race_name"] == "Vietnam Mountain Marathon"
    assert result["matched_race"]["elevation_gain_m"] == 2800


def test_no_race_name_means_no_matched_race_in_response(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_client = _mock_gemini_client(GEAR_JSON)
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka"}}]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.genai.Client", return_value=fake_client),
    ):
        result = asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))
    assert result["matched_race"] is None
