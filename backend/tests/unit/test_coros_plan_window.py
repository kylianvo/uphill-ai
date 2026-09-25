import datetime as dt

from services.coros_plan_window import (
    WINDOW_WEEKS,
    build_window,
    course_list,
    day_hashes,
    has_run,
    monday_of,
    natural_weeks,
    periodization,
    rows_by_date,
    window_end,
    ymd,
)

APPROVED = dt.datetime(2027, 4, 1, tzinfo=dt.UTC)
PLAN = {"id": 1, "start_date": "2027-04-07"}  # a Wednesday -> week 1 starts Mon 2027-04-05


def row(i, week, day, **kw):
    base = {
        "id": i,
        "week_number": week,
        "day_of_week": day,
        "phase": "Base",
        "title": f"Run {i}",
        "type": "Easy",
        "duration_minutes": 40,
        "target_zone": "Zone 2",
        "target_hr_range": "120-135",
        "approved_at": APPROVED,
        "is_completed": 0,
        "matched_activity_id": None,
        "session_slot": "main",
    }
    base.update(kw)
    return base


def test_date_helpers():
    wed = dt.date(2027, 4, 7)
    assert monday_of(wed) == dt.date(2027, 4, 5)
    assert window_end(wed) == dt.date(2027, 5, 2)  # Sunday of the 4th week
    assert window_end(dt.date(2027, 4, 11)) == dt.date(2027, 5, 2)  # from a Sunday
    assert natural_weeks(wed, dt.date(2027, 5, 2)) == 4
    assert natural_weeks(dt.date(2027, 4, 11), dt.date(2027, 4, 11)) == 1
    assert ymd(wed) == 20270407
    assert WINDOW_WEEKS == 4


def test_rows_by_date_uses_monday_aligned_weeks():
    by = rows_by_date(PLAN, [row(1, 1, "Monday"), row(2, 2, "Sunday"), row(3, 1, "Funday")])
    assert set(by) == {dt.date(2027, 4, 5), dt.date(2027, 4, 18)}
    assert rows_by_date({"start_date": None}, [row(1, 1, "Monday")]) == {}


def test_build_window_locks_completed_and_matched_days_and_fills_rest():
    rows = [
        row(1, 1, "Wednesday", is_completed=1),
        row(2, 1, "Thursday", matched_activity_id=77),
        row(3, 1, "Friday"),
        row(4, 1, "Friday", type="Strength", title="Gym", session_slot="secondary"),
    ]
    by = rows_by_date(PLAN, rows)
    today = dt.date(2027, 4, 7)
    w = build_window(by, today, window_end(today), "en")
    assert w.locked_dates == [dt.date(2027, 4, 7), dt.date(2027, 4, 8)]
    dates = [d.date for d in w.days]
    assert dates[0] == dt.date(2027, 4, 9) and dates[-1] == dt.date(2027, 5, 2)
    assert len(dates) == 24  # 26 days Wed 04-07 .. Sun 05-02, minus 2 locked
    friday = w.days[0]
    assert [c["courseName"] for c in friday.courses] == ["Run 3"]
    assert w.left_in_uphill == 1
    assert w.days[1].courses[0]["sportType"] == 4  # Saturday: rest
    assert w.invalid == 0


def test_zero_duration_run_becomes_rest():
    by = rows_by_date(PLAN, [row(1, 1, "Friday", duration_minutes=0)])
    w = build_window(by, dt.date(2027, 4, 9), dt.date(2027, 4, 9), "en")
    assert w.days[0].courses[0]["sportType"] == 4 and w.invalid == 0


def test_invalid_course_is_dropped_counted_and_day_falls_back_to_rest(monkeypatch):
    import services.coros_plan_window as cpw

    broken = {"sportType": 1, "courseName": "", "courseDescription": "d", "sections": []}
    monkeypatch.setattr(cpw, "build_day", lambda rows, lang, hr_zones=None: ([broken], 0))
    w = build_window(rows_by_date(PLAN, [row(1, 1, "Friday")]), dt.date(2027, 4, 9), dt.date(2027, 4, 9), "en")
    assert w.invalid == 1
    assert w.days[0].courses[0]["sportType"] == 4


def test_course_list_day_numbers_relative_to_anchor():
    by = rows_by_date(PLAN, [row(1, 1, "Friday"), row(2, 2, "Monday")])
    w = build_window(by, dt.date(2027, 4, 9), dt.date(2027, 4, 12), "en")
    cl = course_list(w, dt.date(2027, 4, 7))
    assert [(c["dayNo"], c["sportType"]) for c in cl] == [(2, 1), (3, 4), (4, 4), (5, 1)]


def test_has_run():
    by = rows_by_date(PLAN, [row(1, 1, "Friday")])
    w = build_window(by, dt.date(2027, 4, 9), dt.date(2027, 4, 18), "en")
    assert has_run(w, dt.date(2027, 4, 5), dt.date(2027, 4, 11)) is True
    assert has_run(w, dt.date(2027, 4, 12), dt.date(2027, 4, 18)) is False


def test_day_hashes_change_only_for_changed_days():
    rows = [row(1, 1, "Friday"), row(2, 1, "Saturday")]
    start, end = dt.date(2027, 4, 9), dt.date(2027, 4, 11)
    before = day_hashes(rows_by_date(PLAN, rows), start, end)
    assert set(before) == {"2027-04-09", "2027-04-10", "2027-04-11"}
    rows[1] = row(2, 1, "Saturday", duration_minutes=60)
    after = day_hashes(rows_by_date(PLAN, rows), start, end)
    assert before["2027-04-09"] == after["2027-04-09"]
    assert before["2027-04-10"] != after["2027-04-10"]
    assert before["2027-04-11"] == after["2027-04-11"]


def test_periodization_merges_weeks_and_anchors_partial_first_week():
    rows = [
        row(1, 1, "Friday", phase="Base"),
        row(2, 2, "Monday", phase="Base"),
        row(3, 3, "Monday", phase="Build"),
        row(4, 5, "Monday", phase="Taper"),
    ]
    phases = periodization(rows_by_date(PLAN, rows), dt.date(2027, 4, 7), 5)
    assert phases == [
        {"phaseType": 2, "startDate": 20270407, "endDate": 20270418, "durationWeeks": 2},
        {"phaseType": 3, "startDate": 20270419, "endDate": 20270502, "durationWeeks": 2},  # week 4 inherits Build
        {"phaseType": 5, "startDate": 20270503, "endDate": 20270509, "durationWeeks": 1},
    ]
    assert sum(p["durationWeeks"] for p in phases) == 5


def test_periodization_unknown_phase_defaults_to_preparation():
    phases = periodization({}, dt.date(2027, 4, 5), 4)
    assert phases == [{"phaseType": 1, "startDate": 20270405, "endDate": 20270502, "durationWeeks": 4}]
