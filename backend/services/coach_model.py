"""Provider-neutral model boundary and Gemini adapter for Coach Chat."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from uuid import UUID

from services import observability
from services.observability import Usage


class CoachModelError(Exception):
    """Base exception for model adapter errors."""


class CoachModelUpstreamError(CoachModelError):
    """Upstream provider error without content-bearing messages."""

    def __init__(self, message: str, error_type: str | None = None) -> None:
        super().__init__(message)
        self.error_type = error_type or message


class ToolCallsNotSupportedError(CoachModelError):
    """Raised when model returns tool calls in Foundation phase."""


@dataclass(frozen=True)
class ChatMessage:
    role: str  # 'user' | 'assistant' | 'system'
    content: str


@dataclass(frozen=True)
class ModelRequest:
    messages: tuple[ChatMessage, ...]
    system: str
    max_output_tokens: int
    call_id: UUID


@dataclass(frozen=True)
class ModelEvent:
    kind: Literal["text", "usage", "tool_call"]
    text: str | None = None
    usage: Usage | None = None
    tool_call: dict[str, Any] | None = None


class CoachModel(Protocol):
    async def count_tokens(self, request: ModelRequest) -> int: ...
    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...
    async def close(self) -> None: ...


class FakeCoachModel:
    """Mock CoachModel for orchestration tests and non-Gemini unit tests."""

    def __init__(self, responses: list[ModelEvent] | None = None, token_count: int = 100) -> None:
        self.responses = responses or []
        self.token_count = token_count
        self.closed = False
        self.requests: list[ModelRequest] = []

    async def count_tokens(self, request: ModelRequest) -> int:
        return self.token_count

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        self.requests.append(request)
        for event in self.responses:
            yield event

    async def close(self) -> None:
        self.closed = True


class GeminiCoachModel:
    """ChatGoogleGenerativeAI adapter implementing CoachModel."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.8-flash",
        thinking_level: str | None = "low",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.thinking_level = thinking_level
        self._chat: Any = None
        self._closed = False

    def _get_chat(self) -> Any:
        if self._chat is None:
            from langchain_google_genai import ChatGoogleGenerativeAI

            # max_retries=0: SDK retries are disabled per spec
            self._chat = ChatGoogleGenerativeAI(
                model=self.model,
                api_key=self.api_key,
                max_retries=0,
                temperature=0.3,
            )
        return self._chat

    async def count_tokens(self, request: ModelRequest) -> int:
        """Estimate or count provider tokens for the assembled request."""
        chat = self._get_chat()
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        lc_messages = [SystemMessage(content=request.system)]
        for msg in request.messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                lc_messages.append(AIMessage(content=msg.content))

        if hasattr(chat, "get_num_tokens_from_messages"):
            return int(chat.get_num_tokens_from_messages(lc_messages))
        # Fallback character estimation if method unavailable
        total_chars = len(request.system) + sum(len(m.content) for m in request.messages)
        return max(1, total_chars // 4)

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        """Stream normalized model events inside a single canonical observability.generation scope."""
        chat = self._get_chat()
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        lc_messages = [SystemMessage(content=request.system)]
        for msg in request.messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                lc_messages.append(AIMessage(content=msg.content))

        with observability.generation(
            "generation",
            feature="coach_chat",
            model=self.model,
            metadata={"call_id": str(request.call_id)},
        ) as gen:
            try:
                stream_iter = chat.astream(lc_messages)
                async for chunk in stream_iter:
                    # 1. Check for tool calls (rejected in Foundation)
                    tool_calls = getattr(chunk, "tool_calls", None) or getattr(chunk, "tool_call_chunks", None)
                    if tool_calls:
                        raise ToolCallsNotSupportedError("Tool calls are not supported in foundation phase")

                    # 2. Exclude thinking blocks
                    kwargs = getattr(chunk, "additional_kwargs", {}) or {}
                    if "thinking" in kwargs or "thought" in kwargs:
                        # Thinking content excluded from client stream
                        pass

                    # 3. Extract text content
                    content = getattr(chunk, "content", None)
                    if isinstance(content, str) and content:
                        yield ModelEvent(kind="text", text=content)
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, str) and part:
                                yield ModelEvent(kind="text", text=part)
                            elif isinstance(part, dict) and part.get("type") == "text":
                                yield ModelEvent(kind="text", text=part.get("text", ""))

                    # 4. Check for usage metadata
                    usage_meta = getattr(chunk, "usage_metadata", None)
                    if not usage_meta and hasattr(chunk, "response_metadata"):
                        usage_meta = chunk.response_metadata.get("usage_metadata")

                    if usage_meta:
                        input_tokens = usage_meta.get("input_tokens") or 0
                        output_tokens = usage_meta.get("output_tokens") or 0
                        thinking_tokens = 0
                        if "output_token_details" in usage_meta:
                            thinking_tokens = usage_meta["output_token_details"].get("reasoning", 0)
                        cached_tokens = 0
                        if "input_token_details" in usage_meta:
                            cached_tokens = usage_meta["input_token_details"].get("cache_read", 0)

                        norm_usage = Usage(
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            thinking_tokens=thinking_tokens,
                            cached_tokens=cached_tokens,
                        )
                        gen.set_usage(norm_usage)
                        yield ModelEvent(kind="usage", usage=norm_usage)

            except ToolCallsNotSupportedError:
                raise
            except Exception as exc:
                err_type = type(exc).__name__
                raise CoachModelUpstreamError(err_type, error_type=err_type) from None

    async def close(self) -> None:
        self._closed = True
