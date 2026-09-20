"""Coach Chat lifecycle, turn runner, and call accounting orchestration."""

import time
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any
from uuid import UUID

import db
from services import observability
from services.coach_model import CoachModel, ModelEvent, ModelRequest
from services.observability import Usage


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
