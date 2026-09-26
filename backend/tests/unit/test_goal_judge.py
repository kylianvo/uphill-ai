import json

import pytest

from services import goal_judge
from services.goal_judge import GoalOutput

CURVE = [(5.0, 400.0), (10.0, 420.0), (25.0, 460.0), (50.0, 520.0), (75.0, 580.0), (90.0, 620.0)]
ANCHORS = [
    {"id": "phys_r1", "method": "physics", "minutes": 480.0, "source_result_id": 1, "notes": []},
    {"id": "rank_r1", "method": "field_rank", "minutes": 500.0, "source_result_id": 1, "notes": []},
]
RACE = {"field": {"curve": CURVE, "fastest_winner_mins": 380.0}}


def _output(a=460.0, b=490.0, c=530.0, confidence="medium", reasoning=3, ids=("phys_r1",)):
    return {
        "goals": {"a": a, "b": b, "c": c},
        "confidence": confidence,
        "reasoning": [f"bullet {i}" for i in range(reasoning)],
        "anchors_weighted": [{"id": i, "weight": 1.0} for i in ids],
        "missing": [],
    }


def _errors(race=RACE, anchors=ANCHORS, cutoff=None, **kw):
    return goal_judge.validate(GoalOutput.model_validate(_output(**kw)), anchors, race, cutoff)


def test_valid_output_passes():
    assert _errors() == []


def test_goals_must_be_ordered():
    assert "goals must satisfy a < b < c" in _errors(a=500.0, b=490.0)


def test_spread_cap_depends_on_confidence():
    assert _errors(a=420.0, b=490.0, c=560.0)  # 1.33 at medium
    assert _errors(a=420.0, b=490.0, c=560.0, confidence="low") == []


def test_a_cannot_beat_the_winner():
    assert any("winning time" in e for e in _errors(a=360.0, b=400.0, c=420.0))


def test_c_must_respect_cutoff():
    assert any("cutoff" in e for e in _errors(cutoff=520.0))


def test_b_must_stay_near_anchors():
    assert any("anchors' range" in e for e in _errors(a=560.0, b=600.0, c=640.0))


def test_without_anchors_b_must_sit_in_field():
    assert _errors(anchors=[], ids=(), a=300.0, b=410.0, c=440.0, confidence="low") != []
    assert _errors(anchors=[], ids=(), a=480.0, b=520.0, c=560.0, confidence="low") == []


def test_without_anchors_or_field_confidence_must_be_low():
    assert _errors(race={}, anchors=[], ids=()) == ["confidence must be low without anchors or field data"]


def test_reasoning_count_and_anchor_ids():
    assert "give 3 to 5 reasoning bullets" in _errors(reasoning=2)
    assert any("unknown anchor ids" in e for e in _errors(ids=("made_up",)))


def test_deterministic_uses_anchor_median_and_improvement():
    result = goal_judge.deterministic(ANCHORS, weeks_to_race=8)
    assert result["engine"] == "rules"
    assert result["goals"]["b"] == pytest.approx(490.0 * (1 - 0.02), abs=0.1)
    assert result["goals"]["a"] < result["goals"]["b"] < result["goals"]["c"]
    assert result["confidence"] == "medium"
    assert goal_judge.deterministic([], 8) is None


def test_assess_accepts_first_valid_answer(monkeypatch):
    monkeypatch.setattr(goal_judge, "_call_gemini", lambda prompt, key: json.dumps(_output()))
    result = goal_judge.assess({"race": RACE}, ANCHORS, api_key="k")
    assert result["engine"] == "gemini"
    assert result["goals"]["b"] == 490.0


def test_assess_retries_with_reduced_prompt_and_error(monkeypatch):
    prompts = []
    answers = iter([json.dumps(_output(a=500.0)), json.dumps(_output())])

    def fake(prompt, key):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(goal_judge, "_call_gemini", fake)
    context = {"race": {**RACE, "climate": {"avg_temp_c": 30}}, "history": [{"id": i} for i in range(9)]}
    result = goal_judge.assess(context, ANCHORS, api_key="k")
    assert result["engine"] == "gemini_retry"
    assert "previous answer was rejected: goals must satisfy a < b < c" in prompts[1]
    assert "avg_temp_c" not in prompts[1]


def test_assess_falls_back_to_rules(monkeypatch):
    def boom(prompt, key):
        raise RuntimeError("quota")

    monkeypatch.setattr(goal_judge, "_call_gemini", boom)
    assert goal_judge.assess({"race": RACE, "weeks_to_race": 0}, ANCHORS, api_key="k")["engine"] == "rules"


def test_assess_skips_llm_when_disabled_or_keyless(monkeypatch):
    monkeypatch.setattr(goal_judge, "_call_gemini", lambda p, k: pytest.fail("should not call"))
    assert goal_judge.assess({"race": RACE}, ANCHORS, api_key=None)["engine"] == "rules"
    assert goal_judge.assess({"race": RACE}, ANCHORS, api_key="k", llm_enabled=False)["engine"] == "rules"


def test_prompt_carries_language_instruction():
    assert "Vietnamese" in goal_judge.build_prompt({}, [], "vi")
    assert "in English." in goal_judge.build_prompt({}, [], "en")
