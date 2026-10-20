from datetime import date

from services import plan_journey
from services.athlete_tier import TIER_PROFILES

REC = TIER_PROFILES["recreational"]


def w(week, day, type_, minutes, phase, **kw):
    return {"week_number": week, "day_of_week": day, "type": type_, "duration_minutes": minutes,
            "phase": phase, "target_zone": "Zone 2", **kw}  # fmt: skip


def plan():
    out = []
    for wk in range(1, 11):
        phase = (
            "Base" if wk <= 4 else "Build" if wk <= 7 else "Peak" if wk == 8 else "Taper" if wk == 9 else "Race Week"
        )
        long_min = {1: 90, 2: 100, 3: 120, 4: 90, 5: 150, 6: 185, 7: 195, 8: 200, 9: 90}.get(wk, 0)
        if wk == 10:
            out += [w(wk, "Saturday", "Race", 600, phase)]
            continue
        out += [w(wk, "Saturday", "Long Run", long_min, phase), w(wk, "Tuesday", "Easy", 60 if wk != 4 else 40, phase)]
    return out


def test_phases_are_contiguous_week_ranges():
    got = [(p.name, p.start_week, p.end_week) for p in plan_journey.phases(plan())]
    assert got == [("Base", 1, 4), ("Build", 5, 7), ("Peak", 8, 8), ("Taper", 9, 9), ("Race Week", 10, 10)]


def test_milestones_in_week_order_with_done_flags():
    ms = plan_journey.milestones(plan(), current_week=6)
    assert [(m.key, m.week, m.done) for m in ms] == [
        ("first_recovery_week", 4, True),
        ("long_run_3h", 6, False),
        ("peak_week", 8, False),
        ("taper_start", 9, False),
        ("race_week", 10, False),
    ]


def test_a_plan_without_a_three_hour_long_run_has_no_such_milestone():
    short = [x for x in plan() if not (x["type"] == "Long Run" and x["duration_minutes"] >= 180)]
    assert "long_run_3h" not in [m.key for m in plan_journey.milestones(short, current_week=1)]


def test_days_to_race():
    assert plan_journey.days_to_race("2026-11-01", date(2026, 10, 21)) == 11
    assert plan_journey.days_to_race("2026-10-01", date(2026, 10, 21)) == 0
    assert plan_journey.days_to_race(None, date(2026, 10, 21)) is None


def test_preference_deviations_name_only_future_weeks_that_break_a_preference():
    ws = plan()
    for x in ws:
        if x["week_number"] in (1, 7) and x["type"] == "Long Run":
            x["day_of_week"] = "Friday"  # off the athlete's Saturday; week 1 is past and must be ignored
    prefs = plan_journey.Preferences(long_run_day="Saturday", days_per_week=2)
    got = plan_journey.deviations(ws, REC, prefs, current_week=6)
    assert got and all(d["week"] >= 6 for d in got)
    assert {d["code"] for d in got} <= {"LONG_RUN_DAY", "DAYS_SHORT"}


def test_journey_payload_shape():
    p = {"race_date": "2026-11-01", "total_weeks": 10, "start_date": "2026-08-25", "athlete_tier": "recreational",
         "days_per_week": 2, "long_run_day": "Saturday", "training_mountain": "chau_thoi"}  # fmt: skip
    j = plan_journey.journey(p, plan(), today=date(2026, 10, 21))
    assert set(j) == {
        "current_week",
        "total_weeks",
        "days_to_race",
        "phases",
        "milestones",
        "preferences",
        "deviations",
    }
    assert j["days_to_race"] == 11 and j["preferences"]["mountain"] == "chau_thoi"
