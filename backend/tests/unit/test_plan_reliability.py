"""The reliability scorecard (scripts/plan_reliability.py) must pass: it is what backs the claim that a
generated plan is reliable for the goal, or says plainly that it is not."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import plan_reliability  # noqa: E402


@pytest.mark.parametrize("scenario", plan_reliability.SCENARIOS, ids=lambda s: s.name)
def test_scenario_passes(scenario):
    result = plan_reliability.run(scenario)
    assert result.failures == [], (result.verdict, result.issues, result.failures)


def test_a_three_day_hundred_k_is_never_called_supported():
    s = next(s for s in plan_reliability.SCENARIOS if s.name.startswith("25km 3d | 100K | time | flat"))
    assert plan_reliability.run(s).verdict == "unsupported"


def test_scorecard_never_calls_gemini(monkeypatch):
    import google.genai

    def boom(*a, **k):
        raise AssertionError("the scorecard must not call Gemini")

    monkeypatch.setattr(google.genai, "Client", boom)
    assert plan_reliability.run(plan_reliability.SCENARIOS[0]).failures == []
