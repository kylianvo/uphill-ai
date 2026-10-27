from services import goal_demands, goal_feasibility
from services.athlete_tier import TIER_PROFILES

REC = TIER_PROFILES["recreational"]
ELITE = TIER_PROFILES["sub_elite"]
FLAT_PACE = 5.45


def _assess(demands, profile=REC, days=6, weeks=26, current=60.0, estimated=False, **kw):
    return goal_feasibility.assess(demands, profile, days, FLAT_PACE, current, weeks, estimated, **kw)


def _100k(target=14.67):
    return goal_demands.compute(104.2, 5533, target, 29)


def test_capacity_matches_tier_caps():
    cap = goal_feasibility.week_capacity_minutes
    assert abs(cap(REC, 3) - 222) < 2
    assert abs(cap(REC, 4) - 224) < 2  # from four days one day is strength, not run time
    assert abs(cap(REC, 6) - 448) < 2


def test_unset_days_assumes_five():
    cap = goal_feasibility.week_capacity_minutes
    assert cap(REC, None) == cap(REC, 5)


def test_three_day_100k_is_unsupported():
    f = _assess(_100k(), days=3)
    assert f.verdict == "unsupported"
    assert "more_days" in f.levers


def test_six_day_elite_100k_finish_is_supported_and_the_time_target_is_a_stretch_with_doubles():
    finish = goal_demands.compute(104.2, 5533, None, 29)
    assert _assess(finish, profile=ELITE, days=6, weeks=26, current=80.0).verdict == "supported"
    f = _assess(_100k(), profile=ELITE, days=6, weeks=26, current=80.0)
    assert f.verdict in {"stretch", "unsupported"} and "double_sessions" in f.levers


def test_finish_goal_needs_less_than_a_time_target():
    finish = goal_demands.compute(104.2, 5533, None, 29)
    assert _assess(finish, profile=ELITE, days=6).verdict == "supported"
    assert _assess(_100k(), days=6).needed_h > _assess(finish, days=6).needed_h


def test_not_enough_weeks_is_unsupported_with_more_weeks_lever():
    f = _assess(_100k(), profile=ELITE, days=6, weeks=4, current=30.0)
    assert f.verdict == "unsupported"
    assert "more_weeks" in f.levers
    assert f.weeks_needed > 4


def test_zero_current_volume_does_not_crash():
    f = _assess(_100k(), profile=ELITE, days=6, weeks=10, current=0.0)
    assert f.verdict == "unsupported"


def test_stretch_when_capacity_binds_slightly():
    d = goal_demands.compute(104.2, 5533, 14.67, 29)
    f = _assess(d, profile=REC, days=6, weeks=40, current=80.0)
    assert f.verdict in {"stretch", "unsupported"}
    f2 = _assess(goal_demands.compute(56.4, 2946, None, 12), profile=REC, days=5, weeks=26, current=50.0)
    assert f2.verdict in {"supported", "stretch"}


def test_none_demands():
    assert _assess(None) is None


def test_estimated_pace_marks_confidence():
    assert _assess(_100k(), estimated=True).confidence == "estimated"
    assert _assess(_100k()).confidence == "measured"


def test_weak_training_mountain_is_a_lever_not_a_failure():
    d = goal_demands.compute(104.2, 5533, None, 29, venue_climb_rate=28.0)  # Châu Thới vs 53 m D+/km
    f = _assess(d, profile=ELITE, days=6, weeks=26, current=80.0)
    assert f.verdict == "stretch"
    assert "steeper_venue" in f.levers


def test_strong_training_mountain_is_fine():
    d = goal_demands.compute(104.2, 5533, None, 29, venue_climb_rate=60.0)  # Núi Dinh
    assert _assess(d, profile=ELITE, days=6, weeks=26, current=80.0).verdict == "supported"


def test_mountain_minimum_must_fit_the_week():
    d = goal_demands.compute(56.4, 2946, None, 12)
    f = _assess(d, profile=REC, days=3, weeks=26, current=40.0, mountain_min_minutes=180)
    assert "fewer_mountain_minimum" in f.levers
    assert f.verdict != "supported"
    ok = _assess(d, profile=ELITE, days=7, weeks=26, current=110.0, mountain_min_minutes=180)
    assert "fewer_mountain_minimum" not in ok.levers


def test_flat_city_athlete_on_steep_course_needs_mountain_access():
    d = goal_demands.compute(104.2, 5533, None, 29)
    f = _assess(d, profile=ELITE, days=6, weeks=26, current=80.0, flat_only=True)
    assert "mountain_access" in f.levers and f.verdict != "supported"
    flat_race = goal_demands.compute(50.0, 100, None, 8)
    assert "mountain_access" not in _assess(flat_race, profile=ELITE, flat_only=True).levers


def test_sub_elite_hundred_milers_get_longer_weekday_runs_and_a_larger_long_run_share():
    from services.athlete_tier import for_race

    assert for_race(ELITE, 161).weekday_minutes[1] == 150 and for_race(ELITE, 161).long_run_share_cap == 0.35
    assert for_race(ELITE, 104) is ELITE  # a 100K athlete keeps the standard caps
    assert for_race(REC, 161) is REC  # and so does everyone below sub-elite
    mile100 = goal_demands.compute(161, 8000, None, 36)
    with_exception = _assess(mile100, profile=ELITE, days=6, weeks=30, current=90.0)
    plain = _assess(goal_demands.compute(104.2, 5533, None, 29), profile=ELITE, days=6, weeks=30, current=90.0)
    assert with_exception.capacity_h > plain.capacity_h


def test_brief_line_says_the_verdict_and_what_would_help():
    from services.goal_feasibility import brief_line

    line = brief_line(
        {
            "verdict": "unsupported",
            "needed_h": 11.6,
            "capacity_h": 14.5,
            "weeks_needed": 14,
            "levers": ["more_weeks", "shorter_race", "finish_only", "steeper_venue"],
        }
    )
    assert line.startswith("Goal check: unsupported.") and "about 14 weeks" in line
    assert "more weeks before the race, a shorter race, a finish-only goal." in line
    assert brief_line({"verdict": "supported", "levers": []}) is None and brief_line(None) is None
