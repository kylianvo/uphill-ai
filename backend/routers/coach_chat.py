"""Coach Chat endpoints — streaming, turn lifecycle, and legacy compatibility."""

import asyncio
import json
from dataclasses import asdict
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel, Field

import db
from config import settings
from db import (
    ChatInProgressError,
    CoachChatError,
    get_active_plan,
    get_all_grounding_content,
    get_matches_for_review,
    get_plan_workouts,
    verify_session,
)
from log_utils import get_logger
from services import coach_chat, schedule_proposals
from services.coach_graph import AppEvent
from services.coach_prompts import (
    COACH_SYSTEM_INSTRUCTION,
    COACH_VI_LANGUAGE_INSTRUCTION,
    is_vietnamese_request,
)
from services.training_rules import resolve_zone2_pace

logger = get_logger(__name__)

router = APIRouter(tags=["coach-chat"])


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    # Backward compatible with legacy caller patterns
    messages: list[ChatMessage] | None = None
    message: str | None = None
    history: list[dict[str, Any]] | None = None
    lang: str | None = None
    # Body-provided identity/key fields are explicitly ignored for security
    user_profile: dict[str, Any] | None = None
    context_data: dict[str, Any] | None = None


class ChatStreamRequest(BaseModel):
    request_id: str = Field(..., description="Client-generated unique UUID string for turn deduplication")
    message: str | None = Field(None, description="Athlete message for a new turn")
    retry_of: str | None = Field(None, description="Root turn UUID to retry")
    lang: str = Field("en", description="Language ('en' or 'vi')")
    client_today: str | None = Field(
        None, description="Athlete's local date YYYY-MM-DD (clamped server-side to ±1 day)"
    )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token missing or invalid.")
    token = authorization.split(" ")[1]
    user = verify_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    return user


def _z2_min_for(user: dict[str, Any]) -> str:
    return resolve_zone2_pace(user.get("zone2_pace_min"), user.get("zone2_pace_max"), user.get("goal_type"))[0]


def _z2_max_for(user: dict[str, Any]) -> str:
    return resolve_zone2_pace(user.get("zone2_pace_min"), user.get("zone2_pace_max"), user.get("goal_type"))[1]


# ---------------------------------------------------------------------------
# Streaming Endpoint (SSE)
# ---------------------------------------------------------------------------


@router.post("/api/coach/chat/stream")
async def coach_chat_stream(
    request: ChatStreamRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Authenticated SSE endpoint streaming tokens, status, citations, and recovery events.

    Runs pre-stream validation (UUID check, mutual exclusion, length limits, quotas).
    """
    # 1. Validate request_id format
    try:
        req_uuid = UUID(request.request_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="request_id must be a valid UUID.",
        )

    # 2. Validate mutual exclusion of message and retry_of
    has_msg = bool(request.message and request.message.strip())
    has_retry = bool(request.retry_of and request.retry_of.strip())

    if has_msg == has_retry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either message or retry_of must be specified, not both.",
        )

    # 3. Validate input length
    if has_msg and len(request.message) > settings.COACH_CHAT_MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Message exceeds maximum allowed length of {settings.COACH_CHAT_MAX_INPUT_CHARS} characters.",
        )

    # 4. SSE Stream generator with idle heartbeat framing
    async def sse_event_generator():
        event_queue = asyncio.Queue()
        stop_sentinel = object()

        async def run_producer():
            try:
                req_dict = {
                    "request_id": req_uuid,
                    "message": request.message.strip() if request.message else None,
                    "retry_of": request.retry_of.strip() if request.retry_of else None,
                    "lang": request.lang or "en",
                    "client_today": request.client_today,
                }
                async for app_event in coach_chat.run_turn(user=user, request=req_dict):
                    await event_queue.put(app_event)
            except CoachChatError as err:
                logger.warning(f"Turn admission/domain error: {err.code}")
                from services.coach_graph import ErrorEvent

                await event_queue.put(ErrorEvent(code=err.code, message=err.message))
            except Exception as exc:
                logger.error(f"Unexpected turn stream error: {type(exc).__name__}: {exc}", exc_info=True)
                from services.coach_graph import ErrorEvent

                await event_queue.put(ErrorEvent(code="coach_upstream_error"))
            finally:
                await event_queue.put(stop_sentinel)

        producer_task = asyncio.create_task(run_producer())

        try:
            while True:
                try:
                    # 10s idle heartbeat window
                    item = await asyncio.wait_for(event_queue.get(), timeout=10.0)
                    if item is stop_sentinel:
                        break
                    if isinstance(item, AppEvent):
                        event_type = item.type
                        payload = json.dumps(asdict(item))
                        yield f"event: {event_type}\ndata: {payload}\n\n"
                except TimeoutError:
                    # Emit heartbeat comment to keep proxy connection alive
                    yield ": heartbeat\n\n"
        finally:
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except asyncio.CancelledError:
                    pass

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Conversation & Lifecycle Endpoints
# ---------------------------------------------------------------------------


@router.get("/api/coach/chat/thread")
async def get_chat_thread(
    before_id: int | None = Query(None, description="Fetch messages older than before_id"),
    limit: int = Query(50, ge=1, le=50, description="Page limit (max 50)"),
    user: dict[str, Any] = Depends(get_current_user),
):
    """Retrieve chronologically ordered messages in the athlete's thread with pagination cursor."""
    user_id = user["id"]
    data = db.get_chat_thread_paginated(user_id=user_id, before_id=before_id, limit=limit)
    statuses = db.get_chat_proposal_statuses(user_id, [m["id"] for m in data["messages"]])
    data["proposals"] = {str(pid): s for pid, s in statuses.items()}
    return data


class ProposalApplyRequest(BaseModel):
    client_today: str | None = None


@router.post("/api/coach/chat/proposals/{proposal_id}/apply")
def apply_chat_proposal(
    proposal_id: int,
    body: ProposalApplyRequest | None = None,
    user: dict[str, Any] = Depends(get_current_user),
):
    """The Apply button is the only confirmation (roadmap decision 9)."""
    status_code, payload = schedule_proposals.apply_proposal(
        user["id"], proposal_id, body.client_today if body else None
    )
    if status_code == 200:
        plan_id = payload.pop("plan_id")
        payload["workouts"] = get_plan_workouts(plan_id)
        return payload
    if status_code == 404:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return JSONResponse(status_code=status_code, content=payload)


@router.post("/api/coach/chat/proposals/{proposal_id}/discard")
def discard_chat_proposal(proposal_id: int, user: dict[str, Any] = Depends(get_current_user)):
    status_code, payload = schedule_proposals.discard_proposal(user["id"], proposal_id)
    if status_code == 404:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return payload


@router.get("/api/coach/chat/turns/{request_id}")
async def get_chat_turn_status(
    request_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Retrieve execution status and result message ID for an owned turn."""
    user_id = user["id"]
    try:
        req_uuid = UUID(request_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request_id format.")

    turn = db.get_chat_turn(user_id=user_id, request_id=req_uuid)
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found.")
    if turn["status"] == "cleared":
        raise HTTPException(status_code=410, detail="Turn was cleared.")

    return {
        "request_id": str(turn["request_id"]),
        "status": turn["status"],
        "result_message_id": turn.get("result_message_id"),
        "attempt_number": turn.get("attempt_number", 1),
    }


@router.get("/api/coach/chat/messages/{message_id}/sources")
async def get_chat_message_sources(
    message_id: int,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Fetch retained retrieval evidence and citations for an owned message."""
    user_id = user["id"]
    sources = db.get_chat_message_sources(message_id=message_id, user_id=user_id)
    if not sources:
        raise HTTPException(status_code=404, detail="Message sources not found.")
    return sources


@router.delete("/api/coach/chat/thread")
async def clear_chat_thread(
    user: dict[str, Any] = Depends(get_current_user),
):
    """Clear athlete's conversation messages and summary. Quotas and accounting remain intact."""
    user_id = user["id"]
    try:
        db.clear_chat_thread(user_id=user_id)
        return {"status": "cleared"}
    except ChatInProgressError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot clear thread while a turn is active.",
        )


# ---------------------------------------------------------------------------
# Legacy Endpoint (Backward Compatibility)
# ---------------------------------------------------------------------------


@router.post("/api/coach/chat")
async def coach_chat_legacy(
    request: ChatRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Legacy unmigrated chat endpoint.

    Profile, active plan, recent activities and Gemini key are resolved exclusively
    from the authenticated session user -- never from the request body.
    """
    messages_list = request.messages or []
    if not messages_list and request.message:
        messages_list = [ChatMessage(role="user", content=request.message)]

    if not messages_list:
        raise HTTPException(status_code=400, detail="Message history cannot be empty.")

    user_id = user["id"]

    # 1. Fetch grounding content
    grounding_docs = get_all_grounding_content()
    grounding_context = ""
    if grounding_docs:
        context_parts = []
        for idx, doc in enumerate(grounding_docs, 1):
            truncated_content = doc["content"][:15000]
            context_parts.append(
                f"[Document #{idx}] Title: {doc['title']} | Type: {doc['type'].upper()}\n"
                f"Content: {truncated_content}"
            )
        grounding_context = (
            "\n\n=== GROUNDING REFERENCE DATABASE (Use this to ground answers and cite names when relevant) ===\n"
            + "\n\n".join(context_parts)
            + "\n=======================================================\n"
        )

    # 2. Setup system instructions from authenticated user only
    plan = get_active_plan(user_id)
    profile = {
        "age": user.get("age"),
        "current_weekly_km": user.get("current_weekly_km"),
        "max_hr": user.get("max_hr"),
        "resting_hr": user.get("resting_hr"),
        "aet_hr": user.get("aet_hr"),
        "ant_hr": user.get("ant_hr"),
        "use_treadmill": bool(plan and plan.get("use_treadmill")),
        "zone2_pace_min": _z2_min_for(user),
        "zone2_pace_max": _z2_max_for(user),
    }
    profile_summary = f"\nUser Running Profile: {profile}"
    context_summary = ""
    if plan:
        plan_context = {
            "race_name": plan["race_name"],
            "race_date": plan["race_date"],
            "goal_type": plan["goal_type"],
            "total_weeks": plan["total_weeks"],
            "workouts": get_plan_workouts(plan["id"]),
        }
        context_summary = f"\nContext/Activity Data: {plan_context}"

    # 3. Dynamic watch activities
    recent_activity_context = ""
    try:
        until = date.today() + timedelta(days=1)
        since = until - timedelta(days=14)
        recent_matches = get_matches_for_review(user_id, since, until)
        if recent_matches:
            act_lines = ["\n=== RECENT WATCH ACTIVITIES & EXECUTION QUALITY ==="]
            for act in recent_matches[-8:]:
                dist = f"{act['distance_km']:.1f}km" if act.get("distance_km") else f"{act.get('sets') or 'N/A'} sets"
                dur = f"{round((act.get('duration_seconds') or 0)/60)}m"
                hr = f"avg HR {act['avg_hr']} bpm" if act.get("avg_hr") else ""
                q_grade = (
                    f"Quality: {act.get('quality_grade')} ({act.get('quality_score')}%)"
                    if act.get("quality_score") is not None
                    else ""
                )
                w_title = act.get("workout_title") or "Unplanned / Free session"
                details = act.get("quality_details") or {}
                takeaways = "; ".join(details.get("takeaways", [])) if isinstance(details, dict) else ""
                notes = f" | Takeaways: {takeaways}" if takeaways else ""
                act_lines.append(
                    f"- {str(act.get('start_time'))[:10]}: '{w_title}' ({dist}, {dur}, {hr}) {q_grade}{notes}"
                )
            act_lines.append("===================================================")
            recent_activity_context = "\n".join(act_lines)
    except Exception as exc:
        logger.warning(f"[Chat] Warning loading recent activities: {exc}")

    vi_rule = ""
    if is_vietnamese_request(lang=request.lang, messages=messages_list):
        vi_rule = f"\n\n{COACH_VI_LANGUAGE_INSTRUCTION}"

    full_system_prompt = (
        f"{COACH_SYSTEM_INSTRUCTION}"
        f"{vi_rule}"
        f"{grounding_context}"
        f"{profile_summary}"
        f"{context_summary}"
        f"{recent_activity_context}"
        f"\n\nNote: If the user asks questions referring to uploaded documents or materials, retrieve answers from the GROUNDING REFERENCE DATABASE and state which document/link you got it from."
    )

    model_api_key = user.get("gemini_api_key") or settings.GEMINI_API_KEY

    if model_api_key:
        try:
            formatted_contents = []
            for msg in messages_list[-20:]:  # Cap history to 20 items
                role = "user" if msg.role == "user" else "model"
                formatted_contents.append({"role": role, "parts": [{"text": msg.content}]})

            client = genai.Client(api_key=model_api_key)

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=formatted_contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=full_system_prompt,
                    thinking_config=genai_types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL),
                ),
            )
            reply_text = response.text or ""
            return {
                "role": "assistant",
                "content": reply_text,
                "reply": reply_text,
                "sources": [],
            }
        except Exception as e:
            logger.warning(f"[Chat][Gemini] FAILED: {type(e).__name__}")

    raise HTTPException(
        status_code=503,
        detail="Coach Uphill is currently unavailable. Please verify your Gemini API key configuration in settings.",
    )
