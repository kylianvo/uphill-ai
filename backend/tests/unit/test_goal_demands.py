from services import goal_demands
from services.pacing_calculator import PacingCalculator
from services.race_estimator import RaceEstimator


def test_vht_100k_target_demands():
    d = goal_demands.compute(104.2, 5533, 14.67, 29)
    assert d.source == "target"
    assert d.race_class == "100K"
    assert abs(d.steepness_m_per_km - 53.1) < 0.1
    assert abs(d.climb_rate_m_per_h - 5533 / 14.67) / (5533 / 14.67) < 0.01
    assert d.time_on_feet_min == 14.67 * 60


def test_longest_session_is_capped():
    assert goal_demands.compute(104.2, 5533, 14.67, 29).longest_session_min <= 300


def test_finish_goal_uses_cutoff_safe_time():
    d = goal_demands.compute(56.4, 2946, None, 12)
    assert d.source == "cutoff_safe"
    assert d.target_time_min == 12 * 60 * 0.85


def test_no_course_returns_none():
    assert goal_demands.compute(None, 2946, 14, 29) is None
    assert goal_demands.compute(104.2, 5533, None, None) is None
    flat = goal_demands.compute(104.2, None, 14, 29)
    assert flat is not None and flat.climb_rate_m_per_h == 0


def test_pace_matches_solver():
    d = goal_demands.compute(56.4, 2946, 9.0, 12)
    expected = PacingCalculator.solve_base_pace(RaceEstimator.synthesize_course(56.4, 2946), 9.0 * 60)
    assert abs(d.required_flat_pace_min_km - expected) < 1e-9


def test_venue_rate_is_carried():
    assert goal_demands.compute(56.4, 2946, 9.0, 12, venue_climb_rate=28.0).venue_climb_rate == 28.0


def test_prompt_block_mentions_the_demands_in_both_languages():
    d = goal_demands.compute(104.2, 5533, 14.67, 29)
    en, vi = goal_demands.prompt_block(d, "en"), goal_demands.prompt_block(d, "vi")
    assert "5533" in en or str(round(d.climb_rate_m_per_h)) in en
    assert str(round(d.longest_session_min)) in en and str(round(d.longest_session_min)) in vi


def test_races_below_ultra_distance_get_no_demands():
    # the book's peak-week benchmarks start at the 50K; a half or full marathon must not inherit them
    assert goal_demands.compute(21.1, 100, None, 3.5) is None
    assert goal_demands.compute(42.2, 300, None, 7) is None
    assert goal_demands.compute(50.0, 2000, None, 10) is not None


def _plan_with_long_runs(longs):
    return [
        {
            "week_number": i + 1,
            "type": "Long Run",
            "duration_minutes": m,
            "day_of_week": "Sunday",
            "phase": "Base" if i < 4 else "Build",
        }  # fmt: skip
        for i, m in enumerate(longs)
    ]


def test_long_run_line_grows_the_long_run_toward_the_target_within_the_weekly_cap():
    d = goal_demands.compute(104.2, 5533, 14.67, 29)  # longest session target 300 min
    ws = _plan_with_long_runs([110, 115, 120])
    line = goal_demands.long_run_line(ws, week=4, total_weeks=11, demands=d, profile_long_cap_min=185)
    # the even climb from 120 to the 185 the days can hold, by week 7 (a 100 km race tapers two weeks)
    assert line and "at least 134" in line and "185" in line and "week 7" in line


def test_long_run_line_is_silent_without_history_or_after_the_build():
    d = goal_demands.compute(104.2, 5533, 14.67, 29)
    assert goal_demands.long_run_line([], week=1, total_weeks=11, demands=d, profile_long_cap_min=185) is None
    ws = _plan_with_long_runs([110, 115, 120])
    assert goal_demands.long_run_line(ws, week=9, total_weeks=11, demands=d, profile_long_cap_min=185) is None


def test_back_to_back_line_names_the_weekend_only_for_ultras_in_the_last_build_weeks():
    d = goal_demands.compute(104.2, 5533, 14.67, 29)
    on = goal_demands.back_to_back_line(
        _plan_with_long_runs([110, 120, 130, 140, 145]), week=6, total_weeks=11, demands=d, days_per_week=6
    )
    assert on and "Saturday" in on and "Sunday" in on and "recovery week" in on
    assert goal_demands.back_to_back_line([], week=2, total_weeks=11, demands=d, days_per_week=6) is None
    assert goal_demands.back_to_back_line([], week=6, total_weeks=11, demands=d, days_per_week=4) is None
    fifty = goal_demands.compute(56.4, 2946, 9.0, 12)
    assert goal_demands.back_to_back_line([], week=6, total_weeks=11, demands=fifty, days_per_week=6) is None


def test_climb_line_only_for_steep_courses_without_hills():
    d = goal_demands.compute(104.2, 5533, 14.67, 29)
    line = goal_demands.climb_line(week=5, total_weeks=11, demands=d, flat_only=True)
    assert line and "stair" in line and "53 m D+/km" in line
    assert goal_demands.climb_line(week=5, total_weeks=11, demands=d, flat_only=False) is None
    assert goal_demands.climb_line(week=1, total_weeks=11, demands=d, flat_only=True) is None
    rolling = goal_demands.compute(42.0, 300, None, 7)
    assert rolling is None


def test_back_to_back_targets_keep_the_long_run_near_last_weeks_and_add_a_long_saturday():
    from services.plan_lint import b2b_targets

    ws = _plan_with_long_runs([120, 140, 145])
    sat, sun = b2b_targets(ws, week=6, longest_target=300)
    assert 145 <= sun <= 145 * 1.25 and 90 <= sat <= sun  # within the 25% weekly long-run growth cap


def test_ladder_plans_get_no_second_longest_session_target():
    """A mountain-day ultra's long runs come from the ladder (7 h); the 300 min demand line contradicted it."""
    d = goal_demands.compute(104.2, 5533, 15.75, None)
    assert "longest session should reach about 300 min" in goal_demands.prompt_block(d, "en")
    assert "longest session" not in goal_demands.prompt_block(d, "en", ladder=True)
    assert "buổi dài nhất" not in goal_demands.prompt_block(d, "vi", ladder=True)


def test_vert_targets_ramp_from_recent_vert_to_40_percent_of_race_d_plus():
    """VHT 100K (5533 m D+), 13 weeks, a runner climbing 589 m a week now: the peak build week asks 40% of race
    D+, no week grows more than 20%, and recovery weeks have no target."""
    d = goal_demands.compute(104.2, 5533, 15.75, None)
    t = goal_demands.vert_targets(d, 13, 589, indoor_only=False)
    assert 4 not in t and 8 not in t  # recovery weeks
    assert t[9] == round(0.40 * 5533, -1)
    weeks = sorted(t)
    assert all(t[b] <= t[a] * 1.2 ** (b - a) + 10 for a, b in zip(weeks, weeks[1:]))
    assert t[1] >= 589


def test_vert_targets_indoor_only_and_flat_courses():
    d = goal_demands.compute(104.2, 5533, 15.75, None)
    assert max(goal_demands.vert_targets(d, 13, None, indoor_only=True).values()) == round(0.25 * 5533, -1)
    flat = goal_demands.compute(50, 400, 5, None)
    assert goal_demands.vert_targets(flat, 13, 500, indoor_only=False) == {}
    assert goal_demands.vert_targets(None, 13, 500, indoor_only=False) == {}
