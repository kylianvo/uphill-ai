import db


def test_get_plan_workouts_for_week_scopes_to_one_week(auth_headers):
    user_id = auth_headers["user_id"]
    with db.engine.connect() as conn:
        plan_id = conn.execute(
            db.text("""
                INSERT INTO plans (user_id, race_name, race_date, goal_type, total_weeks, plan_status)
                VALUES (:uid, 'Test Race', '2026-10-01', 'time', 8, 'active')
                RETURNING id
            """),
            {"uid": user_id},
        ).scalar()
        conn.execute(
            db.text("""
                INSERT INTO workouts (plan_id, week_number, day_of_week, phase, title, type, duration_minutes, distance_km, target_zone)
                VALUES
                    (:pid, 1, 'Monday', 'Base', 'Easy Run', 'Easy', 40, 6.0, 'Z2'),
                    (:pid, 2, 'Monday', 'Base', 'Week 2 Run', 'Easy', 40, 6.0, 'Z2')
            """),
            {"pid": plan_id},
        )
        conn.commit()

    week1 = db.get_plan_workouts_for_week(plan_id, 1)
    assert len(week1) == 1
    assert week1[0]["title"] == "Easy Run"
