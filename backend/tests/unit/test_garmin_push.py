"""Garmin workout conversion and calendar sync -- no DB, no live Garmin."""

import asyncio
import datetime as dt
import json

import httpx
import pytest

from services import garmin_oauth, garmin_push, garmin_workouts
from services.coros_plan_window import DayPush, PushWindow
from services.coros_workouts import SECTION_COOLDOWN, SECTION_RECOVERY, SECTION_TRAINING, SECTION_WARMUP

TODAY = dt.date(2026, 10, 26)


def _course(name="Tempo"):
    return {
        "courseName": name,
        "courseDescription": "Warm up, then 3x8 min tempo.",
        "sections": [
            {"sectionType": SECTION_WARMUP, "targetType": 2, "targetValue": 600, "intensityType": 1, "sectionIntensity": 1},
            {
                "intervalGroup": True,
                "repeats": 3,
                "sets": [
                    {"sectionType": SECTION_TRAINING, "targetType": 2, "targetValue": 480,
                     "intensityType": 1, "intensityValueStart": 150, "intensityValueEnd": 160},
                    {"sectionType": SECTION_RECOVERY, "targetType": 2, "targetValue": 120, "intensityType": 1, "sectionIntensity": 1},
                ],
            },
            {"sectionType": SECTION_COOLDOWN, "targetType": 1, "targetValue": 2000, "intensityType": 1, "sectionIntensity": 1},
        ],
    }  # fmt: skip


def test_course_becomes_a_garmin_running_workout_with_repeats_and_hr_targets():
    w = garmin_workouts.to_workout(_course())
    assert w["sport"] == "RUNNING" and w["workoutProvider"] == "Uphill AI"
    warm, repeat, cool = w["segments"][0]["steps"]
    assert (warm["intensity"], warm["durationType"], warm["durationValue"]) == ("WARMUP", "TIME", 600)
    assert (warm["targetType"], warm["targetValue"]) == ("HEART_RATE", 1)
    assert repeat["type"] == "WorkoutRepeatStep" and repeat["repeatValue"] == 3
    work, rest = repeat["steps"]
    assert work["intensity"] == "INTERVAL" and (work["targetValueLow"], work["targetValueHigh"]) == (150, 160)
    assert rest["intensity"] == "RECOVERY"
    assert (cool["durationType"], cool["durationValue"], cool["durationValueType"]) == ("DISTANCE", 2000, "METER")
    orders = [warm["stepOrder"], repeat["stepOrder"], work["stepOrder"], rest["stepOrder"], cool["stepOrder"]]
    assert orders == [1, 2, 3, 4, 5]


def test_a_course_without_sections_is_one_open_step():
    w = garmin_workouts.to_workout({"courseName": "Race", "courseDescription": "", "sections": []})
    assert w["segments"][0]["steps"][0]["durationType"] == "OPEN"


class FakeGarmin:
    """Records calls; numbers workouts and schedules from 1."""

    def __init__(self, fail_on_create: int | None = None):
        self.calls: list[tuple[str, str]] = []
        self.fail_on_create = fail_on_create
        self.created = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.method, request.url.path))
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.url.path == "/workoutportal/workout/v2":
            self.created += 1
            if self.created == self.fail_on_create:
                return httpx.Response(429)
            return httpx.Response(200, json={"workoutId": self.created, **json.loads(request.content)})
        return httpx.Response(200, json={"scheduleId": 100 + self.created})


@pytest.fixture
def world(monkeypatch):
    state = {"link": None, "window": None, "hashes": {}}
    monkeypatch.setattr(garmin_push, "CALL_SPACING_SECONDS", 0)
    monkeypatch.setattr(
        garmin_push.db,
        "get_connection",
        lambda u, p: {"user_id": u, "status": "active", "scopes": "ACTIVITY_EXPORT WORKOUT_IMPORT"},
    )
    monkeypatch.setattr(garmin_push.db, "get_active_plan", lambda u: {"id": 9, "user_id": u})
    monkeypatch.setattr(garmin_push.db, "claim_garmin_push_slot", lambda u, d, limit: True)
    monkeypatch.setattr(garmin_push.db, "get_garmin_push_link", lambda u: state["link"])

    def save(user_id, **kw):
        state["link"] = {**kw, "last_pushed_at": dt.datetime(2026, 10, 26, tzinfo=dt.UTC)}

    async def token(connection):
        return "tok"

    monkeypatch.setattr(garmin_push.db, "save_garmin_push_link", save)
    monkeypatch.setattr(garmin_oauth, "access_token", token)
    monkeypatch.setattr(
        garmin_push, "_plan_window", lambda plan, today, lang: (type("St", (), {"by_date": {}})(), state["window"])
    )
    monkeypatch.setattr(
        garmin_push,
        "day_hashes_for",
        lambda by_date, dates: {d.isoformat(): state["hashes"].get(d, "h") for d in dates},
    )
    return state


def _window(*days):
    return PushWindow(start=TODAY, end=TODAY + dt.timedelta(days=27), days=[DayPush(d, [_course()]) for d in days])


def _push(fake):
    return asyncio.run(garmin_push.push(42, TODAY, "en", transport=httpx.MockTransport(fake)))


def test_first_send_creates_and_schedules_each_run_then_a_resend_skips_unchanged_days(world):
    d1, d2 = TODAY + dt.timedelta(days=1), TODAY + dt.timedelta(days=3)
    world["window"] = _window(d1, d2)
    fake = FakeGarmin()
    result = _push(fake)
    assert result["status"] == "sent" and result["summary"]["workouts_sent"] == 2
    assert [m for m, _ in fake.calls] == ["POST", "POST", "POST", "POST"]
    assert world["link"]["scheduled"] == {d1.isoformat(): [["1", "101"]], d2.isoformat(): [["2", "102"]]}

    again = FakeGarmin()
    _push(again)
    assert again.calls == []


def test_a_changed_day_is_replaced_and_a_day_without_a_run_is_deleted(world):
    d1, d2 = TODAY + dt.timedelta(days=1), TODAY + dt.timedelta(days=3)
    world["window"] = _window(d1, d2)
    _push(FakeGarmin())
    world["window"] = _window(d1)
    world["hashes"] = {d1: "changed"}
    fake = FakeGarmin()
    _push(fake)
    assert ("DELETE", "/training-api/schedule/102") in fake.calls  # d2's run is gone from the plan
    assert ("DELETE", "/training-api/workout/v2/1") in fake.calls  # d1 changed: old copy removed
    assert list(world["link"]["scheduled"]) == [d1.isoformat()]


def test_a_rate_limited_send_keeps_what_was_created(world):
    d1, d2 = TODAY + dt.timedelta(days=1), TODAY + dt.timedelta(days=3)
    world["window"] = _window(d1, d2)
    result = _push(FakeGarmin(fail_on_create=2))
    assert result["status"] == "partial"
    assert world["link"]["scheduled"][d1.isoformat()] == [["1", "101"]]
    assert world["link"]["partial"] is True
    assert d2.isoformat() not in world["link"]["day_hashes"]  # retried on the next send


def test_send_needs_the_workout_permission(world, monkeypatch):
    monkeypatch.setattr(
        garmin_push.db, "get_connection", lambda u, p: {"status": "active", "scopes": "ACTIVITY_EXPORT"}
    )
    with pytest.raises(garmin_push.PushError) as exc:
        _push(FakeGarmin())
    assert exc.value.code == "GARMIN_no_workout_permission"


def test_the_daily_send_cap_counts_on_the_server_date(world, monkeypatch):
    seen = []
    monkeypatch.setattr(garmin_push.db, "claim_garmin_push_slot", lambda u, d, limit: seen.append(d) or True)
    world["window"] = _window(TODAY + dt.timedelta(days=1))
    asyncio.run(garmin_push.push(42, dt.date(2030, 1, 1), "en", transport=httpx.MockTransport(FakeGarmin())))
    assert seen == [dt.datetime.now(dt.UTC).date()]
