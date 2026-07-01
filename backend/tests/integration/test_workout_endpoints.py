"""Integration tests for PATCH /api/coach/workouts/log."""

from unittest.mock import AsyncMock, patch

from db import get_plan_workouts, save_workouts


def _create_plan_with_one_workout(client, headers):
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=[],
    ):
        resp = client.post(
            "/api/coach/generate-plan",
            headers=headers,
            json={
                "goal_type": "finish",
                "race_name": "Test 50K",
                "race_date": "2027-05-01",
                "plan_start_date": "2027-03-15",
                "days_per_week": 4,
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
                "duration_minutes": 45,
                "distance_km": 8.0,
                "target_zone": "Z2",
                "description": "Conversational pace.",
            }
        ],
    )
    workout_id = get_plan_workouts(plan_id)[0]["id"]
    return plan_id, workout_id


class TestLogWorkout:
    def test_marks_a_workout_completed_with_rpe_and_notes(self, client, auth_headers):
        _plan_id, workout_id = _create_plan_with_one_workout(client, auth_headers["headers"])

        resp = client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1, "rpe": 6, "notes": "Felt strong."},
        )
        assert resp.status_code == 200, resp.text
        updated = next(w for w in resp.json()["workouts"] if w["id"] == workout_id)
        assert updated["is_completed"] == 1
        assert updated["rpe"] == 6
        assert updated["notes"] == "Felt strong."

    def test_rejects_a_workout_not_in_the_active_plan(self, client, auth_headers):
        resp = client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": 999999, "is_completed": 1},
        )
        assert resp.status_code in (403, 404)

    def test_rejects_when_the_user_has_no_active_plan(self, client, auth_headers):
        resp = client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": 1, "is_completed": 1},
        )
        assert resp.status_code == 404

    def test_cannot_log_a_workout_belonging_to_another_users_plan(self, client, auth_headers):
        _plan_id, workout_id = _create_plan_with_one_workout(client, auth_headers["headers"])

        other_login = client.post("/api/auth/mock-login", json={"email": "workout-other@uphill.ai"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['session_token']}"}

        resp = client.patch(
            "/api/coach/workouts/log",
            headers=other_headers,
            json={"workout_id": workout_id, "is_completed": 1},
        )
        assert resp.status_code in (403, 404)
