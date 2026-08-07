"""Integration tests for POST /api/coach/generate-next-block's 70% completion gate."""

from db import get_plan_workouts, save_workouts


def _create_plan_with_two_weeks_of_workouts(client, headers):
    resp = client.post(
        "/api/coach/generate-plan",
        headers=headers,
        json={
            "goal_type": "finish",
            "race_name": "Gate Test 50K",
            "race_date": "2027-05-01",
            "plan_start_date": "2027-03-15",
            "days_per_week": 4,
        },
    )
    plan_id = resp.json()["plan"]["id"]

    # Block 1 = weeks 1-2. Two workouts, 60 min each -- mark only one
    # completed so the block sits at 50%, well under the 70% gate.
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
                "target_zone": "Z2",
                "description": "Conversational pace.",
            },
            {
                "week_number": 2,
                "day_of_week": "Monday",
                "phase": "base",
                "title": "Easy Run 2",
                "type": "easy",
                "duration_minutes": 60,
                "target_zone": "Z2",
                "description": "Conversational pace.",
            },
        ],
    )
    workouts = get_plan_workouts(plan_id)
    return plan_id, workouts[0]["id"]


class TestGenerateNextBlockGate:
    def test_blocks_generation_below_70_percent_without_override(self, client, auth_headers, mock_plan_generation):
        plan_id, workout_id = _create_plan_with_two_weeks_of_workouts(client, auth_headers["headers"])
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        resp = client.post(
            "/api/coach/generate-next-block",
            headers=auth_headers["headers"],
            json={"plan_id": plan_id, "block_number": 2},
        )
        assert resp.status_code == 403
        assert "70%" in resp.json()["detail"]

    def test_override_gate_allows_generation_below_70_percent(self, client, auth_headers, mock_plan_generation):
        plan_id, workout_id = _create_plan_with_two_weeks_of_workouts(client, auth_headers["headers"])
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        resp = client.post(
            "/api/coach/generate-next-block",
            headers=auth_headers["headers"],
            json={"plan_id": plan_id, "block_number": 2, "override_gate": True},
        )
        assert resp.status_code == 200, resp.text
        assert "job_id" in resp.json()
