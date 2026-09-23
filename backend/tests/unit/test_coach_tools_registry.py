from unittest.mock import patch

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
