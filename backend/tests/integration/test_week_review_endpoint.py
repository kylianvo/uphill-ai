"""Integration tests for GET /api/coach/week-review/{plan_id}/{week_number} and
its coach-scoped mirror -- exercises get_week_planned_volume/get_week_review's
raw SQL against a real Postgres, which the mocked unit tests in
tests/unit/test_week_review.py can't catch (column typos, join mistakes)."""

from unittest.mock import patch

from db import get_plan_workouts, save_workouts


def _create_plan_with_one_week_of_workouts(client, headers):
    resp = client.post(
        "/api/coach/generate-plan",
        headers=headers,
        json={
            "goal_type": "finish",
            "race_name": "Week Review Test 50K",
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
                "title": "Easy Run",
                "type": "easy",
                "duration_minutes": 60,
                "distance_km": 10,
                "elevation_gain_m": 100,
                "target_zone": "Z2",
                "description": "Conversational pace.",
            },
            {
                "week_number": 1,
                "day_of_week": "Wednesday",
                "phase": "base",
                "title": "Long Run",
                "type": "long_run",
                "duration_minutes": 90,
                "distance_km": 15,
                "elevation_gain_m": 300,
                "target_zone": "Z2",
                "description": "Steady climb.",
            },
        ],
    )
    workouts = get_plan_workouts(plan_id)
    return plan_id, workouts


def test_week_review_endpoint_returns_planned_actual_and_narrative(client, auth_headers, mock_plan_generation):
    plan_id, workouts = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
    easy_run = next(w for w in workouts if w["title"] == "Easy Run")

    client.patch(
        "/api/coach/workouts/log",
        headers=auth_headers["headers"],
        json={"workout_id": easy_run["id"], "is_completed": 1},
    )

    fake_narrative = {"summary": "fake", "highlights": ["h1"], "watch": ["w1"]}
    with patch("main.generate_week_narrative", return_value=fake_narrative):
        resp = client.get(f"/api/coach/week-review/{plan_id}/1", headers=auth_headers["headers"])

    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["week_number"] == 1
    assert data["planned"]["duration_minutes"] == 150.0  # 60 + 90
    assert data["planned"]["distance_km"] == 25.0
    assert data["planned"]["elevation_gain_m"] == 400.0
    assert data["planned"]["workout_count"] == 2

    # No synced watch activity for the "completed" workout -- checkbox-based
    # completion (1/2 sessions ticked, both 60/90-min -- 60 completed of 150
    # planned) diverges from recording-based completion (nothing recorded).
    assert data["checkbox_completion_pct"] == 40  # round(60/150*100)
    assert data["completion_pct"] == 0
    assert data["completion_pct"] != data["checkbox_completion_pct"]

    states = {w["workout_id"]: w["actual"]["state"] for w in data["per_workout"]}
    assert states[easy_run["id"]] == "checkbox_only"

    assert data["coverage"] == {"completed_count": 1, "matched_count": 0, "checkbox_only_count": 1}
    assert data["unplanned"] == []
    assert data["missed"] == []
    assert data["narrative"] == fake_narrative


def test_week_review_endpoint_requires_plan_ownership(client, auth_headers):
    resp = client.get("/api/coach/week-review/999999/1", headers=auth_headers["headers"])
    assert resp.status_code == 404
