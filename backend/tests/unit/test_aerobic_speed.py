from datetime import date, datetime, timedelta

from services import aerobic_speed

MONDAY = date(2026, 8, 3)
AET = 145


def run(week, pace_s, hr=143, minutes=45, day=1, kind="running", gap=True):
    start = datetime.combine(MONDAY + timedelta(weeks=week - 1, days=day), datetime.min.time())
    return {"start_time": start, "duration_seconds": minutes * 60, "avg_hr": hr, "distance_km": minutes / 6,
            "adjusted_pace_sec_per_km": pace_s if gap else None, "activity_type": kind}  # fmt: skip


def week_runs(week, pace_s, n=3):
    return [run(week, pace_s, day=d) for d in range(n)]


def test_only_steady_aerobic_runs_qualify():
    q = aerobic_speed.qualifying
    assert q(run(1, 360), AET)
    assert not q(run(1, 360, hr=165), AET)  # a hard effort
    assert not q(run(1, 360, hr=110), AET)  # a recovery jog says little about aerobic speed
    assert not q(run(1, 360, minutes=20), AET)
    assert not q(run(1, 360, kind="cycling"), AET)
    assert not q(run(1, 360, gap=False), AET)


def test_weekly_point_is_the_median_and_needs_three_runs():
    acts = [run(1, 360), run(1, 380, day=2), run(1, 340, day=3), run(2, 360), run(2, 360, day=2)]
    pts = aerobic_speed.weekly_points(acts, AET, MONDAY, through_week=2)
    assert [(p.week, p.n, round(p.pace_min_km, 2)) for p in pts] == [(1, 3, 6.0)]  # week 2 has only two runs


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
