import datetime as dt

from services.coach_chat import today_line


def test_today_line_uses_monday_aligned_plan_week():
    # start Wed 2026-09-09 -> week 1 begins Mon 2026-09-07; Thu 2026-09-24 is in week 3
    line = today_line({"start_date": "2026-09-09"}, dt.date(2026, 9, 24))
    assert line == "Today is Thursday 2026-09-24 (plan week 3, days Monday–Sunday)"


def test_today_line_without_start_date_omits_the_week():
    assert today_line({"start_date": None}, dt.date(2026, 9, 24)) == "Today is Thursday 2026-09-24"
