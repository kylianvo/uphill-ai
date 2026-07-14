"""Tests for race_matcher.race_benchmarks — course results served to the
Pace Strategy finish-time slider. DB access is patched out."""

from unittest.mock import patch

from services.race_matcher import race_benchmarks

VMM_CHUNK = {
    "title": "Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam",
    "content": "The VMM runs through Sa Pa...",
    "payload": {
        "race_name": "Vietnam Mountain Marathon",
        "aliases": ["VMM", "Sapa Marathon"],
        "distances": [
            {"label": "70km", "distance_km": 69.5, "elevation_gain_m": 4000},
            {"label": "100km", "distance_km": 100.0, "elevation_gain_m": 5500},
        ],
        "matching_hints": {"name_keywords": ["vmm", "vietnam mountain marathon"]},
        "results": [
            {
                "year": 2025,
                "distance_label": "70km",
                "distance_km": 69.5,
                "finishers": 289,
                "winner_time": "9:10:58",
                "winner_time_women": "11:52:42",
            },
            {"year": 2025, "distance_label": "100km", "distance_km": 100.0, "finishers": 150},
        ],
    },
}

NO_RESULTS_CHUNK = {
    "title": "UTA — Blue Mountains, Australia",
    "content": "Ultra-Trail Australia...",
    "payload": {
        "race_name": "Ultra-Trail Australia",
        "aliases": ["UTA"],
        "distances": [{"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2600}],
        "matching_hints": {"name_keywords": ["uta", "ultra-trail australia"]},
    },
}


def test_returns_results_filtered_by_distance():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, NO_RESULTS_CHUNK]):
        bench = race_benchmarks("VMM", distance_km=70)
    assert bench is not None
    assert bench["race_name"] == "Vietnam Mountain Marathon"
    assert len(bench["results"]) == 1
    assert bench["results"][0]["winner_time"] == "9:10:58"


def test_returns_all_results_without_distance():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK]):
        bench = race_benchmarks("VMM")
    assert bench is not None
    assert len(bench["results"]) == 2


def test_race_without_results_returns_none():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, NO_RESULTS_CHUNK]):
        assert race_benchmarks("Ultra-Trail Australia") is None


def test_unmatched_name_returns_none():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK]):
        assert race_benchmarks("Totally Unknown Race 12345") is None
