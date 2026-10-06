"""services/llm_judge: rubric prompt, background sampling and score export."""

import asyncio

from config import settings
from services import llm_judge, observability


def test_prompt_fills_every_placeholder_and_uses_vi_copy_rules():
    tpl, text = llm_judge.build_prompt("Q?", "Reply.", {"citations": [1]}, "vi")

    assert "{{" not in text
    assert "Q?" in text and "Reply." in text
    assert "thể tích" in text  # the VI ban list from the coach prompt is the language rubric
    assert tpl.name == "llm_judge"


def test_record_scores_writes_one_idempotent_score_per_criterion(monkeypatch):
    calls = []
    monkeypatch.setattr(observability, "score", lambda **kw: calls.append(kw))

    llm_judge.record_scores("a" * 32, {"grounded": 1.0, "safe": 1.0, "actionable": 0.5, "language": 0.75}, "42")

    assert [c["name"] for c in calls] == ["judge_grounded", "judge_safe", "judge_actionable", "judge_language"]
    assert calls[2]["value"] == 0.5 and calls[2]["score_id"] == "judge-actionable-42"


def test_maybe_judge_turn_skips_when_unsampled_or_disabled(monkeypatch):
    started = []
    monkeypatch.setattr(llm_judge, "_judge_and_score", lambda *a, **k: started.append(1))
    monkeypatch.setattr(observability, "enabled", lambda: True)
    kwargs = dict(trace_id="a" * 32, message_id=1, question="q", reply="r", evidence=None, lang="en", api_key="k")

    monkeypatch.setattr(settings, "LLM_JUDGE_SAMPLE_RATE", 0.0)
    llm_judge.maybe_judge_turn(**kwargs)
    monkeypatch.setattr(settings, "LLM_JUDGE_SAMPLE_RATE", 1.0)
    llm_judge.maybe_judge_turn(**{**kwargs, "trace_id": None})

    assert started == []


def test_maybe_judge_turn_scores_in_the_background(monkeypatch):
    recorded = []

    async def fake_judge(**kwargs):
        return {"grounded": 1.0, "safe": 1.0, "actionable": 1.0, "language": 1.0}

    monkeypatch.setattr(llm_judge, "judge_reply", fake_judge)
    monkeypatch.setattr(llm_judge, "record_scores", lambda *a, **k: recorded.append(a))
    monkeypatch.setattr(observability, "enabled", lambda: True)
    monkeypatch.setattr(settings, "LLM_JUDGE_SAMPLE_RATE", 1.0)

    async def run():
        llm_judge.maybe_judge_turn(
            trace_id="a" * 32, message_id=7, question="q", reply="r", evidence=None, lang="en", api_key="k"
        )
        await asyncio.gather(*llm_judge._background_tasks)

    asyncio.run(run())
    assert recorded and recorded[0][0] == "a" * 32


def test_score_accepts_judge_values_in_the_unit_interval_only(monkeypatch):
    class Client:
        calls: list = []

        def create_score(self, **kw):
            self.calls.append(kw)

    client = Client()
    monkeypatch.setattr(observability, "_client", client)
    observability.score(trace_id="a" * 32, name="judge_safe", value=0.75, score_id="judge-safe-1")
    observability.score(trace_id="a" * 32, name="judge_safe", value=1.5)
    observability.score(trace_id="a" * 32, name="plan_engine", value="rules")
    observability.score(trace_id="a" * 32, name="plan_engine", value="bogus")

    assert [(c["name"], c["value"], c["data_type"]) for c in client.calls] == [
        ("judge_safe", 0.75, "NUMERIC"),
        ("plan_engine", "rules", "CATEGORICAL"),
    ]
    assert client.calls[0]["score_id"] == "judge-safe-1"


def test_calibration_agreement_counts_only_labelled_criteria():
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from scripts.judge_calibration import agreement

    table = agreement(
        [
            ({"safe": 1}, {"safe": 0.75, "grounded": 0.0}),
            ({"safe": 0, "grounded": 0}, {"safe": 0.5, "grounded": 0.25}),
        ]
    )
    assert table == {"safe": {"tp": 1, "tn": 0, "fp": 1, "fn": 0}, "grounded": {"tp": 0, "tn": 1, "fp": 0, "fn": 0}}
