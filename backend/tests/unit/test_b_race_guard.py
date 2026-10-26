import copy
from datetime import date

from services import b_race

MON = date(2026, 9, 28)
DAYS = b_race.DAYS


def w(week, day, type_="Easy", minutes=50, phase="Build", **kw):
    return {"week_number": week, "day_of_week": day, "type": type_, "duration_minutes": minutes, "phase": phase,
            "title": kw.pop("title", type_), "description": "", "target_zone": "Zone 2", **kw}  # fmt: skip


def week(n, phase="Build"):
    return [
        w(n, "Monday", "Rest", 0, phase),
        w(n, "Tuesday", "Interval", 60, phase, target_zone="Zone 4"),
        w(n, "Wednesday", "Easy", 50, phase),
        w(n, "Thursday", "Strength", 45, phase),
        w(n, "Friday", "Easy", 50, phase),
        w(n, "Saturday", "Easy", 40, phase),
        w(n, "Sunday", "Long Run", 180, phase),
    ]


RACE = {"id": 9, "race_name": "Ta Xua 25K", "race_date": "2026-11-01", "distance_km": 25, "elevation_gain_m": 1000,
        "effort": "race", "kept_against": None, "predicted": {"low_sec": 11100, "high_sec": 12300}}  # fmt: skip


def day(ws, wk, d):
    return [x for x in ws if x["week_number"] == wk and x["day_of_week"] == d]


def test_race_row_replaces_long_run_on_race_day():
    ws = b_race.enforce(week(5) + week(6), [RACE], MON)
    sunday = day(ws, 5, "Sunday")
    assert [x["type"] for x in sunday] == ["Race"] and sunday[0]["plan_race_id"] == 9
    assert sunday[0]["duration_minutes"] == 195 and sunday[0]["is_priority"] is True
    assert not [x for x in ws if x["week_number"] == 5 and x["type"] == "Long Run"]


def test_taper_days_capped_and_hard_session_dropped():
    ws = b_race.enforce(week(5) + week(6), [RACE], MON)  # 25K / 1000 m → 3 taper days: Thu, Fri, Sat
    for d in ("Thursday", "Friday", "Saturday"):
        x = day(ws, 5, d)[0]
        assert x["type"] in ("Easy", "Rest") and x["duration_minutes"] <= 25
    assert "strides" in day(ws, 5, "Saturday")[0]["description"]
    assert day(ws, 5, "Tuesday")[0]["type"] == "Interval"  # before the taper: untouched


def test_recovery_window_is_zone1_and_capped_across_week_boundary():
    ws = b_race.enforce(week(5) + week(6), [RACE], MON)  # recovery 5 days: Mon–Fri of week 6
    for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
        x = day(ws, 6, d)[0]
        assert x["type"] in ("Easy", "Rest") and x["duration_minutes"] <= 60
        assert x["type"] == "Rest" or x["target_zone"] == "Zone 1"
    assert day(ws, 6, "Sunday")[0]["type"] == "Long Run"  # after the window: untouched


def test_a_race_taper_untouched():
    late = {**RACE, "race_date": "2026-11-29"}  # Sunday of week 9, the A-race taper follows
    ws = week(9, "Peak") + week(10, "Taper")
    out = b_race.enforce(copy.deepcopy(ws), [late], MON)
    assert [x for x in out if x["week_number"] == 10] == [x for x in ws if x["week_number"] == 10]


def test_back_to_back_races_recovery_wins():
    second = {**RACE, "id": 10, "race_date": "2026-11-08"}  # its taper (Thu–Sat wk 6) overlaps the first recovery
    ws = b_race.enforce(week(5) + week(6) + week(7), [RACE, second], MON)
    thursday = day(ws, 6, "Thursday")[0]
    assert thursday["type"] in ("Easy", "Rest") and (thursday["type"] == "Rest" or thursday["target_zone"] == "Zone 1")
    assert [x["type"] for x in day(ws, 6, "Sunday")] == ["Race"]


def test_not_recommended_race_has_no_taper_of_its_own():
    late = {**RACE, "effort": "training", "kept_against": "not_recommended"}
    ws = b_race.enforce(week(5) + week(6), [late], MON)
    assert day(ws, 5, "Friday")[0]["duration_minutes"] == 50


def test_guard_is_idempotent():
    once = b_race.enforce(week(5) + week(6), [RACE], MON)
    assert b_race.enforce(copy.deepcopy(once), [RACE], MON) == once


def test_cost_lists_long_run_lost_and_peak_minutes():
    ws = week(5) + week(6) + week(8, "Peak")
    cost = b_race.cost(RACE, ws, MON)
    lost = [c for c in cost["changed"] if c["week"] == 5 and c["day"] == "Sunday"]
    assert lost and lost[0]["title_before"] == "Long Run" and lost[0]["title_after"] == "Ta Xua 25K"
    assert cost["peak_week_minutes"] == {"before": 425, "after": 425}


def test_prompt_block_names_fixed_days():
    text = b_race.prompt_block([RACE], MON)
    assert "Week 5 Sunday: Ta Xua 25K" in text and "Thu" in text


def test_race_inside_the_a_taper_takes_only_its_own_day():
    late = {**RACE, "race_date": "2026-12-02", "effort": "training", "kept_against": "not_recommended"}
    ws = week(10, "Taper")  # Wednesday of week 10
    out = b_race.enforce(copy.deepcopy(ws), [late], MON)
    assert [x["type"] for x in day(out, 10, "Wednesday")] == ["Race"]
    assert [x for x in out if x["day_of_week"] != "Wednesday"] == [x for x in ws if x["day_of_week"] != "Wednesday"]
