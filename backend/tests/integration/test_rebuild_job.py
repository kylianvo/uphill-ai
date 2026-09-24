import asyncio
from unittest.mock import AsyncMock, patch

import pytest

import db
from config import settings
from services import week_rebuild
from services.calendar_rules import GuardViolation
from tests.integration.calendar_helpers import add_workout, link_coach, make_plan, server_today, this_monday

TODAY = server_today()


def _gen_ok(title="Rebuilt"):
    async def _gen(plan_id, user_profile, race_info, total_weeks=12, **kwargs):
        wk = kwargs["target_week"]
        return [
            {
                "week_number": wk,
                "day_of_week": d,
                "phase": "Base",
                "title": title,
                "type": "Easy",
                "duration_minutes": 30,
                "target_zone": "Zone 2",
                "description": "n",
            }
            for d in ("Tuesday", "Thursday")
        ], "recreational"

    return _gen


@pytest.fixture
def sync_spawn(monkeypatch):
    monkeypatch.setattr(week_rebuild, "spawn", lambda factory: asyncio.run(factory()))


@pytest.fixture
def held_spawn(monkeypatch):
    held = []
    monkeypatch.setattr(week_rebuild, "spawn", held.append)
    return held


def _setup(uid):
    plan_id = make_plan(uid, start_date=this_monday())
    add_workout(plan_id, 1, "Monday")
    add_workout(plan_id, 2, "Tuesday", title="Old Tue")
    add_workout(plan_id, 2, "Wednesday", title="Old Wed")
    add_workout(plan_id, 3, "Monday")
    return plan_id, db.get_or_create_chat_thread(uid)


def _request(uid, plan_id, thread, week=2, today=TODAY):
    return week_rebuild.request_rebuild(
        user_id=uid,
        thread_id=thread["id"],
        plan_id=plan_id,
        today=today,
        request=week_rebuild.RebuildRequest(week_number=week, fatigue_level="hard", fatigue_notes="tired"),
        rationale="tired",
    )


def test_request_drafts_in_background_and_writes_nothing(auth_headers, sync_spawn):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen_ok())):
        out = _request(uid, plan_id, thread)
    assert out["week"] == 2 and out["from_day"] == "Monday"
    row = db.get_chat_proposal(out["proposal_id"])
    assert row["kind"] == "rebuild" and row["status"] == "proposed"
    assert [w["title"] for w in row["draft"]["workouts"]] == ["Rebuilt", "Rebuilt"]
    assert row["draft"]["resolved_tier"] == "recreational"
    days = {d["day"]: d for d in row["diff"]["days"]}
    assert days["Tuesday"]["before"][0]["title"] == "Old Tue" and days["Tuesday"]["after"][0]["title"] == "Rebuilt"
    assert row["operations"]["request"]["fatigue_level"] == "hard"
    titles = {w["title"] for w in db.get_plan_workouts(plan_id)}
    assert "Old Tue" in titles and "Rebuilt" not in titles  # nothing written


def test_generation_error_marks_failed(auth_headers, sync_spawn):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        out = _request(uid, plan_id, thread)
    row = db.get_chat_proposal(out["proposal_id"])
    assert row["status"] == "failed" and row["stale_reason"] == "generation_error"


def test_empty_generation_marks_failed(auth_headers, sync_spawn):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new=AsyncMock(return_value=([], "recreational")),
    ):
        out = _request(uid, plan_id, thread)
    assert db.get_chat_proposal(out["proposal_id"])["stale_reason"] == "generation_empty"


def test_timeout_marks_failed(auth_headers, sync_spawn, monkeypatch):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    monkeypatch.setattr(week_rebuild, "REBUILD_TIMEOUT_SECONDS", 0.01)

    async def _slow(*a, **k):
        await asyncio.sleep(1)

    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_slow)):
        out = _request(uid, plan_id, thread)
    assert db.get_chat_proposal(out["proposal_id"])["stale_reason"] == "generation_timeout"


def test_discard_during_generation_wins(auth_headers, held_spawn):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    out = _request(uid, plan_id, thread)
    assert db.discard_chat_proposal(out["proposal_id"], uid) == "discarded"
    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen_ok())):
        asyncio.run(held_spawn[0]())
    assert db.get_chat_proposal(out["proposal_id"])["status"] == "discarded"


@pytest.mark.parametrize(
    ("week", "code"),
    [(3, "G4_window"), (0, "G4_window")],
)
def test_window_is_this_week_and_next(auth_headers, held_spawn, week, code):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    with pytest.raises(GuardViolation) as e:
        _request(uid, plan_id, thread, week=week)
    assert e.value.code == code and held_spawn == []


def test_duplicate_open_week_and_daily_limit(auth_headers, held_spawn, monkeypatch):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    monkeypatch.setattr(settings, "COACH_CHAT_DAILY_REBUILDS_LIMIT", 1)
    first = _request(uid, plan_id, thread, week=2)
    with pytest.raises(GuardViolation) as dup:
        _request(uid, plan_id, thread, week=2)
    assert dup.value.code == "DUPLICATE_pending" and dup.value.params["proposal_id"] == first["proposal_id"]
    with pytest.raises(GuardViolation) as lim:
        _request(uid, plan_id, thread, week=1)
    assert lim.value.code == "REBUILD_limit"
    assert len(held_spawn) == 1


def test_coach_linked_and_undated_plans_are_refused(auth_headers, held_spawn):
    uid = auth_headers["user_id"]
    plan_id, thread = _setup(uid)
    link_coach(uid)
    with pytest.raises(GuardViolation) as e:
        _request(uid, plan_id, thread)
    assert e.value.code == "G6_coach_linked"


def test_undated_plan_is_refused(auth_headers, held_spawn):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=None)
    add_workout(plan_id, 1, "Monday")
    with pytest.raises(GuardViolation) as e:
        _request(uid, plan_id, db.get_or_create_chat_thread(uid), week=1)
    assert e.value.code == "G7_no_dates"
