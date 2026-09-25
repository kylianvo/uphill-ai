"""push_plan / push_status in plan mode (race goals), against a real DB and a fake COROS MCP client."""

import asyncio
import datetime as dt
import json
from unittest.mock import AsyncMock, patch

import pytest

import db
from services import coros_push
from services.coros_push import PushError
from services.mcp_client import McpError, McpToolError

TODAY = dt.date(2027, 4, 7)  # Wednesday of plan week 1 (plan starts Monday 2027-04-05)
RACE = "2027-07-01"  # Thursday of natural week 13 counting from TODAY
RACE_DAYNO = (dt.date(2027, 7, 1) - TODAY).days  # 85


class FakeCoros:
    """Records calls; answers the library query from the plans it created."""

    def __init__(self, fail: dict[str, Exception] | None = None):
        self.calls: list[tuple[str, dict]] = []
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


def _setup(client, auth_headers, rows, race_date=RACE, goal_type="finish"):
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=([], "recreational"),
    ):
        resp = client.post(
            "/api/coach/generate-plan",
            headers=auth_headers["headers"],
            json={
                "goal_type": goal_type,
                "race_name": "UTMB 50K",
                "race_date": race_date,
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


def _weekly_rows(weeks, first=1):
    return [_wo(w, d) for w in range(first, weeks + 1) for d in ("Tuesday", "Thursday", "Saturday")]


def _set_race(plan_id, race_date):
    with db.engine.connect() as conn:
        conn.execute(db.text("UPDATE plans SET race_date = :d WHERE id = :id"), {"d": race_date, "id": plan_id})
        conn.commit()


@pytest.fixture
def token():
    with patch("services.coros_push.coros_sync._access_token", new=AsyncMock(return_value="tok")):
        yield


def _push(uid, fake, today=TODAY, lang="en"):
    return asyncio.run(coros_push.push_plan(uid, today, lang, client_factory=lambda _t: fake))


def _days(call):
    return sorted({c["dayNo"] for c in call["courseList"]})


def _race_course(call):
    return next(c for c in call["courseList"] if c["courseName"].startswith("Race day"))


def test_first_push_creates_plan_through_race_week_with_generated_days_and_race_day(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(2))
    fake = FakeCoros()
    res = _push(uid, fake)
    assert res["status"] == "sent"
    (create,) = fake.tool_calls("createTrainingPlan")
    info = create["planInfo"]
    assert (info["planStartDate"], info["totalWeeks"], info["planName"]) == (20270407, 13, "Uphill AI · UTMB 50K")
    assert _days(create) == [*range(0, 12), RACE_DAYNO]  # Wed 04-07 .. Sun 04-18, then race day only
    race = _race_course(create)
    assert race["dayNo"] == RACE_DAYNO and race["courseName"] == "Race day: UTMB 50K"
    assert not any("intensityType" in s for s in race["sections"])
    assert sum(p["durationWeeks"] for p in create["phaseInfo"]["periodization"]) == 13
    assert create["phaseInfo"]["periodization"][-1]["phaseType"] == 5  # race week
    link = db.get_coros_plan_link(uid)
    assert (link["mode"], link["coros_plan_id"], link["coros_start_date"], link["total_weeks"]) == (
        "plan",
        "500000000000000001",
        TODAY,
        13,
    )
    assert link["window_end"] == dt.date(2027, 7, 4) and link["plan_id"] == plan_id
    assert res["summary"]["workouts_sent"] == 5 + 1  # 2 weeks x 3 runs minus Tue before today, plus race day
    assert (res["summary"]["mode"], res["summary"]["plan_start"]) == ("plan", "2027-04-07")
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is False


def test_newly_generated_week_is_added_to_the_same_plan(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(2))
    fake = FakeCoros()
    _push(uid, fake)
    db.save_workouts(plan_id, _weekly_rows(3, first=3))
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is True
    res = _push(uid, fake)
    assert res["status"] == "sent" and len(fake.tool_calls("createTrainingPlan")) == 1
    (update,) = fake.tool_calls("updateTrainingPlan")
    assert update["planInfo"] == {"planId": "500000000000000001"}  # length unchanged
    assert "phaseInfo" not in update
    assert _days(update) == [*range(0, 19), RACE_DAYNO]  # through Sun 04-25 now
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is False


def test_race_moved_later_extends_plan_and_clears_old_race_day(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(2))
    fake = FakeCoros()
    _push(uid, fake)
    _set_race(plan_id, "2027-07-15")
    assert coros_push.push_status(uid, TODAY)["out_of_date"] is True
    _push(uid, fake)
    (update,) = fake.tool_calls("updateTrainingPlan")
    assert update["planInfo"] == {"planId": "500000000000000001", "totalWeeks": 15}
    assert sum(p["durationWeeks"] for p in update["phaseInfo"]["periodization"]) == 15
    by_day = {c["dayNo"]: c for c in update["courseList"]}
    assert by_day[RACE_DAYNO]["sportType"] == 4  # old race day cleared
    assert by_day[RACE_DAYNO + 14]["courseName"] == "Race day: UTMB 50K"
    assert db.get_coros_plan_link(uid)["total_weeks"] == 15


def test_race_moved_earlier_shortens_plan(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(2))
    fake = FakeCoros()
    _push(uid, fake)
    _set_race(plan_id, "2027-06-03")
    _push(uid, fake)
    (update,) = fake.tool_calls("updateTrainingPlan")
    assert update["planInfo"] == {"planId": "500000000000000001", "totalWeeks": 9}
    assert max(_days(update)) == (dt.date(2027, 6, 3) - TODAY).days  # old race day is past the new end: not sent


def test_locked_days_are_not_sent(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(2))
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
    assert 1 not in _days(create)  # Thu 04-08
    assert res["summary"]["locked_days"] == 1


def test_plan_quit_in_coros_app_recreates(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2))
    fake = FakeCoros()
    _push(uid, fake)
    fake.plans.clear()  # athlete quit it in the COROS app
    _push(uid, fake)
    assert len(fake.tool_calls("createTrainingPlan")) == 2
    assert db.get_coros_plan_link(uid)["coros_plan_id"] == "500000000000000002"


def test_adopts_existing_plan_by_name_when_link_missing(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2))
    fake = FakeCoros()
    fake.plans["777"] = {"name": "Uphill AI · UTMB 50K", "start": TODAY, "weeks": 13}
    _push(uid, fake)
    assert fake.tool_calls("createTrainingPlan") == []
    assert db.get_coros_plan_link(uid)["coros_plan_id"] == "777"


def test_far_race_starts_plan_in_the_future(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(3), race_date="2027-08-05")  # race Monday 08-02
    fake = FakeCoros()
    res = _push(uid, fake)
    (create,) = fake.tool_calls("createTrainingPlan")
    assert (create["planInfo"]["planStartDate"], create["planInfo"]["totalWeeks"]) == (20270419, 16)
    assert min(_days(create)) == 0  # Mon 04-19 is dayNo 0; days before the start aren't sent
    assert res["summary"]["plan_start"] == "2027-04-19"


def test_race_too_far_refuses_before_any_coros_call(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(3), race_date="2027-09-30")
    fake = FakeCoros()
    with pytest.raises(PushError) as info:
        _push(uid, fake)
    assert (info.value.code, info.value.status) == ("RACE_too_far", 409)
    assert info.value.params == {"opens_on": "2027-05-31"}  # race Monday 09-27 - 15 weeks - 14 days
    assert fake.calls == []


def test_race_too_close_refuses_before_any_coros_call(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2), race_date="2027-04-22")
    fake = FakeCoros()
    with pytest.raises(PushError) as info:
        _push(uid, fake)
    assert (info.value.code, info.value.params) == ("RACE_too_close", {"weeks": 3})
    assert fake.calls == []


def test_rollover_when_race_moves_past_sixteen_weeks(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(14), race_date="2027-07-22")
    fake = FakeCoros()
    _push(uid, fake)
    assert fake.tool_calls("createTrainingPlan")[0]["planInfo"]["totalWeeks"] == 16
    _set_race(plan_id, "2027-08-19")
    late = dt.date(2027, 6, 30)  # Wednesday of week 13
    res = _push(uid, fake, today=late)
    assert res["status"] == "sent"
    (shorten,) = fake.tool_calls("updateTrainingPlan")
    assert shorten["planInfo"] == {"planId": "500000000000000001", "totalWeeks": 13}
    create = fake.tool_calls("createTrainingPlan")[1]
    assert (create["planInfo"]["planStartDate"], create["planInfo"]["totalWeeks"]) == (20270705, 7)
    assert _race_course(create)["dayNo"] == (dt.date(2027, 8, 19) - dt.date(2027, 7, 5)).days
    link = db.get_coros_plan_link(uid)
    assert link["coros_plan_id"] == "500000000000000002" and link["coros_start_date"] == dt.date(2027, 7, 5)


def test_rollover_refused_as_too_far_leaves_old_plan_untouched(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(14), race_date="2027-07-22")
    fake = FakeCoros()
    _push(uid, fake)
    _set_race(plan_id, "2028-03-02")
    with pytest.raises(PushError) as info:
        _push(uid, fake, today=dt.date(2027, 6, 30))
    assert info.value.code == "RACE_too_far"
    assert fake.tool_calls("updateTrainingPlan") == []


def test_rollover_create_failure_is_partial(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(14), race_date="2027-07-22")
    fake = FakeCoros()
    _push(uid, fake)
    _set_race(plan_id, "2027-08-19")
    fake.fail["createTrainingPlan"] = McpError("timeout")
    res = _push(uid, fake, today=dt.date(2027, 6, 30))
    assert res["status"] == "partial"
    link = db.get_coros_plan_link(uid)
    assert link["partial"] is True and link["coros_plan_id"] == "500000000000000001" and link["total_weeks"] == 13
    assert coros_push.push_status(uid, dt.date(2027, 6, 30))["partial"] is True


def test_race_in_the_past_is_nothing_to_push(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2), race_date="2027-04-06")
    with pytest.raises(PushError) as info:
        _push(uid, FakeCoros())
    assert info.value.code == "NOTHING_to_push"


def test_errors(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2))
    fake = FakeCoros(fail={"createTrainingPlan": McpToolError("tool x reported an error", reason="bad course")})
    with pytest.raises(PushError) as info:
        _push(uid, fake)
    assert (info.value.code, info.value.status) == ("COROS_rejected", 502)
    assert db.get_coros_plan_link(uid) is None

    with pytest.raises(PushError) as info:
        _push(uid, FakeCoros(fail={"queryTrainingPlanLibrary": McpError("down")}))
    assert (info.value.code, info.value.status) == ("COROS_unavailable", 504)


def test_not_connected(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2))
    db.delete_provider_data(uid, "coros")
    with pytest.raises(PushError) as info:
        _push(uid, FakeCoros())
    assert info.value.code == "COROS_not_connected"


def test_daily_limit(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2))
    with patch("services.coros_push.settings.COROS_DAILY_PUSH_LIMIT", 1):
        _push(uid, FakeCoros())
        with pytest.raises(PushError) as info:
            _push(uid, FakeCoros())
    assert (info.value.code, info.value.status) == ("PUSH_limit", 429)


def test_in_progress(client, auth_headers, token):
    uid, _ = _setup(client, auth_headers, _weekly_rows(2))
    with db.coros_push_lock(uid):
        with pytest.raises(PushError) as info:
            _push(uid, FakeCoros())
    assert info.value.code == "PUSH_in_progress"


def test_status_out_of_date_after_move_and_clears_after_push(client, auth_headers, token):
    uid, plan_id = _setup(client, auth_headers, _weekly_rows(2))
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
