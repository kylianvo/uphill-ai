from unittest.mock import MagicMock, patch

from services import kb_retrieval


def _fake_embed(model, content, task_type):
    return {"embedding": [0.1] * kb_retrieval.VECTOR_SIZE}


def test_reindex_recreates_collection_and_upserts():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    chunks = [
        {"title": "ME circuits", "content": "One pass per exercise, 6-8 rounds."},
        {"title": "Taper", "content": "Cut volume ~50% in taper week."},
    ]
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.generativeai.embed_content", side_effect=_fake_embed),
        patch("google.generativeai.configure"),
    ):
        count = kb_retrieval.reindex_scheduler_chunks(chunks, api_key="test-key")

    assert count == 2
    fake_client.delete_collection.assert_called_once_with(kb_retrieval.COLLECTION)
    fake_client.create_collection.assert_called_once()
    points = fake_client.upsert.call_args.kwargs.get("points") or fake_client.upsert.call_args[0][1]
    assert len(points) == 2
    assert points[0].payload["title"] == "ME circuits"


def test_search_returns_payloads():
    fake_hit = MagicMock()
    fake_hit.payload = {"title": "Taper", "content": "Cut volume ~50%."}
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    fake_client.query_points.return_value.points = [fake_hit]
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.generativeai.embed_content", side_effect=_fake_embed),
        patch("google.generativeai.configure"),
    ):
        results = kb_retrieval.search_scheduler_chunks("taper rules", api_key="test-key", k=3)
    assert results == [{"title": "Taper", "content": "Cut volume ~50%."}]


def test_search_missing_collection_returns_empty():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = False
    with patch.object(kb_retrieval, "_client", return_value=fake_client):
        assert kb_retrieval.search_scheduler_chunks("anything", api_key="test-key") == []
