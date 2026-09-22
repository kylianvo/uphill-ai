from unittest.mock import patch

from services.coach_tools.plan_tools import get_week_impl, week_review_impl


def test_get_week_no_active_plan_returns_error():
    with patch("db.get_active_plan", return_value=None):
        result = get_week_impl(user_id=1)
    assert result.status == "error"
    assert result.error == "no_active_plan"


def test_get_week_defaults_to_current_week():
    plan = {"id": 42, "current_week": 3}
    workouts = [
        {
            "day_of_week": "Tuesday",
            "title": "Hill Repeats",
            "type": "Hills",
            "distance_km": 10.0,
            "elevation_gain_m": 450.0,
            "description": "6x3min uphill Zone 4",
        }
    ]
    with (
        patch("db.get_active_plan", return_value=plan),
        patch("db.get_plan_workouts_for_week", return_value=workouts) as mock_week,
    ):
        result = get_week_impl(user_id=1)
    mock_week.assert_called_once_with(42, 3)
    assert result.status == "success"
    assert result.card_type == "week_schedule"
    assert result.card_data["week_number"] == 3
    assert result.card_data["total_distance_km"] == 10.0
    assert result.card_data["total_elevation_gain_m"] == 450
    assert result.card_data["workouts"][0]["day"] == "Tuesday"
    assert result.card_data["workouts"][0]["name"] == "Hill Repeats"


def test_get_week_explicit_week_number():
    plan = {"id": 42, "current_week": 3}
    with (
        patch("db.get_active_plan", return_value=plan),
        patch("db.get_plan_workouts_for_week", return_value=[]) as mock_week,
    ):
        result = get_week_impl(user_id=1, week_number=1)
    mock_week.assert_called_once_with(42, 1)
    assert result.card_data["week_number"] == 1


def test_week_review_no_active_plan_returns_error():
    with patch("db.get_active_plan", return_value=None):
        result = week_review_impl(user_id=1)
    assert result.status == "error"
    assert result.error == "no_active_plan"


def test_week_review_computes_current_week_minus_weeks_ago():
    plan = {"id": 7, "current_week": 5, "start_date": "2026-01-01"}
    review = {
        "week_number": 4,
        "planned": {"duration_minutes": 300, "distance_km": 45.0, "elevation_gain_m": 1500},
        "actual": {
            "total_actual_minutes": 280,
            "total_actual_vert_m": 1420,
            "matched_km": 42.0,
            "unplanned_km": 0.0,
            "total_actual_km": 42.0,
            "total_activities_count": 4,
        },
        "completion_pct": 93,
        "checkbox_completion_pct": 90,
        "per_workout": [],
        "unplanned": [],
        "missed": [{"title": "Rest Day mobility", "type": "Mobility"}],
        "coverage": {},
    }
    with (
        patch("db.get_active_plan", return_value=plan),
        patch("db.get_week_review", return_value=review) as mock_review,
    ):
        result = week_review_impl(user_id=1, weeks_ago=1)
    mock_review.assert_called_once_with(user_id=1, plan_id=7, week_number=4, plan_start_date="2026-01-01")
    assert result.status == "success"
    assert result.card_type == "week_review"
    assert result.card_data["completed_km"] == 42.0
    assert result.card_data["planned_km"] == 45.0
    assert result.card_data["compliance_pct"] == 93
    assert result.card_data["missed_workouts"] == ["Rest Day mobility"]
    assert "coach_verdict" in result.card_data
