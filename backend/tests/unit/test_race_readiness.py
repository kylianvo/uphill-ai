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


# --- flat-equivalent km (owner decision 2026-10-20) ---------------------------------------------------


def run_week(n, minutes, km, extra=()):
    base = [
        {
            "week_number": n,
            "day_of_week": "Tuesday",
            "type": "Easy",
            "duration_minutes": minutes,
            "distance_km": km,
            "phase": "Base",
        }
    ]
    return base + [dict(x, week_number=n) for x in extra]


def test_flat_equivalent_km_counts_run_minutes_over_the_flat_pace_and_skips_strength_and_rest():
    ws = run_week(
        1,
        300,
        30,
        extra=[
            {"type": "Muscular Endurance", "duration_minutes": 60, "distance_km": 0},
            {"type": "Strength", "duration_minutes": 45, "distance_km": 0},
            {"type": "Rest", "duration_minutes": 0, "distance_km": 0},
        ],
    )
    assert weekly_km(ws) == 30  # without a pace: the plan's own distance
    assert abs(weekly_km(ws, 5.0) - 60.0) < 1e-9  # 300 run min / 5 min per km; ME and strength excluded


def test_a_slow_mountain_pace_no_longer_makes_a_hard_plan_read_as_light():
    # prod 100K plan: ~445 min/week but only ~47 km at trail pace. Against the 100K benchmark (120-130 km):
    hist = [w for n, km in enumerate([43.3, 46.3, 48.8, 47.1, 44.6, 47.4], start=1) for w in run_week(n, 440, km)]
    as_is = assess_week(hist, 7, total_weeks=13, distance_km=104.2, max_prog=0.10)
    flat = assess_week(hist, 7, total_weeks=13, distance_km=104.2, max_prog=0.10, flat_pace_min_km=5.45)
    assert as_is.status == "at_risk" and as_is.reachable_km < 75  # reads as hopeless on plan km
    assert flat.base_km > 75  # 440 min / 5.45 = ~81 km flat-equivalent
    # the honest verdict: right at the benchmark line (~118 of 120 km), not 50 km short of it
    assert flat.reachable_km > 110 and flat.reachable_km - as_is.reachable_km > 40


def test_flat_zone2_pace_reads_the_athletes_stored_zone_and_never_raises():
    from services.plan_generator import PlanGenerator

    user = {
        "zone2_pace_min": "5:40",
        "zone2_pace_max": "5:13",
        "max_hr": 197,
        "resting_hr": 50,
        "aet_hr": 159,
        "ant_hr": 174,
    }
    pace = PlanGenerator.flat_zone2_pace(user, "time", "sub_elite")
    assert 5.2 < pace < 5.7
    PlanGenerator.flat_zone2_pace({"zone2_pace_min": "garbage"}, "time", "sub_elite")  # must not raise
    assert (
        PlanGenerator.flat_zone2_pace({}, "time", None) is None or PlanGenerator.flat_zone2_pace({}, "time", None) > 0
    )
