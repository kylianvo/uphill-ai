from db import create_plan, get_plan_workouts, save_workouts, update_workout_log


def test_completion_timestamp_and_skip_provenance(auth_headers):
    plan = create_plan(auth_headers["user_id"], "Race", "2026-12-20", "finish", None, 12)
    save_workouts(
        plan,
        [
            dict(
                week_number=1,
                day_of_week="Monday",
                phase="Base",
                title="Easy",
                type="Easy",
                duration_minutes=45,
                target_zone="Z2",
            )
        ],
    )
    workout = get_plan_workouts(plan)[0]["id"]
    update_workout_log(workout, is_missed=1, missed_origin="matching")
    assert get_plan_workouts(plan)[0]["missed_origin"] == "matching"
    update_workout_log(workout, is_completed=1)
    row = get_plan_workouts(plan)[0]
    assert row["first_completed_at"] is not None and row["missed_origin"] is None
    update_workout_log(workout, is_completed=1)
    assert get_plan_workouts(plan)[0]["first_completed_at"] == row["first_completed_at"]
