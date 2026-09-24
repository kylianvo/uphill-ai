import datetime as dt
import uuid

import pytest
from sqlalchemy import text

import db
from services.coach_chat import run_turn
from services.coach_graph import ToolResultEvent
from services.coach_model import FakeCoachModel, ModelEvent
from services.observability import Usage
from tests.integration.calendar_helpers import add_workout, link_coach, make_plan, this_monday


def _model(tool_args):
    return FakeCoachModel(
        responses=[
            [
                ModelEvent(
                    kind="tool_call", tool_call={"id": "p1", "name": "propose_schedule_change", "args": tool_args}
                )
            ],
            [
                ModelEvent(kind="text", text="Here's a proposal -- tap Apply if it works for you."),
                ModelEvent(kind="usage", usage=Usage(input_tokens=5, output_tokens=5)),
            ],
        ]
    )


async def _turn(user_id, model, message="Move my Tuesday run to Friday"):
    req = {
        "request_id": str(uuid.uuid4()),
        "message": message,
        "lang": "en",
        "client_today": dt.datetime.now(dt.UTC).date().isoformat(),
    }
    return [e async for e in run_turn(user={"id": user_id}, request=req, model=model)]


@pytest.mark.asyncio
async def test_turn_creates_a_proposal_card_and_backfills_message(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    args = {
        "operations": [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday", "user_id": 999}],
        "rationale": "Busy Tuesday",
    }
    events = await _turn(uid, _model(args))
    cards = [e for e in events if isinstance(e, ToolResultEvent) and e.card_type == "schedule_proposal"]
    assert len(cards) == 1
    pid = cards[0].card_data["proposal_id"]
    row = db.get_chat_proposal(pid)
    assert row["status"] == "proposed"
    assert row["user_id"] == uid  # closure identity, not the argument
    assert row["message_id"] is not None
    assert db.get_workout_by_id(wid)["day_of_week"] == "Tuesday"  # nothing written


@pytest.mark.asyncio
async def test_guard_refusal_writes_no_row(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday", completed=1)
    events = await _turn(
        uid,
        _model(
            {
                "operations": [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}],
                "rationale": "x",
            }
        ),
    )
    results = [e for e in events if isinstance(e, ToolResultEvent)]
    assert results and results[0].status == "error"
    with db.engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM chat_proposals WHERE user_id = :u"), {"u": uid}).scalar() == 0


@pytest.mark.asyncio
async def test_tool_is_not_offered_to_coach_linked_athletes(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    link_coach(uid)
    events = await _turn(
        uid,
        _model(
            {
                "operations": [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}],
                "rationale": "x",
            }
        ),
    )
    results = [e for e in events if isinstance(e, ToolResultEvent)]
    assert results and results[0].status == "error"  # unknown_tool: never registered
    assert db.get_workout_by_id(wid)["day_of_week"] == "Tuesday"


@pytest.mark.asyncio
async def test_typed_yes_writes_nothing(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    await _turn(
        uid,
        _model(
            {
                "operations": [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}],
                "rationale": "x",
            }
        ),
    )
    reply_only = FakeCoachModel(responses=[ModelEvent(kind="text", text="Tap Apply on the card to confirm.")])
    await _turn(uid, reply_only, message="yes")
    assert db.get_workout_by_id(wid)["day_of_week"] == "Tuesday"


@pytest.mark.asyncio
async def test_turn_prompt_tells_the_model_today(auth_headers):
    uid = auth_headers["user_id"]
    make_plan(uid, start_date=this_monday())
    model = FakeCoachModel(responses=[ModelEvent(kind="text", text="ok")])
    await _turn(uid, model, message="what's on tomorrow?")
    today = dt.datetime.now(dt.UTC).date()
    assert f"Today is {today.strftime('%A')} {today.isoformat()} (plan week 1," in model.requests[0].system


def _propose(uid, plan_id, operations):
    from services.coach_tools.proposal_tools import propose_schedule_change_impl
    from services.coach_tools.registry import ProposalContext

    thread = db.get_or_create_chat_thread(uid)
    ctx = ProposalContext(thread_id=thread["id"], plan_id=plan_id, today=dt.datetime.now(dt.UTC).date())
    return propose_schedule_change_impl(user_id=uid, ctx=ctx, operations=operations, rationale="r")


def _proposal_count(uid):
    with db.engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM chat_proposals WHERE user_id = :u"), {"u": uid}).scalar()


def _move(wid, day, week=2):
    return {"op": "move", "workout_id": wid, "target_week": week, "target_day": day}


def test_same_move_twice_is_deduped_while_pending(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    first = _propose(uid, plan_id, [_move(wid, "Friday")])
    assert first.status == "success"
    second = _propose(uid, plan_id, [_move(wid, "Friday")])
    assert second.status == "error"
    assert second.error.startswith("DUPLICATE_pending")
    assert f"#{first.card_data['proposal_id']}" in second.error
    assert _proposal_count(uid) == 1


def test_same_move_can_be_proposed_again_after_discard(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    first = _propose(uid, plan_id, [_move(wid, "Friday")])
    assert db.discard_chat_proposal(first.card_data["proposal_id"], uid) == "discarded"
    again = _propose(uid, plan_id, [_move(wid, "Friday")])
    assert again.status == "success"
    assert again.card_data["proposal_id"] != first.card_data["proposal_id"]
    assert _proposal_count(uid) == 2


def test_swap_days_matching_an_open_proposal_is_deduped(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    w_tue = add_workout(plan_id, 2, "Tuesday")
    w_fri = add_workout(plan_id, 2, "Friday")
    assert _propose(uid, plan_id, [_move(w_tue, "Friday"), _move(w_fri, "Tuesday")]).status == "success"
    swap = _propose(uid, plan_id, [{"op": "swap_days", "week": 2, "day_1": "Tuesday", "day_2": "Friday"}])
    assert swap.status == "error" and swap.error.startswith("DUPLICATE_pending")
    assert _proposal_count(uid) == 1


def test_different_proposal_touching_same_workout_is_allowed(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    assert _propose(uid, plan_id, [_move(wid, "Friday")]).status == "success"
    assert _propose(uid, plan_id, [_move(wid, "Saturday")]).status == "success"
    assert _proposal_count(uid) == 2


def test_nothing_to_move_tells_the_model_not_to_ask_for_apply(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Friday")
    result = _propose(uid, plan_id, [_move(wid, "Friday")])
    assert result.status == "error" and result.error.startswith("NOTHING_to_move")
    assert "already on those days" in result.error
    assert "do not ask the athlete to apply anything" in result.error
    assert _proposal_count(uid) == 0


def test_move_proposal_succeeds_while_a_rebuild_card_is_open(auth_headers):
    """get_open_chat_proposals must exclude kind='rebuild' rows: their diff is a
    dict, and _moves_key(dict) blows up with a TypeError, breaking every 4a move
    proposal in the thread for as long as any rebuild card is open."""
    import asyncio
    from unittest.mock import AsyncMock, patch

    from services import week_rebuild
    from services.coach_tools import proposal_tools
    from services.coach_tools.registry import ProposalContext

    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    thread = db.get_or_create_chat_thread(uid)
    ctx = ProposalContext(thread_id=thread["id"], plan_id=plan_id, today=dt.datetime.now(dt.UTC).date())

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

    with (
        patch.object(week_rebuild, "spawn", lambda factory: asyncio.run(factory())),
        patch("services.plan_generator.PlanGenerator.generate_plan_workouts", new=AsyncMock(side_effect=_gen)),
    ):
        rebuild_res = proposal_tools.propose_rebuild_week_impl(
            user_id=uid, ctx=ctx, week=2, fatigue_level="hard", reason="tired"
        )
    assert rebuild_res.status == "success"

    move_res = proposal_tools.propose_schedule_change_impl(
        user_id=uid,
        ctx=ctx,
        operations=[{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}],
        rationale="Busy Tuesday",
    )
    assert move_res.status == "success" and move_res.card_type == "schedule_proposal"


@pytest.mark.asyncio
async def test_no_proposal_lookups_without_an_api_key(auth_headers, monkeypatch):
    from config import settings

    uid = auth_headers["user_id"]
    make_plan(uid, start_date=this_monday())
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    calls = []
    monkeypatch.setattr(db, "get_active_coach_link_for_athlete", lambda user_id: calls.append(user_id))
    await _turn(uid, FakeCoachModel(responses=[ModelEvent(kind="text", text="ok")]), message="hi")
    assert calls == []
