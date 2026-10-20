import asyncio

import telemetry
from services import plan_lint
from services.plan_generator import PlanGenerator


def _count(counter, **labels):
    return counter.labels(**labels)._value.get()


def _issue(code):
    return plan_lint.Issue(code, 1, "fix it")


def _run_loop(monkeypatch, drafts):
    """_lint_and_correct over scripted lint results: first draft, then the retry's."""
    results = iter(drafts)
    monkeypatch.setattr(PlanGenerator, "_lint_issues", staticmethod(lambda *a, **k: next(results)))

    async def generate(**kw):
        return [{"week_number": 1}], "recreational"

    return asyncio.run(
        PlanGenerator._lint_and_correct(
            [{"week_number": 1}],
            "recreational",
            generate=generate,
            plan_id=0,
            race_info={},
            total_weeks=10,
            cutoff_time_hours=None,
            block_context=None,
            target_week=None,
        )  # fmt: skip
    )


def test_a_retry_that_fixes_the_week_is_counted_as_kept(monkeypatch):
    found = _count(telemetry.plan_lint_total, code="LONG_SHARE", outcome="found")
    kept = _count(telemetry.plan_lint_total, code="LONG_SHARE", outcome="retry_kept")
    _run_loop(monkeypatch, [[_issue("LONG_SHARE")], []])
    assert _count(telemetry.plan_lint_total, code="LONG_SHARE", outcome="found") == found + 1
    assert _count(telemetry.plan_lint_total, code="LONG_SHARE", outcome="retry_kept") == kept + 1


def test_a_retry_that_does_not_help_is_counted_as_discarded(monkeypatch):
    dropped = _count(telemetry.plan_lint_total, code="VERT_JUMP", outcome="retry_discarded")
    _run_loop(monkeypatch, [[_issue("VERT_JUMP")], [_issue("VERT_JUMP")]])
    assert _count(telemetry.plan_lint_total, code="VERT_JUMP", outcome="retry_discarded") == dropped + 1


def test_verdict_nudge_and_path_counters_accept_their_labels():
    telemetry.goal_feasibility_total.labels(verdict="stretch").inc()
    telemetry.coach_nudge_total.labels(tone="push", source="rules").inc()
    telemetry.aerobic_path_total.labels(b="on", a="behind", confidence="medium").inc()
    assert _count(telemetry.goal_feasibility_total, verdict="stretch") >= 1
