"""Tests for race_matcher.course_profile -- curated GPX checkpoints served
to the Goal Determiner when an admin has uploaded them. DB access is
patched out, following test_race_benchmarks.py's pattern."""

from unittest.mock import patch

from services.race_matcher import course_profile

VMM_CHUNK_WITH_PROFILE = {
    "title": "Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam",
    "content": "The VMM runs through Sa Pa...",
    "payload": {
        "race_name": "Vietnam Mountain Marathon",
        "aliases": ["VMM"],
        "distances": [{"label": "70km", "distance_km": 69.5, "elevation_gain_m": 4000}],
        "matching_hints": {"name_keywords": ["vmm", "vietnam mountain marathon"]},
        "course_profiles": {
            "70km": {
                "checkpoints": [
                    {
                        "name": "Start",
                        "distance_meters": 0,
                        "elevation_meters": 1500.0,
                        "segment_gain_meters": 0.0,
                        "segment_loss_meters": 0.0,
                    },
                    {
                        "name": "KM 5.0",
                        "distance_meters": 5000.0,
                        "elevation_meters": 2200.0,
                        "segment_gain_meters": 700.0,
                        "segment_loss_meters": 0.0,
                    },
                ],
                "source": "gpx_upload",
                "curated_at": "2026-08-22",
            }
        },
    },
}

NO_PROFILE_CHUNK = {
    "title": "UTA — Blue Mountains, Australia",
    "content": "Ultra-Trail Australia...",
    "payload": {
        "race_name": "Ultra-Trail Australia",
        "aliases": ["UTA"],
        "distances": [{"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2600}],
        "matching_hints": {"name_keywords": ["uta", "ultra-trail australia"]},
    },
}


def test_returns_checkpoints_for_matched_race_and_distance():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_WITH_PROFILE]):
        checkpoints = course_profile("VMM", "70km")
    assert checkpoints is not None
    assert len(checkpoints) == 2
    assert checkpoints[1]["elevation_meters"] == 2200.0


def test_returns_none_for_wrong_distance_label():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_WITH_PROFILE]):
        assert course_profile("VMM", "100km") is None


def test_returns_none_for_race_without_profile():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_WITH_PROFILE, NO_PROFILE_CHUNK]):
        assert course_profile("Ultra-Trail Australia", "50km") is None


def test_returns_none_for_unmatched_race():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_WITH_PROFILE]):
        assert course_profile("Totally Unknown Race 12345", "70km") is None


def test_returns_none_without_distance_label():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_WITH_PROFILE]):
        assert course_profile("VMM", None) is None
