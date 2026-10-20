from datetime import date, datetime, timedelta

from sqlalchemy import text

import db


def _seed(user_id, weeks, pace0_s, gain_per_week):
    monday = date.today() - timedelta(days=date.today().weekday() + 7 * (weeks - 1))
    plan_id = db.create_plan(
        user_id, "Tracking Test", (date.today() + timedelta(weeks=8)).isoformat(), "finish", None, weeks + 8,
        course_distance_km=56.0, course_elevation_gain_m=2500.0, start_date=monday.isoformat(), days_per_week=4,
    )  # fmt: skip
    with db.engine.begin() as conn:
        conn.execute(text("UPDATE users SET aet_hr = 145 WHERE id = :u"), {"u": user_id})
        for w in range(weeks):
            for d in (0, 2, 4):
                conn.execute(
                    text("""INSERT INTO activities (user_id, source_provider, activity_type, start_time, duration_seconds,
                            distance_km, avg_hr, adjusted_pace_sec_per_km)
                            VALUES (:u, 'coros', 'running', :t, 2700, 7, 143, :p)"""),
                    {"u": user_id, "t": datetime.combine(monday + timedelta(weeks=w, days=d), datetime.min.time()),
                     "p": pace0_s * (1 - gain_per_week * w)},
                )  # fmt: skip
    return plan_id


def test_goal_payload_carries_the_path_and_the_weekly_points_are_stored(client, auth_headers):
    plan_id = _seed(auth_headers["user_id"], weeks=8, pace0_s=360, gain_per_week=0.01)
    goal = client.get(f"/api/plans/{plan_id}/goal", headers=auth_headers["headers"]).json()
    path = goal["path"]
    assert (
        path["b"] == "ahead" and path["a"] == "ahead" and path["weeks"] >= 6 and path["confidence"] == "medium"
    )  # this week may not have 3 runs yet
    assert [c["week_number"] for c in db.get_fitness_checkpoints(plan_id)][:7] == list(range(1, 8))


def test_flat_training_is_behind_and_no_history_is_null(client, auth_headers):
    behind = _seed(auth_headers["user_id"], weeks=8, pace0_s=360, gain_per_week=0.0)
    assert client.get(f"/api/plans/{behind}/goal", headers=auth_headers["headers"]).json()["path"]["b"] == "behind"
    empty = db.create_plan(
        auth_headers["user_id"], "No Runs", (date.today() + timedelta(weeks=8)).isoformat(), "finish", None, 12,
        start_date=date.today().isoformat(),
    )  # fmt: skip
    assert client.get(f"/api/plans/{empty}/goal", headers=auth_headers["headers"]).json()["path"] is None
