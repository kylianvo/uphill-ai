import datetime as dt

import pytest

from services.calendar_rules import GuardViolation
from services.week_rebuild import (
    build_diff,
    filter_draft,
    rebuild_range,
    rebuild_warnings,
    week_fingerprints,
)

PLAN = {"id": 1, "start_date": "2026-09-07", "total_weeks": 8}  # Monday; week 3 = Sep 21-27
THU_W3 = dt.date(2026, 9, 24)


def w(id_, week, day, *, title="Easy", type_="Easy", zone="Zone 2", mins=40, done=0, matched=None, slot="main"):
    return {
        "id": id_,
        "week_number": week,
        "day_of_week": day,
        "title": title,
        "type": type_,
        "target_zone": zone,
        "duration_minutes": mins,
        "distance_km": mins / 6,
        "elevation_gain_m": 0,
        "is_completed": done,
        "is_missed": 0,
        "matched_activity_id": matched,
        "approved_at": "2026-09-01T00:00:00",
        "session_slot": slot,
    }


def gen(day, week=3, *, title="New", type_="Easy", zone="Zone 2", mins=30, slot="main"):
    return {
        "week_number": week,
        "day_of_week": day,
        "title": title,
        "type": type_,
        "target_zone": zone,
        "duration_minutes": mins,
        "distance_km": mins / 6,
        "session_slot": slot,
        "phase": "Base",
    }


ROWS = [
    w(1, 3, "Monday", done=1),  # past + completed
    w(2, 3, "Tuesday"),  # past, missed -> kept
    w(3, 3, "Thursday"),  # today -> replaceable
    w(4, 3, "Saturday", matched=99),  # future but GPS-matched -> kept
    w(5, 3, "Sunday", type_="Long Run", mins=120),
    w(6, 4, "Monday"),
    w(7, 5, "Monday"),
]


def test_current_week_starts_today_and_keeps_past_and_history():
    rng = rebuild_range(PLAN, ROWS, 3, THU_W3)
    assert rng.from_day == "Thursday"
    assert set(rng.kept_ids) == {1, 2, 4}
    assert set(rng.replaceable_ids) == {3, 5}
    assert ("Saturday", "main") in rng.kept_slots


def test_next_week_starts_monday():
    rng = rebuild_range(PLAN, ROWS, 4, THU_W3)
    assert rng.from_day == "Monday" and rng.replaceable_ids == (6,)


def test_past_week_is_refused():
    with pytest.raises(GuardViolation) as e:
        rebuild_range(PLAN, ROWS, 2, THU_W3)
    assert e.value.code == "G3_past_target"


@pytest.mark.parametrize("week", [0, 9, 6])  # outside plan, beyond total, not generated (max is 5)
def test_out_of_plan_or_ungenerated_week_is_refused(week):
    with pytest.raises(GuardViolation) as e:
        rebuild_range(PLAN, ROWS, week, THU_W3)
    assert e.value.code == "G5_out_of_plan"


def test_plan_not_started_rebuilds_from_monday():
    rng = rebuild_range(PLAN, ROWS, 3, dt.date(2026, 9, 1))
    assert rng.from_day == "Monday" and set(rng.kept_ids) == {1, 4}


def test_no_start_date_rebuilds_from_monday_keeping_only_history():
    rng = rebuild_range({**PLAN, "start_date": None}, ROWS, 3, THU_W3)
    assert rng.from_day == "Monday" and set(rng.kept_ids) == {1, 4}


def test_nothing_to_rebuild_when_every_remaining_day_is_kept():
    rows = [w(i + 10, 3, d, done=1) for i, d in enumerate(["Saturday", "Sunday"])]
    rows.append(w(20, 4, "Monday"))
    with pytest.raises(GuardViolation) as e:
        rebuild_range(PLAN, rows, 3, dt.date(2026, 9, 26))  # Saturday
    assert e.value.code == "NOTHING_to_rebuild"


def test_empty_free_day_left_still_allows_a_rebuild():
    rows = [w(10, 3, "Saturday", done=1), w(20, 4, "Monday")]
    rng = rebuild_range(PLAN, rows, 3, dt.date(2026, 9, 26))
    assert rng.replaceable_ids == () and rng.from_day == "Saturday"


def test_fingerprints_cover_every_workout_in_the_week_and_detect_edits():
    fps = week_fingerprints(ROWS, 3)
    assert set(fps) == {"1", "2", "3", "4", "5"}
    edited = [dict(r, title="Changed") if r["id"] == 3 else r for r in ROWS]
    assert week_fingerprints(edited, 3) != fps


def test_filter_draft_drops_days_before_from_day_and_kept_slots():
    rng = rebuild_range(PLAN, ROWS, 3, THU_W3)
    draft = [
        gen("Monday"),
        gen("Thursday"),
        gen("Saturday"),
        gen("Saturday", slot="pm"),
        gen("Sunday"),
        gen("Sunday", week=9),
    ]
    kept = filter_draft(draft, rng)
    assert [(d["day_of_week"], d["session_slot"], d["week_number"]) for d in kept] == [
        ("Thursday", "main", 3),
        ("Saturday", "pm", 3),
        ("Sunday", "main", 3),
    ]


def test_build_diff_rows_and_totals():
    rng = rebuild_range(PLAN, ROWS, 3, THU_W3)
    draft = filter_draft([gen("Thursday", mins=30), gen("Sunday", type_="Long Run", mins=90)], rng)
    diff = build_diff(ROWS, rng, draft)
    assert diff["week"] == 3 and diff["from_day"] == "Thursday"
    by_day = {d["day"]: d for d in diff["days"]}
    assert [k["id"] for k in by_day["Monday"]["kept"]] == [1]
    assert [b["id"] for b in by_day["Thursday"]["before"]] == [3]
    assert by_day["Thursday"]["after"][0]["title"] == "New"
    assert diff["totals"]["before"]["min"] == 40 * 4 + 120
    assert diff["totals"]["after"]["min"] == 40 * 3 + 30 + 90


def test_warnings_flag_volume_shift_and_hard_before_long_run():
    rng = rebuild_range(PLAN, ROWS, 3, THU_W3)
    draft = filter_draft(
        [gen("Friday", type_="Tempo", zone="Zone 3", mins=40), gen("Sunday", type_="Long Run", mins=30)], rng
    )
    # Saturday is kept (matched), so Friday tempo is not the day before the Sunday long run.
    codes = [x["code"] for x in rebuild_warnings(ROWS, rng, draft)]
    assert "W2_volume_shift" in codes  # 280 -> 190 min
    draft2 = filter_draft([gen("Thursday", type_="Tempo", zone="Zone 3"), gen("Friday", type_="Long Run")], rng)
    w1 = [x for x in rebuild_warnings(ROWS, rng, draft2) if x["code"] == "W1_hard_stacking"]
    assert w1 == [{"code": "W1_hard_stacking", "params": {"kind": "before_long_run", "week": 3, "day": "Thursday"}}]
