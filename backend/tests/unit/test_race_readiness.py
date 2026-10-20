from services.plan_lint import Issue
from services.race_readiness import (
    assess_week,
    max_reachable,
    race_class,
    readiness_issue,
    target_vs_cutoff_issue,
    weekly_km,
)


def week(n, km, phase="Base"):
    return [
        {
            "week_number": n,
            "type": "Easy",
            "distance_km": km,
            "duration_minutes": km * 6,
            "phase": phase,
            "day_of_week": "Tuesday",
        }
    ]


def history(*kms):
    return [w for i, km in enumerate(kms, start=1) for w in week(i, km)]


def test_race_class_follows_the_book_table():
    assert race_class(56.4)[0] == "50K" and race_class(56.4)[2:] == (80.0, 88.0)
    assert race_class(100)[0] == "100K" and race_class(100)[2:] == (120.0, 130.0)
    assert race_class(170)[0] == "100 miles" and race_class(170)[2:] == (145.0, 160.0)


def test_max_reachable_grows_at_the_cap_and_skips_a_week_for_recovery():
    # build week 1 of a run: two more builds, then the 4th week is a recovery week (no growth)
    assert abs(max_reachable(50, 2, 1, 0.10) - 50 * 1.1**2) < 1e-9
    assert abs(max_reachable(50, 3, 1, 0.10) - 50 * 1.1**2) < 1e-9
    assert abs(max_reachable(50, 4, 1, 0.10) - 50 * 1.1**3) < 1e-9
    # three builds already behind us: the next week is recovery, so only one of two steps grows
    assert abs(max_reachable(50, 2, 3, 0.10) - 50 * 1.1) < 1e-9
    assert max_reachable(50, 0, 1, 0.10) == 50


def test_a_strong_athlete_with_time_to_spare_is_on_track_and_gets_no_floor():
    r = assess_week(history(70, 72, 74), 4, total_weeks=12, distance_km=56.4, max_prog=0.10)
    assert r.status == "on_track" and r.floor_km == 0 and r.message == ""
    assert r.race_class == "50K" and r.peak_week == 10


def test_behind_but_reachable_gets_a_floor_between_the_base_and_the_cap():
    # 62 km weeks with one planned down week; week 7 is build week 3 of a run, peak due in week 10
    h = history(62, 62, 62, 52, 62, 62)
    r = assess_week(h, 7, total_weeks=12, distance_km=56.4, max_prog=0.10)
    assert r.status == "behind"
    assert 62 < r.floor_km <= r.cap_km == 62 * 1.1
    assert "at least" in r.message and "80-88 km" in r.message
    assert readiness_issue(r, 7, r.floor_km - 5).code == "READINESS_BEHIND"
    assert readiness_issue(r, 7, r.floor_km) is None


def test_a_due_recovery_week_gets_no_floor_so_it_cannot_fight_the_3_to_1_rule():
    r = assess_week(history(60, 60, 60, 60, 60), 6, total_weeks=12, distance_km=56.4, max_prog=0.10)
    assert r.status == "on_track" and r.floor_km == 0 and r.message == ""


def test_a_timeline_that_cannot_reach_the_benchmark_is_at_risk_and_says_so():
    # a 26 km/week athlete with a planned down week behind them: week 7 is build week 3, three weeks left
    r = assess_week(history(20, 22, 24, 18, 25, 26), 7, total_weeks=12, distance_km=56.4, max_prog=0.10)
    assert r.status == "at_risk" and r.floor_km == r.cap_km
    assert "cannot reach" in r.message and r.reachable_km < 80
    assert readiness_issue(r, 7, 1) is None  # at_risk is reported, not forced past the cap


def test_nothing_to_judge_without_distance_history_or_in_the_taper():
    assert assess_week(history(50), 2, total_weeks=12, distance_km=None, max_prog=0.1) is None
    assert assess_week([], 1, total_weeks=12, distance_km=56.4, max_prog=0.1) is None
    assert assess_week(history(*[60] * 9), 10, total_weeks=12, distance_km=56.4, max_prog=0.1) is None
    assert assess_week(history(50), 2, total_weeks=3, distance_km=56.4, max_prog=0.1) is None


def test_the_base_is_the_last_non_down_week_not_a_recovery_dip():
    wks = history(60, 62, 64) + week(4, 50, phase="Recovery")
    r = assess_week(wks, 5, total_weeks=12, distance_km=56.4, max_prog=0.10)
    assert r.base_km == 64


def test_weekly_km_ignores_rest_and_missing_distance():
    assert weekly_km([{"type": "Rest", "distance_km": 5}, {"type": "Easy", "distance_km": 10}, {"type": "Easy"}]) == 10


def test_target_time_past_the_cutoff_is_flagged_once_both_are_known():
    assert isinstance(target_vs_cutoff_issue(11.0, 10.0, 1), Issue)
    assert target_vs_cutoff_issue(9.5, 10.0, 1) is None
    assert target_vs_cutoff_issue(9.5, None, 1) is None


def test_a_due_recovery_week_does_not_hide_an_unreachable_timeline():
    # prod 100K plan: ~47 km weeks, no recovery in 6 weeks -> week 7 is a recovery week, yet the peak is out of reach
    r = assess_week(history(43, 46, 49, 47, 45, 47), 7, total_weeks=13, distance_km=104.2, max_prog=0.10)
    assert r.race_class == "100K" and r.status == "at_risk"
    assert r.floor_km == 0  # it is a recovery week: no volume floor
    assert "cannot reach" in r.message and r.reachable_km < 120
