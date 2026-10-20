import pytest

from services import goal_service
from services.athlete_tier import get_profile
from services.plan_adequacy import adjust_goals, assess, summary_lines

SUB = get_profile("sub_elite")


def week(n, minutes, km, phase="Base", sessions=5):
    """A structurally clean week: evenly spread Easy sessions."""
    days = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][:sessions]
    return [
        {
            "week_number": n,
            "day_of_week": d,
            "type": "Easy",
            "duration_minutes": minutes / sessions,
            "distance_km": km / sessions,
            "elevation_gain_m": 0,
            "target_zone": "Zone 2",
            "phase": phase,
            "title": "Easy",
        }
        for d in days
    ]


def plan(*weeks):
    return [w for wk in weeks for w in wk]


# The prod 100K plan generated at the 14h40 A goal: flat ~440 min / ~47 km for six weeks, no recovery week.
PROD_100K = plan(
    week(1, 450, 43.3),
    week(2, 415, 46.3),
    week(3, 435, 48.8),
    week(4, 425, 47.1),
    week(5, 440, 44.6),
    week(6, 445, 47.4),
)


def run(workouts, **kw):
    args = dict(total_weeks=13, current_week=1, weeks_to_race=11, distance_km=104.2, profile=SUB)
    return assess(workouts, **{**args, **kw})


def test_the_prod_100k_a_goal_plan_does_not_support_the_improvement_its_goal_assumes():
    a = run(PROD_100K)
    assert a.adequate_weeks == (1, 2, 3)  # weeks 4-6 have no recovery week
    assert set(a.problems) == {4, 5, 6} and all("RECOVERY_DUE" in c for c in a.problems.values())
    assert 0.5 < a.reach_ratio < 0.65  # best reachable peak ~69 km of the 120 km 100K benchmark
    assert a.improvement_assumed == pytest.approx(11 * 0.0025)
    assert a.improvement_supported < a.improvement_assumed
    assert a.shortfall_factor > 1.005 and not a.a_supported


def test_a_clean_plan_that_can_still_reach_the_benchmark_supports_the_goal():
    good = plan(week(1, 450, 85), week(2, 470, 90), week(3, 490, 95), week(4, 400, 80, phase="Recovery"))
    a = run(good, distance_km=56.4, total_weeks=12, weeks_to_race=11)
    assert a.a_supported and a.shortfall_factor == pytest.approx(1.0, abs=0.003)
    assert summary_lines(a) == []


def test_credit_is_capped_at_what_the_goal_assumed_and_at_five_percent():
    a = run(plan(week(1, 450, 85)), distance_km=56.4, total_weeks=30, weeks_to_race=29)
    assert a.improvement_assumed == 0.05 and a.improvement_supported <= 0.05


def test_adjust_goals_pushes_a_b_and_c_later_by_the_unsupported_credit_only():
    a = run(PROD_100K)
    goals = {"a": 810.0, "b": 855.0, "c": 945.0}
    adj = adjust_goals(goals, a)
    assert all(adj[k] > goals[k] for k in goals)
    assert adj["a"] == pytest.approx(810 * a.shortfall_factor, abs=0.1)
    assert (adj["a"] / 810 - 1) < 0.05  # never more than the whole 5% credit
    assert adjust_goals(goals, None) == goals
    assert adjust_goals(goals, run(plan(week(1, 450, 85)), distance_km=56.4, total_weeks=12)) is not goals


def test_summary_explains_the_shortfall_and_names_the_rule_breaks():
    lines = summary_lines(run(PROD_100K))
    text = " ".join(lines)
    assert "assume" in text and "RECOVERY_DUE" in text and "cannot reach" in text


def test_nothing_to_judge_without_a_date_a_distance_or_after_the_race():
    assert run(PROD_100K, weeks_to_race=None) is None
    assert run(PROD_100K, weeks_to_race=0) is None
    assert run(PROD_100K, distance_km=None) is None


def test_ungenerated_weeks_earn_full_credit_when_the_timeline_can_reach_the_benchmark():
    a = run(plan(week(1, 450, 70), week(2, 470, 74)), distance_km=56.4, total_weeks=12, weeks_to_race=11)
    assert a.reach_ratio == 1.0 and a.a_supported


class FakeDb:
    def __init__(self, workouts):
        self._w = workouts

    def get_plan_workouts(self, plan_id):
        return self._w

    def compute_current_week(self, start, total):
        return 1


def _plan_row():
    return {
        "id": 9, "race_date": "2999-01-01", "course_distance_km": 104.2, "total_weeks": 13,
        "start_date": "2026-10-19", "athlete_tier": "sub_elite", "long_run_day": None, "days_per_week": None,
    }  # fmt: skip


def test_goal_service_shows_adjusted_goals_with_the_plan_support_block(monkeypatch):
    monkeypatch.setattr(goal_service, "db", FakeDb(PROD_100K))
    monkeypatch.setattr(goal_service, "_weeks_until", lambda d: 11.0)
    shown = goal_service.with_plan_support({"goals": {"a": 880.0, "b": 940.0, "c": 1040.0}}, _plan_row())
    assert shown["goals_unadjusted"] == {"a": 880.0, "b": 940.0, "c": 1040.0}
    assert shown["goals"]["a"] > 880.0
    ps = shown["plan_support"]
    assert ps["a_supported"] is False and ps["shortfall_pct"] > 0.5 and ps["reasons"]
    assert goal_service.status(shown, None)["a_supported"] is False


def test_goal_service_never_loses_the_goals_when_plan_support_fails(monkeypatch):
    class Boom:
        def get_plan_workouts(self, plan_id):
            raise RuntimeError("db down")

    monkeypatch.setattr(goal_service, "db", Boom())
    original = {"goals": {"a": 880.0, "b": 940.0, "c": 1040.0}}
    assert goal_service.with_plan_support(original, _plan_row()) is original
    assert goal_service.with_plan_support(None, _plan_row()) is None
    assert goal_service.with_plan_support(original, None) is original
