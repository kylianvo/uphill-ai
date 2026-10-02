"""Re-plans (adapt week) read a fresh snapshot, pass the stored tier as previous_tier
rather than as an override, and store the snapshot on the plan. Scratch DB only."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

import db
from services import week_rebuild
from services.calendar_rules import DAYS
from tests.integration.calendar_helpers import add_workout, make_plan, server_today, this_monday

TODAY = server_today()


def _gen_capturing(seen):
    async def _gen(plan_id, user_profile, race_info, total_weeks=12, **kwargs):
        seen.append(race_info)
        wk = kwargs["target_week"]
        return [
            {
                "week_number": wk,
                "day_of_week": d,
                "phase": "Base",
                "title": "Rebuilt",
                "type": "Easy",
                "duration_minutes": 30,
                "target_zone": "Zone 2",
                "description": "n",
            }
            for d in DAYS
        ], "sub_elite"

    return _gen


@pytest.fixture(autouse=True)
def sync_spawn(monkeypatch):
    monkeypatch.setattr(week_rebuild, "spawn", lambda factory: asyncio.run(factory()))


@pytest.fixture(autouse=True)
def no_coros_refresh(monkeypatch):
    from services import coros_sync

    async def no_refresh(uid, **kw):
        return None

    monkeypatch.setattr(coros_sync, "ensure_fresh_assessment", no_refresh)


def _plan(uid):
    plan_id = make_plan(uid, start_date=this_monday())
    for wk in (1, 2, 3):
        add_workout(plan_id, wk, "Monday", title=f"W{wk} Mon")
    db.set_plan_athlete_tier(plan_id, "recreational")
    return plan_id


def test_rebuild_proposal_carries_the_snapshot_and_unfreezes_the_tier(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = _plan(uid)
    thread = db.get_or_create_chat_thread(uid)
    seen = []
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen_capturing(seen))
    ):
        out = week_rebuild.request_rebuild(
            user_id=uid,
            thread_id=thread["id"],
            plan_id=plan_id,
            today=TODAY,
            request=week_rebuild.RebuildRequest(week_number=2, fatigue_level="hard"),
            rationale="r",
        )
    race_info = seen[0]
    assert race_info["athlete_tier"] is None
    assert race_info["previous_tier"] == "recreational"
    assert race_info["fitness_snapshot"] is not None

    row = db.get_chat_proposal(out["proposal_id"])
    assert row["draft"]["fitness_snapshot"]["weekly_km_source"] == "self_reported"

    mid = db.append_chat_message(thread["id"], "assistant", "drafting")
    db.set_proposals_message_id(thread["id"], [out["proposal_id"]], mid)
    resp = client.post(
        f"/api/coach/chat/proposals/{out['proposal_id']}/apply",
        headers=auth_headers["headers"],
        json={"client_today": TODAY.isoformat()},
    )
    assert resp.status_code == 200, resp.text
    plan = db.get_plan_by_id(plan_id)
    assert plan["athlete_tier"] == "sub_elite"
    assert plan["fitness_snapshot"]["weekly_km_source"] == "self_reported"


def test_direct_write_stores_the_snapshot(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = _plan(uid)
    plan = db.get_plan_by_id(plan_id)
    draft = week_rebuild.WeekDraft(
        workouts=[
            {
                "week_number": 2,
                "day_of_week": d,
                "phase": "Base",
                "title": "Rebuilt",
                "type": "Easy",
                "duration_minutes": 30,
                "target_zone": "Zone 2",
                "description": "n",
            }
            for d in DAYS
        ],
        resolved_tier="sub_elite",
        fitness_snapshot={"weekly_km": 138.0, "tier": "sub_elite"},
    )
    week_rebuild.write_draft(plan, 2, TODAY, draft)
    assert db.get_plan_by_id(plan_id)["fitness_snapshot"] == {"weekly_km": 138.0, "tier": "sub_elite"}


def test_snapshot_failure_never_blocks_the_rebuild(auth_headers, monkeypatch):
    from services import fitness_snapshot

    def boom(uid, **kw):
        raise RuntimeError("db down")

    monkeypatch.setattr(fitness_snapshot, "build", boom)
    uid = auth_headers["user_id"]
    plan_id = _plan(uid)
    thread = db.get_or_create_chat_thread(uid)
    seen = []
    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen_capturing(seen))
    ):
        out = week_rebuild.request_rebuild(
            user_id=uid,
            thread_id=thread["id"],
            plan_id=plan_id,
            today=TODAY,
            request=week_rebuild.RebuildRequest(week_number=2, fatigue_level="hard"),
            rationale="r",
        )
    row = db.get_chat_proposal(out["proposal_id"])
    assert row["status"] == "proposed"
    assert row["draft"]["fitness_snapshot"] is None
