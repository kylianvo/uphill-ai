import datetime as dt

import pytest

import db
from services import calendar_ops
from services.calendar_rules import GuardViolation
from tests.integration.calendar_helpers import add_workout, link_coach, make_plan, match_activity, this_monday

TODAY = dt.datetime.now(dt.UTC).date()


def _future_day_this_or_next_week():
    """(week, day) strictly after today, in the current or next plan week, for a plan starting this Monday."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    idx = TODAY.weekday()
    return (1, days[idx + 1]) if idx < 6 else (2, "Tuesday")


def test_apply_moves_and_clears_missed(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 1, "Monday", missed=1)
    week, day = _future_day_this_or_next_week()
    changes = calendar_ops.apply(
        uid, plan_id, [{"op": "move", "workout_id": wid, "target_week": week, "target_day": day}], TODAY, agent=False
    )
    assert changes.moves[0]["to_day"] == day
    row = db.get_workout_by_id(wid)
    assert (row["week_number"], row["day_of_week"], row["is_missed"]) == (week, day, 0)


def test_g1_plan_must_be_the_callers_active_plan(auth_headers):
    uid = auth_headers["user_id"]
    other = db.create_or_get_user("other-4a@uphill.ai", "Other", "mock", "mock-other-4a")
    plan_id = make_plan(other["id"], start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    with pytest.raises(GuardViolation) as e:
        calendar_ops.apply(
            uid,
            plan_id,
            [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}],
            TODAY,
            agent=False,
        )
    assert e.value.code == "G1_not_owner"


def test_g6_only_for_agent_writes(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    link_coach(uid)
    op = [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}]
    with pytest.raises(GuardViolation) as e:
        calendar_ops.preview(uid, plan_id, op, TODAY, agent=True)
    assert e.value.code == "G6_coach_linked"
    calendar_ops.apply(uid, plan_id, op, TODAY, agent=False)  # manual stays allowed
    assert db.get_workout_by_id(wid)["day_of_week"] == "Friday"


def test_matched_activity_blocks_the_move(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    match_activity(uid, wid)
    with pytest.raises(GuardViolation) as e:
        calendar_ops.apply(
            uid,
            plan_id,
            [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}],
            TODAY,
            agent=False,
        )
    assert e.value.code == "G2_history"


def test_fingerprint_mismatch_is_stale_and_writes_nothing(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    op = [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}]
    preview = calendar_ops.preview(uid, plan_id, op, TODAY, agent=True)
    calendar_ops.apply(
        uid,
        plan_id,
        [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Wednesday"}],
        TODAY,
        agent=False,
    )
    with pytest.raises(GuardViolation) as e:
        calendar_ops.apply(uid, plan_id, op, TODAY, agent=True, expected_fingerprints=preview.fingerprints)
    assert e.value.code == "STALE_changed"
    assert db.get_workout_by_id(wid)["day_of_week"] == "Wednesday"


def test_preview_writes_nothing(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    calendar_ops.preview(
        uid, plan_id, [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Friday"}], TODAY, agent=True
    )
    assert db.get_workout_by_id(wid)["day_of_week"] == "Tuesday"
