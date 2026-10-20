from datetime import date, timedelta

import db
from services import coach_nudge


def _plan_with_weeks(user_id, week1_done, week1_missed):
    start = date.today() - timedelta(days=date.today().weekday() + 7)  # last Monday: this is week 2
    plan_id = db.create_plan(
        user_id, "Nudge Test", (date.today() + timedelta(weeks=10)).isoformat(), "finish", None, 12,
        course_distance_km=56.0, course_elevation_gain_m=2500.0, start_date=start.isoformat(),
        days_per_week=4, long_run_day="Saturday",
    )  # fmt: skip
    days = ["Monday", "Tuesday", "Thursday", "Saturday"]
    rows = [
        {"week_number": 1, "day_of_week": d, "phase": "Base", "title": "Easy run", "type": "Easy",
         "duration_minutes": 60, "target_zone": "Zone 2"} for d in days
    ]  # fmt: skip
    db.save_workouts(plan_id, rows)
    for i, w in enumerate(db.get_plan_workouts(plan_id)):
        if i < week1_done:
            db.update_workout_log(w["id"], is_completed=1)
        elif i < week1_done + week1_missed:
            db.update_workout_log(w["id"], is_missed=1)
    return plan_id


def test_a_slipped_week_gets_a_gentle_push_in_both_languages_and_is_cached(client, auth_headers, monkeypatch):
    plan_id = _plan_with_weeks(auth_headers["user_id"], 1, 3)
    calls = []
    real = coach_nudge.nudge

    async def counting(f, lang, key):
        calls.append(lang)
        return await real(f, lang, None)  # rules tier: never calls Gemini in tests

    monkeypatch.setattr(coach_nudge, "nudge", counting)
    h = auth_headers["headers"]
    first = client.get(f"/api/plans/{plan_id}/coach-nudge?lang=en", headers=h).json()["nudge"]
    assert first["tone"] == "push" and "1/4" in first["text"] and first["source"] == "rules"
    again = client.get(f"/api/plans/{plan_id}/coach-nudge?lang=en", headers=h).json()["nudge"]
    assert again["text"] == first["text"] and calls == ["en"]  # the second read is served from the table
    vi = client.get(f"/api/plans/{plan_id}/coach-nudge?lang=vi", headers=h).json()["nudge"]
    assert "Tuần trước" in vi["text"]


def test_a_quiet_week_says_nothing(client, auth_headers):
    plan_id = _plan_with_weeks(auth_headers["user_id"], 3, 0)  # 3 of 4 = 75%: neither solid nor slipped
    assert client.get(f"/api/plans/{plan_id}/coach-nudge", headers=auth_headers["headers"]).json() == {"nudge": None}
