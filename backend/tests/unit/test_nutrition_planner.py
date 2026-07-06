import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.nutrition_planner as np_mod
from config import settings
from services.nutrition_planner import NutritionParams

NUTRITION_JSON = json.dumps(
    {
        "products": [
            {
                "brand": "Maurten",
                "name": "Gel 100",
                "total_quantity": 6,
                "carbs_per_unit": 25.0,
                "sodium_per_unit": 22.0,
                "protein_per_unit": 0.0,
                "tech_notes": "Hydrogel encapsulation for high carb tolerance.",
            }
        ],
        "hourly_plan": [{"hour": 1, "action": "2x Gel 100", "carbs": 50.0, "sodium": 44.0}],
        "tips": ["Practice fueling in training."],
    }
)


@pytest.fixture(autouse=True)
def clear_cache():
    np_mod._NUTRITION_CACHE.clear()
    yield
    np_mod._NUTRITION_CACHE.clear()


def _mock_gemini_model(response_text):
    fake_response = MagicMock()
    fake_response.text = response_text
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response
    return fake_model


def test_gemini_engine_primary_injects_catalog_and_principles(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_model = _mock_gemini_model(NUTRITION_JSON)

    def fake_get_kb_chunks(domain, kind=None):
        assert domain == "nutrition"
        if kind == "catalog_item":
            return [{"title": "Maurten Gel 100", "payload": {"brand": "Maurten", "carbs_per_unit": 25.0}}]
        return [{"title": "Sodium in heat", "content": "Hot races need ~1000mg sodium/h."}]

    with (
        patch("db.get_kb_chunks", side_effect=fake_get_kb_chunks),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
    ):
        result = asyncio.run(
            np_mod.nutrition_planner.generate_plan("", NutritionParams(distance_km=50, weather_temp="hot"))
        )
    assert result["products"][0]["name"] == "Gel 100"
    prompt_sent = fake_model.generate_content.call_args[0][0]
    assert "KNOWLEDGE BASE" in prompt_sent
    assert "Maurten Gel 100" in prompt_sent
    assert "Sodium in heat" in prompt_sent  # principles injected too
    assert "Target Sodium/Hour: 1000.0mg" in prompt_sent  # hot-weather macro logic untouched


def test_default_flag_keeps_notebooklm_primary(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "notebooklm")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok": 1}')
    monkeypatch.setattr(settings, "NOTEBOOKLM_NUTRITION_ID", "nb-nutrition")
    with patch(
        "services.notebooklm_service.NotebookLmService.query_notebook",
        new_callable=AsyncMock,
        return_value=NUTRITION_JSON,
    ) as nlm:
        result = asyncio.run(np_mod.nutrition_planner.generate_plan("", NutritionParams(distance_km=42)))
    nlm.assert_called_once()
    assert result["hourly_plan"][0]["hour"] == 1
