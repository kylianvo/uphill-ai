"""Unit tests for two-domain principle retrieval."""

from unittest.mock import MagicMock, patch

import pytest

from services import kb_retrieval


def test_search_principles_queries_both_collections():
    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True

    hit_sched = MagicMock()
    hit_sched.payload = {"title": "Aerobic Threshold", "content": "Keep heart rate low"}
    hit_sched.score = 0.88

    hit_nutr = MagicMock()
    hit_nutr.payload = {"title": "Carb Intake", "content": "30-60g carbs per hour"}
    hit_nutr.score = 0.82

    def mock_query_points(collection_name, query, limit):
        res = MagicMock()
        if collection_name == kb_retrieval.COLLECTION_SCHEDULER:
            res.points = [hit_sched]
        else:
            res.points = [hit_nutr]
        return res

    mock_qdrant.query_points.side_effect = mock_query_points

    with (
        patch.object(kb_retrieval, "_client", return_value=mock_qdrant),
        patch.object(kb_retrieval, "_embed", return_value=[[0.1] * kb_retrieval.VECTOR_SIZE]) as mock_embed,
    ):
        results = kb_retrieval.search_principles("how to fuel long run", api_key="test-key", scheduler_k=4, nutrition_k=2)

        # Verified single embedding call
        assert mock_embed.call_count == 1

        # Verified two results across both domains
        assert len(results) == 2
        sched_res = next(r for r in results if r["domain"] == "scheduler")
        nutr_res = next(r for r in results if r["domain"] == "nutrition")

        assert sched_res["title"] == "Aerobic Threshold"
        assert nutr_res["title"] == "Carb Intake"
        assert sched_res["ref"] == kb_retrieval._chunk_ref("Aerobic Threshold", "Keep heart rate low")


def test_search_principles_tolerates_missing_collection():
    mock_qdrant = MagicMock()
    # Scheduler exists, nutrition missing
    mock_qdrant.collection_exists.side_effect = lambda name: name == kb_retrieval.COLLECTION_SCHEDULER

    hit_sched = MagicMock()
    hit_sched.payload = {"title": "Recovery", "content": "Rest is key"}
    hit_sched.score = 0.90

    res = MagicMock()
    res.points = [hit_sched]
    mock_qdrant.query_points.return_value = res

    with (
        patch.object(kb_retrieval, "_client", return_value=mock_qdrant),
        patch.object(kb_retrieval, "_embed", return_value=[[0.1] * kb_retrieval.VECTOR_SIZE]),
    ):
        results = kb_retrieval.search_principles("recovery", api_key="test-key")
        assert len(results) == 1
        assert results[0]["domain"] == "scheduler"


def test_search_principles_both_collections_missing():
    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = False

    with (
        patch.object(kb_retrieval, "_client", return_value=mock_qdrant),
        patch.object(kb_retrieval, "_embed", return_value=[[0.1] * kb_retrieval.VECTOR_SIZE]),
    ):
        results = kb_retrieval.search_principles("anything", api_key="test-key")
        assert results == []
