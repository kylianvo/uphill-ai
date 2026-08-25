from unittest.mock import patch

from google.genai import types as genai_types

from main import _resolve_course_match, _session_review_status
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


def test_session_review_status_completed():
    assert _session_review_status({"is_completed": 1, "is_missed": 0}) == "completed"


def test_session_review_status_explicit_missed():
    assert _session_review_status({"is_completed": 0, "is_missed": 1}) == "MISSED"


def test_session_review_status_not_logged():
    assert _session_review_status({"is_completed": 0, "is_missed": 0}) == "not logged"


def test_session_review_status_defaults_missing_keys_to_not_logged():
    assert _session_review_status({}) == "not logged"


def test_chat_formatted_contents_shape_is_valid_genai_content():
    """The two /api/coach/chat endpoints build formatted_contents as
    [{"role": ..., "parts": [{"text": ...}]}, ...] before passing it to
    genai.Client.models.generate_content. Unlike the old google-generativeai
    SDK, google-genai's real pydantic validation rejects a bare string in
    "parts" (e.g. {"parts": ["hello"]}) -- it must be a Part-shaped dict.
    Mocked tests can't catch this since they never touch real validation,
    so this test builds contents the same way main.py does and validates
    each item against the actual SDK type."""
    messages = [
        {"role": "user", "content": "How do I taper?"},
        {"role": "assistant", "content": "Cut volume ~50% in the final week."},
    ]
    formatted_contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        formatted_contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    for item in formatted_contents:
        genai_types.Content.model_validate(item)
