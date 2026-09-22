from services.coach_tools.base import ToolResult


def test_tool_result_success_shape():
    r = ToolResult(
        tool_call_id="call_1", name="get_week", status="success", card_type="week_schedule", card_data={"a": 1}
    )
    assert r.status == "success"
    assert r.error is None


def test_tool_result_error_shape():
    r = ToolResult(tool_call_id="call_2", name="get_week", status="error", error="no_active_plan")
    assert r.card_data is None
    assert r.error == "no_active_plan"
