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


def test_save_workouts_flattens_nested_llm_fields(client, auth_headers):
    """Gemini occasionally nests a text field as an object/array (sectioned
    description, {min,max} HR range) — saving must flatten, not crash with
    psycopg2 "can't adapt type 'dict'"."""
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=[],
    ):
        resp = client.post(
            "/api/coach/generate-plan",
            headers=auth_headers["headers"],
            json={
                "goal_type": "finish",
                "race_name": "Nested 50K",
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
                "day_of_week": "Tue",
                "phase": "Base",
                "title": "Easy Run",
                "type": "Easy",
                "duration_minutes": 45,
                "target_zone": "Zone 2",
                "target_hr_range": {"min": 125, "max": 140},
                "description": {"Process": "Warm up 10min → run 30min", "Overall": "aerobic base"},
                "fueling_tip": ["Water only.", "Gel if hungry."],
            }
        ],
    )
    wo = get_plan_workouts(plan_id)[0]
    assert wo["target_hr_range"] == "125-140"
    assert "Process: Warm up 10min" in wo["description"]
    assert "Overall: aerobic base" in wo["description"]
    assert wo["fueling_tip"] == "Water only. Gel if hungry."


def test_save_workouts_round_trips_interval_fields(client, auth_headers):
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=[],
    ):
        resp = client.post(
            "/api/coach/generate-plan",
            headers=auth_headers["headers"],
            json={
                "goal_type": "finish",
                "race_name": "Interval Fields 50K",
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
                "day_of_week": "Wednesday",
                "phase": "Base",
                "title": "Hill Sprints",
                "type": "Interval",
                "duration_minutes": 30,
                "target_zone": "Zone 4",
                "description": "8 x 12s hill sprints.",
                "interval_reps": 8,
                "interval_rep_value": 12.0,
                "interval_rep_unit": "s",
            },
            {
                "week_number": 1,
                "day_of_week": "Thursday",
                "phase": "Base",
                "title": "Pyramid Intervals",
                "type": "Interval",
                "duration_minutes": 40,
                "target_zone": "Zone 4",
                "description": "1x1min, 1x2min, 1x3min, 1x2min, 1x1min pyramid.",
            },
        ],
    )
    saved = get_plan_workouts(plan_id)
    clean_block = next(w for w in saved if w["title"] == "Hill Sprints")
    pyramid = next(w for w in saved if w["title"] == "Pyramid Intervals")

    assert clean_block["interval_reps"] == 8
    assert clean_block["interval_rep_value"] == 12.0
    assert clean_block["interval_rep_unit"] == "s"

    assert pyramid["interval_reps"] is None
    assert pyramid["interval_rep_value"] is None
    assert pyramid["interval_rep_unit"] is None


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
