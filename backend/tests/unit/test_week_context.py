from services.week_context import week_context


def _w(id_, day, minutes, type_="Easy", **kw):
    return {"id": id_, "day_of_week": day, "duration_minutes": minutes, "type": type_, "title": f"{type_} {id_}", **kw}


WEEK = [
    _w(1, "Tuesday", 50, is_completed=1),
    _w(2, "Wednesday", 60, "Easy", is_missed=1),
    _w(3, "Thursday", 45, "Muscular Endurance"),
    _w(4, "Friday", 45, "Rest"),
    _w(5, "Saturday", 60),
    _w(6, "Sunday", 115, "Long Run"),
]


def test_totals_count_completed_planned_time_and_ignore_rest():
    ctx = week_context(WEEK, WEEK[0])
    assert ctx["done_min"] == 50
    assert ctx["planned_min"] == 50 + 60 + 45 + 60 + 115 + 0


def test_next_key_session_is_the_next_unfinished_ME_or_long_run():
    assert week_context(WEEK, WEEK[0])["next_key"] == {
        "day_of_week": "Thursday",
        "title": "Muscular Endurance 3",
        "type": "Muscular Endurance",
    }


def test_missed_and_completed_sessions_are_skipped_and_none_when_nothing_is_left():
    after_me = [dict(w, is_completed=1) if w["id"] in (3, 6) else w for w in WEEK]
    assert week_context(after_me, WEEK[0])["next_key"] is None


def test_the_session_itself_is_never_its_own_next_key():
    assert week_context(WEEK, WEEK[5])["next_key"] is None
