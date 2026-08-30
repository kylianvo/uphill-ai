"""Integration tests for POST /api/coach/generate-next-block's 70% completion gate."""

import json
import time
from unittest.mock import AsyncMock, patch

from db import get_plan_by_id, get_plan_workouts, save_workouts, update_plan_schedule


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
            "current_weekly_km": 30,
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


def _create_plan_with_two_weeks_of_workouts_no_mock(client, headers):
    """Same as _create_plan_with_two_weeks_of_workouts, but for tests that
    install their own long-lived patch on generate_plan_workouts (to capture
    call args from the later generate-next-block background task) instead of
    the mock_plan_generation fixture."""
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=[],
    ):
        return _create_plan_with_two_weeks_of_workouts(client, headers)


class TestGenerateNextBlockOverrideAnnotation:
    def test_override_annotation_reaches_the_generation_prompt(self, client, auth_headers):
        plan_id, workout_id = _create_plan_with_two_weeks_of_workouts_no_mock(client, auth_headers["headers"])
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        captured = {}

        async def _capture(*args, **kwargs):
            captured["block_context"] = kwargs.get("block_context")
            return []

        with patch(
            "services.plan_generator.PlanGenerator.generate_plan_workouts",
            new=AsyncMock(side_effect=_capture),
        ):
            resp = client.post(
                "/api/coach/generate-next-block",
                headers=auth_headers["headers"],
                json={"plan_id": plan_id, "block_number": 2, "override_gate": True},
            )
            assert resp.status_code == 200, resp.text
            job_id = resp.json()["job_id"]

            status = None
            for _ in range(20):
                poll = client.get(f"/api/coach/plan-status/{job_id}", headers=auth_headers["headers"])
                status = poll.json()["status"]
                if status == "done":
                    break
                time.sleep(0.05)
            assert status == "done"

        assert "generated via override at 50%" in (captured.get("block_context") or "")


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


class TestUpdatePlanSchedule:
    def test_updates_only_provided_fields_and_keeps_others(self, client, auth_headers, mock_plan_generation):
        plan_id, _ = _create_plan_with_two_weeks_of_workouts(client, auth_headers["headers"])
        before = get_plan_by_id(plan_id)

        updated = update_plan_schedule(plan_id, days_per_week=5, long_run_day="Sunday")

        assert updated["days_per_week"] == 5
        assert updated["long_run_day"] == "Sunday"
        # Untouched fields keep their prior value
        assert updated["preferred_run_days"] == before["preferred_run_days"]
        assert updated["training_environment"] == before["training_environment"]

    def test_returns_none_for_unknown_plan_id(self):
        assert update_plan_schedule(plan_id=999999999, days_per_week=5) is None

    def test_json_encodes_list_fields(self, client, auth_headers, mock_plan_generation):
        plan_id, _ = _create_plan_with_two_weeks_of_workouts(client, auth_headers["headers"])

        updated = update_plan_schedule(
            plan_id,
            preferred_run_days=["Tuesday", "Thursday", "Sunday"],
            double_session_days=["Sunday"],
        )

        assert json.loads(updated["preferred_run_days"]) == ["Tuesday", "Thursday", "Sunday"]
        assert json.loads(updated["double_session_days"]) == ["Sunday"]
