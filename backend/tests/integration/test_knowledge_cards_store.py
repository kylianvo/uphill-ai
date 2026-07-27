"""Round-trip tests for the knowledge_cards data-access functions in db.py."""

from db import get_knowledge_card_source_labels, save_knowledge_cards


def _sample_card(source_label="Uphill Athlete Podcasts", topic="Training"):
    return {
        "chapter_title": "Zone 2 Basics",
        "summary": "Zone 2 builds aerobic base.",
        "key_points": ["Run slower than you think", "Use a talk test"],
        "tags": ["zone2", "aerobic"],
        "topic": topic,
        "source_label": source_label,
    }


def test_get_knowledge_card_source_labels_returns_distinct_labels(_init_test_database):
    save_knowledge_cards([_sample_card(), _sample_card(source_label="https://youtu.be/abc123")])
    labels = get_knowledge_card_source_labels()
    assert labels == {"Uphill Athlete Podcasts", "https://youtu.be/abc123"}


def test_get_knowledge_card_source_labels_empty_when_no_cards(_init_test_database):
    assert get_knowledge_card_source_labels() == set()
