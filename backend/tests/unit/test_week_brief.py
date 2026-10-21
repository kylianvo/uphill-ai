import asyncio

from services import week_brief
from services.week_brief import _clean, generate_week_brief, week_diff


def _wo(type_, minutes, **kw):
    return {"type": type_, "duration_minutes": minutes, **kw}


def test_week_diff_reports_total_long_run_and_session_type_changes():
    prev = [_wo("Easy", 60), _wo("Easy", 45), _wo("Long Run", 105), _wo("Rest", 0)]
    cur = [_wo("Easy", 65), _wo("Long Run", 115), _wo("Muscular Endurance", 45)]
    lines = week_diff(prev, cur)
    assert "Total time: 210 -> 225 min (+7%)." in lines
    assert "Long run: 105 -> 115 min." in lines
    assert "Easy sessions: 2 -> 1." in lines
    assert "Muscular Endurance sessions: 0 -> 1." in lines


def test_week_diff_without_a_previous_week_or_changes():
    assert week_diff([], [_wo("Easy", 60)]) == ["No earlier week to compare with."]
    same = [_wo("Easy", 60)]
    assert week_diff(same, same) == ["Total time: 60 -> 60 min (+0%)."]


def test_clean_requires_a_why_and_trims_benefits():
    assert _clean({"benefits": ["x"]}) is None
    out = _clean({"why": " Held volume. ", "benefits": ["a", "", "b", "c", "d"], "watch": ""})
    assert out == {"why": "Held volume.", "benefits": ["a", "b", "c"], "watch": None}


def test_no_key_or_no_decision_log_skips_the_model():
    kw = dict(race_info={}, block_context="", week_number=2, workouts=[], prev_workouts=[])
    assert asyncio.run(generate_week_brief(**kw, decision_log=["fact"], api_key=None)) is None
    assert asyncio.run(generate_week_brief(**kw, decision_log=[], api_key="k")) is None


def test_prompt_carries_the_decision_log_and_diff(monkeypatch):
    seen = {}

    class _Resp:
        text = '{"why": "Because.", "benefits": ["Long Run: durability"], "watch": null}'
        usage_metadata = None

    class _Models:
        def generate_content(self, model, contents, config):
            seen["prompt"] = contents
            return _Resp()

    class _Client:
        def __init__(self, api_key):
            self.models = _Models()

    import google.genai as genai

    monkeypatch.setattr(genai, "Client", _Client)
    monkeypatch.setattr(week_brief.observability.Usage, "from_genai", staticmethod(lambda _: None), raising=False)
    out = asyncio.run(
        generate_week_brief(
            race_info={},
            block_context="",
            week_number=2,
            workouts=[_wo("Easy", 60, day_of_week="Tuesday", title="Easy Run", target_zone="Zone 2")],
            prev_workouts=[_wo("Easy", 80)],
            decision_log=["Week 1 was 87% complete (344 of 395 planned min)."],
            api_key="k",
        )
    )
    assert out == {"why": "Because.", "benefits": ["Long Run: durability"], "watch": None}
    assert "Week 1 was 87% complete" in seen["prompt"]
    assert "Total time: 80 -> 60 min (-25%)." in seen["prompt"]
    assert "Week 2" in seen["prompt"] and "Easy Run" in seen["prompt"]


def test_decision_log_includes_milestone_fact():
    from datetime import UTC, datetime

    from services import beginner_milestones as bm

    rows = [{"milestone_key": "first_session", "achieved_at": datetime(2026, 10, 6, tzinfo=UTC), "source": "auto"}]
    fact = bm.brief_fact(bm.serialize("5k", False, rows), 5)
    assert fact.startswith("Milestone: next = 5 minutes of unbroken jogging") and "1 of 6 reached" in fact
