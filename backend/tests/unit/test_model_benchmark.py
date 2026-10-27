import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts import model_benchmark  # noqa: E402

FIXTURE = {
    "lang": "en",
    "cutoff_mins": 700,
    "context": {"race": {"field": {}}},
    "anchors": [{"id": "r1", "minutes": 560}],
}
REF = {"output": {"goals": {"a": 535.0, "b": 565.0, "c": 595.0}}}


def _answer(a=540, b=570, c=600, bullets=3, anchor_id="r1"):
    return json.dumps(
        {
            "goals": {"a": a, "b": b, "c": c},
            "confidence": "medium",
            "reasoning": ["x"] * bullets,
            "anchors_weighted": [{"id": anchor_id, "weight": 1.0}],
            "missing": [],
        }
    )


def test_score_accepts_a_valid_answer_and_measures_distance_to_ref():
    result = model_benchmark.score(_answer(), FIXTURE, REF)
    assert result["parsed"] and result["accepted"]
    assert result["errors"] == []
    assert round(result["b_vs_ref_pct"], 2) == 0.88  # |570 - 565| / 565


def test_score_reports_guardrail_violations():
    result = model_benchmark.score(_answer(a=600, b=570, c=540), FIXTURE, REF)
    assert result["parsed"] and not result["accepted"]
    assert "goals must satisfy a < b < c" in result["errors"]


def test_score_handles_unparseable_output():
    result = model_benchmark.score("not json", FIXTURE, REF)
    assert result == {"parsed": False, "accepted": False, "errors": ["unparseable"], "b_vs_ref_pct": None}


def test_summarize_per_engine():
    rows = [
        {
            "engine": "haiku",
            "seconds": s,
            "input_tokens": 2000,
            "output_tokens": 400,
            "parsed": True,
            "accepted": ok,
            "errors": [],
            "b_vs_ref_pct": 1.0,
        }
        for s, ok in [(1.0, True), (2.0, True), (3.0, False)]
    ]
    summary = model_benchmark.summarize(rows)["haiku"]
    assert summary["calls"] == 3
    assert summary["p50_s"] == 2.0
    assert round(summary["accepted_rate"], 3) == 0.667
    # 2000 * 0.10 / 1e6 + 400 * 0.50 / 1e6
    assert round(summary["usd_per_call"], 6) == 0.0004


def test_render_report_lists_metrics_and_rejections():
    rows = [
        {
            "engine": "gemini",
            "fixture": "fixture_a.json",
            "seconds": 4.0,
            "input_tokens": 2000,
            "output_tokens": 600,
            "parsed": True,
            "accepted": False,
            "errors": ["give 3 to 5 reasoning bullets"],
            "b_vs_ref_pct": 2.0,
        },
    ]
    report = model_benchmark.render_report(model_benchmark.summarize(rows), rows)
    assert "| p50_s | 4.00 |" in report
    assert "gemini / fixture_a.json: give 3 to 5 reasoning bullets" in report


def test_gemini_rows_from_refs_reuse_saved_answers_without_calls():
    fixtures = [
        ("fixture_a.json", FIXTURE, {"latency_s": 3.2, "engine_used": "gemini", "output": json.loads(_answer())}),
        ("fixture_b.json", FIXTURE, {"latency_s": 6.7, "engine_used": "gemini_retry", "output": json.loads(_answer())}),
        ("fixture_c.json", FIXTURE, None),
    ]
    rows = model_benchmark.gemini_rows_from_refs(fixtures)

    assert [r["fixture"] for r in rows] == ["fixture_a.json"]  # retried and missing refs are skipped
    assert rows[0]["seconds"] == 3.2 and rows[0]["accepted"]
    assert rows[0]["b_vs_ref_pct"] is None  # the ref is this answer; distance to itself means nothing
    summary = model_benchmark.summarize(rows)["gemini"]
    assert summary["usd_per_call"] is None and summary["mean_input_tokens"] is None
