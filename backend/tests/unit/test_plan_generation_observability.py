"""LLMOps coverage for the standalone plan-generation paths."""

import asyncio
import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from config import settings
from services import observability as obs
from services.kb_retrieval import search_scheduler_chunks
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
            "description": "Warm up, run easy, cool down.",
            "fueling_tip": "Water only.",
        }
    ]
)
USER_PROFILE = {
    "id": 42,
    "age": 34,
    "max_hr": 188,
    "resting_hr": 52,
    "injury_history": "CANARY-ACHILLES-INJURY",
}
RACE_INFO = {"lang": "en", "terrain": "trail", "athlete_notes": "CANARY-PRIVATE-NOTE"}


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
    client.models.embed_content.return_value = SimpleNamespace(
        embeddings=[SimpleNamespace(values=[0.1, 0.2])],
    )
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


async def _generate(*, api_key="test-key"):
    return await PlanGenerator.generate_plan_workouts(
        plan_id=999999,
        user_profile=USER_PROFILE,
        race_info=RACE_INFO,
        total_weeks=8,
        api_key=api_key,
        block_number=1,
    )


def test_primary_plan_call_exports_safe_hierarchy_usage_and_identity(langfuse_spans, monkeypatch):
    fake = _client(_response(WORKOUT_JSON, prompt=120, output=30))
    qdrant = MagicMock()
    qdrant.collection_exists.return_value = True
    qdrant.query_points.return_value = SimpleNamespace(
        points=[
            SimpleNamespace(
                payload={"title": "Private title", "content": "CANARY-PRIVATE-CHUNK"},
                score=0.75,
            )
        ]
    )
    monkeypatch.setattr("services.kb_retrieval._client", lambda: qdrant)

    with patch("google.genai.Client", return_value=fake):
        workouts, tier = asyncio.run(_generate())

    spans = _finished(langfuse_spans)
    root = _by_name(spans, "plan_generation")[0]
    primary = _by_name(spans, "gemini")[0]
    retrieval = _by_name(spans, "retrieval")[0]
    plan_generation = _generation_for_feature(spans, "plan_generation")[0]
    embedding = _generation_for_feature(spans, "embeddings")[0]

    assert workouts[0]["title"] == "Easy Aerobic Run"
    assert tier
    assert fake.models.generate_content.call_count == 1
    assert primary.parent.span_id == root.context.span_id
    assert retrieval.parent.span_id == primary.context.span_id
    assert embedding.parent.span_id == retrieval.context.span_id
    assert plan_generation.parent.span_id == primary.context.span_id
    assert json.loads(_attrs(plan_generation)["langfuse.observation.usage_details"])["total"] == 150
    assert "langfuse.observation.usage_details" not in _attrs(embedding)
    assert json.loads(_metadata(retrieval, "collections")) == ["uphill_kb_scheduler"]
    assert _metadata(retrieval, "retrieval_k") == 6
    assert json.loads(_metadata(retrieval, "chunk_scores")) == [0.75]
    assert json.loads(_metadata(retrieval, "chunk_refs")) == [
        hashlib.sha1(b"Private title\nCANARY-PRIVATE-CHUNK").hexdigest()[:12]
    ]

    expected_user = hmac.new(b"test-salt", b"42", hashlib.sha256).hexdigest()[:32]
    assert _attrs(root)["user.id"] == expected_user
    exported = repr([_attrs(span) for span in spans])
    for canary in ("CANARY-ACHILLES-INJURY", "CANARY-PRIVATE-NOTE", "CANARY-PRIVATE-CHUNK", "Private title"):
        assert canary not in exported


def test_parse_failure_keeps_primary_usage_and_successful_retry_bills_again(langfuse_spans):
    fake = _client(
        _response("not json", prompt=100, output=9),
        _response(WORKOUT_JSON, prompt=80, output=20),
    )
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake),
    ):
        workouts, _tier = asyncio.run(_generate())

    spans = _finished(langfuse_spans)
    generations = _generation_for_feature(spans, "plan_generation")
    totals = sorted(json.loads(_attrs(span)["langfuse.observation.usage_details"])["total"] for span in generations)

    assert workouts[0]["title"] == "Easy Aerobic Run"
    assert fake.models.generate_content.call_count == 2
    assert totals == [100, 109]
    assert _metadata(_by_name(spans, "gemini")[0], "status") == "fallback"
    assert _metadata(_by_name(spans, "gemini")[0], "error_type") == "JSONDecodeError"
    assert _metadata(_by_name(spans, "gemini_retry")[0], "status") == "used"


def test_two_provider_errors_then_rule_fallback_records_two_unknown_failures_only(langfuse_spans):
    fake = MagicMock()
    fake.models.generate_content.side_effect = RuntimeError("provider unavailable")
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake),
    ):
        workouts, _tier = asyncio.run(_generate())

    spans = _finished(langfuse_spans)
    generations = _generation_for_feature(spans, "plan_generation")

    assert workouts
    assert fake.models.generate_content.call_count == 2
    assert len(generations) == 2
    assert all(_metadata(span, "status") == "error" for span in generations)
    assert all("langfuse.observation.usage_details" not in _attrs(span) for span in generations)
    [rule_based] = _by_name(spans, "rule_based")
    assert _metadata(rule_based, "latency_ms") >= 0
    assert not _generation_for_feature_or_empty(spans, "other")


def _generation_for_feature_or_empty(spans, feature):
    return [
        span
        for span in spans
        if _attrs(span).get("langfuse.observation.type") == "generation" and _metadata(span, "feature") == feature
    ]


def test_missing_api_key_uses_rule_fallback_without_a_provider_generation(langfuse_spans):
    workouts, _tier = asyncio.run(_generate(api_key=None))
    spans = _finished(langfuse_spans)

    assert workouts
    assert not [span for span in spans if _attrs(span).get("langfuse.observation.type") == "generation"]
    assert len(_by_name(spans, "plan_generation")) == 1
    assert len(_by_name(spans, "rule_based")) == 1


def test_single_workout_records_one_paid_generation_without_changing_result(langfuse_spans):
    body = json.dumps(
        {
            "title": "Threshold Repeats",
            "target_zone": "Zone 4",
            "description": "Warm up, complete repeats, cool down.",
            "fueling_tip": None,
        }
    )
    fake = _client(_response(body, prompt=40, output=12))
    with patch("google.genai.Client", return_value=fake):
        result = asyncio.run(
            PlanGenerator.generate_single_workout(
                user_profile=USER_PROFILE,
                workout_type="Interval",
                duration_minutes=30,
                day_of_week="Tuesday",
                week_number=2,
                api_key="test-key",
            )
        )

    spans = _finished(langfuse_spans)
    generation = _generation_for_feature(spans, "workout_ai_create")[0]
    root = _by_name(spans, "workout_ai_create")[0]

    assert result["title"] == "Threshold Repeats"
    assert result["target_zone"] == "Zone 4"
    assert generation.parent.span_id == root.context.span_id
    assert json.loads(_attrs(generation)["langfuse.observation.usage_details"])["total"] == 52


def test_week_narrative_records_one_paid_generation_and_preserves_output(langfuse_spans):
    body = json.dumps({"last_week_review": "Strong week.", "this_week_description": "Build volume."})
    fake = _client(_response(body, prompt=50, output=10))
    with patch("google.genai.Client", return_value=fake):
        result = asyncio.run(
            PlanGenerator.generate_week_narrative(
                race_info={"lang": "en"},
                block_context="3/3 sessions",
                workouts=[
                    {
                        "day_of_week": "Monday",
                        "title": "Easy Run",
                        "type": "Easy",
                        "duration_minutes": 60,
                        "target_zone": "Zone 2",
                    }
                ],
                api_key="test-key",
            )
        )

    spans = _finished(langfuse_spans)
    generation = _generation_for_feature(spans, "block_narrative")[0]
    root = _by_name(spans, "block_narrative")[0]

    assert result == ("Strong week.", "Build volume.")
    assert generation.parent.span_id == root.context.span_id
    assert json.loads(_attrs(generation)["langfuse.observation.usage_details"])["total"] == 60


def test_observability_failure_does_not_change_single_workout_output(langfuse_spans):
    class ExplodingClient:
        def __getattr__(self, _name):
            def explode(*_args, **_kwargs):
                raise RuntimeError("observability unavailable")

            return explode

    body = json.dumps(
        {
            "title": "Easy Aerobic Run",
            "target_zone": "Zone 2",
            "description": "Run easy.",
            "fueling_tip": None,
        }
    )
    fake = _client(_response(body, prompt=20, output=5))
    real_client, obs._client = obs._client, ExplodingClient()
    try:
        with patch("google.genai.Client", return_value=fake):
            result = asyncio.run(
                PlanGenerator.generate_single_workout(
                    user_profile=USER_PROFILE,
                    workout_type="Easy",
                    duration_minutes=30,
                    day_of_week="Tuesday",
                    week_number=2,
                    api_key="test-key",
                )
            )
    finally:
        obs._client = real_client

    assert result["title"] == "Easy Aerobic Run"
    assert result["description"] == "Run easy."


def test_scheduler_embedding_without_provider_usage_is_recorded_as_unknown(langfuse_spans, monkeypatch):
    fake = _client()
    qdrant = MagicMock()
    qdrant.collection_exists.return_value = True
    qdrant.query_points.return_value = SimpleNamespace(points=[])
    monkeypatch.setattr("services.kb_retrieval._client", lambda: qdrant)

    with patch("google.genai.Client", return_value=fake):
        assert search_scheduler_chunks("CANARY-QUERY", "test-key", 3) == []

    spans = _finished(langfuse_spans)
    [embedding] = _generation_for_feature(spans, "embeddings")
    [retrieval] = _by_name(spans, "retrieval")

    assert embedding.parent.span_id == retrieval.context.span_id
    assert "langfuse.observation.usage_details" not in _attrs(embedding)
    assert "langfuse.observation.cost_details" not in _attrs(embedding)
    assert _metadata(retrieval, "retrieval_k") == 3
    assert _metadata(retrieval, "grounded") is False
    assert "CANARY-QUERY" not in repr([_attrs(span) for span in spans])
    assert settings.GEMINI_MODEL not in repr(_attrs(embedding))
