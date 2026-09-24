import datetime as dt
import time
from unittest.mock import AsyncMock, patch

import db
from services.calendar_rules import DAYS
from tests.integration.calendar_helpers import add_workout, make_plan, server_today, this_monday


def _fake(captured):
    async def _gen(plan_id, user_profile, race_info, total_weeks=12, **kwargs):
        captured.update(kwargs)
        wk = kwargs["target_week"]
        return [
            {
                "week_number": wk,
                "day_of_week": d,
                "phase": "Base",
                "title": f"New {d}",
                "type": "Easy",
                "duration_minutes": 30,
                "target_zone": "Zone 2",
                "description": "n",
            }
            for d in DAYS
        ], "recreational"

    return _gen


def _adapt(client, headers, plan_id, week, captured):
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_fake(captured))
    ):
        resp = client.post(
            "/api/coach/adapt-week",
            headers=headers,
            json={
                "plan_id": plan_id,
                "week_number": week,
                "fatigue_level": "hard",
                "client_today": server_today().isoformat(),
            },
        )
        if resp.status_code != 200:
            return resp
        job_id = resp.json()["job_id"]
        for _ in range(40):
            status = client.get(f"/api/coach/plan-status/{job_id}", headers=headers).json()
            if status.get("status") in ("done", "error"):
                break
            time.sleep(0.05)
        assert status["status"] == "done", status
    return resp


def test_current_week_adapt_keeps_past_days_and_rebuilds_from_today(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    old_ids = {d: add_workout(plan_id, 1, d, title=f"Old {d}") for d in DAYS}
    add_workout(plan_id, 2, "Monday")
    captured = {}
    _adapt(client, auth_headers["headers"], plan_id, 1, captured)

    today_idx = server_today().weekday()
    week1 = [w for w in db.get_plan_workouts(plan_id) if w["week_number"] == 1]
    for i, d in enumerate(DAYS):
        titles = sorted(w["title"] for w in week1 if w["day_of_week"] == d)
        if i < today_idx:
            assert titles == [f"Old {d}"], d
            assert any(w["id"] == old_ids[d] for w in week1)
        else:
            assert titles == [f"New {d}"], d
    if today_idx > 0:
        assert "Do NOT make up missed sessions" in captured["block_context"]
        assert f"schedule sessions only from {DAYS[today_idx]} to Sunday" in captured["block_context"]


def test_next_week_adapt_prompt_has_no_fixed_days_line(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    add_workout(plan_id, 1, "Monday")
    add_workout(plan_id, 2, "Tuesday", title="Old Tue")
    captured = {}
    _adapt(client, auth_headers["headers"], plan_id, 2, captured)
    assert "are fixed and already happened" not in captured["block_context"]
    titles = {w["title"] for w in db.get_plan_workouts(plan_id) if w["week_number"] == 2}
    assert "Old Tue" not in titles and "New Tuesday" in titles


def test_adapting_a_week_that_is_over_is_refused_with_a_code(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday() - dt.timedelta(days=14))
    add_workout(plan_id, 1, "Monday")
    add_workout(plan_id, 3, "Monday")
    resp = _adapt(client, auth_headers["headers"], plan_id, 1, {})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "G3_past_target"
