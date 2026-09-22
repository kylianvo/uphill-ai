from unittest.mock import patch

from services.coach_tools.pacing_tools import pace_strategy_impl
from services.race_matcher import MatchedRace


def _matched_race(**overrides):
    base = dict(
        race_name="Dalat Ultra Trail 70K",
        distance_label="70K",
        distance_km=71.2,
        elevation_gain_m=3150.0,
        terrain=[],
        course_context="",
        confidence=0.95,
    )
    base.update(overrides)
    return MatchedRace(**base)


def test_pace_strategy_no_race_match_returns_error():
    with patch("services.race_matcher.match_race", return_value=None):
        result = pace_strategy_impl(user_id=1, race_name="Nonexistent Race")
    assert result.status == "error"
    assert result.error == "race_not_found"


def test_pace_strategy_uses_curated_course_profile_when_available():
    matched = _matched_race()
    checkpoints = [{"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}]
    paced = [{"name": "Start", "distance_km": 0.0, "elevation_m": 0, "target_pace": "0:00", "split_time": "0:00:00"}]

    with (
        patch("services.race_matcher.match_race", return_value=matched),
        patch("services.race_matcher.course_profile", return_value={"checkpoints": checkpoints}) as mock_profile,
        patch("services.race_estimator.RaceEstimator.synthesize_course") as mock_synth,
        # Patched at its source (main._calculate_pacing_core), not on
        # pacing_tools, since pacing_tools imports it lazily inside the
        # function body (see Step 3's circular-import note) rather than at
        # module level -- there's no module-level attribute to patch here.
        patch("main._calculate_pacing_core", return_value=paced) as mock_calc,
    ):
        result = pace_strategy_impl(user_id=1, race_name="Dalat Ultra Trail", target_time_hours=12.75)

    mock_profile.assert_called_once_with("Dalat Ultra Trail", "70K")
    mock_synth.assert_not_called()
    assert mock_calc.call_args.kwargs["request"].checkpoints == checkpoints
    assert mock_calc.call_args.kwargs["request"].target_time_mins == 12.75 * 60
    assert result.status == "success"
    assert result.card_type == "pacing_splits"
    assert result.card_data["race_name"] == "Dalat Ultra Trail 70K"
    assert result.card_data["distance_label"] == "70K"
    assert result.card_data["splits"] == paced


def test_pace_strategy_falls_back_to_synthesized_course():
    matched = _matched_race()
    synthesized = [{"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}]

    with (
        patch("services.race_matcher.match_race", return_value=matched),
        patch("services.race_matcher.course_profile", return_value=None),
        patch("services.race_estimator.RaceEstimator.synthesize_course", return_value=synthesized) as mock_synth,
        patch("main._calculate_pacing_core", return_value=[]),
    ):
        result = pace_strategy_impl(user_id=1, race_name="Dalat Ultra Trail", target_time_hours=10.0)

    mock_synth.assert_called_once_with(71.2, 3150.0)
    assert result.status == "success"
