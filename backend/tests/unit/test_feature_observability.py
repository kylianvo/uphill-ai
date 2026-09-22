"""LLMOps coverage for Gear, Nutrition, KB distillation, and Knowledge cards."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from services import kb_distiller
from services import observability as obs
from services.gear_planner import _GEAR_CACHE, GearParams, GearPlanner
from services.knowledge_extractor import translate_cards_to_vi_with_gemini
from services.nutrition_planner import _NUTRITION_CACHE, NutritionParams, NutritionPlanner


def _usage(prompt: int, output: int, thinking: int = 0, cached: int = 0):
    return SimpleNamespace(
        prompt_token_count=prompt,
        candidates_token_count=output,
        thoughts_token_count=thinking,
        cached_content_token_count=cached,
    )


def _response(text: str, *, prompt: int, output: int):
    return SimpleNamespace(text=text, usage_metadata=_usage(prompt, output))


def _client(*responses):
    client = MagicMock()
    client.models.generate_content.side_effect = list(responses)
    return client


def _attrs(span):
    return dict(span.attributes or {})


def _finished(exporter):
    obs.flush()
    return exporter.get_finished_spans()


def _metadata(span, key):
    return _attrs(span).get(f"langfuse.observation.metadata.{key}")


def _by_name(spans, name):
    return [span for span in spans if span.name == name]


def _generation_for_feature(spans, feature):
    matches = [
        span
        for span in spans
        if _attrs(span).get("langfuse.observation.type") == "generation" and _metadata(span, "feature") == feature
    ]
    assert matches, f"no generation for {feature}; spans={[span.name for span in spans]}"
    return matches


GEAR_JSON = json.dumps(
    {
        "recommendations": [
            {
                "shoe_name": "Speedcross 6",
                "brand": "Salomon",
                "price": "$140",
                "specs": {
                    "weight": "10.5 oz / 298 g",
                    "drop": "10 mm",
                    "stack": "32/22 mm",
                    "lug_depth": "5 mm",
                    "foam_material": "EnergyCell+ (EVA)",
                    "outsole_compound": "Contagrip",
                    "carbon_plate": False,
                    "foot_shape": "Standard",
                    "arch_support": "Neutral",
                    "cushioning": "Moderate",
                    "terrain": "Technical Trail",
                    "intended_use": "Mud / Soft ground",
                },
                "pros": "Great grip.",
                "cons": "Heavy.",
                "tips": "Size up.",
            }
        ],
        "tips": ["Tip 1", "Tip 2"],
        "disclaimer": "Test disclaimer",
    }
)

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
        "hourly_plan": [
            {
                "hour": 1,
                "action": "Take 1 gel",
                "carbs": 25.0,
                "sodium": 22.0,
            }
        ],
        "tips": ["Drink water with gels"],
    }
)


def test_gear_cache_miss_makes_one_generation_and_cache_hit_makes_none(langfuse_spans, monkeypatch):
    _GEAR_CACHE.clear()
    fake = _client(_response(GEAR_JSON, prompt=85, output=40))
    planner = GearPlanner()
    params = GearParams(
        experience="Intermediate",
        race_distance="50km",
        preferred_brands="Salomon",
        additional_context="CANARY-GEAR-CONTEXT",
    )
    chunks = [
        {
            "id": 1,
            "domain": "gear",
            "kind": "catalog_item",
            "title": "Salomon Speedcross 6",
            "payload": {"brand": "Salomon", "model": "Speedcross 6"},
        }
    ]

    monkeypatch.setattr("services.gear_planner.settings.GEMINI_API_KEY", "test-key")
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("services.race_matcher.match_race", return_value=None),
        patch("google.genai.Client", return_value=fake),
    ):
        # 1. Cache MISS
        result1 = asyncio.run(planner.generate_plan("Athlete profile", params))
        assert result1["recommendations"][0]["shoe_name"] == "Speedcross 6"
        assert fake.models.generate_content.call_count == 1

        spans1 = _finished(langfuse_spans)
        generations1 = _generation_for_feature(spans1, "gear_finder")
        assert len(generations1) == 1
        assert json.loads(_attrs(generations1[0])["langfuse.observation.usage_details"])["total"] == 125
        [trace_span] = _by_name(spans1, "gear_finder")
        assert _metadata(trace_span, "catalog_entries") == 1
        assert _metadata(trace_span, "cache_hit") is False
        assert "user.id" not in _attrs(trace_span)
        assert "CANARY-GEAR-CONTEXT" not in repr([_attrs(s) for s in spans1])

        # 2. Cache HIT
        result2 = asyncio.run(planner.generate_plan("Athlete profile", params))
        assert result2["recommendations"][0]["shoe_name"] == "Speedcross 6"
        assert fake.models.generate_content.call_count == 1  # No additional provider call

        obs.flush()
        spans2 = langfuse_spans.get_finished_spans()
        generations2 = [s for s in spans2 if _attrs(s).get("langfuse.observation.type") == "generation"]
        assert len(generations2) == 1  # Still only the original generation


def test_gear_empty_catalog_refusal_makes_no_generation(langfuse_spans, monkeypatch):
    _GEAR_CACHE.clear()
    fake = _client()
    planner = GearPlanner()
    params = GearParams(race_distance="50km")

    monkeypatch.setattr("services.gear_planner.settings.GEMINI_API_KEY", "test-key")
    with (
        patch("db.get_kb_chunks", return_value=[]),
        patch("services.race_matcher.match_race", return_value=None),
        patch("google.genai.Client", return_value=fake),
    ):
        result = asyncio.run(planner.generate_plan("Athlete profile", params))
        # Empty catalog handled gracefully with error explanation in tips
        assert not result["recommendations"]
        assert "gear KB is empty" in result["tips"][0]
        assert fake.models.generate_content.call_count == 0

    spans = _finished(langfuse_spans)
    assert not [s for s in spans if _attrs(s).get("langfuse.observation.type") == "generation"]


def test_nutrition_cache_miss_makes_one_generation_and_cache_hit_makes_none(langfuse_spans, monkeypatch):
    _NUTRITION_CACHE.clear()
    fake = _client(_response(NUTRITION_JSON, prompt=90, output=35))
    planner = NutritionPlanner()
    params = NutritionParams(
        race_distance="100km",
        preferred_brands="Maurten",
        additional_context="CANARY-NUTRITION-CONTEXT",
    )
    catalog_chunks = [
        {
            "id": 1,
            "domain": "nutrition",
            "kind": "catalog_item",
            "title": "Maurten Gel 100",
            "payload": {"brand": "Maurten", "product_name": "Gel 100"},
        }
    ]
    principle_chunks = [
        {
            "id": 2,
            "domain": "nutrition",
            "kind": "principle",
            "title": "Carb Intake",
            "payload": {"rule": "60g/hr"},
        }
    ]

    monkeypatch.setattr("services.nutrition_planner.settings.GEMINI_API_KEY", "test-key")
    with (
        patch(
            "db.get_kb_chunks",
            side_effect=lambda domain, kind: catalog_chunks if kind == "catalog_item" else principle_chunks,
        ),
        patch("google.genai.Client", return_value=fake),
    ):
        # 1. Cache MISS
        result1 = asyncio.run(planner.generate_plan("Athlete profile", params))
        assert result1["products"][0]["name"] == "Gel 100"
        assert fake.models.generate_content.call_count == 1

        spans1 = _finished(langfuse_spans)
        generations1 = _generation_for_feature(spans1, "nutrition_lab")
        assert len(generations1) == 1
        assert json.loads(_attrs(generations1[0])["langfuse.observation.usage_details"])["total"] == 125
        [trace_span] = _by_name(spans1, "nutrition_lab")
        assert _metadata(trace_span, "catalog_entries") == 1
        assert _metadata(trace_span, "cache_hit") is False
        assert "user.id" not in _attrs(trace_span)
        assert "CANARY-NUTRITION-CONTEXT" not in repr([_attrs(s) for s in spans1])

        # 2. Cache HIT
        result2 = asyncio.run(planner.generate_plan("Athlete profile", params))
        assert result2["products"][0]["name"] == "Gel 100"
        assert fake.models.generate_content.call_count == 1

        obs.flush()
        spans2 = langfuse_spans.get_finished_spans()
        generations2 = [s for s in spans2 if _attrs(s).get("langfuse.observation.type") == "generation"]
        assert len(generations2) == 1


def test_nutrition_empty_catalog_refusal_makes_no_generation(langfuse_spans, monkeypatch):
    _NUTRITION_CACHE.clear()
    fake = _client()
    planner = NutritionPlanner()
    params = NutritionParams(race_distance="100km")

    monkeypatch.setattr("services.nutrition_planner.settings.GEMINI_API_KEY", "test-key")
    with (
        patch("db.get_kb_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake),
    ):
        result = asyncio.run(planner.generate_plan("Athlete profile", params))
        assert result["hourly_plan"] == []
        assert "nutrition KB is empty" in result["tips"][0]
        assert fake.models.generate_content.call_count == 0

    spans = _finished(langfuse_spans)
    assert not [s for s in spans if _attrs(s).get("langfuse.observation.type") == "generation"]


def test_kb_distiller_records_generation_with_feature_kb_distill(langfuse_spans):
    class SimpleSchema(BaseModel):
        name: str

    body = json.dumps({"name": "Test Item"})
    fake = _client(_response(body, prompt=60, output=15))

    with patch("google.genai.Client", return_value=fake):
        result = asyncio.run(
            kb_distiller._gemini_structured(
                api_key="test-key",
                prompt="CANARY-DISTILL-PROMPT",
                schema=SimpleSchema,
            )
        )

    assert result == {"name": "Test Item"}
    spans = _finished(langfuse_spans)
    [generation] = _generation_for_feature(spans, "kb_distill")
    assert json.loads(_attrs(generation)["langfuse.observation.usage_details"])["total"] == 75
    assert "user.id" not in _attrs(generation)
    assert "CANARY-DISTILL-PROMPT" not in repr([_attrs(s) for s in spans])


def test_knowledge_extractor_translation_records_generation_as_knowledge_cards(langfuse_spans):
    translated_body = json.dumps(
        {
            "chapter_title": "Tập luyện hiếu khí",
            "summary": "Tóm tắt về bài tập",
            "key_points": ["Điểm 1", "Điểm 2"],
        }
    )
    fake = _client(_response(translated_body, prompt=50, output=25))
    card = {
        "chapter_title": "Aerobic Base",
        "summary": "CANARY-EN-SUMMARY",
        "key_points": ["Point 1"],
        "tags": ["aerobic"],
        "topic": "training",
        "source_label": "https://youtube.com/watch?v=123",
    }

    results = asyncio.run(
        translate_cards_to_vi_with_gemini(
            fake,
            [card],
        )
    )

    assert results[0]["chapter_title"] == "Tập luyện hiếu khí"
    spans = _finished(langfuse_spans)
    [generation] = _generation_for_feature(spans, "knowledge_cards")
    assert json.loads(_attrs(generation)["langfuse.observation.usage_details"])["total"] == 75
    assert "user.id" not in _attrs(generation)
    assert "CANARY-EN-SUMMARY" not in repr([_attrs(s) for s in spans])


def test_knowledge_extractor_structured_call_uses_knowledge_cards_feature(langfuse_spans):
    class SimpleSchema(BaseModel):
        cards: list[str]

    body = json.dumps({"cards": ["Card 1"]})
    fake = _client(_response(body, prompt=45, output=15))

    with patch("google.genai.Client", return_value=fake):
        result = asyncio.run(
            kb_distiller._gemini_structured(
                api_key="test-key",
                prompt="Extract cards",
                schema=SimpleSchema,
                feature="knowledge_cards",
            )
        )

    assert result == {"cards": ["Card 1"]}
    spans = _finished(langfuse_spans)
    [generation] = _generation_for_feature(spans, "knowledge_cards")
    assert json.loads(_attrs(generation)["langfuse.observation.usage_details"])["total"] == 60


def test_upstream_provider_failure_preserves_error_behavior(langfuse_spans, monkeypatch):
    _GEAR_CACHE.clear()
    fake = MagicMock()
    fake.models.generate_content.side_effect = RuntimeError("provider down")
    planner = GearPlanner()
    params = GearParams(race_distance="50km")
    chunks = [
        {
            "id": 1,
            "domain": "gear",
            "kind": "catalog_item",
            "title": "Salomon Speedcross",
            "payload": {"brand": "Salomon"},
        }
    ]

    monkeypatch.setattr("services.gear_planner.settings.GEMINI_API_KEY", "test-key")
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("services.race_matcher.match_race", return_value=None),
        patch("google.genai.Client", return_value=fake),
    ):
        result = asyncio.run(planner.generate_plan("Athlete profile", params))
        assert not result["recommendations"]
        assert "Could not retrieve recommendations" in result["tips"][0]

    spans = _finished(langfuse_spans)
    [generation] = _generation_for_feature(spans, "gear_finder")
    assert _metadata(generation, "status") == "error"
    assert "langfuse.observation.usage_details" not in _attrs(generation)
