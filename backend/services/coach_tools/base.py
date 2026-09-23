"""Shared result type for Coach Chat tool executions."""

import datetime
import decimal
import uuid
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class ToolResult:
    """Normalized outcome of one tool execution -- feeds both the SSE
    tool_result event's card_data and the ToolMessage content sent back
    to the model."""

    tool_call_id: str
    name: str
    status: Literal["success", "error"]
    card_type: str | None = None
    card_data: dict[str, Any] | None = None
    error: str | None = None
    clarify: dict[str, Any] | None = None


def json_safe(value: Any) -> Any:
    """Recursively convert a value (row dict, list, or scalar) into
    something json.dumps can serialize: datetime/date -> isoformat string,
    Decimal -> float, UUID -> str, everything else unchanged.

    Needed because card_data is json.dumps-ed into chat_messages.tool_calls_json
    and the SSE stream, and DB rows can carry datetime/Decimal/UUID values."""
    if isinstance(value, datetime.datetime | datetime.date):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value
