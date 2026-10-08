from unittest.mock import MagicMock, patch

import pytest

from services import kb_retrieval


@pytest.fixture(autouse=True)
def _reset_kb_retrieval_caches():
    kb_retrieval._genai_client.cache_clear()
    kb_retrieval._existing_collections.clear()
    yield
    kb_retrieval._genai_client.cache_clear()
    kb_retrieval._existing_collections.clear()


def _fake_embed_response(model, contents, config):
    fake_embedding = MagicMock()
    fake_embedding.values = [0.1] * kb_retrieval.VECTOR_SIZE
    fake_response = MagicMock()
    fake_response.embeddings = [fake_embedding]
    return fake_response


def _fake_genai_client(api_key):
    fake_genai_client = MagicMock()
    fake_genai_client.models.embed_content.side_effect = _fake_embed_response
    return fake_genai_client


def test_reindex_recreates_collection_and_upserts():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    chunks = [
        {"title": "ME circuits", "content": "One pass per exercise, 6-8 rounds."},
        {"title": "Taper", "content": "Cut volume ~50% in taper week."},
    ]
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.genai.Client", side_effect=_fake_genai_client),
    ):
        count = kb_retrieval.reindex_scheduler_chunks(chunks, api_key="test-key")

    assert count == 2
    fake_client.delete_collection.assert_called_once_with(kb_retrieval.COLLECTION)
    fake_client.create_collection.assert_called_once()
    points = fake_client.upsert.call_args.kwargs.get("points") or fake_client.upsert.call_args[0][1]
    assert len(points) == 2
    assert points[0].payload["title"] == "ME circuits"


def test_search_returns_payloads_with_score_and_stable_ref():
    fake_hit = MagicMock()
    fake_hit.payload = {"title": "Taper", "content": "Cut volume ~50%."}
    fake_hit.score = 0.83
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    fake_client.query_points.return_value.points = [fake_hit]
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.genai.Client", side_effect=_fake_genai_client),
    ):
        results = kb_retrieval.search_scheduler_chunks("taper rules", api_key="test-key", k=3)

    # ref is sha1("Taper\nCut volume ~50%.")[:12], computed independently.
    assert results == [{"title": "Taper", "content": "Cut volume ~50%.", "score": 0.83, "ref": "44c51538e091"}]


def test_search_missing_collection_returns_empty():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = False
    with patch.object(kb_retrieval, "_client", return_value=fake_client):
        assert kb_retrieval.search_scheduler_chunks("anything", api_key="test-key") == []


def test_search_with_keep_overfetches_filters_and_caps_at_k():
    hits = []
    for title in ("Gym ME", "Walk-to-Run", "Doubles", "Taper"):
        hit = MagicMock()
        hit.payload = {"title": title, "content": "x"}
        hit.score = 0.5
        hits.append(hit)
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    fake_client.query_points.return_value.points = hits
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.genai.Client", side_effect=_fake_genai_client),
    ):
        results = kb_retrieval.search_scheduler_chunks(
            "q", api_key="test-key", k=1, fetch_k=4, keep=lambda hit: hit["title"] not in ("Gym ME", "Doubles")
        )

    assert fake_client.query_points.call_args.kwargs["limit"] == 4
    assert [r["title"] for r in results] == ["Walk-to-Run"]


def test_genai_client_is_built_once_per_api_key():
    fake_hit = MagicMock()
    fake_hit.payload = {"title": "Taper", "content": "Cut volume ~50%."}
    fake_hit.score = 0.83
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    fake_client.query_points.return_value.points = [fake_hit]
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.genai.Client", side_effect=_fake_genai_client) as genai_ctor,
    ):
        kb_retrieval.search_scheduler_chunks("taper", api_key="test-key")
        kb_retrieval.search_scheduler_chunks("taper again", api_key="test-key")

    assert genai_ctor.call_count == 1


def test_existing_collection_is_checked_once():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    fake_client.query_points.return_value.points = []
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.genai.Client", side_effect=_fake_genai_client),
    ):
        kb_retrieval.search_principles("q1", api_key="test-key")
        kb_retrieval.search_principles("q2", api_key="test-key")

    # Two collections, one existence check each across both searches.
    assert fake_client.collection_exists.call_count == 2


def test_missing_collection_is_rechecked_on_next_search():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = False
    with patch.object(kb_retrieval, "_client", return_value=fake_client):
        kb_retrieval.search_scheduler_chunks("q", api_key="test-key")
        kb_retrieval.search_scheduler_chunks("q", api_key="test-key")

    assert fake_client.collection_exists.call_count == 2
