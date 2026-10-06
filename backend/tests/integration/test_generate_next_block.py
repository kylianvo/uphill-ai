"""Integration tests for POST /api/coach/generate-next-block's 70% completion gate."""

import json
import time
from unittest.mock import AsyncMock, patch

from db import get_plan_by_id, get_plan_workouts, save_workouts, update_plan_schedule


def _create_plan_with_one_week_of_workouts(client, headers):
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

    # Block 1 = week 1. Two workouts, 60 min each -- mark only one
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
                "week_number": 1,
                "day_of_week": "Wednesday",
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


def _create_plan_with_one_week_of_workouts_no_mock(client, headers):
    """Same as _create_plan_with_one_week_of_workouts, but for tests that
    install their own long-lived patch on generate_plan_workouts (to capture
    call args from the later generate-next-block background task) instead of
    the mock_plan_generation fixture."""
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=([], "recreational"),
    ):
        return _create_plan_with_one_week_of_workouts(client, headers)


class TestGenerateNextBlockOverrideAnnotation:
    def test_override_annotation_reaches_the_generation_prompt(self, client, auth_headers):
        plan_id, workout_id = _create_plan_with_one_week_of_workouts_no_mock(client, auth_headers["headers"])
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        captured = {}

        async def _capture(*args, **kwargs):
            captured["block_context"] = kwargs.get("block_context")
            return [], "recreational"

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
        assert "Coach evaluation (Block 1):" in (captured.get("block_context") or "")


class TestGenerateNextBlockGate:
    def test_blocks_generation_below_70_percent_without_override(self, client, auth_headers, mock_plan_generation):
        plan_id, workout_id = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
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
        plan_id, workout_id = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
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
        plan_id, _ = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
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
        plan_id, _ = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])

        updated = update_plan_schedule(
            plan_id,
            preferred_run_days=["Tuesday", "Thursday", "Sunday"],
            double_session_days=["Sunday"],
        )

        assert json.loads(updated["preferred_run_days"]) == ["Tuesday", "Thursday", "Sunday"]
        assert json.loads(updated["double_session_days"]) == ["Sunday"]

    def test_training_venue_fields_round_trip(self, client, auth_headers, mock_plan_generation):
        plan_id, _ = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
        before = get_plan_by_id(plan_id)
        assert before["stair_access"] is False
        assert before["treadmill_max_incline"] == 15

        updated = update_plan_schedule(plan_id, mountain_days=["Saturday"], stair_access=True, treadmill_max_incline=25)

        assert json.loads(updated["mountain_days"]) == ["Saturday"]
        assert updated["stair_access"] is True
        assert updated["treadmill_max_incline"] == 25


class TestGenerateNextBlockScheduleEdit:
    def test_schedule_fields_update_plan_row_and_flow_into_generation(self, client, auth_headers):
        plan_id, workout_id = _create_plan_with_one_week_of_workouts_no_mock(client, auth_headers["headers"])
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        captured = {}

        async def _capture(*args, **kwargs):
            captured["race_info"] = args[2] if len(args) > 2 else kwargs.get("race_info")
            return [], "recreational"

        with patch(
            "services.plan_generator.PlanGenerator.generate_plan_workouts",
            new=AsyncMock(side_effect=_capture),
        ):
            resp = client.post(
                "/api/coach/generate-next-block",
                headers=auth_headers["headers"],
                json={
                    "plan_id": plan_id,
                    "block_number": 2,
                    "override_gate": True,
                    "days_per_week": 5,
                    "long_run_day": "Sunday",
                    "preferred_days": ["Tuesday", "Thursday", "Sunday"],
                    "double_session_days": ["Sunday"],
                    "has_gym_access": True,
                    "use_treadmill": True,
                    "training_environment": "hilly",
                    "mountain_days": ["Saturday", "Sunday"],
                    "stair_access": True,
                    "treadmill_max_incline": 20,
                },
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

        race_info = captured["race_info"]
        assert race_info["days_per_week"] == 5
        assert race_info["long_run_day"] == "Sunday"
        assert race_info["preferred_days"] == json.dumps(["Tuesday", "Thursday", "Sunday"])
        assert race_info["training_environment"] == "hilly"
        assert race_info["has_gym_access"] is True
        assert race_info["use_treadmill"] is True
        assert json.loads(race_info["mountain_days"]) == ["Saturday", "Sunday"]
        assert race_info["stair_access"] is True
        assert race_info["treadmill_max_incline"] == 20

        updated_plan = get_plan_by_id(plan_id)
        assert updated_plan["days_per_week"] == 5
        assert json.loads(updated_plan["double_session_days"]) == ["Sunday"]

    def test_omitted_schedule_fields_leave_plan_unchanged(self, client, auth_headers, mock_plan_generation):
        plan_id, workout_id = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
        before = get_plan_by_id(plan_id)
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

        after = get_plan_by_id(plan_id)
        assert after["days_per_week"] == before["days_per_week"]
        assert after["long_run_day"] == before["long_run_day"]

    def test_gate_rejection_does_not_persist_schedule_fields(self, client, auth_headers, mock_plan_generation):
        """A request that submits schedule-preference fields alongside a
        block that is still below the 70% completion gate (and no
        override_gate) must be rejected with 403 -- and, critically, must
        NOT have written the schedule fields to the plan row. Only requests
        that get past every rejection check may mutate the plan."""
        plan_id, workout_id = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
        before = get_plan_by_id(plan_id)
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        resp = client.post(
            "/api/coach/generate-next-block",
            headers=auth_headers["headers"],
            json={
                "plan_id": plan_id,
                "block_number": 2,
                "days_per_week": 6,
                "long_run_day": "Friday",
                "preferred_days": ["Monday", "Friday"],
                "training_environment": "flat",
            },
        )
        assert resp.status_code == 403
        assert "70%" in resp.json()["detail"]

        after = get_plan_by_id(plan_id)
        assert after["days_per_week"] == before["days_per_week"]
        assert after["long_run_day"] == before["long_run_day"]
        assert after["preferred_run_days"] == before["preferred_run_days"]
        assert after["training_environment"] == before["training_environment"]


def test_get_block_evaluation_endpoint(client, auth_headers):
    plan_id, workout_id = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
    client.patch(
        "/api/coach/workouts/log",
        headers=auth_headers["headers"],
        json={"workout_id": workout_id, "is_completed": 1},
    )
    resp = client.get(
        f"/api/coach/block-evaluation/{plan_id}/1",
        headers=auth_headers["headers"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["block_number"] == 1
    assert data["sessions_total"] == 2
    assert data["sessions_completed"] == 1
    assert data["completion_pct"] == 50
    assert "coach_summary" in data


def test_next_block_passes_the_stored_tier_as_previous_tier_and_stores_the_snapshot(client, auth_headers):
    """REGRESSION: next block passed plans.athlete_tier as the explicit override, so a
    plan first resolved as recreational stayed recreational forever."""
    captured = {}

    async def _gen(*args, **kwargs):
        if kwargs.get("block_number", 1) == 1:
            return [], "recreational"
        captured["race_info"] = args[2] if len(args) > 2 else kwargs.get("race_info")
        return [], "sub_elite"

    def _wait(job_id):
        status = None
        for _ in range(40):
            status = client.get(f"/api/coach/plan-status/{job_id}", headers=auth_headers["headers"]).json()["status"]
            if status == "done":
                break
            time.sleep(0.05)
        assert status == "done"

    # One patch for the whole test: both jobs run in background tasks.
    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen)):
        plan_id, workout_id = _create_plan_with_one_week_of_workouts(client, auth_headers["headers"])
        for _ in range(40):
            if get_plan_by_id(plan_id)["athlete_tier"]:
                break
            time.sleep(0.05)
        assert get_plan_by_id(plan_id)["athlete_tier"] == "recreational"
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
        _wait(resp.json()["job_id"])

    race_info = captured["race_info"]
    assert race_info["athlete_tier"] is None
    assert race_info["previous_tier"] == "recreational"
    assert race_info["fitness_snapshot"] is not None
    plan = get_plan_by_id(plan_id)
    assert plan["athlete_tier"] == "sub_elite"
    assert plan["fitness_snapshot"]["weekly_km_source"] == "self_reported"


class TestGenerateNextBlockUpcomingSessions:
    """#89: reviewing a week before it ends must not count the sessions still ahead
    as missed. Plan starts Monday 2027-03-15; week 1's long run is Sunday 03-21."""

    def _seed_week_with_sunday_long_run(self, client, headers):
        plan_id, _ = _create_plan_with_one_week_of_workouts_no_mock(client, headers)
        save_workouts(
            plan_id,
            [
                {
                    "week_number": 1,
                    "day_of_week": day,
                    "phase": "base",
                    "title": title,
                    "type": kind,
                    "duration_minutes": mins,
                    "target_zone": "Z2",
                    "description": "d",
                }
                for day, title, kind, mins in [
                    ("Monday", "Easy Run", "easy", 60),
                    ("Tuesday", "Easy Run 2", "easy", 60),
                    ("Wednesday", "Easy Run 3", "easy", 60),
                    ("Friday", "Easy Run 4", "easy", 60),
                    ("Sunday", "Long Run", "long run", 90),
                ]
            ],
        )
        for w in get_plan_workouts(plan_id):
            if w["day_of_week"] != "Sunday":
                client.patch(
                    "/api/coach/workouts/log",
                    headers=headers,
                    json={"workout_id": w["id"], "is_completed": 1},
                )
        return plan_id

    def _block_context_on(self, client, headers, plan_id, today):
        import datetime as dt

        captured = {}

        async def _capture(*args, **kwargs):
            captured["block_context"] = kwargs.get("block_context")
            return [], "recreational"

        with (
            patch(
                "services.plan_generator.PlanGenerator.generate_plan_workouts",
                new=AsyncMock(side_effect=_capture),
            ),
            patch("services.calendar_ops.server_today", return_value=dt.date.fromisoformat(today)),
        ):
            resp = client.post(
                "/api/coach/generate-next-block",
                headers=headers,
                json={"plan_id": plan_id, "block_number": 2, "client_today": today},
            )
            assert resp.status_code == 200, resp.text
            job_id = resp.json()["job_id"]
            for _ in range(40):
                if client.get(f"/api/coach/plan-status/{job_id}", headers=headers).json()["status"] == "done":
                    break
                time.sleep(0.05)
        return captured["block_context"] or ""

    def test_saturday_review_leaves_sundays_long_run_upcoming(self, client, auth_headers):
        headers = auth_headers["headers"]
        plan_id = self._seed_week_with_sunday_long_run(client, headers)

        ctx = self._block_context_on(client, headers, plan_id, "2027-03-20")

        assert "Week not finished: W1 Sunday Long Run still upcoming" in ctx
        assert "4/4 sessions (100%)" in ctx
        assert "Planned 0.0km/4.0h" in ctx
        assert "Sunday — Long Run (90min): upcoming" in ctx
        assert "not logged" not in ctx

    def test_after_the_week_ends_an_unticked_long_run_is_not_logged(self, client, auth_headers):
        headers = auth_headers["headers"]
        plan_id = self._seed_week_with_sunday_long_run(client, headers)

        ctx = self._block_context_on(client, headers, plan_id, "2027-03-22")

        assert "Week not finished" not in ctx
        assert "4/5 sessions (80%)" in ctx
        assert "Sunday — Long Run (90min): not logged" in ctx
