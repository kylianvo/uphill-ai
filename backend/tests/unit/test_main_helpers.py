from unittest.mock import patch

from main import _resolve_course_match
from services.race_matcher import MatchedRace


def _fake_match():
    return MatchedRace(
        race_name="Vietnam Mountain Marathon",
        distance_label="50km",
        distance_km=46.7,
        elevation_gain_m=2800,
        terrain=["rice terraces"],
        course_context="Course prose here.",
        confidence=100.0,
    )


def test_backfills_blank_numeric_fields_from_match():
    with patch("services.race_matcher.match_race", return_value=_fake_match()):
        distance, elevation, context = _resolve_course_match("VMM", None, None)
    assert distance == 46.7
    assert elevation == 2800
    assert context == "Course prose here."


def test_never_overwrites_manual_values():
    with patch("services.race_matcher.match_race", return_value=_fake_match()):
        distance, elevation, context = _resolve_course_match("VMM", 50.0, 3000.0)
    assert distance == 50.0  # manual value kept
    assert elevation == 3000.0  # manual value kept
    assert context == "Course prose here."  # qualitative context still applied


def test_no_match_returns_inputs_unchanged_and_no_context():
    with patch("services.race_matcher.match_race", return_value=None):
        distance, elevation, context = _resolve_course_match("Unknown Race", 50.0, None)
    assert distance == 50.0
    assert elevation is None
    assert context is None


def test_never_raises_even_if_match_race_raises_unexpectedly():
    with patch("services.race_matcher.match_race", side_effect=RuntimeError("malformed KB payload")):
        distance, elevation, context = _resolve_course_match("VMM", 50.0, None)
    assert distance == 50.0
    assert elevation is None
    assert context is None
