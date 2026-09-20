"""Typed LangGraph retrieve-generate runner and application event projection."""

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any, Literal, TypedDict
from uuid import UUID, uuid4

from langgraph.graph import END, START, StateGraph

from log_utils import get_logger
from services import coach_context, coach_prompts
from services.coach_model import (
    ChatMessage,
    CoachModel,
    ModelRequest,
    ToolCallsNotSupportedError,
)
from services.observability import Usage

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Typed Turn State
# ---------------------------------------------------------------------------


class TurnState(TypedDict, total=False):
    # Request & session identity
    user_id: int
    thread_id: int | None
    request_id: str
    call_id: UUID
    question: str
    lang: str
    messages: list[ChatMessage]
    max_output_tokens: int

    # Server trusted context & prompt assembly
    context: dict[str, Any]
    system_prompt: str
    prompt_name: str
    prompt_version: str
    prompt_source: str

    # Retrieval outputs
    evidence: list[dict[str, Any]]
    evidence_status: Literal["available", "empty", "unavailable"]

    # Generation outputs
    reply_text: str
    citations: list[dict[str, Any]]
    usage: Usage | None
    status: str
    error_code: str | None


# ---------------------------------------------------------------------------
# Application Event Union
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StatusEvent:
    step: Literal["retrieving", "generating"]
    request_id: str
    type: str = "status"


@dataclass(frozen=True)
class TokenEvent:
    text: str
    type: str = "token"


@dataclass(frozen=True)
class CitationsEvent:
    citations: list[dict[str, Any]]
    evidence_status: Literal["available", "empty", "unavailable"]
    type: str = "citations"


@dataclass(frozen=True)
class DoneEvent:
    request_id: str
    message_id: int | None = None
    replayed: bool = False
    type: str = "done"


@dataclass(frozen=True)
class ErrorEvent:
    code: str
    message: str | None = None
    type: str = "error"


AppEvent = StatusEvent | TokenEvent | CitationsEvent | DoneEvent | ErrorEvent


def _emit_custom(writer: Any, event: dict[str, Any]) -> None:
    """Safely emit an event to the LangGraph stream writer."""
    if writer is not None and callable(writer):
        try:
            writer(event)
            return
        except Exception:
            pass
    try:
        from langgraph.config import get_stream_writer

        w = get_stream_writer()
        if w is not None and callable(w):
            w(event)
    except Exception:
        pass


def parse_app_event(data: Any) -> AppEvent | None:
    """Validate and convert custom event dict into typed AppEvent."""
    if not isinstance(data, dict):
        return None
    evt_type = data.get("type")
    if evt_type == "status":
        step = data.get("step")
        req_id = str(data.get("request_id", ""))
        if step in ("retrieving", "generating"):
            return StatusEvent(step=step, request_id=req_id)
    elif evt_type == "token":
        text = data.get("text", "")
        return TokenEvent(text=str(text))
    elif evt_type == "citations":
        citations = list(data.get("citations") or [])
        status = data.get("evidence_status", "empty")
        if status not in ("available", "empty", "unavailable"):
            status = "empty"
        return CitationsEvent(citations=citations, evidence_status=status)
    elif evt_type == "done":
        req_id = str(data.get("request_id", ""))
        msg_id = data.get("message_id")
        replayed = bool(data.get("replayed", False))
        return DoneEvent(request_id=req_id, message_id=msg_id, replayed=replayed)
    elif evt_type == "error":
        code = str(data.get("code", "unknown_error"))
        msg = data.get("message")
        return ErrorEvent(code=code, message=str(msg) if msg else None)
    return None


# ---------------------------------------------------------------------------
# Node Factories & Graph Builder
# ---------------------------------------------------------------------------


def _make_retrieve_node(
    retrieve_fn: Callable[..., Any] | None,
    assemble_context_fn: Callable[..., Any] | None,
):
    async def retrieve_node(state: TurnState, writer: Any = None) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        _emit_custom(writer, {"type": "status", "step": "retrieving", "request_id": req_id})

        question = state.get("question", "")
        lang = state.get("lang", "en")
        evidence: list[dict[str, Any]] = []
        evidence_status: Literal["available", "empty", "unavailable"] = "empty"

        if retrieve_fn is not None:
            try:
                res = retrieve_fn(question)
                if asyncio.iscoroutine(res):
                    res = await res
                evidence = list(res or [])
                evidence_status = "available" if len(evidence) > 0 else "empty"
            except Exception as exc:
                logger.warning(f"KB retrieval failed/unavailable: {exc}")
                evidence = []
                evidence_status = "unavailable"
        else:
            evidence_status = "empty"

        # Context assembly & prompt compilation
        context = dict(state.get("context") or {})
        if assemble_context_fn is not None and not context:
            try:
                user_id = state.get("user_id")
                thread_id = state.get("thread_id")
                assembled = assemble_context_fn(
                    user_id=user_id,
                    question=question,
                    thread_id=thread_id,
                    retrieval_evidence=evidence,
                )
                if asyncio.iscoroutine(assembled):
                    assembled = await assembled
                context = dict(assembled or {})
            except Exception as exc:
                logger.warning(f"Context assembly failed: {exc}")

        context["evidence"] = evidence

        # Prompt template with local fallback
        prompt_tpl = coach_prompts.get_coach_prompt_template(name="coach_chat")

        system_prompt = coach_prompts.compile_coach_prompt(
            template=prompt_tpl,
            lang=lang,
            context=context,
            evidence=evidence,
            messages=state.get("messages"),
        )

        _emit_custom(
            writer,
            {
                "type": "citations",
                "citations": [],
                "evidence_status": evidence_status,
            },
        )

        return {
            "evidence": evidence,
            "evidence_status": evidence_status,
            "context": context,
            "system_prompt": system_prompt,
            "prompt_name": prompt_tpl.name,
            "prompt_version": prompt_tpl.version,
            "prompt_source": prompt_tpl.source,
        }

    return retrieve_node


def _make_generate_node(model: CoachModel):
    async def generate_node(state: TurnState, writer: Any = None) -> dict[str, Any]:
        req_id = state.get("request_id", "")
        _emit_custom(writer, {"type": "status", "step": "generating", "request_id": req_id})

        call_id = state.get("call_id") or uuid4()
        messages_input = state.get("messages")
        if messages_input:
            msg_tuple = tuple(messages_input)
        else:
            msg_tuple = (ChatMessage(role="user", content=state.get("question", "")),)

        system_prompt = state.get("system_prompt", "")
        max_output_tokens = state.get("max_output_tokens", 2048)

        model_request = ModelRequest(
            messages=msg_tuple,
            system=system_prompt,
            max_output_tokens=max_output_tokens,
            call_id=call_id,
        )

        accumulated: list[str] = []
        final_usage: Usage | None = None

        stream_gen = model.stream(model_request)
        try:
            async for event in stream_gen:
                if event.kind == "text" and event.text:
                    accumulated.append(event.text)
                    _emit_custom(writer, {"type": "token", "text": event.text})
                elif event.kind == "usage":
                    final_usage = event.usage
                elif event.kind == "tool_call":
                    raise ToolCallsNotSupportedError("Tool calls are rejected in Coach Chat Foundation.")
        finally:
            if hasattr(stream_gen, "aclose"):
                await stream_gen.aclose()

        full_reply = "".join(accumulated)

        # Resolve citations against turn evidence
        evidence = state.get("evidence", [])
        citations = coach_context.resolve_citations(full_reply, evidence)

        _emit_custom(
            writer,
            {
                "type": "citations",
                "citations": citations,
                "evidence_status": state.get("evidence_status", "empty"),
            },
        )

        return {
            "reply_text": full_reply,
            "citations": citations,
            "usage": final_usage,
            "status": "ok",
        }

    return generate_node


def build_graph(
    model: CoachModel,
    retrieve_fn: Callable[..., Any] | None = None,
    assemble_context_fn: Callable[..., Any] | None = None,
):
    """Build and compile the linear retrieve-generate StateGraph without checkpointer."""
    workflow = StateGraph(TurnState)
    workflow.add_node("retrieve", _make_retrieve_node(retrieve_fn, assemble_context_fn))
    workflow.add_node("generate", _make_generate_node(model))
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


async def astream_turn_graph(
    graph: Any,
    initial_state: TurnState,
) -> AsyncIterator[AppEvent]:
    """Stream application events from graph execution.

    Uses stream_mode=['custom', 'updates'], version='v2'. Yields only validated AppEvents.
    Private state updates are consumed internally.
    """
    stream_iter = graph.astream(
        initial_state,
        stream_mode=["custom", "updates"],
        version="v2",
    )
    try:
        async for mode, payload in stream_iter:
            if mode == "custom":
                evt = parse_app_event(payload)
                if evt is not None:
                    yield evt
            elif mode == "updates":
                # Private internal state updates (never emitted directly)
                pass
    finally:
        if hasattr(stream_iter, "aclose"):
            await stream_iter.aclose()
