"""Coach Chat lifecycle, turn runner, and call accounting orchestration."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import db
from config import settings
from db import CoachChatError
from log_utils import get_logger
from services import coach_context, kb_retrieval, observability
from services.coach_graph import (
    AppEvent,
    CitationsEvent,
    DoneEvent,
    ErrorEvent,
    StatusEvent,
    TokenEvent,
    TurnState,
    astream_turn_graph,
    build_graph,
)
from services.coach_model import (
    ChatMessage,
    CoachModel,
    ModelEvent,
    ModelRequest,
)
from services.observability import Usage

logger = get_logger(__name__)


async def track_chat_call(
    call_id: UUID,
    request_id: UUID,
    feature: str,
    model_name: str,
    model_adapter: CoachModel,
    model_request: ModelRequest,
) -> AsyncIterator[ModelEvent]:
    """Execute a model stream within a reserved and durable chat_llm_calls row.

    Reserves the call row prior to execution, measures latency, extracts usage,
    calculates cost via observability.cost_usd, and finalizes call row in finally.
    """
    db.reserve_chat_call(
        call_id=call_id,
        request_id=request_id,
        feature=feature,
        model=model_name,
    )
    start_time = time.perf_counter()
    status = "ok"
    last_usage: Usage | None = None

    try:
        async for event in model_adapter.stream(model_request):
            if event.kind == "usage" and event.usage is not None:
                last_usage = event.usage
            yield event
    except Exception:
        status = "error"
        raise
    finally:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        usage_known = last_usage is not None

        input_tokens = last_usage.input_tokens if last_usage else 0
        output_tokens = last_usage.output_tokens if last_usage else 0
        thinking_tokens = last_usage.thinking_tokens if last_usage else 0
        cached_tokens = last_usage.cached_tokens if last_usage else 0

        cost = None
        if last_usage is not None:
            calc_cost = observability.cost_usd(model_name, last_usage)
            if calc_cost is not None:
                cost = Decimal(str(calc_cost))

        final_status = status if usage_known else ("interrupted" if status == "ok" else "error")

        db.finish_chat_call(
            call_id=call_id,
            status=final_status,
            usage_known=usage_known,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            cached_tokens=cached_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )


async def _update_thread_summary(
    user_id: int,
    thread_id: int,
    through_message_id: int,
    model: CoachModel,
    request_id: UUID,
) -> None:
    """Generate summary of recent thread messages up to through_message_id and CAS update thread."""
    try:
        thread = db.get_or_create_chat_thread(user_id)
        expected_through = thread.get("summarized_through_id")
        if expected_through is not None and through_message_id <= expected_through:
            return

        recent_msgs = db.get_chat_thread_messages(user_id=user_id, limit=20)
        if not recent_msgs:
            return

        valid_msgs = [
            m
            for m in recent_msgs
            if m.get("status") == "ok"
            and (expected_through is None or m["id"] > expected_through)
            and m["id"] <= through_message_id
        ]
        if not valid_msgs:
            return

        formatted_lines = []
        for m in valid_msgs:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            formatted_lines.append(f"{role.capitalize()}: {content}")

        summary_input = "\n\n".join(formatted_lines)
        from services.coach_prompts import COACH_SUMMARY_INSTRUCTION

        summary_call_id = uuid4()
        model_req = ModelRequest(
            messages=(ChatMessage(role="user", content=summary_input),),
            system=COACH_SUMMARY_INSTRUCTION,
            max_output_tokens=512,
            call_id=summary_call_id,
        )

        summary_chunks: list[str] = []
        async for event in track_chat_call(
            call_id=summary_call_id,
            request_id=request_id,
            feature="chat_summary",
            model_name="gemini-3.8-flash",
            model_adapter=model,
            model_request=model_req,
        ):
            if event.kind == "text" and event.text:
                summary_chunks.append(event.text)

        summary_text = "".join(summary_chunks).strip()
        if summary_text:
            db.update_chat_thread_summary_cas(
                thread_id=thread_id,
                user_id=user_id,
                new_summary=summary_text,
                new_summarized_through_id=through_message_id,
                expected_summarized_through_id=expected_through,
            )
    except Exception as exc:
        logger.warning(f"Thread summary failed: {exc}")


async def run_turn(
    user: dict[str, Any],
    request: dict[str, Any],
    model: CoachModel | None = None,
) -> AsyncIterator[AppEvent]:
    """Execute a single Coach Chat turn with admission, locking, streaming and recovery."""
    user_id = user["id"]
    req_raw = request.get("request_id") or uuid4()
    req_uuid = UUID(str(req_raw)) if not isinstance(req_raw, UUID) else req_raw
    message = request.get("message")
    retry_of = request.get("retry_of")
    lang = request.get("lang") or "en"

    with db.chat_turn_lock(user_id):
        thread = db.get_or_create_chat_thread(user_id)
        thread_id = request.get("thread_id") or thread["id"]

        admission = db.admit_chat_turn(
            request_id=req_uuid,
            user_id=user_id,
            thread_id=thread_id,
            message=message,
            retry_of=retry_of,
        )

        if admission["kind"] == "replay":
            msg_id = admission.get("result_message_id")
            if msg_id:
                msg = db.get_chat_message(msg_id, user_id=user_id)
                if msg and msg.get("status") == "ok":
                    yield StatusEvent(step="retrieving", request_id=str(req_uuid))
                    yield StatusEvent(step="generating", request_id=str(req_uuid))
                    raw_cit = msg.get("citations")
                    citations = json.loads(raw_cit) if isinstance(raw_cit, str) else (raw_cit or [])
                    yield CitationsEvent(
                        citations=citations,
                        evidence_status="available" if citations else "empty",
                    )
                    if msg.get("content"):
                        yield TokenEvent(text=msg["content"])
                    yield DoneEvent(
                        request_id=str(req_uuid),
                        message_id=msg_id,
                        replayed=True,
                    )
                    return
            yield ErrorEvent(code=admission.get("status", "unknown_error"))
            return

        question = ""
        if admission["kind"] == "new":
            db.append_chat_message(
                thread_id=thread_id,
                role="user",
                content=message or "",
                lang=lang,
                status="ok",
            )
            question = message or ""
        elif admission["kind"] == "retry":
            recent_msgs = db.get_chat_thread_messages(user_id=user_id, limit=10)
            for m in reversed(recent_msgs):
                if m.get("role") == "user":
                    question = m.get("content", "")
                    break

        try:
            assistant_msg_id = db.append_chat_message(
                thread_id=thread_id,
                role="assistant",
                content="",
                lang=lang,
                status="interrupted",
            )
            db.update_chat_turn_status(request_id=req_uuid, status="active", result_message_id=assistant_msg_id)

            if model is None:
                from services.coach_model import GeminiCoachModel

                api_key = user.get("gemini_api_key") or settings.GEMINI_API_KEY
                model = GeminiCoachModel(api_key=api_key)
        except Exception:
            db.finish_chat_turn(request_id=req_uuid, status="error")
            raise

        def _retrieve_kb(q: str):
            api_key = user.get("gemini_api_key") or settings.GEMINI_API_KEY
            if api_key:
                return kb_retrieval.search_principles(query=q, api_key=api_key)
            return []

        graph = build_graph(model=model, retrieve_fn=_retrieve_kb)
        call_id = uuid4()
        initial_state: TurnState = {
            "user_id": user_id,
            "thread_id": thread_id,
            "request_id": str(req_uuid),
            "call_id": call_id,
            "question": question,
            "lang": lang,
            "context": coach_context.build_chat_context(user_id=user_id, question=question, thread_id=thread_id),
        }

        accumulated: list[str] = []
        last_persisted_time = time.monotonic()
        last_persisted_len = 0
        final_citations: list[dict[str, Any]] = []

        try:
            async with asyncio.timeout(settings.COACH_CHAT_TURN_TIMEOUT_SECONDS):
                async for event in astream_turn_graph(graph, initial_state):
                    if isinstance(event, TokenEvent):
                        accumulated.append(event.text)
                        curr_len = sum(len(t) for t in accumulated)
                        now = time.monotonic()
                        if (curr_len - last_persisted_len >= 256) or (now - last_persisted_time >= 1.0):
                            db.update_chat_message(assistant_msg_id, content="".join(accumulated))
                            last_persisted_len = curr_len
                            last_persisted_time = now
                        yield event
                    elif isinstance(event, CitationsEvent):
                        final_citations = event.citations
                        yield event
                    else:
                        yield event

            full_text = "".join(accumulated)

            # 1. Finalize message in DB
            db.update_chat_message(
                message_id=assistant_msg_id,
                content=full_text,
                status="ok",
                citations=final_citations,
            )

            # 2. Finalize turn in DB
            db.finish_chat_turn(
                request_id=req_uuid,
                status="ok",
                result_message_id=assistant_msg_id,
            )

            # 3. Emit done event (only after successful DB finalization)
            yield DoneEvent(
                request_id=str(req_uuid),
                message_id=assistant_msg_id,
                replayed=False,
            )

            # 4. Trigger bounded summary update under same lock
            try:
                async with asyncio.timeout(settings.COACH_CHAT_SUMMARY_TIMEOUT_SECONDS):
                    await _update_thread_summary(
                        user_id=user_id,
                        thread_id=thread_id,
                        through_message_id=assistant_msg_id,
                        model=model,
                        request_id=req_uuid,
                    )
            except Exception as exc:
                logger.warning(f"Summary update failed or timed out: {exc}")

        except (asyncio.CancelledError, GeneratorExit):
            full_text = "".join(accumulated)
            db.update_chat_message(assistant_msg_id, content=full_text, status="interrupted")
            db.finish_chat_turn(request_id=req_uuid, status="interrupted", result_message_id=assistant_msg_id)
            raise
        except TimeoutError:
            full_text = "".join(accumulated)
            db.update_chat_message(assistant_msg_id, content=full_text, status="interrupted", error_code="chat_timeout")
            db.finish_chat_turn(request_id=req_uuid, status="interrupted", result_message_id=assistant_msg_id)
            yield ErrorEvent(code="chat_timeout")
        except CoachChatError as exc:
            full_text = "".join(accumulated)
            db.update_chat_message(assistant_msg_id, content=full_text, status="error", error_code=exc.code)
            db.finish_chat_turn(request_id=req_uuid, status="error", result_message_id=assistant_msg_id)
            yield ErrorEvent(code=exc.code, message=exc.message)
        except Exception:
            full_text = "".join(accumulated)
            db.update_chat_message(
                assistant_msg_id, content=full_text, status="error", error_code="coach_upstream_error"
            )
            db.finish_chat_turn(request_id=req_uuid, status="error", result_message_id=assistant_msg_id)
            yield ErrorEvent(code="coach_upstream_error")
