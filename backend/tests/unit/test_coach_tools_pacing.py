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
    with (
        patch("db.get_active_plan", return_value=None),
        patch("services.race_matcher.match_race", return_value=None),
    ):
        result = pace_strategy_impl(user_id=1, race_name="Nonexistent Race")
    assert result.status == "error"
    assert result.error == "race_not_found"


def test_pace_strategy_uses_curated_course_profile_when_available():
    matched = _matched_race()
    checkpoints = [{"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}]
    paced = [{"name": "Start", "distance_km": 0.0, "elevation_m": 0, "target_pace": "0:00", "split_time": "0:00:00"}]

    with (
        patch("db.get_active_plan", return_value=None),
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
    # target_time_hours is carried into card_data so the frontend can pass it
    # through the "Open in Pace Strategy" deep link.
    assert result.card_data["target_time_hours"] == 12.75


def test_pace_strategy_falls_back_to_synthesized_course():
    matched = _matched_race()
    synthesized = [{"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}]

    with (
        patch("services.race_matcher.match_race", return_value=matched),
        patch("db.get_active_plan", return_value=None),
        patch("services.race_matcher.course_profile", return_value=None),
        patch("services.race_estimator.RaceEstimator.synthesize_course", return_value=synthesized) as mock_synth,
        patch("main._calculate_pacing_core", return_value=[]),
    ):
        result = pace_strategy_impl(user_id=1, race_name="Dalat Ultra Trail", target_time_hours=10.0)

    mock_synth.assert_called_once_with(71.2, 3150.0)
    assert result.status == "success"


def test_pace_strategy_uses_active_plan_distance_and_elevation_when_race_matches():
    # No distance_km given by the athlete/model, but their active plan is
    # for the same race and has course_distance_km/course_elevation_gain_m
    # set -> those should be used as defaults instead of erroring out.
    plan = {"race_name": "Dalat Ultra Trail", "course_distance_km": 75.0, "course_elevation_gain_m": 4200.0}
    matched_final = _matched_race(distance_km=75.0, elevation_gain_m=4200.0, distance_label="75km")
    checkpoints = [{"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}]
    paced = [{"name": "Start", "distance_km": 0.0, "elevation_m": 0, "target_pace": "0:00", "split_time": "0:00:00"}]

    with (
        patch("db.get_active_plan", return_value=plan),
        # Both the plan-race lookup and the athlete's query resolve to the
        # same curated race -- proves same-race comparison via matched
        # race_name, not raw string equality.
        patch("services.race_matcher.match_race") as mock_match,
        patch("services.race_matcher.course_profile", return_value={"checkpoints": checkpoints}),
        patch("main._calculate_pacing_core", return_value=paced) as mock_calc,
    ):
        mock_match.side_effect = [
            _matched_race(race_name="Dalat Ultra Trail 70K"),  # plan race lookup
            _matched_race(race_name="Dalat Ultra Trail 70K"),  # query race lookup (comparison)
            matched_final,  # final distance-aware match
        ]
        result = pace_strategy_impl(user_id=1, race_name="Dalat Ultra Trail", target_time_hours=13.0)

    # Final match_race call must have been given the plan's course_distance_km.
    assert mock_match.call_args_list[-1].kwargs.get("distance_km") == 75.0
    assert mock_calc.call_args.kwargs["request"].checkpoints == checkpoints
    assert result.status == "success"


def test_pace_strategy_multi_distance_race_without_distance_returns_clarify():
    matched = _matched_race(distance_label=None, distance_km=None, elevation_gain_m=None)
    distances = [
        {"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2000.0},
        {"label": "75km", "distance_km": 75.0, "elevation_gain_m": 3500.0},
        {"label": "100km", "distance_km": 100.0, "elevation_gain_m": 5000.0},
    ]

    with (
        patch("db.get_active_plan", return_value=None),
        patch("services.race_matcher.match_race", return_value=matched),
        patch("services.race_matcher.race_distances", return_value=distances) as mock_distances,
    ):
        result = pace_strategy_impl(user_id=1, race_name="Dalat Ultra Trail", target_time_hours=13.0)

    mock_distances.assert_called_once_with(matched.race_name)
    assert result.status == "error"
    assert result.error == "distance_required"
    assert result.clarify is not None
    assert result.clarify["options"] == ["50km", "75km", "100km"]
    assert "prompt" in result.clarify


def test_pace_strategy_distance_given_but_no_elevation_anywhere_returns_error():
    matched = _matched_race(distance_km=75.0, elevation_gain_m=None, distance_label="75km")

    with (
        patch("db.get_active_plan", return_value=None),
        patch("services.race_matcher.match_race", return_value=matched),
        patch("services.race_matcher.course_profile", return_value=None),
        patch("services.race_estimator.RaceEstimator.synthesize_course") as mock_synth,
    ):
        result = pace_strategy_impl(user_id=1, race_name="Dalat Ultra Trail", distance_km=75.0, target_time_hours=13.0)

    mock_synth.assert_not_called()
    assert result.status == "error"
    assert result.error == "elevation_required"


def test_pace_strategy_distance_and_elevation_args_succeed_via_synthesize():
    matched = _matched_race(distance_km=75.0, elevation_gain_m=None, distance_label="75km")
    synthesized = [{"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}]
    paced = [{"name": "Start", "distance_km": 0.0, "elevation_m": 0, "target_pace": "0:00", "split_time": "0:00:00"}]

    with (
        patch("db.get_active_plan", return_value=None),
        patch("services.race_matcher.match_race", return_value=matched),
        patch("services.race_matcher.course_profile", return_value=None),
        patch("services.race_estimator.RaceEstimator.synthesize_course", return_value=synthesized) as mock_synth,
        patch("main._calculate_pacing_core", return_value=paced),
    ):
        result = pace_strategy_impl(
            user_id=1,
            race_name="Dalat Ultra Trail",
            distance_km=75.0,
            elevation_gain_m=3800.0,
            target_time_hours=13.0,
        )

    mock_synth.assert_called_once_with(75.0, 3800.0)
    assert result.status == "success"


def test_pace_strategy_synthesized_course_reports_athlete_supplied_elevation():
    # KB has no elevation for this distance (matched.elevation_gain_m is
    # None); the athlete supplied 3500m directly. card_data.total_elevation_m
    # must reflect what was actually used to build the course (3500), not
    # the (missing) KB value.
    matched = _matched_race(distance_km=75.0, elevation_gain_m=None, distance_label="75km")
    synthesized = [{"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0}]
    paced = [{"name": "Start", "distance_km": 0.0, "elevation_m": 0, "target_pace": "0:00", "split_time": "0:00:00"}]

    with (
        patch("db.get_active_plan", return_value=None),
        patch("services.race_matcher.match_race", return_value=matched),
        patch("services.race_matcher.course_profile", return_value=None),
        patch("services.race_estimator.RaceEstimator.synthesize_course", return_value=synthesized) as mock_synth,
        patch("main._calculate_pacing_core", return_value=paced),
    ):
        result = pace_strategy_impl(
            user_id=1,
            race_name="Dalat Ultra Trail",
            distance_km=75.0,
            elevation_gain_m=3500.0,
            target_time_hours=13.0,
        )

    mock_synth.assert_called_once_with(75.0, 3500.0)
    assert result.status == "success"
    assert result.card_data["total_elevation_m"] == 3500


def test_pace_strategy_curated_profile_reports_summed_segment_gains():
    # A curated profile's actual elevation (sum of the checkpoints' own
    # segment_gain_meters) can differ from the race-level matched.elevation_gain_m
    # (e.g. a stale/rounded KB figure); the card must show what the profile
    # itself totals to, not the KB race-level number.
    matched = _matched_race(elevation_gain_m=3150.0)
    checkpoints = [
        {"name": "Start", "distance_meters": 0, "segment_gain_meters": 0.0, "segment_loss_meters": 0.0},
        {"name": "CP1", "distance_meters": 20000, "segment_gain_meters": 900.0, "segment_loss_meters": 200.0},
        {"name": "Finish", "distance_meters": 71200, "segment_gain_meters": 1400.5, "segment_loss_meters": 300.0},
    ]
    paced = [{"name": "Start", "distance_km": 0.0, "elevation_m": 0, "target_pace": "0:00", "split_time": "0:00:00"}]

    with (
        patch("db.get_active_plan", return_value=None),
        patch("services.race_matcher.match_race", return_value=matched),
        patch("services.race_matcher.course_profile", return_value={"checkpoints": checkpoints}),
        patch("main._calculate_pacing_core", return_value=paced),
    ):
        result = pace_strategy_impl(user_id=1, race_name="Dalat Ultra Trail", target_time_hours=12.75)

    assert result.status == "success"
    assert result.card_data["total_elevation_m"] == round(0.0 + 900.0 + 1400.5)
