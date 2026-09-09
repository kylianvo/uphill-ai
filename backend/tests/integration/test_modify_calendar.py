"""Integration tests for POST /api/coach/modify-calendar."""

from unittest.mock import AsyncMock, patch

from db import get_plan_workouts, save_workouts


def _setup_test_plan(client, auth_headers):
    headers = auth_headers["headers"]
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=([], "recreational"),
    ):
        resp = client.post(
            "/api/coach/generate-plan",
            headers=headers,
            json={
                "goal_type": "finish",
                "race_name": "Calendar Swap 50K",
                "race_date": "2027-05-01",
                "plan_start_date": "2027-03-15",
                "days_per_week": 4,
                "current_weekly_km": 30,
            },
        )
    plan_id = resp.json()["plan"]["id"]

    save_workouts(
        plan_id,
        [
            {
                "week_number": 1,
                "day_of_week": "Monday",
                "phase": "base",
                "title": "Monday Easy Run",
                "type": "easy",
                "duration_minutes": 45,
                "distance_km": 8.0,
                "target_zone": "Z2",
            },
            {
                "week_number": 1,
                "day_of_week": "Wednesday",
                "phase": "base",
                "title": "Wednesday Intervals",
                "type": "interval",
                "duration_minutes": 50,
                "distance_km": 9.0,
                "target_zone": "Z4",
            },
        ],
    )
    return plan_id


def test_swap_workouts_between_two_active_days(client, auth_headers):
    plan_id = _setup_test_plan(client, auth_headers)

    resp = client.post(
        "/api/coach/modify-calendar",
        headers=auth_headers["headers"],
        json={
            "plan_id": plan_id,
            "week_number": 1,
            "day_1": "Monday",
            "day_2": "Wednesday",
        },
    )
    assert resp.status_code == 200, resp.text
    workouts = get_plan_workouts(plan_id)
    by_day = {w["day_of_week"]: w["title"] for w in workouts if w["week_number"] == 1}
    assert by_day["Monday"] == "Wednesday Intervals"
    assert by_day["Wednesday"] == "Monday Easy Run"


def test_move_workout_to_rest_day(client, auth_headers):
    plan_id = _setup_test_plan(client, auth_headers)

    # Tuesday has 0 workouts (rest day). Move Monday -> Tuesday
    resp = client.post(
        "/api/coach/modify-calendar",
        headers=auth_headers["headers"],
        json={
            "plan_id": plan_id,
            "week_number": 1,
            "day_1": "Monday",
            "day_2": "Tuesday",
        },
    )
    assert resp.status_code == 200, resp.text
    workouts = get_plan_workouts(plan_id)
    by_day = {w["day_of_week"]: w["title"] for w in workouts if w["week_number"] == 1}
    assert "Monday" not in by_day
    assert by_day["Tuesday"] == "Monday Easy Run"
    assert by_day["Wednesday"] == "Wednesday Intervals"


def test_move_workout_from_rest_day(client, auth_headers):
    plan_id = _setup_test_plan(client, auth_headers)

    # Move from Rest Day (Thursday, 0 workouts) to Wednesday (has workouts)
    # This should relocate Wednesday to Thursday
    resp = client.post(
        "/api/coach/modify-calendar",
        headers=auth_headers["headers"],
        json={
            "plan_id": plan_id,
            "week_number": 1,
            "day_1": "Thursday",
            "day_2": "Wednesday",
        },
    )
    assert resp.status_code == 200, resp.text
    workouts = get_plan_workouts(plan_id)
    by_day = {w["day_of_week"]: w["title"] for w in workouts if w["week_number"] == 1}
    assert "Wednesday" not in by_day
    assert by_day["Thursday"] == "Wednesday Intervals"


def test_swap_two_rest_days_returns_400(client, auth_headers):
    plan_id = _setup_test_plan(client, auth_headers)

    # Friday and Saturday both have 0 workouts
    resp = client.post(
        "/api/coach/modify-calendar",
        headers=auth_headers["headers"],
        json={
            "plan_id": plan_id,
            "week_number": 1,
            "day_1": "Friday",
            "day_2": "Saturday",
        },
    )
    assert resp.status_code == 400


def test_swap_same_day_returns_200(client, auth_headers):
    plan_id = _setup_test_plan(client, auth_headers)

    resp = client.post(
        "/api/coach/modify-calendar",
        headers=auth_headers["headers"],
        json={
            "plan_id": plan_id,
            "week_number": 1,
            "day_1": "Monday",
            "day_2": "Monday",
        },
    )
    assert resp.status_code == 200
