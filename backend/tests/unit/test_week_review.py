"""Unit tests for the week-level planned-vs-actual review: get_week_planned_volume
(the missing week-scoped counterpart to get_block_completion) and get_week_review
(composes planned + actual + per-workout + unplanned + missed + coverage)."""

from unittest.mock import MagicMock, patch

from db import get_week_planned_volume, get_week_review


def _mock_planned_row(duration_minutes=0.0, distance_km=0.0, elevation_gain_m=0.0, workout_count=0):
    row = MagicMock()
    row.duration_minutes = duration_minutes
    row.distance_km = distance_km
    row.elevation_gain_m = elevation_gain_m
    row.workout_count = workout_count
    return row


def _actual_volume(
    total_actual_km=0.0,
    total_actual_minutes=0,
    total_actual_vert_m=0.0,
    matched_km=0.0,
    matched_vert_m=0.0,
    matched_count=0,
    unplanned_km=0.0,
    unplanned_vert_m=0.0,
    unplanned_count=0,
):
    return {
        "total_actual_km": total_actual_km,
        "total_actual_hours": round(total_actual_minutes / 60.0, 1),
        "total_actual_minutes": total_actual_minutes,
        "total_actual_vert_m": total_actual_vert_m,
        "matched_km": matched_km,
        "matched_hours": round(matched_km, 1),
        "matched_vert_m": matched_vert_m,
        "matched_count": matched_count,
        "unplanned_km": unplanned_km,
        "unplanned_hours": 0.0,
        "unplanned_vert_m": unplanned_vert_m,
        "unplanned_count": unplanned_count,
        "total_activities_count": matched_count + unplanned_count,
    }


def _workout(id, day_of_week, title, duration_minutes, distance_km, elevation_gain_m, is_completed=0, is_missed=0):
    return {
        "id": id,
        "week_number": 3,
        "day_of_week": day_of_week,
        "title": title,
        "type": "Run",
        "duration_minutes": duration_minutes,
        "distance_km": distance_km,
        "elevation_gain_m": elevation_gain_m,
        "is_completed": is_completed,
        "is_missed": is_missed,
    }


def _mock_workout_row(workout: dict):
    """A fake SQLAlchemy Row for a `workouts` table row -- _row_to_dict() reads
    `row._mapping`, so the mock needs one rather than plain attributes."""
    row = MagicMock()
    row._mapping = workout
    return row


def test_get_week_planned_volume_aggregates():
    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = _mock_planned_row(150.0, 25.5, 600.0, 3)

        result = get_week_planned_volume(plan_id=5, week_number=3)

    assert result == {
        "week_number": 3,
        "duration_minutes": 150.0,
        "distance_km": 25.5,
        "elevation_gain_m": 600.0,
        "workout_count": 3,
    }


def test_get_week_planned_volume_no_workouts():
    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = _mock_planned_row(0, 0, 0, 0)

        result = get_week_planned_volume(plan_id=5, week_number=3)

    assert result == {
        "week_number": 3,
        "duration_minutes": 0.0,
        "distance_km": 0.0,
        "elevation_gain_m": 0.0,
        "workout_count": 0,
    }


def _run_week_review(
    planned,
    plan_workouts,
    matched_activities,
    actual,
    checkbox_rows,
    matches_for_review,
    plan_start_date="2026-02-01",
):
    with (
        patch("db.get_week_planned_volume", return_value=planned),
        patch("db.get_activities_for_block", return_value=matched_activities),
        patch("db.get_block_actual_volume", return_value=actual),
        patch("db.get_matches_for_review", return_value=matches_for_review),
        patch("db.engine.connect") as mock_connect,
    ):
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        # get_week_review issues two engine.connect().execute().fetchall() calls in
        # order: the checkbox-completion query, then the week-scoped workouts query.
        mock_conn.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=checkbox_rows)),
            MagicMock(fetchall=MagicMock(return_value=[_mock_workout_row(w) for w in plan_workouts])),
        ]

        return get_week_review(user_id=1, plan_id=5, week_number=3, plan_start_date=plan_start_date)


def test_get_week_review_every_workout_matched():
    planned = {
        "week_number": 3,
        "duration_minutes": 120.0,
        "distance_km": 20.0,
        "elevation_gain_m": 400.0,
        "workout_count": 2,
    }
    plan_workouts = [
        _workout(1, "Monday", "Easy Run", 60.0, 10.0, 200.0, is_completed=1),
        _workout(2, "Wednesday", "Tempo", 60.0, 10.0, 200.0, is_completed=1),
    ]
    matched_activities = [
        {"activity_id": 201, "workout_id": 1, "distance_km": 10.0, "duration_seconds": 3600, "elevation_gain_m": 200.0},
        {"activity_id": 202, "workout_id": 2, "distance_km": 10.0, "duration_seconds": 3600, "elevation_gain_m": 200.0},
    ]
    actual = _actual_volume(
        total_actual_km=20.0,
        total_actual_minutes=120,
        total_actual_vert_m=400.0,
        matched_km=20.0,
        matched_vert_m=400.0,
        matched_count=2,
    )
    checkbox_rows = [(1, 60.0), (1, 60.0)]
    matches_for_review = [
        {"activity_id": 201, "workout_id": 1},
        {"activity_id": 202, "workout_id": 2},
    ]

    review = _run_week_review(planned, plan_workouts, matched_activities, actual, checkbox_rows, matches_for_review)

    assert review["completion_pct"] == 100
    assert review["checkbox_completion_pct"] == 100
    assert [w["actual"]["state"] for w in review["per_workout"]] == ["matched", "matched"]
    assert review["missed"] == []
    assert review["unplanned"] == []
    assert review["coverage"] == {"completed_count": 2, "matched_count": 2, "checkbox_only_count": 0}


def test_get_week_review_none_matched():
    planned = {
        "week_number": 3,
        "duration_minutes": 120.0,
        "distance_km": 20.0,
        "elevation_gain_m": 400.0,
        "workout_count": 2,
    }
    plan_workouts = [
        _workout(1, "Monday", "Easy Run", 60.0, 10.0, 200.0, is_completed=1),
        _workout(2, "Wednesday", "Tempo", 60.0, 10.0, 200.0, is_completed=1),
    ]
    actual = _actual_volume()  # nothing recorded at all
    checkbox_rows = [(1, 60.0), (1, 60.0)]

    review = _run_week_review(
        planned, plan_workouts, matched_activities=[], actual=actual, checkbox_rows=checkbox_rows, matches_for_review=[]
    )

    assert review["completion_pct"] == 0
    assert review["checkbox_completion_pct"] == 100
    assert [w["actual"]["state"] for w in review["per_workout"]] == ["checkbox_only", "checkbox_only"]
    assert review["coverage"] == {"completed_count": 2, "matched_count": 0, "checkbox_only_count": 2}


def test_get_week_review_partially_matched():
    planned = {
        "week_number": 3,
        "duration_minutes": 180.0,
        "distance_km": 30.0,
        "elevation_gain_m": 600.0,
        "workout_count": 3,
    }
    plan_workouts = [
        _workout(1, "Monday", "Easy Run", 60.0, 10.0, 200.0, is_completed=1),
        _workout(2, "Wednesday", "Tempo", 60.0, 10.0, 200.0, is_completed=1),
        _workout(3, "Friday", "Recovery Jog", 60.0, 10.0, 200.0, is_completed=0),
    ]
    matched_activities = [
        {"activity_id": 201, "workout_id": 1, "distance_km": 10.0, "duration_seconds": 4200, "elevation_gain_m": 220.0},
    ]
    actual = _actual_volume(
        total_actual_km=10.0,
        total_actual_minutes=70,
        total_actual_vert_m=220.0,
        matched_km=10.0,
        matched_vert_m=220.0,
        matched_count=1,
    )
    checkbox_rows = [(1, 60.0), (1, 60.0), (0, 60.0)]

    review = _run_week_review(planned, plan_workouts, matched_activities, actual, checkbox_rows, matches_for_review=[])

    assert review["completion_pct"] == 39  # round(70/180*100)
    assert review["checkbox_completion_pct"] == 67  # round(120/180*100)
    states = {w["workout_id"]: w["actual"]["state"] for w in review["per_workout"]}
    assert states == {1: "matched", 2: "checkbox_only", 3: "pending"}
    assert review["coverage"] == {"completed_count": 2, "matched_count": 1, "checkbox_only_count": 1}


def test_get_week_review_unplanned_activities_only():
    planned = {
        "week_number": 3,
        "duration_minutes": 60.0,
        "distance_km": 10.0,
        "elevation_gain_m": 200.0,
        "workout_count": 1,
    }
    plan_workouts = [
        _workout(1, "Monday", "Easy Run", 60.0, 10.0, 200.0, is_completed=0, is_missed=1),
    ]
    actual = _actual_volume(
        total_actual_km=5.0,
        total_actual_minutes=30,
        total_actual_vert_m=50.0,
        unplanned_km=5.0,
        unplanned_vert_m=50.0,
        unplanned_count=1,
    )
    checkbox_rows = [(0, 60.0)]
    matches_for_review = [
        {"activity_id": 301, "workout_id": None, "distance_km": 5.0, "duration_seconds": 1800, "activity_type": "Run"},
    ]

    review = _run_week_review(
        planned,
        plan_workouts,
        matched_activities=[],
        actual=actual,
        checkbox_rows=checkbox_rows,
        matches_for_review=matches_for_review,
    )

    assert review["completion_pct"] == 50  # round(30/60*100)
    assert review["checkbox_completion_pct"] == 0
    assert len(review["unplanned"]) == 1
    assert review["unplanned"][0]["workout_id"] is None
    assert review["missed"] == plan_workouts  # the one is_missed=1 workout
    assert review["coverage"] == {"completed_count": 0, "matched_count": 0, "checkbox_only_count": 0}


def test_get_week_review_zero_completed_workouts():
    planned = {
        "week_number": 3,
        "duration_minutes": 60.0,
        "distance_km": 10.0,
        "elevation_gain_m": 200.0,
        "workout_count": 1,
    }
    plan_workouts = [
        _workout(1, "Monday", "Easy Run", 60.0, 10.0, 200.0, is_completed=0, is_missed=0),
    ]
    actual = _actual_volume()
    checkbox_rows = [(0, 60.0)]

    review = _run_week_review(
        planned, plan_workouts, matched_activities=[], actual=actual, checkbox_rows=checkbox_rows, matches_for_review=[]
    )

    assert review["completion_pct"] == 0
    assert review["checkbox_completion_pct"] == 0
    assert review["per_workout"][0]["actual"]["state"] == "pending"
    assert review["missed"] == []
    assert review["coverage"] == {"completed_count": 0, "matched_count": 0, "checkbox_only_count": 0}


def test_get_week_review_actual_exceeding_planned():
    planned = {
        "week_number": 3,
        "duration_minutes": 60.0,
        "distance_km": 10.0,
        "elevation_gain_m": 200.0,
        "workout_count": 1,
    }
    plan_workouts = [
        _workout(1, "Monday", "Easy Run", 60.0, 10.0, 200.0, is_completed=1),
    ]
    matched_activities = [
        {"activity_id": 401, "workout_id": 1, "distance_km": 15.0, "duration_seconds": 5400, "elevation_gain_m": 300.0},
    ]
    actual = _actual_volume(
        total_actual_km=15.0,
        total_actual_minutes=90,
        total_actual_vert_m=300.0,
        matched_km=15.0,
        matched_vert_m=300.0,
        matched_count=1,
    )
    checkbox_rows = [(1, 60.0)]

    review = _run_week_review(planned, plan_workouts, matched_activities, actual, checkbox_rows, matches_for_review=[])

    assert review["completion_pct"] == 150  # round(90/60*100), not capped at 100
    assert review["checkbox_completion_pct"] == 100


def test_get_week_review_completion_figures_can_differ():
    """The exact scenario from the spec: a 90-minute session ticked complete but
    recorded for only 40 minutes reads as 100% checkbox-based and ~44% recording-based."""
    planned = {
        "week_number": 3,
        "duration_minutes": 90.0,
        "distance_km": 15.0,
        "elevation_gain_m": 300.0,
        "workout_count": 1,
    }
    plan_workouts = [
        _workout(1, "Monday", "Long Run", 90.0, 15.0, 300.0, is_completed=1),
    ]
    matched_activities = [
        {"activity_id": 401, "workout_id": 1, "distance_km": 6.0, "duration_seconds": 2400, "elevation_gain_m": 100.0},
    ]
    actual = _actual_volume(
        total_actual_km=6.0,
        total_actual_minutes=40,
        total_actual_vert_m=100.0,
        matched_km=6.0,
        matched_vert_m=100.0,
        matched_count=1,
    )
    checkbox_rows = [(1, 90.0)]

    review = _run_week_review(planned, plan_workouts, matched_activities, actual, checkbox_rows, matches_for_review=[])

    assert review["completion_pct"] == 44
    assert review["checkbox_completion_pct"] == 100
    assert review["completion_pct"] != review["checkbox_completion_pct"]
