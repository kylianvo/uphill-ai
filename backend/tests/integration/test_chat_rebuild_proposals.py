import asyncio
import datetime as dt
import uuid
from unittest.mock import AsyncMock, patch

import pytest

import db
from services import week_rebuild
from services.coach_chat import run_turn
from services.coach_graph import ToolResultEvent
from services.coach_model import FakeCoachModel, ModelEvent
from services.coach_tools import proposal_tools
from services.coach_tools.registry import ProposalContext
from services.observability import Usage
from tests.integration.calendar_helpers import add_workout, make_plan, server_today, this_monday


async def _gen(plan_id, user_profile, race_info, total_weeks=12, **kwargs):
    return [
        {
            "week_number": kwargs["target_week"],
            "day_of_week": "Wednesday",
            "phase": "Base",
            "title": "Rebuilt",
            "type": "Easy",
            "duration_minutes": 30,
            "target_zone": "Zone 2",
            "description": "n",
        }
    ], "recreational"


@pytest.fixture(autouse=True)
def sync_spawn(monkeypatch):
    monkeypatch.setattr(week_rebuild, "spawn", lambda factory: asyncio.run(factory()))


def _plan(uid):
    plan_id = make_plan(uid, start_date=this_monday())
    add_workout(plan_id, 1, "Monday")
    add_workout(plan_id, 2, "Tuesday", title="Old Tue")
    return plan_id


def _ctx(uid, plan_id):
    return ProposalContext(thread_id=db.get_or_create_chat_thread(uid)["id"], plan_id=plan_id, today=server_today())


def test_impl_success_returns_a_generating_card(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = _plan(uid)
    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen)):
        res = proposal_tools.propose_rebuild_week_impl(
            user_id=uid,
            ctx=_ctx(uid, plan_id),
            week=2,
            fatigue_level="hard",
            reason="legs heavy",
            available_days=["Tuesday", "Wednesday", "Tuesday"],
            long_run_day="Wednesday",
        )
    assert res.status == "success" and res.card_type == "schedule_rebuild"
    assert res.card_data["status"] == "generating" and res.card_data["week"] == 2
    assert "do not describe new sessions" in res.card_data["note"]
    row = db.get_chat_proposal(res.card_data["proposal_id"])
    assert row["operations"]["request"]["preferred_days"] == ["Tuesday", "Wednesday"]
    assert row["operations"]["request"]["days_per_week"] == 2


def test_impl_refusals_explain_themselves(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = _plan(uid)
    ctx = _ctx(uid, plan_id)
    bad = proposal_tools.propose_rebuild_week_impl(
        user_id=uid,
        ctx=ctx,
        week=2,
        fatigue_level="hard",
        reason="x",
        available_days=["Monday"],
        long_run_day="Sunday",
    )
    assert bad.status == "error" and bad.error.startswith("INVALID_operation")
    far = proposal_tools.propose_rebuild_week_impl(user_id=uid, ctx=ctx, week=5, fatigue_level="hard", reason="x")
    assert far.status == "error" and far.error.startswith("G4_window") and "this week or next week" in far.error
    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen)):
        first = proposal_tools.propose_rebuild_week_impl(user_id=uid, ctx=ctx, week=2, fatigue_level="hard", reason="x")
        again = proposal_tools.propose_rebuild_week_impl(user_id=uid, ctx=ctx, week=2, fatigue_level="hard", reason="x")
    assert again.status == "error" and again.error.startswith("DUPLICATE_pending")
    assert f"#{first.card_data['proposal_id']}" in again.error


@pytest.mark.asyncio
async def test_turn_backfills_the_rebuild_card_message(auth_headers):
    uid = auth_headers["user_id"]
    _plan(uid)
    model = FakeCoachModel(
        responses=[
            [
                ModelEvent(
                    kind="tool_call",
                    tool_call={
                        "id": "r1",
                        "name": "propose_rebuild_week",
                        "args": {"week": 2, "fatigue_level": "hard", "reason": "tired"},
                    },
                )
            ],
            [
                ModelEvent(kind="text", text="Drafting a lighter week 2 -- the card will show it."),
                ModelEvent(kind="usage", usage=Usage(input_tokens=5, output_tokens=5)),
            ],
        ]
    )
    req = {
        "request_id": str(uuid.uuid4()),
        "message": "I'm wrecked, lighten next week",
        "lang": "en",
        "client_today": dt.datetime.now(dt.UTC).date().isoformat(),
    }
    with patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen)):
        events = [e async for e in run_turn(user={"id": uid}, request=req, model=model)]
    cards = [e for e in events if isinstance(e, ToolResultEvent) and e.card_type == "schedule_rebuild"]
    assert len(cards) == 1
    row = db.get_chat_proposal(cards[0].card_data["proposal_id"])
    assert row["user_id"] == uid and row["message_id"] is not None and row["status"] == "proposed"
