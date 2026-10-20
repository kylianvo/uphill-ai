from datetime import date, datetime, timedelta

from services import aerobic_speed

MONDAY = date(2026, 8, 3)
AET = 145


def run(week, pace_s, hr=143, minutes=45, day=1, kind="running", gap=True, workout_type=None, gain=0.0):
    start = datetime.combine(MONDAY + timedelta(weeks=week - 1, days=day), datetime.min.time())
    return {"start_time": start, "duration_seconds": minutes * 60, "avg_hr": hr, "distance_km": minutes / 6,
            "adjusted_pace_sec_per_km": pace_s if gap else None, "avg_pace_sec_per_km": pace_s,
            "elevation_gain_m": gain, "activity_type": kind, "workout_type": workout_type}  # fmt: skip


def test_only_steady_aerobic_runs_qualify():
    q = aerobic_speed.qualifying
    assert q(run(1, 360), AET)
    assert q(run(1, 360, hr=AET - 14), AET)  # most athletes run easy well under their AeT
    assert not q(run(1, 360, hr=165), AET)  # a hard effort
    assert not q(run(1, 360, hr=AET - 25), AET)  # a recovery jog says little about aerobic speed
    assert not q(run(1, 360, minutes=20), AET)
    assert not q(run(1, 360, kind="cycling"), AET)
    assert not q(run(1, 360, workout_type="Interval"), AET)  # a structured hard session is not a steady run
    assert not q(run(1, 360, workout_type="Tempo"), AET)


def test_flat_runs_without_grade_adjusted_pace_use_their_average_pace_but_hilly_ones_do_not():
    assert aerobic_speed.qualifying(run(1, 360, gap=False), AET)  # flat: average pace is the grade-adjusted pace
    assert not aerobic_speed.qualifying(run(1, 360, gap=False, gain=900), AET)  # 20 m D+/km: needs the adjusted pace


def test_efficiency_normalises_for_heart_rate_so_easy_and_steadier_runs_compare():
    slow_easy = run(1, 360, hr=140)  # 2.78 m/s at 140 bpm
    faster_steady = run(1, 360 * 140 / 150, hr=150)  # same fitness: 3.0 m/s at 150 bpm
    assert abs(aerobic_speed.efficiency(slow_easy) - aerobic_speed.efficiency(faster_steady)) < 1e-9


def test_weekly_point_pools_a_three_week_window_so_sparse_weeks_still_count():
    # one qualifying run per week: no single week has three, the trailing window does
    acts = [run(1, 360, day=1), run(2, 360, day=2), run(3, 360, day=3), run(4, 360, day=1)]
    pts = aerobic_speed.weekly_points(acts, AET, MONDAY, through_week=4)
    assert [(p.week, p.n) for p in pts] == [(3, 3), (4, 3)]
    ref = aerobic_speed.weekly_points(acts, AET, MONDAY, through_week=4)[0].pace_min_km
    assert abs(ref - 6.0 * 143 / 145) < 0.05  # the pace this athlete would hold at AeT heart rate


def series(paces):  # one point per week, 3 runs each
    return [aerobic_speed.WeekPoint(i + 1, p, 3) for i, p in enumerate(paces)]


def test_no_path_without_enough_history():
    assert aerobic_speed.path(series([6.0, 6.0]), total_weeks=12) is None


def test_improving_at_the_assumed_rate_is_on_the_b_path():
    # 0.25%/week assumed: ten weeks is 2.5% faster
    paces = [6.0 * (1 - 0.0025 * w) for w in range(10)]
    p = aerobic_speed.path(series(paces), total_weeks=12)
    assert p.b in {"on", "ahead"} and p.weeks == 9 and p.measured_pct > 2.0


def test_flat_fitness_is_behind_after_a_few_weeks():
    p = aerobic_speed.path(series([6.0] * 10), total_weeks=12)
    assert p.b == "behind" or p.a == "behind"
    assert p.a == "behind"


def test_ahead_of_the_line_is_ahead_and_confidence_grows_with_weeks():
    fast = aerobic_speed.path(series([6.0 * (1 - 0.01 * w) for w in range(10)]), total_weeks=12)
    assert fast.b == "ahead" and fast.a == "ahead" and fast.confidence == "high"
    early = aerobic_speed.path(series([6.0, 5.95, 5.9, 5.88]), total_weeks=12)
    assert early.confidence == "low"


def test_noisy_windows_widen_the_tolerance_so_a_borderline_gap_is_not_behind():
    flat = [aerobic_speed.WeekPoint(i + 1, 6.0, 4, rel_se=0.0) for i in range(8)]
    noisy = [aerobic_speed.WeekPoint(i + 1, 6.0, 4, rel_se=0.012) for i in range(8)]
    assert aerobic_speed.path(flat, total_weeks=20).b == "behind"  # no gain over 7 weeks, tight data: behind
    assert aerobic_speed.path(noisy, total_weeks=20).b == "on"  # same, but the data cannot tell: not an alarm


def test_weekly_points_carry_the_windows_relative_standard_error():
    acts = [run(1, 360, day=d, hr=140 + d) for d in range(5)]
    p = aerobic_speed.weekly_points(acts, AET, MONDAY, through_week=1)[0]
    assert 0 <= p.rel_se < 0.05
