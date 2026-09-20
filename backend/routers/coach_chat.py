"""Coach Chat endpoints — streaming, turn lifecycle, and legacy compatibility."""

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel

from config import settings
from db import (
    get_active_plan,
    get_all_grounding_content,
    get_matches_for_review,
    get_plan_workouts,
    verify_session,
)
from services.coach_prompts import (
    COACH_SYSTEM_INSTRUCTION,
    COACH_VI_LANGUAGE_INSTRUCTION,
    is_vietnamese_request,
)
from services.pacing_calculator import resolve_zone2_pace

router = APIRouter(tags=["coach-chat"])


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    # No identity, profile, plan or API-key fields: /api/coach/chat resolves
    # all of those from the session user.
    messages: list[ChatMessage]
    lang: str | None = None


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


@router.post("/api/coach/chat")
async def coach_chat(request: ChatRequest, user: dict[str, Any] = Depends(get_current_user)):
    """
    Query Gemini model grounded with the distilled knowledge base.
    Profile, active plan, recent activities and Gemini key are resolved from
    the session user -- never from the request body.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Message history cannot be empty.")

    # 1. Fetch grounding content
    grounding_docs = get_all_grounding_content()
    grounding_context = ""

    if not grounding_context and grounding_docs:
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

    # 2. Setup system instructions
    user_id = user["id"]
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

    # 3. Dynamic watch activities & execution quality grounding
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
        print(f"[Chat] Warning loading recent activities: {exc}")

    vi_rule = ""
    if is_vietnamese_request(lang=request.lang, messages=request.messages):
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
            for msg in request.messages:
                role = "user" if msg.role == "user" else "model"
                formatted_contents.append({"role": role, "parts": [{"text": msg.content}]})

            client = genai.Client(api_key=model_api_key)

            import asyncio

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=formatted_contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=full_system_prompt,
                    thinking_config=genai_types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL),
                ),
            )
            return {"role": "assistant", "content": response.text}
        except Exception as e:
            print(f"[Chat][Gemini] FAILED: {type(e).__name__}")

    # Fallback response without fabricated offline claims
    return {
        "role": "assistant",
        "content": "Coach Uphill is currently unavailable. Please verify your Gemini API key configuration in settings.",
    }
