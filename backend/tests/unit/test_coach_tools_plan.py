import datetime
import decimal
from unittest.mock import patch

from services.coach_tools.plan_tools import get_week_impl, week_review_impl


def test_get_week_no_active_plan_returns_error():
    with patch("db.get_active_plan", return_value=None):
        result = get_week_impl(user_id=1)
    assert result.status == "error"
    assert result.error == "no_active_plan"


def test_get_week_defaults_to_current_week():
    plan = {"id": 42, "current_week": 3, "start_date": "2026-01-01", "race_date": "2026-06-01"}
    workouts = [
        {
            "id": 100,
            "day_of_week": "Tuesday",
            "title": "Hill Repeats",
            "type": "Hills",
            "distance_km": 10.0,
            "elevation_gain_m": 450.0,
            "description": "6x3min uphill Zone 4",
            "approved_at": datetime.datetime(2026, 1, 2, 12, 0, 0),
            "duration_minutes": decimal.Decimal("60"),
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
    assert result.card_data["plan_start_date"] == "2026-01-01"
    assert result.card_data["race_date"] == "2026-06-01"

    workout = result.card_data["workouts"][0]
    # Full row, not the old renamed keys.
    assert "day" not in workout
    assert "name" not in workout
    assert "workout_type" not in workout
    assert workout["id"] == 100
    assert workout["day_of_week"] == "Tuesday"
    assert workout["title"] == "Hill Repeats"
    assert workout["type"] == "Hills"
    # JSON-safety: datetime -> isoformat string, Decimal -> float.
    assert workout["approved_at"] == "2026-01-02T12:00:00"
    assert workout["duration_minutes"] == 60.0
    assert isinstance(workout["duration_minutes"], float)


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

    card_data = result.card_data
    # Raw db.get_week_review shape, unflattened.
    assert card_data["week_number"] == 4
    assert card_data["planned"] == review["planned"]
    assert card_data["actual"] == review["actual"]
    assert card_data["completion_pct"] == 93
    assert card_data["checkbox_completion_pct"] == 90
    assert card_data["per_workout"] == []
    assert card_data["unplanned"] == []
    assert card_data["missed"] == review["missed"]
    assert card_data["coverage"] == {}
    # Plus the narrative and computed label.
    assert set(card_data["narrative"].keys()) == {"summary", "highlights", "watch"}
    assert card_data["week_label"] == "1 Week Ago (Week 4)"
    # weeks_ago/target_week let the frontend build a bilingual header itself
    # instead of rendering the English week_label string.
    assert card_data["weeks_ago"] == 1
    assert card_data["target_week"] == 4
    # Old flattened keys are gone.
    for removed_key in (
        "completed_km",
        "planned_km",
        "compliance_pct",
        "completed_vert_m",
        "planned_vert_m",
        "missed_workouts",
        "coach_verdict",
    ):
        assert removed_key not in card_data
