"""Pure helpers of the paid persona script (no model, no database)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import plan_live_personas as P  # noqa: E402

NEW = [
    "vn_masters_100k_gated_vi",
    "sub_elite_100mi_mountain",
    "low_base_50k_mountain_10wk",
    "short_8wk_100k_mountain",
    "vi_beginner_10k_road",
]


def test_over_budget():
    assert P.over_budget(5.0, 5.0) and not P.over_budget(4.99, 5.0)


def test_engine_for_picks_the_moved_counter():
    assert P.engine_for({"claude": 1, "claude_retry": 0}, {"claude": 1, "claude_retry": 1}) == "claude_retry"
    assert P.engine_for({"gemini": 2}, {"gemini": 2}) == "rules"


def test_new_personas_are_well_formed():
    for n in NEW:
        p = P.PERSONAS[n]
        assert {"user", "plan", "weeks", "expect"} <= set(p)
        assert p["plan"]["course_distance_km"] > 0 and p["weeks"] >= 8


def test_ladder_personas_no_longer_expect_back_to_back():
    for n, p in P.PERSONAS.items():
        if p["plan"].get("mountain_days") and p["plan"]["course_distance_km"] >= 45:
            assert not p["expect"].get("b2b"), n
            assert p["expect"].get("ladder"), n


def test_latency_summary_percentiles():
    runs = {
        i: {"engine": "claude", "cost_usd": 0.0, "seconds": s, "model_seconds": s - 1}
        for i, s in enumerate([10, 20, 30, 40, 100])
    }
    assert P.latency_summary(runs) == {"blocks": 5, "p50_s": 30, "p95_s": 100, "model_p50_s": 29, "model_p95_s": 99}


def test_model_seconds_come_from_the_latency_histogram():
    from telemetry import rag_latency_seconds

    before = P._counters()
    rag_latency_seconds.labels(service="plan_generator", engine="claude").observe(12.5)
    assert round(P._counters()["model_s"] - before["model_s"], 1) == 12.5
