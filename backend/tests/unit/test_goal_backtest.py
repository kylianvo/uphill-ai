from scripts.goal_backtest import passes_gate, score, summarize


def test_score_hit_and_error():
    assert score({"a": 450, "b": 480, "c": 520}, 500) == {"hit": True, "error": 20 / 500}
    assert score({"a": 450, "b": 480, "c": 520}, 530)["hit"] is False
    assert score(None, 500) is None


def test_summarize_skips_missing_estimates():
    rows = [{"hit": True, "error": 0.02}, None, {"hit": False, "error": 0.10}, {"hit": True, "error": 0.04}]
    s = summarize(rows)
    assert s["n"] == 3 and s["hit_rate"] == 2 / 3 and s["median_error"] == 0.04
    assert summarize([None])["n"] == 0


def test_gate_needs_llm_at_least_as_good_on_both():
    old = {"n": 10, "hit_rate": 0.6, "median_error": 0.08}
    assert passes_gate(old, {"n": 10, "hit_rate": 0.7, "median_error": 0.07})
    assert not passes_gate(old, {"n": 10, "hit_rate": 0.7, "median_error": 0.09})
    assert not passes_gate(old, {"n": 0, "hit_rate": None, "median_error": None})
