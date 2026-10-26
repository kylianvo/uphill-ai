from datetime import date

from services import b_race, plan_lint
from services.athlete_tier import get_profile

MON = date(2026, 9, 28)
RACE = {"id": 9, "race_name": "Ta Xua 25K", "race_date": "2026-11-01", "distance_km": 25, "elevation_gain_m": 1000,
        "effort": "race", "kept_against": None}  # fmt: skip
VIEW = b_race.lint_view([RACE], MON)
PROFILE = get_profile("intermediate")


def w(week, day, type_="Easy", minutes=50, **kw):
    return {"week_number": week, "day_of_week": day, "type": type_, "duration_minutes": minutes, "phase": "Build",
            "title": type_, "target_zone": kw.pop("target_zone", "Zone 2"), **kw}  # fmt: skip


def codes(ws, races=VIEW):
    return {i.code for i in plan_lint.lint_weeks(ws, {5, 6}, PROFILE, races=races)}


def test_lint_view_lists_race_taper_and_recovery_days():
    assert VIEW == [{"week": 5, "day": "Sunday", "plan_race_id": 9,
                     "taper": [(5, "Thursday"), (5, "Friday"), (5, "Saturday")],
                     "recovery": [(6, d) for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")]}]  # fmt: skip


def test_missing_race_row():
    assert "B_RACE_MISSING" in codes([w(5, "Sunday", "Long Run", 180)])
    assert "B_RACE_MISSING" not in codes([w(5, "Sunday", "Race", 195, plan_race_id=9)])


def test_hard_session_in_taper():
    assert "B_RACE_TAPER_HARD" in codes([w(5, "Friday", "Interval", 60, target_zone="Zone 4")])


def test_hard_session_in_recovery():
    assert "B_RACE_RECOVERY_HARD" in codes([w(6, "Tuesday", "Tempo", 50, target_zone="Zone 3")])
    assert "B_RACE_RECOVERY_HARD" in codes([w(6, "Wednesday", "Long Run", 150)])


def test_no_races_no_issues():
    ws = [w(5, "Sunday", "Long Run", 180), w(5, "Friday", "Interval", 60, target_zone="Zone 4")]
    assert not {c for c in codes(ws, races=None) if c.startswith("B_RACE")}


def test_race_week_is_not_asked_for_a_long_run_or_quality():
    ws = [w(5, d) for d in ("Tuesday", "Wednesday", "Friday")] + [w(5, "Sunday", "Race", 195, plan_race_id=9)]
    assert not codes(ws) & {"LONG_RUN_DAY", "QUALITY_COUNT", "LONG_SHARE", "WEEKDAY_SHORT", "DAYS_SHORT"}


def test_recovery_reaching_the_a_taper_is_not_flagged():
    taper_row = {**w(6, "Tuesday", "Interval", 60, target_zone="Zone 4"), "phase": "Taper"}
    assert "B_RACE_RECOVERY_HARD" not in codes([taper_row])
