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
