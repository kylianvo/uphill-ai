"""Phase 1b pure logic: race-day anchor, plan geometry, send/clear dates, standalone window."""

import datetime as dt

import pytest

from services.coros_plan_window import (
    GeometryRefusal,
    build_window,
    clear_dates,
    day_hashes_for,
    is_race_goal,
    last_generated_date,
    last_run_date,
    plan_geometry,
    rows_by_date,
    send_dates,
    standalone_window,
    with_race_day,
)
from services.coros_workouts import SPORT_REST, SPORT_RUNNING, TARGET_FREE, race_day_course, validate_course

APPROVED = dt.datetime(2026, 9, 1, tzinfo=dt.UTC)
TODAY = dt.date(2026, 9, 25)  # Friday
RACE = {
    "id": 1,
    "start_date": "2026-08-31",
    "goal_type": "finish",
    "race_name": "Bondi to Manly Ultra",
    "race_date": "2026-10-24",
    "course_distance_km": 80,
}


def row(i, week, day, **kw):
    base = {
        "id": i,
        "week_number": week,
        "day_of_week": day,
        "phase": "Build",
        "title": f"Run {i}",
        "type": "Easy",
        "duration_minutes": 40,
        "target_hr_range": "120-135",
        "approved_at": APPROVED,
        "is_completed": 0,
        "matched_activity_id": None,
        "session_slot": "main",
    }
    base.update(kw)
    return base


# --- race-day course -------------------------------------------------------------------------


def test_race_day_course_uses_distance_and_no_hr_target():
    c = race_day_course("Bondi to Manly Ultra", 80, "en")
    assert c["sportType"] == SPORT_RUNNING and c["courseName"] == "Race day: Bondi to Manly Ultra"
    (s,) = c["sections"]
    assert (s["targetType"], s["targetValue"]) == (1, 80000)
    assert not {"intensityType", "sectionIntensity", "intensityValueStart"} & set(s)
    assert validate_course(c) == []


def test_race_day_course_without_distance_is_free_mode_and_translated():
    c = race_day_course("UTMB", None, "vi")
    (s,) = c["sections"]
    assert s["targetType"] == TARGET_FREE and "targetValue" not in s
    assert c["courseName"] == "Ngày đua: UTMB"
    assert validate_course(c) == []


def test_validate_free_target_must_not_carry_a_value():
    bad = {
        "sportType": SPORT_RUNNING,
        "courseName": "x",
        "courseDescription": "x",
        "sections": [{"sectionType": 2, "targetType": TARGET_FREE, "targetValue": 5}],
    }
    assert "target_value" in validate_course(bad)


# --- race anchor -----------------------------------------------------------------------------


def test_is_race_goal():
    assert is_race_goal(RACE)
    assert not is_race_goal({**RACE, "goal_type": "base"})
    assert not is_race_goal({**RACE, "race_date": None})


def test_with_race_day_adds_placeholder_only_when_no_run_that_day():
    by = rows_by_date(RACE, [row(1, 4, "Saturday")])
    out = with_race_day(RACE, by)
    (ph,) = out[dt.date(2026, 10, 24)]
    assert ph["race_placeholder"] and ph["race_name"] == "Bondi to Manly Ultra"
    assert by.get(dt.date(2026, 10, 24)) is None  # input untouched

    generated = rows_by_date(RACE, [row(9, 8, "Saturday", type="Race", title="Race")])
    assert with_race_day(RACE, generated)[dt.date(2026, 10, 24)][0]["id"] == 9
    assert with_race_day({**RACE, "goal_type": "base"}, by) == by


def test_race_day_hash_follows_race_name_and_distance():
    d = dt.date(2026, 10, 24)
    h1 = day_hashes_for(with_race_day(RACE, {}), [d])
    h2 = day_hashes_for(with_race_day({**RACE, "race_name": "Other"}, {}), [d])
    h3 = day_hashes_for(with_race_day({**RACE, "course_distance_km": 50}, {}), [d])
    assert len({h1[d.isoformat()], h2[d.isoformat()], h3[d.isoformat()]}) == 3


def test_last_generated_and_last_run_dates():
    by = rows_by_date(RACE, [row(1, 4, "Friday"), row(2, 4, "Sunday", type="Strength")])
    assert last_generated_date(by) == dt.date(2026, 9, 27)
    assert last_run_date(by) == dt.date(2026, 9, 25)
    assert last_generated_date({}) is None and last_run_date({}) is None


# --- plan geometry ---------------------------------------------------------------------------


def test_geometry_starts_today_and_ends_race_week():
    g = plan_geometry(dt.date(2026, 10, 24), None, TODAY)
    assert (g.start, g.end, g.weeks) == (TODAY, dt.date(2026, 10, 25), 5)


def test_geometry_race_too_close_refuses_with_weeks():
    with pytest.raises(GeometryRefusal) as info:
        plan_geometry(dt.date(2026, 10, 10), None, TODAY)  # race in natural week 3
    assert (info.value.code, info.value.params) == ("RACE_too_close", {"weeks": 3})


def test_geometry_race_close_but_recovery_week_run_makes_four_weeks():
    g = plan_geometry(dt.date(2026, 10, 10), dt.date(2026, 10, 13), TODAY)
    assert (g.end, g.weeks) == (dt.date(2026, 10, 18), 4)


def test_geometry_far_race_starts_in_the_future_within_fourteen_days():
    race = dt.date(2027, 1, 16)  # Saturday; race week Monday 2027-01-11, 17 natural weeks from today
    g = plan_geometry(race, None, TODAY)
    assert g.start == dt.date(2026, 9, 28)  # race Monday minus 15 weeks: a 16-week plan ending race week
    assert (g.weeks, g.end) == (16, dt.date(2027, 1, 17))
    assert g.start <= TODAY + dt.timedelta(days=14)


def test_geometry_race_too_far_gives_opening_date():
    race = dt.date(2027, 3, 6)  # race week Monday 2027-03-01
    with pytest.raises(GeometryRefusal) as info:
        plan_geometry(race, None, TODAY)
    assert info.value.code == "RACE_too_far"
    opens = dt.date.fromisoformat(info.value.params["opens_on"])
    assert opens == dt.date(2027, 3, 1) - dt.timedelta(weeks=15, days=14)
    assert plan_geometry(race, None, opens).start == opens + dt.timedelta(days=14)


def test_geometry_generated_runs_past_race_are_capped_at_sixteen_weeks():
    g = plan_geometry(dt.date(2026, 10, 24), dt.date(2027, 3, 1), TODAY)
    assert g.weeks == 16 and g.end == dt.date(2027, 1, 10)


# --- send / clear dates ----------------------------------------------------------------------


def test_send_dates_are_generated_span_plus_race_day():
    dates = send_dates(TODAY, dt.date(2026, 9, 27), dt.date(2026, 10, 24))
    assert dates == [dt.date(2026, 9, 25), dt.date(2026, 9, 26), dt.date(2026, 9, 27), dt.date(2026, 10, 24)]
    assert send_dates(TODAY, None, None) == []
    assert send_dates(TODAY, dt.date(2026, 9, 20), None) == []  # nothing generated from today on


def test_clear_dates_only_previously_sent_in_range_and_not_resent():
    stored = {"2026-09-20": "a", "2026-09-26": "b", "2026-10-03": "c", "2026-10-31": "d"}
    sent = [dt.date(2026, 9, 26)]
    assert clear_dates(stored, sent, TODAY, dt.date(2026, 10, 25)) == [dt.date(2026, 10, 3)]


def test_build_window_over_explicit_dates_and_rest_for_cleared():
    by = with_race_day(RACE, rows_by_date(RACE, [row(1, 4, "Friday")]))
    dates = [dt.date(2026, 9, 25), dt.date(2026, 10, 24)]
    w = build_window(by, TODAY, dt.date(2026, 10, 25), "en", dates=dates, clear=[dt.date(2026, 10, 3)])
    assert [d.date for d in w.days] == [dt.date(2026, 9, 25), dt.date(2026, 10, 3), dt.date(2026, 10, 24)]
    by_date = {d.date: d.courses for d in w.days}
    assert by_date[dt.date(2026, 10, 3)][0]["sportType"] == SPORT_REST
    assert by_date[dt.date(2026, 10, 24)][0]["courseName"] == "Race day: Bondi to Manly Ultra"


# --- standalone window -----------------------------------------------------------------------


def test_standalone_window_sends_runs_only():
    rows = [
        row(1, 4, "Friday"),
        row(2, 4, "Saturday", type="Strength", title="Gym"),
        row(3, 4, "Sunday", type="Rest"),
        row(4, 5, "Monday", is_completed=1),
        row(5, 5, "Tuesday"),
        row(6, 5, "Tuesday", type="Strength", session_slot="second"),
    ]
    w = standalone_window(rows_by_date(RACE, rows), TODAY, dt.date(2026, 10, 18), "en")
    assert [d.date for d in w.days] == [dt.date(2026, 9, 25), dt.date(2026, 9, 29)]
    assert all(c["sportType"] == SPORT_RUNNING for d in w.days for c in d.courses)
    assert w.locked_dates == [dt.date(2026, 9, 28)]
    assert w.left_in_uphill == 2  # Saturday gym + Tuesday second-slot strength
