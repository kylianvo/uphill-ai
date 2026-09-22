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
