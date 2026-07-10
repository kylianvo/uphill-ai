from unittest.mock import patch

from services.race_matcher import match_race

VMM_CHUNK = {
    "title": "Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam",
    "content": "The VMM runs through Sa Pa... humid, technical hand-and-knees scrambles on the final climbs.",
    "payload": {
        "race_name": "Vietnam Mountain Marathon",
        "aliases": ["VMM", "Sapa Marathon"],
        "terrain": ["rice terraces", "technical hand-and-knees scrambles"],
        "distances": [
            {"label": "21km", "distance_km": 21.5, "elevation_gain_m": 1200},
            {"label": "50km", "distance_km": 46.7, "elevation_gain_m": 2800},
            {"label": "100km", "distance_km": 100.0, "elevation_gain_m": 5500},
        ],
        "matching_hints": {
            "name_keywords": ["vmm", "vietnam mountain marathon", "sapa marathon"],
            "distance_km_options": [21.5, 46.7, 100.0],
        },
    },
}

UNRELATED_CHUNK = {
    "title": "UTA — Blue Mountains, Australia",
    "content": "Ultra-Trail Australia runs through the Blue Mountains...",
    "payload": {
        "race_name": "Ultra-Trail Australia",
        "aliases": ["UTA"],
        "terrain": ["sandstone escarpments"],
        "distances": [{"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2600}],
        "matching_hints": {"name_keywords": ["uta", "ultra-trail australia"], "distance_km_options": [50.0]},
    },
}


def test_exact_keyword_match_returns_high_confidence():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("VMM")
    assert matched is not None
    assert matched.race_name == "Vietnam Mountain Marathon"
    assert matched.confidence == 100.0


def test_fuzzy_typo_match_above_threshold():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("Vietnam Montain Marathon")  # missing an 'u'
    assert matched is not None
    assert matched.race_name == "Vietnam Mountain Marathon"


def test_unrelated_name_returns_none():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("Boston Marathon")
    assert matched is None


def test_distance_km_selects_closest_entry():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("VMM", distance_km=48.0)
    assert matched.distance_label == "50km"
    assert matched.elevation_gain_m == 2800


def test_distance_label_with_named_distance_and_miles():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("VMM", distance_label="~13 miles")  # ~20.9km, closest to 21.5km
    assert matched.distance_label == "21km"


def test_no_distance_given_still_returns_course_context():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("VMM")
    assert matched.distance_label is None
    assert matched.elevation_gain_m is None
    assert "technical hand-and-knees" in matched.course_context


def test_empty_catalog_returns_none():
    with patch("db.get_kb_chunks", return_value=[]):
        matched = match_race("VMM")
    assert matched is None


def test_short_name_returns_none_without_querying_db():
    with patch("db.get_kb_chunks") as get_chunks:
        matched = match_race("VM")
    get_chunks.assert_not_called()
    assert matched is None


def test_none_name_returns_none():
    assert match_race(None) is None


def test_db_error_degrades_to_none_instead_of_raising():
    with patch("db.get_kb_chunks", side_effect=RuntimeError("db down")):
        matched = match_race("VMM")
    assert matched is None


def test_substring_of_keyword_does_not_cause_false_positive_match():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("Utah 100 Endurance Run")
    assert matched is None


def test_to_dict_shape():
    with patch("db.get_kb_chunks", return_value=[VMM_CHUNK, UNRELATED_CHUNK]):
        matched = match_race("VMM", distance_km=48.0)
    assert matched.to_dict() == {
        "race_name": "Vietnam Mountain Marathon",
        "distance_label": "50km",
        "distance_km": 46.7,
        "elevation_gain_m": 2800,
        "terrain": ["rice terraces", "technical hand-and-knees scrambles"],
    }
