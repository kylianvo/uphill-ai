import asyncio

import pytest

from config import settings
from services import plan_generator
from services.plan_generator import PlanGenerator


def wo(day, type_, minutes, zone="Zone 2", week=2, gain=0, km=None):
    return {
        "week_number": week,
        "day_of_week": day,
        "type": type_,
        "duration_minutes": minutes,
        "target_zone": zone,
        "elevation_gain_m": gain,
        "distance_km": minutes / 6 if km is None else km,
        "phase": "Base",
        "title": f"{type_} {day[:3]}",
    }


# Strength on Saturday, 24 h before the Sunday long run (plan C's pattern).
BAD = [
    wo("Tuesday", "Easy", 80),
    wo("Wednesday", "Easy", 60),
    wo("Saturday", "Muscular Endurance", 60, "Zone 1"),
    wo("Sunday", "Long Run", 100),
]
# The same week with strength on Thursday, 72 h clear of the long run.
GOOD = [
    wo("Tuesday", "Easy", 80),
    wo("Wednesday", "Easy", 60),
    wo("Thursday", "Muscular Endurance", 60, "Zone 1"),
    wo("Sunday", "Long Run", 100),
]


@pytest.fixture(autouse=True)
def _flags_and_no_db(monkeypatch):
    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", True)
    monkeypatch.setattr(settings, "PLAN_LINT_RETRY", True)
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])


class Gen:
    """A stand-in for the partial of _generate_plan_workouts: records the contexts it was given."""

    def __init__(self, result=None, error=None):
        self.result, self.error, self.contexts = result, error, []

    async def __call__(self, *, block_context=None):
        self.contexts.append(block_context)
        if self.error:
            raise self.error
        return self.result


def run(workouts, gen, tier="recreational", block_context="HISTORY"):
    return asyncio.run(
        PlanGenerator._lint_and_correct(
            workouts,
            tier,
            generate=gen,
            plan_id=7,
            race_info={"course_distance_km": 56.4},
            total_weeks=12,
            cutoff_time_hours=None,
            block_context=block_context,
            target_week=2,
        )
    )


def test_a_clean_draft_is_returned_untouched_without_a_second_model_call():
    gen = Gen(result=(BAD, "recreational"))
    out, tier = run(GOOD, gen)
    assert out is GOOD and tier == "recreational" and gen.contexts == []


def test_a_rule_break_triggers_one_retry_with_the_problems_spelled_out_and_keeps_the_better_draft():
    gen = Gen(result=(GOOD, "recreational"))
    out, _ = run(BAD, gen)
    assert out is GOOD
    assert len(gen.contexts) == 1
    ctx = gen.contexts[0]
    assert ctx.startswith("HISTORY") and "PLAN CHECK" in ctx and "48 hours" in ctx and "Saturday" in ctx


def test_a_retry_that_is_no_better_keeps_the_first_draft():
    gen = Gen(result=(BAD, "recreational"))
    out, _ = run(BAD, gen)
    assert out is BAD and len(gen.contexts) == 1


def test_without_prior_history_the_feedback_is_the_whole_context():
    gen = Gen(result=(GOOD, "recreational"))
    run(BAD, gen, block_context=None)
    assert gen.contexts[0].startswith("PLAN CHECK")


def test_retry_can_be_switched_off_while_linting_still_runs(monkeypatch):
    monkeypatch.setattr(settings, "PLAN_LINT_RETRY", False)
    gen = Gen(result=(GOOD, "recreational"))
    out, _ = run(BAD, gen)
    assert out is BAD and gen.contexts == []


def test_a_failing_retry_never_loses_the_first_draft():
    out, tier = run(BAD, Gen(error=RuntimeError("gemini down")))
    assert out is BAD and tier == "recreational"


def test_a_failing_lint_never_loses_the_draft(monkeypatch):
    def boom(*a, **k):
        raise ValueError("lint bug")

    monkeypatch.setattr(PlanGenerator, "_lint_issues", staticmethod(boom))
    gen = Gen(result=(GOOD, "recreational"))
    out, _ = run(BAD, gen)
    assert out is BAD and gen.contexts == []


def test_a_new_block_behind_the_readiness_path_is_flagged_but_an_adapt_is_not(monkeypatch):
    # 62 km weeks with one planned down week: reachable, but week 7 must not drop to 50 km
    prior = [wo("Tuesday", "Easy", km * 6, week=w, km=km) for w, km in enumerate([62, 62, 62, 52, 62, 62], start=1)]
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: prior)
    thin = [wo(d, "Easy", 60, week=7, km=10) for d in ("Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday")]
    kwargs = dict(plan_id=7, race_info={"course_distance_km": 56.4}, total_weeks=12, cutoff_time_hours=None)
    new_block = PlanGenerator._lint_issues(thin, "recreational", target_week=None, **kwargs)
    adapt = PlanGenerator._lint_issues(thin, "recreational", target_week=7, **kwargs)
    assert "READINESS_BEHIND" in {i.code for i in new_block}
    assert "READINESS_BEHIND" not in {i.code for i in adapt}
