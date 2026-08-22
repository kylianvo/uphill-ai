"""Tests for race_matcher.course_profile / course_profile_variants -- curated
GPX checkpoints (and their route-variant tags) served to the Goal Determiner
when an admin has uploaded them. DB access is patched out, following
test_race_benchmarks.py's pattern."""

from unittest.mock import patch

from services.race_matcher import course_profile, course_profile_variants

VMM_CHUNK_MULTI_YEAR = {
    "title": "Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam",
    "content": "The VMM runs through Sa Pa...",
    "payload": {
        "race_name": "Vietnam Mountain Marathon",
        "aliases": ["VMM"],
        "distances": [{"label": "70km", "distance_km": 69.5, "elevation_gain_m": 4000}],
        "matching_hints": {"name_keywords": ["vmm", "vietnam mountain marathon"]},
        "course_profiles": {
            "70km": {
                "2025": {
                    "checkpoints": [
                        {
                            "name": "Start",
                            "distance_meters": 0,
                            "elevation_meters": 1500.0,
                            "segment_gain_meters": 0.0,
                            "segment_loss_meters": 0.0,
                        },
                    ],
                    "variant": None,
                    "source": "gpx_upload",
                    "curated_at": "2025-09-01",
                },
                "2026": {
                    "checkpoints": [
                        {
                            "name": "KM 5.0",
                            "distance_meters": 5000.0,
                            "elevation_meters": 2200.0,
                            "segment_gain_meters": 700.0,
                            "segment_loss_meters": 0.0,
                        },
                    ],
                    "variant": "langbiang-reversed",
                    "source": "gpx_upload",
                    "curated_at": "2026-08-15",
                },
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


def test_selects_most_recently_curated_year_by_default():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        profile = course_profile("VMM", "70km")
    assert profile is not None
    assert profile["year"] == 2026
    assert profile["variant"] == "langbiang-reversed"
    assert profile["checkpoints"][0]["elevation_meters"] == 2200.0


def test_selects_specific_requested_year():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        profile = course_profile("VMM", "70km", year=2025)
    assert profile is not None
    assert profile["year"] == 2025
    assert profile["variant"] is None
    assert profile["checkpoints"][0]["elevation_meters"] == 1500.0


def test_returns_none_for_uncurated_year():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        assert course_profile("VMM", "70km", year=2020) is None


def test_returns_none_for_wrong_distance_label():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        assert course_profile("VMM", "100km") is None


def test_returns_none_for_race_without_profile():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR, NO_PROFILE_CHUNK]):
        assert course_profile("Ultra-Trail Australia", "50km") is None


def test_returns_none_for_unmatched_race():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        assert course_profile("Totally Unknown Race 12345", "70km") is None


def test_returns_none_without_distance_label():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        assert course_profile("VMM", None) is None


def test_variants_returns_year_to_variant_map():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        variants = course_profile_variants("VMM", "70km")
    assert variants == {2025: None, 2026: "langbiang-reversed"}


def test_variants_empty_for_race_without_profile():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR, NO_PROFILE_CHUNK]):
        assert course_profile_variants("Ultra-Trail Australia", "50km") == {}


def test_variants_empty_for_unmatched_race():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK_MULTI_YEAR]):
        assert course_profile_variants("Totally Unknown Race 12345", "70km") == {}


def _tied_curated_at_chunk(year_order):
    """VMM chunk with two editions curated on the SAME date (same-day batch
    upload), with dict keys constructed in the given literal order."""
    entries = {
        "2025": {
            "checkpoints": [{"name": "Start", "distance_meters": 0, "elevation_meters": 1500.0}],
            "variant": None,
            "source": "gpx_upload",
            "curated_at": "2026-08-15",
        },
        "2026": {
            "checkpoints": [{"name": "KM 5.0", "distance_meters": 5000.0, "elevation_meters": 2200.0}],
            "variant": "langbiang-reversed",
            "source": "gpx_upload",
            "curated_at": "2026-08-15",
        },
    }
    ordered = {year: entries[year] for year in year_order}
    return {
        "title": "Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam",
        "content": "The VMM runs through Sa Pa...",
        "payload": {
            "race_name": "Vietnam Mountain Marathon",
            "aliases": ["VMM"],
            "distances": [{"label": "70km", "distance_km": 69.5, "elevation_gain_m": 4000}],
            "matching_hints": {"name_keywords": ["vmm", "vietnam mountain marathon"]},
            "course_profiles": {"70km": ordered},
        },
    }


def test_tied_curated_at_selects_later_year_ascending_insertion_order():
    chunk = _tied_curated_at_chunk(["2025", "2026"])
    with patch("db.get_kb_chunks", return_value=[chunk]):
        profile = course_profile("VMM", "70km")
    assert profile is not None
    assert profile["year"] == 2026


def test_tied_curated_at_selects_later_year_descending_insertion_order():
    chunk = _tied_curated_at_chunk(["2026", "2025"])
    with patch("db.get_kb_chunks", return_value=[chunk]):
        profile = course_profile("VMM", "70km")
    assert profile is not None
    assert profile["year"] == 2026


def test_returns_none_for_legacy_flat_shape():
    legacy_chunk = {
        "title": "Legacy Shape Ultra",
        "content": "...",
        "payload": {
            "race_name": "Legacy Shape Ultra",
            "aliases": [],
            "distances": [{"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2000}],
            "matching_hints": {"name_keywords": ["legacy shape ultra"]},
            "course_profiles": {
                # old pre-this-feature flat shape: no year keys, a single
                # checkpoints blob directly under the distance label
                "50km": {"checkpoints": [{"distance_meters": 0}], "source": "gpx_upload", "curated_at": "2025-01-01"}
            },
        },
    }
    with patch("db.get_kb_chunks", return_value=[legacy_chunk]):
        assert course_profile("Legacy Shape Ultra", "50km") is None
        assert course_profile_variants("Legacy Shape Ultra", "50km") == {}
