"""kb_search over the curated race and shoe libraries, on the committed seeds and the questions runners type."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from services.coach_tools.knowledge_tools import kb_search_impl

SEED = Path(__file__).resolve().parents[2] / "kb_seed"
CHUNKS = {d: json.loads((SEED / f"{d}.json").read_text())["chunks"] for d in ("race_courses", "gear")}


@pytest.fixture(autouse=True)
def seeds():
    with (
        patch("db.get_kb_chunks", side_effect=lambda domain, kind=None: CHUNKS.get(domain, [])),
        patch("services.kb_retrieval.search_principles", return_value=[]),
    ):
        yield


def search(query, domain):
    return kb_search_impl(user_id=1, query=query, domain=domain, api_key="k").card_data


def test_race_found_from_loose_name_with_course_facts():
    data = search("Vietnam Highlands Trail By Utmb - 100k", "race_courses")
    top = data["citations"][0]
    assert top["chapter_title"].startswith("Vietnam Highlands Trail")
    assert any("100" in p and "D+" in p for p in top["key_points"])  # the distances with their climb
    assert any(p.startswith("Terrain:") for p in top["key_points"])


def test_all_domain_adds_a_confident_race_or_shoe():
    assert search("Vietnam Highlands Trail By Utmb - 100k", "all")["citations"][0]["chapter_title"].startswith(
        "Vietnam Highlands Trail"
    )
    assert search("Norda 001A", "all")["citations"][0]["chapter_title"] == "Norda 001A"
    assert search("how much carbs per hour", "all")["citations"] == []  # no stray race or shoe


def test_shoe_by_name_with_specs():
    data = search("Norda 005 for My race?", "gear")  # the screenshot question
    top = data["citations"][0]
    assert data["exact_match"] is True and top["chapter_title"] == "Norda 005" and top["topic"] == "Gear"
    assert any(p.startswith("Lug depth:") for p in top["key_points"])
    assert any(p.startswith("Drop:") for p in top["key_points"])


def test_unknown_model_says_so_and_offers_the_brand():
    data = search("Norda 002 for my race?", "gear")  # no such model in the catalog
    assert data["exact_match"] is False
    assert data["citations"] and all(c["chapter_title"].startswith("Norda") for c in data["citations"])


def test_no_shoe_named_gives_a_trail_shortlist():
    data = search("trail shoes for a 100k with technical descents", "gear")
    assert data["exact_match"] is False and 0 < len(data["citations"]) <= 15
    assert all(c["chapter_title"] for c in data["citations"])
