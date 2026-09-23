import datetime as dt

import pytest

from services import calendar_rules as cr
from services.calendar_rules import GuardViolation

# Plan week 1 starts Mon 2026-09-07; "today" is Wed 2026-09-23 = week 3 Wednesday.
PLAN = {"id": 1, "start_date": "2026-09-07", "total_weeks": 12}
TODAY = dt.date(2026, 9, 23)


def wo(wid, week, day, **kw):
    row = {
        "id": wid,
        "plan_id": 1,
        "week_number": week,
        "day_of_week": day,
        "title": kw.pop("title", f"W{wid}"),
        "type": kw.pop("type", "Easy"),
        "target_zone": kw.pop("zone", "Zone 2"),
        "duration_minutes": kw.pop("minutes", 60),
        "is_completed": 0,
        "is_missed": 0,
        "matched_activity_id": None,
        "approved_at": "2026-09-01T00:00:00+00:00",
        "session_slot": "main",
    }
    row.update(kw)
    return row


def move(wid, week, day):
    return {"op": "move", "workout_id": wid, "target_week": week, "target_day": day}


def codes(changes):
    return [w["code"] for w in changes.warnings]


# --- dates / today -----------------------------------------------------------


def test_dates_are_monday_aligned():
    monday = cr.start_monday("2026-09-09")  # a Wednesday
    assert monday == dt.date(2026, 9, 7)
    assert cr.workout_date(monday, 3, "Wednesday") == TODAY
    assert cr.current_week(monday, TODAY) == 3


def test_resolve_today_clamps_client_date():
    server = dt.date(2026, 9, 23)
    assert cr.resolve_today("2026-09-22", server) == dt.date(2026, 9, 22)
    assert cr.resolve_today("2026-09-24", server) == dt.date(2026, 9, 24)
    assert cr.resolve_today("2026-09-10", server) == server
    assert cr.resolve_today("not-a-date", server) == server
    assert cr.resolve_today(None, server) == server


# --- shape ---------------------------------------------------------------------


def test_more_than_five_operations_is_invalid():
    rows = [wo(1, 3, "Thursday")]
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, rows, [move(1, 3, "Friday")] * 6, TODAY)
    assert e.value.code == "INVALID_operation"


def test_unknown_day_is_invalid():
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, [wo(1, 3, "Thursday")], [move(1, 3, "Funday")], TODAY)
    assert e.value.code == "INVALID_operation"


def test_noop_only_is_nothing_to_move():
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, [wo(1, 3, "Thursday")], [move(1, 3, "Thursday")], TODAY)
    assert e.value.code == "NOTHING_to_move"


# --- guards --------------------------------------------------------------------


def test_move_same_week_future_ok_and_fingerprinted():
    changes = cr.plan_changes(PLAN, [wo(1, 3, "Thursday")], [move(1, 3, "Saturday")], TODAY)
    assert changes.moves == [
        {"workout_id": 1, "from_week": 3, "from_day": "Thursday", "to_week": 3, "to_day": "Saturday"}
    ]
    assert set(changes.fingerprints) == {"1"}
    assert changes.fingerprints["1"]["day_of_week"] == "Thursday"
    assert changes.diff[0]["workout"]["day_of_week"] == "Saturday"


def test_g1_workout_not_in_plan():
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, [wo(1, 3, "Thursday")], [move(99, 3, "Friday")], TODAY)
    assert e.value.code == "G1_not_owner"


@pytest.mark.parametrize("extra", [{"is_completed": 1}, {"matched_activity_id": 555}])
def test_g2_history_is_frozen(extra):
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, [wo(1, 3, "Thursday", **extra)], [move(1, 3, "Friday")], TODAY)
    assert e.value.code == "G2_history"


def test_g3_past_target_refused():
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, [wo(1, 3, "Thursday")], [move(1, 3, "Monday")], TODAY)
    assert e.value.code == "G3_past_target"


def test_today_is_a_valid_target():
    changes = cr.plan_changes(PLAN, [wo(1, 3, "Thursday")], [move(1, 3, "Wednesday")], TODAY)
    assert changes.moves[0]["to_day"] == "Wednesday"


def test_missed_past_workout_can_move_forward_and_is_unmissed():
    rows = [wo(1, 3, "Monday", is_missed=1)]
    changes = cr.plan_changes(PLAN, rows, [move(1, 3, "Friday")], TODAY)
    assert changes.diff[0]["workout"]["is_missed"] == 0


def test_g4_cross_week_window():
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, [wo(1, 3, "Thursday")], [move(1, 5, "Monday")], TODAY)
    assert e.value.code == "G4_window"
    # previous week (missed) -> current week is allowed
    ok = cr.plan_changes(PLAN, [wo(2, 2, "Tuesday", is_missed=1)], [move(2, 3, "Friday")], TODAY)
    assert ok.moves[0]["to_week"] == 3
    # current -> next week is allowed
    ok2 = cr.plan_changes(PLAN, [wo(3, 3, "Saturday")], [move(3, 4, "Monday")], TODAY)
    assert ok2.moves[0]["to_week"] == 4


def test_same_week_move_in_a_far_week_is_not_windowed():
    changes = cr.plan_changes(PLAN, [wo(1, 9, "Tuesday")], [move(1, 9, "Thursday")], TODAY)
    assert changes.moves[0]["to_week"] == 9


def test_g5_out_of_plan():
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, [wo(1, 12, "Tuesday")], [move(1, 13, "Monday")], TODAY)
    assert e.value.code == "G5_out_of_plan"


def test_g7_no_start_date_refuses_moves_but_allows_same_week_swaps():
    plan = {"id": 1, "start_date": None, "total_weeks": 12}
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(plan, [wo(1, 3, "Thursday")], [move(1, 3, "Friday")], TODAY)
    assert e.value.code == "G7_no_dates"
    swap = {"op": "swap_days", "week": 3, "day_1": "Thursday", "day_2": "Friday"}
    changes = cr.plan_changes(plan, [wo(1, 3, "Thursday")], [swap], TODAY)
    assert changes.moves[0]["to_day"] == "Friday"


# --- swap_days -----------------------------------------------------------------


def test_swap_days_moves_every_row_including_double_days():
    rows = [wo(1, 3, "Thursday"), wo(2, 3, "Thursday", session_slot="morning"), wo(3, 3, "Friday")]
    swap = {"op": "swap_days", "week": 3, "day_1": "Thursday", "day_2": "Friday"}
    changes = cr.plan_changes(PLAN, rows, [swap], TODAY)
    placed = {m["workout_id"]: m["to_day"] for m in changes.moves}
    assert placed == {1: "Friday", 2: "Friday", 3: "Thursday"}


def test_swap_that_pushes_future_workouts_into_the_past_is_refused():
    rows = [wo(1, 3, "Monday", is_missed=1), wo(2, 3, "Friday")]
    swap = {"op": "swap_days", "week": 3, "day_1": "Monday", "day_2": "Friday"}
    with pytest.raises(GuardViolation) as e:
        cr.plan_changes(PLAN, rows, [swap], TODAY)
    assert e.value.code == "G3_past_target"


# --- stacking + batches --------------------------------------------------------


def test_move_onto_an_occupied_day_stacks():
    rows = [wo(1, 3, "Thursday"), wo(2, 3, "Saturday")]
    changes = cr.plan_changes(PLAN, rows, [move(1, 3, "Saturday")], TODAY)
    assert [m["workout_id"] for m in changes.moves] == [1]


def test_warnings_use_final_state_only():
    rows = [
        wo(1, 3, "Thursday", type="Interval", zone="Zone 4"),
        wo(2, 3, "Friday", type="Tempo", zone="Zone 3"),
    ]
    # op1 stacks two hard sessions on Friday (intermediate), op2 moves one away again
    changes = cr.plan_changes(PLAN, rows, [move(1, 3, "Friday"), move(2, 3, "Sunday")], TODAY)
    assert "W1_hard_stacking" not in codes(changes)


# --- warnings ------------------------------------------------------------------


def test_w1_two_hard_sessions_same_day():
    rows = [wo(1, 3, "Thursday", type="Interval", zone="Zone 4"), wo(2, 3, "Friday", type="Tempo", zone="Z3")]
    changes = cr.plan_changes(PLAN, rows, [move(1, 3, "Friday")], TODAY)
    w = [x for x in changes.warnings if x["code"] == "W1_hard_stacking"]
    assert w and w[0]["params"]["kind"] == "same_day" and w[0]["params"]["day"] == "Friday"


def test_w1_hard_session_before_long_run():
    rows = [wo(1, 3, "Thursday", type="Interval", zone="Zone 4"), wo(2, 3, "Saturday", type="Long Run")]
    changes = cr.plan_changes(PLAN, rows, [move(1, 3, "Friday")], TODAY)
    kinds = [x["params"]["kind"] for x in changes.warnings if x["code"] == "W1_hard_stacking"]
    assert "before_long_run" in kinds


def test_w2_volume_shift_over_20_percent():
    rows = [wo(1, 3, "Friday", minutes=60), wo(2, 3, "Saturday", minutes=60), wo(3, 4, "Monday", minutes=60)]
    changes = cr.plan_changes(PLAN, rows, [move(1, 4, "Tuesday")], TODAY)
    shifted = {x["params"]["week"] for x in changes.warnings if x["code"] == "W2_volume_shift"}
    assert shifted == {3, 4}


def test_w3_pending_coach_draft():
    rows = [wo(1, 3, "Thursday", approved_at=None)]
    changes = cr.plan_changes(PLAN, rows, [move(1, 3, "Friday")], TODAY)
    assert "W3_pending_draft" in codes(changes)
