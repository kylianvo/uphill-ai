"""push_plan / push_status in standalone mode (non-race goals): one COROS scheduled
workout per Uphill run, against a real DB and a fake COROS MCP client."""

import asyncio
import datetime as dt
import json
from unittest.mock import AsyncMock, patch

import pytest

import db
from services import coros_push
from services.coros_push import PushError, parse_id_in_plan
from services.mcp_client import McpError, McpToolError

TODAY = dt.date(2027, 4, 7)  # Wednesday of plan week 1 (plan starts Monday 2027-04-05)


class FakeSchedule:
    def __init__(self, fail_after: int | None = None, fail: Exception | None = None):
        self.calls: list[tuple[str, dict]] = []
        self.next_id = 900
        self.fail_after = fail_after
        self.fail = fail

    async def initialize(self):
        pass

    async def aclose(self):
        pass

    async def call_tool(self, name, args):
        writes = [c for c in self.calls if c[0] != "queryTrainingPlanLibrary"]
        if self.fail_after is not None and len(writes) >= self.fail_after:
            raise self.fail
        self.calls.append((name, json.loads(json.dumps(args))))
        if name == "createScheduledWorkout":
            self.next_id += 1
            return f"Workout created on {args['date']}.\nidInPlan: {self.next_id}"
        if name == "updateScheduledWorkout":
            return f"Workout updated.\nidInPlan: {args['idInPlan']}"
        raise AssertionError(name)

    def tool_calls(self, name):
        return [a for n, a in self.calls if n == name]


def _setup(client, auth_headers, rows):
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=([], "recreational"),
    ):
        resp = client.post(
            "/api/coach/generate-plan",
            headers=auth_headers["headers"],
            json={
                "goal_type": "return",
                "plan_duration_weeks": 8,
                "plan_start_date": "2027-04-05",
                "days_per_week": 3,
                "current_weekly_km": 20,
            },
        )
    assert resp.status_code == 200, resp.text
    plan_id = resp.json()["plan"]["id"]
    db.save_workouts(plan_id, rows)
    uid = auth_headers["user_id"]
    db.save_connection(uid, "coros", access_token_enc="x", refresh_token_enc=None, token_expires_at=None, scopes="")
    return uid, plan_id


def _wo(week, day, **kw):
    base = {
        "week_number": week,
        "day_of_week": day,
        "phase": "Base",
        "title": f"Easy {week}{day[:2]}",
        "type": "Easy",
        "duration_minutes": 30,
        "target_zone": "Zone 2",
        "target_hr_range": "120-135 bpm",
        "description": "Easy.",
    }
    base.update(kw)
    return base


ROWS = [_wo(1, "Thursday"), _wo(1, "Saturday"), _wo(1, "Sunday", type="Strength", title="Gym"), _wo(2, "Tuesday")]


@pytest.fixture
def token():
    with patch("services.coros_push.coros_sync._access_token", new=AsyncMock(return_value="tok")):
        yield


def _push(uid, fake, today=TODAY):
    return asyncio.run(coros_push.push_plan(uid, today, "en", client_factory=lambda _t: fake))


def _move(plan_id, week, day, to_day):
    row = next(w for w in db.get_plan_workouts(plan_id) if w["week_number"] == week and w["day_of_week"] == day)
    with db.engine.connect() as conn:
        conn.execute(db.text("UPDATE workouts SET day_of_week = :d WHERE id = :id"), {"d": to_day, "id": row["id"]})
        conn.commit()


def test_parse_id_in_plan():
    assert parse_id_in_plan("Created.\nidInPlan: 467917012245594132") == "467917012245594132"
    assert parse_id_in_plan("id in plan = 42") is None
    assert parse_id_in_plan("") is None


def test_first_push_schedules_each_run_and_skips_strength_and_rest(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, ROWS)
    fake = FakeSchedule()
    res = _push(uid, fake)
    assert res["status"] == "sent"
    creates = fake.tool_calls("createScheduledWorkout")
    assert [c["date"] for c in creates] == ["20270408", "20270410", "20270413"]
    assert all(c["course"]["sportType"] == 1 and "dayNo" not in c["course"] for c in creates)
    assert fake.tool_calls("createTrainingPlan") == [] and fake.tool_calls("queryTrainingPlanLibrary") == []
    link = db.get_coros_plan_link(uid)
    assert (link["mode"], link["coros_plan_id"], link["total_weeks"]) == ("standalone", None, None)
    assert link["scheduled"] == {"2027-04-08": ["901"], "2027-04-10": ["902"], "2027-04-13": ["903"]}
    s = res["summary"]
    assert (s["mode"], s["workouts_sent"], s["left_in_uphill"], s["stale"], s["plan_start"]) == (
        "standalone",
        3,
        1,
        0,
        None,
    )
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is False


def test_unchanged_days_are_not_sent_again(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, ROWS)
    fake = FakeSchedule()
    _push(uid, fake)
    fake.calls.clear()
    res = _push(uid, fake)
    assert fake.calls == [] and res["summary"]["workouts_sent"] == 0


def test_changed_workout_is_updated_in_place(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, ROWS)
    fake = FakeSchedule()
    _push(uid, fake)
    sat = next(w for w in db.get_plan_workouts(plan_id) if w["day_of_week"] == "Saturday")
    with db.engine.connect() as conn:
        conn.execute(db.text("UPDATE workouts SET duration_minutes = 50 WHERE id = :id"), {"id": sat["id"]})
        conn.commit()
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is True
    fake.calls.clear()
    _push(uid, fake)
    (update,) = fake.tool_calls("updateScheduledWorkout")
    assert (update["date"], update["idInPlan"]) == ("20270410", "902")
    assert fake.tool_calls("createScheduledWorkout") == []
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is False


def test_moved_workout_leaves_a_stale_copy_that_is_reported_then_reused(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, ROWS)
    fake = FakeSchedule()
    _push(uid, fake)
    _move(plan_id, 1, "Saturday", "Friday")
    fake.calls.clear()
    res = _push(uid, fake)
    (create,) = fake.tool_calls("createScheduledWorkout")
    assert create["date"] == "20270409"
    assert res["summary"]["stale"] == 1  # Saturday's copy can't be deleted over MCP
    assert db.get_coros_plan_link(uid)["scheduled"]["2027-04-10"] == ["902"]
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is False

    _move(plan_id, 1, "Friday", "Saturday")  # moved back: Saturday's old copy is reused, Friday's goes stale
    fake.calls.clear()
    res = _push(uid, fake)
    (update,) = fake.tool_calls("updateScheduledWorkout")
    assert (update["date"], update["idInPlan"]) == ("20270410", "902")
    assert res["summary"]["stale"] == 1


def test_non_race_plan_with_nothing_ahead_is_nothing_to_push(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, [_wo(1, "Monday"), _wo(1, "Sunday", type="Strength")])
    fake = FakeSchedule()
    with pytest.raises(PushError) as info:
        _push(uid, fake)
    assert info.value.code == "NOTHING_to_push" and fake.calls == []


def test_failure_after_a_write_is_partial_and_keeps_what_was_written(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, ROWS)
    fake = FakeSchedule(fail_after=1, fail=McpError("timeout"))
    res = _push(uid, fake)
    assert res["status"] == "partial"
    link = db.get_coros_plan_link(uid)
    assert link["partial"] is True and link["scheduled"] == {"2027-04-08": ["901"]}
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is True

    retry = FakeSchedule()
    retry.next_id = 901
    _push(uid, retry)
    assert [c["date"] for c in retry.tool_calls("createScheduledWorkout")] == ["20270410", "20270413"]


def test_rejection_before_any_write_raises(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, ROWS)
    fake = FakeSchedule(fail_after=0, fail=McpToolError("tool x reported an error", reason="bad"))
    with pytest.raises(PushError) as info:
        _push(uid, fake)
    assert info.value.code == "COROS_rejected"
    assert db.get_coros_plan_link(uid) is None
