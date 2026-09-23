"""Shared result type for Coach Chat tool executions."""

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
