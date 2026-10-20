from datetime import date, timedelta

import db


def _plan(user_id):
    return db.create_plan(
        user_id, "Journey Test", (date.today() + timedelta(weeks=10)).isoformat(), "finish", None, 12,
        course_distance_km=56.0, course_elevation_gain_m=2500.0, start_date=date.today().isoformat(),
        days_per_week=4, long_run_day="Saturday",
    )  # fmt: skip


def test_journey_payload(client, auth_headers):
    plan_id = _plan(auth_headers["user_id"])
    j = client.get(f"/api/plans/{plan_id}/journey", headers=auth_headers["headers"]).json()
    assert j["total_weeks"] == 12 and j["current_week"] == 1
    assert 60 <= j["days_to_race"] <= 71
    assert j["preferences"]["long_run_day"] == "Saturday" and j["preferences"]["days_per_week"] == 4
    assert j["phases"] == [] and j["milestones"] == []


def test_journey_is_owner_only(client, auth_headers):
    other = client.post("/api/auth/mock-login", json={"email": "someone-else@uphill.ai"}).json()
    plan_id = _plan(other["user"]["id"])
    assert client.get(f"/api/plans/{plan_id}/journey", headers=auth_headers["headers"]).status_code == 404
