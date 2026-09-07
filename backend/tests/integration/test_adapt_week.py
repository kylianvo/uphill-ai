"""Integration tests for POST /api/coach/adapt-week and preserve_completed behavior."""

import time
from unittest.mock import AsyncMock, patch

from db import get_plan_by_id, get_plan_workouts, save_workouts


def _create_test_plan(client, headers):
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
                "race_name": "Adapt Test 50K",
                "race_date": "2027-06-01",
                "plan_start_date": "2027-04-01",
                "days_per_week": 4,
                "current_weekly_km": 30,
            },
        )
    assert resp.status_code == 200
    return resp.json()["plan"]["id"]


class TestSaveWorkoutsPreserveCompleted:
    def test_preserve_completed_keeps_completed_and_gps_matched_workouts(self, client, auth_headers):
        plan_id = _create_test_plan(client, auth_headers["headers"])

        # Seed Week 2 with two workouts
        initial_wos = [
            {
                "week_number": 2,
                "day_of_week": "Tuesday",
                "phase": "Base",
                "title": "Easy Aerobic",
                "type": "Easy Run",
                "duration_minutes": 45,
                "target_zone": "Zone 2",
                "description": "Keep it conversational.",
            },
            {
                "week_number": 2,
                "day_of_week": "Thursday",
                "phase": "Base",
                "title": "Tempo Run",
                "type": "Tempo",
                "duration_minutes": 50,
                "target_zone": "Zone 3",
                "description": "Tempo pace.",
            },
        ]
        save_workouts(plan_id, initial_wos)
        saved = get_plan_workouts(plan_id)
        assert len(saved) == 2

        # Mark Tuesday completed with RPE and notes
        tuesday_id = next(w["id"] for w in saved if w["day_of_week"] == "Tuesday")
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": tuesday_id, "is_completed": 1, "rpe": 6, "notes": "Felt smooth"},
        )

        # Regenerate week 2 with new workouts (e.g. Tuesday rest, Wednesday easy, Friday long)
        new_wos = [
            {
                "week_number": 2,
                "day_of_week": "Tuesday",
                "phase": "Base",
                "title": "New Proposed Tuesday Run",
                "type": "Easy Run",
                "duration_minutes": 40,
                "target_zone": "Zone 2",
                "description": "New description.",
            },
            {
                "week_number": 2,
                "day_of_week": "Friday",
                "phase": "Base",
                "title": "Adapted Friday Run",
                "type": "Easy Run",
                "duration_minutes": 60,
                "target_zone": "Zone 2",
                "description": "Adapted run.",
            },
        ]

        # Call save_workouts with preserve_completed=True
        save_workouts(plan_id, new_wos, preserve_completed=True)

        refreshed = get_plan_workouts(plan_id)
        # Tuesday workout should remain the original completed one, NOT replaced
        tuesday_refreshed = next(w for w in refreshed if w["day_of_week"] == "Tuesday")
        assert tuesday_refreshed["id"] == tuesday_id
        assert tuesday_refreshed["is_completed"] == 1
        assert tuesday_refreshed["rpe"] == 6
        assert tuesday_refreshed["notes"] == "Felt smooth"
        assert tuesday_refreshed["title"] == "Easy Aerobic"

        # Thursday (uncompleted) should have been removed
        assert not any(w["day_of_week"] == "Thursday" for w in refreshed)

        # Friday should have been added
        friday_refreshed = next(w for w in refreshed if w["day_of_week"] == "Friday")
        assert friday_refreshed["title"] == "Adapted Friday Run"

    def test_preserve_completed_keeps_activity_matched_workouts(self, client, auth_headers):
        from sqlalchemy import text

        from db import engine

        plan_id = _create_test_plan(client, auth_headers["headers"])
        user_id = auth_headers["user_id"]

        save_workouts(
            plan_id,
            [
                {
                    "week_number": 2,
                    "day_of_week": "Wednesday",
                    "phase": "Base",
                    "title": "Wednesday Run",
                    "type": "Easy Run",
                    "duration_minutes": 45,
                    "target_zone": "Zone 2",
                    "description": "Original Wed run.",
                }
            ],
        )
        wed_wo = get_plan_workouts(plan_id)[0]
        wed_id = wed_wo["id"]

        # Insert a matched activity in activities table pointing to wed_id
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO activities (
                        user_id, source_provider, external_ids, activity_type,
                        start_time, duration_seconds, distance_km, matched_workout_id
                    )
                    VALUES (
                        :uid, 'coros', jsonb_build_object('coros', 'coros_123'), 'run',
                        '2027-04-08T07:00:00Z', 2400, 8.0, :wid
                    )
                """),
                {"uid": user_id, "wid": wed_id},
            )
            conn.commit()

        # Regenerate week 2
        new_wos = [
            {
                "week_number": 2,
                "day_of_week": "Wednesday",
                "phase": "Base",
                "title": "New Proposed Wed Run",
                "type": "Easy Run",
                "duration_minutes": 50,
                "target_zone": "Zone 2",
                "description": "Replaced Wed run.",
            }
        ]
        save_workouts(plan_id, new_wos, preserve_completed=True)

        refreshed = get_plan_workouts(plan_id)
        assert len(refreshed) == 1
        assert refreshed[0]["id"] == wed_id
        assert refreshed[0]["title"] == "Wednesday Run"  # Kept original matched workout


class TestAdaptWeekEndpoint:
    def test_adapt_week_rejects_unstarted_or_ungenerated_week(self, client, auth_headers):
        plan_id = _create_test_plan(client, auth_headers["headers"])
        # No workouts generated yet (max_week is 0)
        resp = client.post(
            "/api/coach/adapt-week",
            headers=auth_headers["headers"],
            json={"plan_id": plan_id, "week_number": 5},
        )
        assert resp.status_code == 400
        assert "has not been generated yet" in resp.json()["detail"]

    def test_adapt_week_reaches_plan_generator_with_target_week_and_does_not_mutate_baseline_plan(
        self, client, auth_headers
    ):
        plan_id = _create_test_plan(client, auth_headers["headers"])

        # Seed Week 1 & 2
        save_workouts(
            plan_id,
            [
                {
                    "week_number": 1,
                    "day_of_week": "Monday",
                    "phase": "Base",
                    "title": "Week 1 Run",
                    "type": "Easy Run",
                    "duration_minutes": 40,
                    "target_zone": "Zone 2",
                    "description": "Base run.",
                },
                {
                    "week_number": 2,
                    "day_of_week": "Monday",
                    "phase": "Base",
                    "title": "Week 2 Run",
                    "type": "Easy Run",
                    "duration_minutes": 45,
                    "target_zone": "Zone 2",
                    "description": "Base run.",
                },
            ],
        )

        captured_args = {}

        async def _fake_generate(plan_id, user_profile, race_info, total_weeks=12, **kwargs):
            captured_args["race_info"] = race_info
            captured_args["target_week"] = kwargs.get("target_week")
            captured_args["block_context"] = kwargs.get("block_context")
            return [
                {
                    "week_number": 2,
                    "day_of_week": "Tuesday",
                    "phase": "Base",
                    "title": "Adapted Tuesday Run",
                    "type": "Easy Run",
                    "duration_minutes": 40,
                    "target_zone": "Zone 2",
                    "description": "Adapted.",
                }
            ]

        with patch(
            "services.plan_generator.PlanGenerator.generate_plan_workouts",
            new=AsyncMock(side_effect=_fake_generate),
        ):
            resp = client.post(
                "/api/coach/adapt-week",
                headers=auth_headers["headers"],
                json={
                    "plan_id": plan_id,
                    "week_number": 2,
                    "overall_rpe": 8,
                    "fatigue_notes": "Calf tightness after long trail run",
                    "athlete_notes": "Traveling Wed-Thu, prefer running on weekend",
                    "preferred_days": ["Tuesday", "Saturday", "Sunday"],
                    "days_per_week": 3,
                    "has_gym_access": True,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "job_id" in data
            assert data["week_number"] == 2

            # Poll for job completion
            job_id = data["job_id"]
            status_resp = None
            for _ in range(20):
                status_resp = client.get(f"/api/coach/plan-status/{job_id}", headers=auth_headers["headers"])
                if status_resp.json().get("status") in ("done", "error"):
                    break
                time.sleep(0.05)

            assert status_resp is not None
            assert status_resp.json()["status"] == "done"

            # Check that captured kwargs have target_week = 2
            assert captured_args["target_week"] == 2
            # Check captured race_info has week-specific overrides
            assert captured_args["race_info"]["preferred_days"] == ["Tuesday", "Saturday", "Sunday"]
            assert captured_args["race_info"]["days_per_week"] == 3
            assert captured_args["race_info"]["has_gym_access"] is True
            # Check context contains fatigue notes and RPE
            assert "Calf tightness" in captured_args["block_context"]
            assert "8/10" in captured_args["block_context"]

            # Verify the plan in the DB was NOT mutated (baseline defaults retained)
            db_plan = get_plan_by_id(plan_id)
            assert db_plan["days_per_week"] == 4  # original from _create_test_plan
