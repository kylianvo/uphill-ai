import asyncio
import json
from unittest.mock import MagicMock, patch

from prometheus_client import REGISTRY

import services.gear_planner as gp
from config import settings
from services.gear_planner import GearParams


def _sample(name, labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_gear_gemini_success_records_metrics(monkeypatch):
    monkeypatch.setattr(settings, "RAG_ENGINE", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    gp._GEAR_CACHE.clear()

    labels_ok = {"service": "gear_finder", "engine": "gemini", "status": "success"}
    before = _sample("rag_attempts_total", labels_ok)

    fake_response = MagicMock()
    fake_response.text = json.dumps({"recommendations": [], "tips": ["t"]})
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response
    chunks = [{"title": "Speedgoat 7", "payload": {"brand": "Hoka"}}]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.generativeai.GenerativeModel", return_value=fake_model),
        patch("google.generativeai.configure"),
    ):
        asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="trail")))

    assert _sample("rag_attempts_total", labels_ok) == before + 1
    assert _sample("rag_latency_seconds_count", {"service": "gear_finder", "engine": "gemini"}) >= 1
    gp._GEAR_CACHE.clear()
