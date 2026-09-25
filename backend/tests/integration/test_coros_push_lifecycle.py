"""push_plan / push_status against a real DB and a fake COROS MCP client."""

import asyncio
import datetime as dt
import json
from unittest.mock import AsyncMock, patch

import pytest

import db
from services import coros_push
from services.coros_push import PushError
from services.mcp_client import McpError, McpToolError

MONDAY = dt.date(2027, 4, 5)  # plan week 1
TODAY = dt.date(2027, 4, 7)  # Wednesday of week 1


class FakeCoros:
    """Records calls; answers the library query from `self.library`."""

    def __init__(self, fail: dict[str, Exception] | None = None):
        self.calls: list[tuple[str, dict]] = []
        self.library = "No training plans found."
        self.fail = fail or {}
        self.next_plan_id = 500000000000000001
        self.plans: dict[str, dict] = {}

    async def initialize(self):
        pass

    async def aclose(self):
        pass

    async def call_tool(self, name, args):
        self.calls.append((name, json.loads(json.dumps(args))))
        if name in self.fail:
            raise self.fail.pop(name)
        if name == "queryTrainingPlanLibrary":
            return self._library_text()
        if name == "createTrainingPlan":
            pid = str(self.next_plan_id)
            self.next_plan_id += 1
            info = args["planInfo"]
            start = dt.datetime.strptime(str(info["planStartDate"]), "%Y%m%d").date()
            self.plans[pid] = {"name": info["planName"], "start": start, "weeks": info["totalWeeks"]}
            return "Training plan created and started."  # no id: forces the name lookup path
        if name == "updateTrainingPlan":
            weeks = args["planInfo"].get("totalWeeks")
            if weeks:
                self.plans[args["planInfo"]["planId"]]["weeks"] = weeks
            return "Plan updated."
        raise AssertionError(name)

    def _library_text(self):
        blocks = []
        for i, (pid, p) in enumerate(reversed(self.plans.items()), 1):
            end = p["start"] + dt.timedelta(days=p["weeks"] * 7 - 1 - p["start"].weekday())
            blocks.append(
                f"{i}. {p['name']} [In progress] [mcp]\n   Plan ID: {pid}\n   Record role: execution\n"
                f"   Editable via MCP: yes\n   Dates: {p['start']} to {end}\n   Weeks: {p['weeks']}\n"
            )
        return "Training Plan Library\n\n" + "\n".join(blocks) if blocks else "No training plans found."

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
                "goal_type": "finish",
                "race_name": "UTMB 50K",
                "race_date": "2027-07-01",
                "plan_start_date": "2027-04-05",
                "days_per_week": 4,
                "current_weekly_km": 30,
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
        "duration_minutes": 45,
        "target_zone": "Zone 2",
        "target_hr_range": "120-135 bpm",
        "description": "Easy.",
    }
    base.update(kw)
    return base


def _weekly_rows(weeks):
    return [_wo(w, d) for w in range(1, weeks + 1) for d in ("Tuesday", "Thursday", "Saturday")]


@pytest.fixture
def token():
    with patch("services.coros_push.coros_sync._access_token", new=AsyncMock(return_value="tok")):
        yield


def _push(uid, fake, today=TODAY, lang="en"):
    return asyncio.run(coros_push.push_plan(uid, today, lang, client_factory=lambda _t: fake))


def test_first_push_creates_four_week_plan_from_today(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(8))
    fake = FakeCoros()
    res = _push(uid, fake)
    assert res["status"] == "sent"
    (create,) = fake.tool_calls("createTrainingPlan")
    info = create["planInfo"]
    assert (info["planStartDate"], info["totalWeeks"], info["planName"]) == (20270407, 4, "Uphill AI · UTMB 50K")
    days = sorted({c["dayNo"] for c in create["courseList"]})
    assert days == list(range(0, 26))  # Wed 04-07 .. Sun 05-02
    assert create["courseList"][0]["dayNo"] == 0 and create["courseList"][0]["sportType"] == 4  # Wednesday rest
    assert sum(p["durationWeeks"] for p in create["phaseInfo"]["periodization"]) == 4
    link = db.get_coros_plan_link(uid)
    assert (link["coros_plan_id"], link["coros_start_date"], link["total_weeks"]) == ("500000000000000001", TODAY, 4)
    assert link["window_end"] == dt.date(2027, 5, 2) and link["plan_id"] == plan_id
    assert res["summary"]["workouts_sent"] == 3 * 4 - 1  # Tue of week 1 is before today
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is False


def test_second_push_updates_same_plan_and_extends(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(8))
    fake = FakeCoros()
    _push(uid, fake)
    later = TODAY + dt.timedelta(days=7)  # next Wednesday -> window reaches week 5
    res = _push(uid, fake, today=later)
    assert res["status"] == "sent"
    assert len(fake.tool_calls("createTrainingPlan")) == 1
    (update,) = fake.tool_calls("updateTrainingPlan")
    assert update["planInfo"] == {"planId": "500000000000000001", "totalWeeks": 5}
    assert sum(p["durationWeeks"] for p in update["phaseInfo"]["periodization"]) == 5
    assert min(c["dayNo"] for c in update["courseList"]) == 7
    assert db.get_coros_plan_link(uid)["total_weeks"] == 5


def test_update_within_length_sends_no_totalweeks(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(8))
    fake = FakeCoros()
    _push(uid, fake)
    _push(uid, fake)
    (update,) = fake.tool_calls("updateTrainingPlan")
    assert update["planInfo"] == {"planId": "500000000000000001"}
    assert "phaseInfo" not in update


def test_locked_days_are_not_sent(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(8))
    thursday = next(
        w for w in db.get_plan_workouts(plan_id) if w["week_number"] == 1 and w["day_of_week"] == "Thursday"
    )
    client.patch(
        "/api/coach/workouts/log",
        headers=auth_headers["headers"],
        json={"workout_id": thursday["id"], "is_completed": 1},
    )
    fake = FakeCoros()
    res = _push(uid, fake)
    (create,) = fake.tool_calls("createTrainingPlan")
    assert 1 not in {c["dayNo"] for c in create["courseList"]}  # Thu 04-08
    assert res["summary"]["locked_days"] == 1


def test_plan_quit_in_coros_app_recreates(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(8))
    fake = FakeCoros()
    _push(uid, fake)
    fake.plans.clear()  # athlete quit it in the COROS app
    _push(uid, fake)
    assert len(fake.tool_calls("createTrainingPlan")) == 2
    assert db.get_coros_plan_link(uid)["coros_plan_id"] == "500000000000000002"


def test_rollover_past_sixteen_weeks(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(20))
    fake = FakeCoros()
    _push(uid, fake)
    late = TODAY + dt.timedelta(weeks=13)  # Wed of week 14; window end week 17 -> 17 weeks from 04-07
    res = _push(uid, fake, today=late)
    assert res["status"] == "sent"
    (shorten,) = fake.tool_calls("updateTrainingPlan")
    assert shorten["planInfo"] == {"planId": "500000000000000001", "totalWeeks": 14}
    assert max(c["dayNo"] for c in shorten["courseList"]) == (late - TODAY).days + 4  # through Sunday
    create = fake.tool_calls("createTrainingPlan")[1]
    next_monday = late + dt.timedelta(days=5)
    assert create["planInfo"]["planStartDate"] == int(next_monday.strftime("%Y%m%d"))
    assert create["planInfo"]["totalWeeks"] == 4
    link = db.get_coros_plan_link(uid)
    assert link["coros_plan_id"] == "500000000000000002" and link["coros_start_date"] == next_monday


def test_rollover_create_failure_is_partial(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(20))
    fake = FakeCoros()
    _push(uid, fake)
    fake.fail["createTrainingPlan"] = McpError("timeout")
    res = _push(uid, fake, today=TODAY + dt.timedelta(weeks=13))
    assert res["status"] == "partial"
    link = db.get_coros_plan_link(uid)
    assert link["partial"] is True and link["coros_plan_id"] == "500000000000000001" and link["total_weeks"] == 14
    assert coros_push.push_status(uid, TODAY + dt.timedelta(weeks=13))["partial"] is True


def test_adopts_existing_plan_by_name_when_link_missing(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(8))
    fake = FakeCoros()
    fake.plans["777"] = {"name": "Uphill AI · UTMB 50K", "start": TODAY, "weeks": 4}
    _push(uid, fake)
    assert fake.tool_calls("createTrainingPlan") == []
    assert db.get_coros_plan_link(uid)["coros_plan_id"] == "777"


def test_errors(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(8))
    fake = FakeCoros(fail={"createTrainingPlan": McpToolError("tool x reported an error", reason="bad course")})
    with pytest.raises(PushError) as info:
        _push(uid, fake)
    assert (info.value.code, info.value.status) == ("COROS_rejected", 502)
    assert db.get_coros_plan_link(uid) is None

    with pytest.raises(PushError) as info:
        _push(uid, FakeCoros(fail={"queryTrainingPlanLibrary": McpError("down")}))
    assert (info.value.code, info.value.status) == ("COROS_unavailable", 504)


def test_plan_too_short(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2))
    with pytest.raises(PushError) as info:
        _push(uid, FakeCoros())
    assert info.value.code == "PLAN_too_short"


def test_not_connected_and_nothing_to_push(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, [])
    with pytest.raises(PushError) as info:
        _push(uid, FakeCoros())
    assert info.value.code == "NOTHING_to_push"
    db.delete_provider_data(uid, "coros")
    with pytest.raises(PushError) as info:
        _push(uid, FakeCoros())
    assert info.value.code == "COROS_not_connected"


def test_daily_limit(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(8))
    with patch("services.coros_push.settings.COROS_DAILY_PUSH_LIMIT", 1):
        _push(uid, FakeCoros())
        with pytest.raises(PushError) as info:
            _push(uid, FakeCoros())
    assert (info.value.code, info.value.status) == ("PUSH_limit", 429)


def test_in_progress(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(8))
    with db.coros_push_lock(uid):
        with pytest.raises(PushError) as info:
            _push(uid, FakeCoros())
    assert info.value.code == "PUSH_in_progress"


def test_status_out_of_date_after_move_and_clears_after_push(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(8))
    assert coros_push.push_status(uid, TODAY) == {
        "connected": True,
        "last_pushed_at": None,
        "out_of_date": False,
        "partial": False,
        "last_summary": None,
    }
    fake = FakeCoros()
    _push(uid, fake)
    sat = next(w for w in db.get_plan_workouts(plan_id) if w["week_number"] == 1 and w["day_of_week"] == "Saturday")
    with db.engine.connect() as conn:
        conn.execute(db.text("UPDATE workouts SET day_of_week = 'Sunday' WHERE id = :id"), {"id": sat["id"]})
        conn.commit()
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is True
    _push(uid, fake)
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is False


def test_status_not_connected(client, auth_headers):
    assert coros_push.push_status(auth_headers["user_id"], TODAY) == {"connected": False}
