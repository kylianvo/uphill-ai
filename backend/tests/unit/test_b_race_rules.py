from datetime import date

from services.b_race import BRace, PlanFacts, assess, recovery_days, suggest, taper_days, week_and_day

A = date(2026, 12, 13)
MON = date(2026, 9, 28)  # 12-week plan, A-race on Sunday of week 11


def facts(**kw):
    return PlanFacts(
        a_date=A,
        a_distance_km=70,
        a_gain_m=4000,
        plan_monday=MON,
        total_weeks=12,
        longest_recent_km=kw.pop("longest_recent_km", 34),
        longest_recent_min=190,
        **kw,
    )


def race(d, km, gain=1200, effort="race", options=()):
    return BRace(d, km, gain, effort, options)


def test_25k_six_weeks_out_is_good():
    v = assess(race(date(2026, 11, 1), 25, 1000), facts())
    assert v.level == "good" and v.taper_days == 3 and v.recovery_days == 5  # effort-km 35


def test_inside_14_days_is_not_recommended():
    v = assess(race(date(2026, 12, 3), 15, 500), facts())
    assert v.level == "not_recommended" and "too_close" in v.reasons


def test_recovery_overlapping_taper_is_risky():
    v = assess(race(date(2026, 11, 22), 50, 2500), facts())
    assert v.level == "risky" and ("overlaps_taper" in v.reasons or "overlaps_peak" in v.reasons)


def test_much_longer_than_trained_is_risky_and_moderately_longer_has_conditions():
    assert assess(race(date(2026, 11, 1), 42, 2400), facts()).level == "risky"  # 66 ekm vs 34 km
    assert assess(race(date(2026, 11, 1), 30, 0), facts(longest_recent_km=24)).level == "conditions"  # 1.25


def test_training_effort_lowers_cost():
    hard = assess(race(date(2026, 11, 1), 30, 0), facts(longest_recent_km=24))
    easy = assess(race(date(2026, 11, 1), 30, 0, effort="training"), facts(longest_recent_km=24))
    assert easy.level == "good" and easy.recovery_days < hard.recovery_days


def test_stacked_races_are_risky():
    other = race(date(2026, 10, 25), 25, 1000)
    v = assess(race(date(2026, 11, 8), 25, 1000), facts(other_races=(other,)))
    assert v.level == "risky" and "stacked" in v.reasons


def test_suggestion_prefers_shorter_option_then_training_effort():
    r = race(date(2026, 11, 1), 42, 2400, options=(15, 25, 42, 70))
    assert suggest(r, facts()) == {"distance_km": 25, "effort": "race"}
    assert suggest(race(date(2026, 11, 1), 42, 2400), facts())["effort"] == "training"


def test_good_race_has_no_suggestion():
    assert assess(race(date(2026, 11, 1), 25, 1000), facts()).suggestion is None


def test_taper_and_recovery_table():
    assert [taper_days(k, "race") for k in (21, 42, 70, 71)] == [2, 3, 3, 4]
    assert [recovery_days(k, "race") for k in (21, 42, 70, 71)] == [3, 5, 7, 10]
    assert recovery_days(42, "race", kept_risky=True) == 7 and recovery_days(42, "training") == 3


def test_week_and_day():
    assert week_and_day(MON, date(2026, 11, 1)) == (5, "Sunday")
