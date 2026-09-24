import datetime as dt
from unittest.mock import patch

from services.coach_tools import ProposalContext
from services.coach_tools.registry import build_tools


def test_build_tools_returns_all_four_tools():
    tools = build_tools(user_id=1, kb_api_key="k")
    names = {t.name for t in tools}
    assert names == {"get_week", "pace_strategy", "week_review", "kb_search"}


def test_tool_schemas_never_expose_user_id():
    tools = build_tools(user_id=1, kb_api_key="k")
    for t in tools:
        schema_fields = t.args_schema.model_fields if t.args_schema else {}
        assert "user_id" not in schema_fields
        assert "athlete_id" not in schema_fields


def test_pace_strategy_schema_has_distance_and_elevation_fields():
    tools = build_tools(user_id=1, kb_api_key="k")
    pace_tool = next(t for t in tools if t.name == "pace_strategy")
    schema_fields = pace_tool.args_schema.model_fields if pace_tool.args_schema else {}
    assert "distance_km" in schema_fields
    assert "elevation_gain_m" in schema_fields
    assert "user_id" not in schema_fields
    assert "athlete_id" not in schema_fields


def test_pace_strategy_tool_passes_distance_and_elevation_through():
    tools = build_tools(user_id=1, kb_api_key="k")
    pace_tool = next(t for t in tools if t.name == "pace_strategy")
    with patch("services.coach_tools.pacing_tools.pace_strategy_impl") as mock_impl:
        mock_impl.return_value.__dict__ = {}
        pace_tool.invoke(
            {
                "race_name": "Dalat Ultra Trail",
                "target_time_hours": 13.0,
                "distance_km": 75.0,
                "elevation_gain_m": 3800.0,
            }
        )
    mock_impl.assert_called_once_with(
        user_id=1,
        race_name="Dalat Ultra Trail",
        target_time_hours=13.0,
        strategy="conservative_start",
        distance_km=75.0,
        elevation_gain_m=3800.0,
    )


def test_get_week_tool_ignores_llm_supplied_user_id_and_uses_closure():
    tools = build_tools(user_id=999, kb_api_key="k")
    get_week_tool = next(t for t in tools if t.name == "get_week")
    with patch("services.coach_tools.plan_tools.get_week_impl") as mock_impl:
        mock_impl.return_value.model_dump = lambda: {}
        # Even if a caller tries to smuggle user_id through kwargs, the
        # generated schema has no such field to accept it -- invoke() would
        # reject an unknown field before this ever reaches get_week_impl.
        # Here we test with a different user_id value (1) to prove the closure's
        # user_id=999 is what actually gets passed, not the smuggled value.
        get_week_tool.invoke({"week_number": 2, "user_id": 1})
    mock_impl.assert_called_once_with(user_id=999, week_number=2)


def test_proposal_tool_absent_without_context():
    names = {t.name for t in build_tools(user_id=1, kb_api_key="k")}
    assert "propose_schedule_change" not in names


def test_proposal_tool_present_with_context_and_never_takes_identity():
    ctx = ProposalContext(thread_id=5, plan_id=9, today=dt.date(2026, 9, 23))
    tools = build_tools(user_id=1, kb_api_key="k", proposals=ctx)
    tool = next(t for t in tools if t.name == "propose_schedule_change")
    fields = tool.args_schema.model_fields
    assert set(fields) == {"operations", "rationale"}
    op_fields = fields["operations"].annotation.__args__[0].model_fields
    assert "user_id" not in op_fields and "athlete_id" not in op_fields and "plan_id" not in op_fields


def test_proposal_tool_uses_closure_identity(monkeypatch):
    seen = {}

    def fake_impl(*, user_id, ctx, operations, rationale):
        seen.update(user_id=user_id, ctx=ctx, operations=operations)
        from services.coach_tools.base import ToolResult

        return ToolResult(tool_call_id="", name="propose_schedule_change", status="success")

    monkeypatch.setattr("services.coach_tools.proposal_tools.propose_schedule_change_impl", fake_impl)
    ctx = ProposalContext(thread_id=5, plan_id=9, today=dt.date(2026, 9, 23))
    tool = next(t for t in build_tools(user_id=1, kb_api_key="k", proposals=ctx) if t.name == "propose_schedule_change")
    tool.invoke(
        {
            "operations": [{"op": "move", "workout_id": 3, "target_week": 4, "target_day": "Monday", "user_id": 42}],
            "rationale": "travel",
        }
    )
    assert seen["user_id"] == 1
    assert seen["ctx"] is ctx
    assert seen["operations"] == [{"op": "move", "workout_id": 3, "target_week": 4, "target_day": "Monday"}]


def _get_week_with_ctx(today, plan):
    ctx = ProposalContext(thread_id=5, plan_id=9, today=today)
    tool = next(t for t in build_tools(user_id=1, kb_api_key="k", proposals=ctx) if t.name == "get_week")
    with (
        patch("db.get_active_plan", return_value=plan),
        patch("services.coach_tools.plan_tools.get_week_impl") as mock_impl,
    ):
        mock_impl.return_value.__dict__ = {}
        tool.invoke({})
    return mock_impl


def test_get_week_default_uses_monday_aligned_week_with_context():
    # start 2026-09-09 is a Wednesday -> week 1 starts Mon 2026-09-07; Mon 2026-09-14 is week 2
    # (db.compute_current_week would say week 1: only 5 days since the start date).
    plan = {"id": 9, "start_date": "2026-09-09", "total_weeks": 12, "current_week": 1}
    mock_impl = _get_week_with_ctx(dt.date(2026, 9, 14), plan)
    mock_impl.assert_called_once_with(user_id=1, week_number=2)


def test_get_week_default_is_clamped_to_plan_weeks():
    plan = {"id": 9, "start_date": "2026-09-09", "total_weeks": 12, "current_week": 1}
    assert _get_week_with_ctx(dt.date(2026, 9, 1), plan).call_args.kwargs["week_number"] == 1
    assert _get_week_with_ctx(dt.date(2027, 9, 1), plan).call_args.kwargs["week_number"] == 12


def test_get_week_explicit_week_wins_over_context_default():
    ctx = ProposalContext(thread_id=5, plan_id=9, today=dt.date(2026, 9, 14))
    tool = next(t for t in build_tools(user_id=1, kb_api_key="k", proposals=ctx) if t.name == "get_week")
    with patch("services.coach_tools.plan_tools.get_week_impl") as mock_impl:
        mock_impl.return_value.__dict__ = {}
        tool.invoke({"week_number": 5})
    mock_impl.assert_called_once_with(user_id=1, week_number=5)


def test_get_week_default_without_context_is_unchanged():
    tool = next(t for t in build_tools(user_id=1, kb_api_key="k") if t.name == "get_week")
    with patch("services.coach_tools.plan_tools.get_week_impl") as mock_impl:
        mock_impl.return_value.__dict__ = {}
        tool.invoke({})
    mock_impl.assert_called_once_with(user_id=1, week_number=None)


def test_rebuild_tool_absent_without_context_and_present_with_it():
    assert "propose_rebuild_week" not in {t.name for t in build_tools(user_id=1, kb_api_key="k")}
    ctx = ProposalContext(thread_id=5, plan_id=9, today=dt.date(2026, 9, 24))
    tool = next(t for t in build_tools(user_id=1, kb_api_key="k", proposals=ctx) if t.name == "propose_rebuild_week")
    assert set(tool.args_schema.model_fields) == {
        "week",
        "fatigue_level",
        "reason",
        "available_days",
        "long_run_day",
        "has_gym_access",
        "use_treadmill",
    }


def test_rebuild_tool_uses_closure_identity(monkeypatch):
    seen = {}

    def fake_impl(**kwargs):
        seen.update(kwargs)
        from services.coach_tools.base import ToolResult

        return ToolResult(tool_call_id="", name="propose_rebuild_week", status="success")

    monkeypatch.setattr("services.coach_tools.proposal_tools.propose_rebuild_week_impl", fake_impl)
    ctx = ProposalContext(thread_id=5, plan_id=9, today=dt.date(2026, 9, 24))
    tool = next(t for t in build_tools(user_id=1, kb_api_key="k", proposals=ctx) if t.name == "propose_rebuild_week")
    tool.invoke({"week": 4, "fatigue_level": "hard", "reason": "legs heavy", "available_days": ["Tuesday"]})
    assert seen["user_id"] == 1 and seen["ctx"] is ctx and seen["week"] == 4
    assert seen["available_days"] == ["Tuesday"]
