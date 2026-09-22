from unittest.mock import patch

from services.coach_tools.knowledge_tools import kb_search_impl


def test_kb_search_scheduler_domain_uses_scheduler_search():
    hits = [{"title": "Muscular Endurance", "content": "...", "chapter": "Chapter 6", "score": 0.89}]
    with patch("services.kb_retrieval.search_scheduler_chunks", return_value=hits) as mock_search:
        result = kb_search_impl(user_id=1, query="muscular endurance uphill", domain="scheduler", api_key="k")
    mock_search.assert_called_once_with(query="muscular endurance uphill", api_key="k")
    assert result.status == "success"
    assert result.card_type == "knowledge_citations"
    assert result.card_data["citations"][0]["book"] == "Training for the Uphill Athlete"


def test_kb_search_all_domain_uses_search_principles():
    with patch("services.kb_retrieval.search_principles", return_value=[]) as mock_search:
        kb_search_impl(user_id=1, query="fueling rate", domain="all", api_key="k")
    mock_search.assert_called_once_with(query="fueling rate", api_key="k")


def test_kb_search_race_courses_domain_uses_db_lookup_not_qdrant():
    chunks = [{"title": "Dalat Ultra Trail", "content": "Course description", "payload": {}}]
    with (
        patch("services.kb_retrieval.search_scheduler_chunks") as mock_qdrant,
        patch("db.get_kb_chunks", return_value=chunks) as mock_db,
    ):
        result = kb_search_impl(user_id=1, query="Dalat", domain="race_courses", api_key="k")
    mock_qdrant.assert_not_called()
    mock_db.assert_called_once_with("race_courses", kind="race_profile")
    assert result.status == "success"


def test_kb_search_no_results_still_succeeds_with_empty_citations():
    with patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]):
        result = kb_search_impl(user_id=1, query="unrelated topic", domain="scheduler", api_key="k")
    assert result.status == "success"
    assert result.card_data["citations"] == []
