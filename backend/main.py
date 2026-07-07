import os
import uuid as _uuid
from typing import Any

import google.generativeai as genai
import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from config import settings
from db import (
    add_source,
    create_or_get_user,
    create_plan,
    create_session,
    create_user_with_password,
    delete_session,
    delete_source,
    get_active_plan,
    get_all_grounding_content,
    get_all_knowledge_cards,
    get_block_completion,
    get_block_reviews,
    get_kb_chunk_count,
    get_knowledge_card_count,
    get_knowledge_topics,
    get_max_generated_week,
    get_plan_workouts,
    get_random_knowledge_cards,
    get_recent_plans,
    get_user_by_email,
    get_user_by_id,
    get_workout_type_count,
    get_workout_types,
    init_db,
    list_sources,
    mark_onboarding_complete,
    query_nutrition_catalog,
    save_block_review,
    save_workouts,
    set_plan_active,
    set_user_password,
    swap_workouts,
    update_onboarding_profile,
    update_user_profile,
    update_workout_log,
    verify_session,
)
from parsers.fit_parser import FitParser
from parsers.gpx_parser import GpxParser
from routers.analytics import router as analytics_router
from services.auth_service import hash_password, verify_password
from services.calendar_service import CalendarService
from services.gear_planner import GearParams, gear_planner
from services.nutrition_planner import NutritionParams, nutrition_planner
from services.pacing_calculator import PacingCalculator
from services.plan_generator import PlanGenerator
from services.rag_service import RagService
from services.training_rules import TrainingRules

_is_prod = os.getenv("ENVIRONMENT", "development") == "production"
app = FastAPI(
    title="Uphill AI Backend",
    description="Core processing engine and coaching chat API for Uphill AI.",
    version="1.6.0",
    # Disable interactive docs in production — avoids leaking full API schema
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

app.include_router(analytics_router, prefix="/api")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.trycloudflare\.com|https://uphill-ai\.io\.vn|https://kylianvo\.github\.io|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI for Prometheus metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)


# Initialize SQLite database on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Initialize Gemini SDK if API key is provided
has_gemini = False
if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        has_gemini = True
        print("Gemini SDK configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini SDK: {e}")
else:
    print("Warning: GEMINI_API_KEY is not configured. Running coach chat in fallback mock mode.")

# Global extraction status (in-memory, single-user simplification)
extraction_status: dict[str, Any] = {
    "status": "idle",  # idle | extracting | done | error
    "current_topic": None,
    "progress": 0,
    "total": 8,
    "card_count": 0,
    "last_extracted": None,
    "message": None,
}

workout_type_extraction_status: dict[str, Any] = {
    "status": "idle",
    "current_type": None,
    "progress": 0,
    "total": 12,
    "type_count": 0,
    "last_extracted": None,
    "message": None,
}

# Plan generation job store — keyed by job_id (UUID string)
# Each entry: {status, user_id, plan_id, workouts, error}
plan_jobs: dict[str, dict[str, Any]] = {}


# Data Models
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    user_profile: dict[str, Any] | None = None
    context_data: dict[str, Any] | None = None


class LinkIngestRequest(BaseModel):
    url: str


class PlanGenerateRequest(BaseModel):
    lang: str | None = "en"
    race_name: str | None = None
    race_date: str | None = None  # YYYY-MM-DD
    goal_type: str  # 'finish', 'time', 'optimal', 'start_running', 'return', 'recovery'
    target_time_hours: float | None = None
    cutoff_time_hours: float | None = None
    terrain: str | None = "trail"
    course_distance_km: float | None = None
    course_elevation_gain_m: float | None = None
    # Scheduling preferences
    preferred_days: list[str] | None = None  # e.g. ["Monday","Wednesday","Saturday"]
    long_run_day: str | None = None  # e.g. "Saturday"
    days_per_week: int | None = None  # 3-7
    # Non-race / start date fields
    plan_start_date: str | None = None  # YYYY-MM-DD
    plan_duration_weeks: int | None = None
    time_away: str | None = None
    fitness_feel: str | None = None
    race_distance_completed: str | None = None
    days_since_race: int | None = None
    recovery_feel: str | None = None


class SelectPlanRequest(BaseModel):
    plan_id: int


class ModifyCalendarRequest(BaseModel):
    plan_id: int
    week_number: int
    day_1: str
    day_2: str


class BlockReviewRequest(BaseModel):
    plan_id: int
    block_number: int
    overall_rpe: int | None = None
    notes: str | None = None


class GenerateNextBlockRequest(BaseModel):
    plan_id: int
    block_number: int  # the next block to generate (1-indexed)
    overall_rpe: int | None = None  # optional pre-submission of RPE for current block
    notes: str | None = None


# Phase 3 Request Models
class PacingRequest(BaseModel):
    checkpoints: list[dict[str, Any]]
    target_flat_pace_min_km: float
    climb_coef: float | None = 10.0
    descent_coef: float | None = 2.0


class FuelingRequest(BaseModel):
    duration_hours: float
    sweat_rate: str  # 'low', 'moderate', 'high'
    weather_temp: str  # 'cool', 'moderate', 'hot'


class ShoeRecommendRequest(BaseModel):
    surface: str
    cushioning: str
    width: str


# Auth Request Models
class GoogleAuthRequest(BaseModel):
    credential: str


class FacebookAuthRequest(BaseModel):
    access_token: str


class MockLoginRequest(BaseModel):
    email: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SetPasswordRequest(BaseModel):
    password: str


class OnboardingRequest(BaseModel):
    lang: str | None = "en"
    # Step 1
    dob: str | None = None  # YYYY-MM-DD
    age: int | None = None
    # Step 2
    goal_type: str  # race|distance|start_running|return|recovery
    # Fitness
    aet_hr: int | None = None
    ant_hr: int | None = None
    max_hr: int | None = None
    resting_hr: int | None = None
    zone2_pace_min: str | None = None
    zone2_pace_max: str | None = None
    # Injury
    injury_history: str | None = None
    # Race / distance target
    race_name: str | None = None
    race_date: str | None = None
    course_distance_km: float | None = None
    course_elevation_gain_m: float | None = None
    terrain: str | None = "trail"
    race_goal: str | None = "finish"
    expected_finish_time: str | None = None
    # Weekly schedule
    days_per_week: int | None = 4
    preferred_run_days: list[str] | None = None
    long_run_day: str | None = None
    current_weekly_km: float | None = 30.0
    has_gym_access: bool | None = False
    # Goal-specific extras
    time_away: str | None = None
    reason_for_break: str | None = None
    fitness_feel: str | None = None
    race_distance_completed: str | None = None
    days_since_race: int | None = None
    recovery_feel: str | None = None
    next_goal: str | None = None
    # Double session preference
    double_session_days: list[str] | None = None
    plan_start_date: str | None = None  # YYYY-MM-DD


class UpdateProfileRequest(BaseModel):
    age: int
    current_weekly_km: float
    max_hr: int
    resting_hr: int
    aet_hr: int
    ant_hr: int
    use_treadmill: bool
    gemini_api_key: str | None = None
    zone2_pace_min: str | None = None
    zone2_pace_max: str | None = None
    double_session_days: list[str] | None = None


def format_user_response(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "onboarding_complete": bool(user.get("onboarding_complete", False)),
        "provider": user.get("provider", "email"),
        "has_password": bool(user.get("password_hash")),
        "age": user.get("age", 30),
        "dob": str(user["dob"]) if user.get("dob") else None,
        "goal_type": user.get("goal_type"),
        "current_weekly_km": user.get("current_weekly_km", 30.0),
        "max_hr": user.get("max_hr", 185),
        "resting_hr": user.get("resting_hr", 60),
        "aet_hr": user.get("aet_hr", 135),
        "ant_hr": user.get("ant_hr", 165),
        "use_treadmill": user.get("use_treadmill", 0),
        "has_gym_access": bool(user.get("has_gym_access", False)),
        "days_per_week": user.get("days_per_week", 4),
        "preferred_run_days": user.get("preferred_run_days") or "[]",
        "long_run_day": user.get("long_run_day") or "",
        "injury_history": user.get("injury_history") or "",
        "gemini_api_key": user.get("gemini_api_key") or "",
        "zone2_pace_min": user.get("zone2_pace_min") or "6:30",
        "zone2_pace_max": user.get("zone2_pace_max") or "5:45",
        "double_session_days": user.get("double_session_days") or "[]",
    }


# Auth Dependencies
async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token missing or invalid.")
    token = authorization.split(" ")[1]
    user = verify_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    return user


async def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Administrator privileges required.")
    return user


COACH_SYSTEM_INSTRUCTION = """
You are Coach Uphill, an elite running coach speaking directly to your athlete — natural, warm, and direct, never robotic.

MUST: Keep every reply to 1-2 short paragraphs or a brief bullet list. NEVER open with a preamble or repeat the athlete's question back to them. NEVER pad with essay-like explanation.
NEVER fabricate a workout detail, product spec, or statistic you are not confident about. If the grounding data below doesn't cover what's asked, say so plainly and answer from general coaching principles instead of inventing specifics.

Coaching principles — apply strictly:
1. Trail Running: Scott Johnston's "Training for the Uphill Athlete" principles. Emphasize muscular endurance (e.g., weighted step-ups, hill sprints).
2. Road Running: 80/20 rule — 80% of volume in Zone 1-2, 20% in Zone 3-5.
3. Nutrition: Hydration/electrolyte rates based on sweat rate and target time. Progressive gut-training plans.
4. Gear: Match shoes to foot biomechanics, goals, and surface.
5. Active Training Plan: If calendar workouts appear in Context/Activity Data below, reference them directly for specific pacing, nutrition, or recovery tips.

Tone: warm and encouraging, always actionable — focus on the next concrete step the runner should take.
"""


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "gemini_api_configured": has_gemini, "allowed_origins": settings.ALLOWED_ORIGINS}


# --- Authentication Endpoints ---


@app.post("/api/auth/google")
async def auth_google(request: GoogleAuthRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo", params={"id_token": request.credential}
            )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google credential token.")

        token_info = response.json()
        email = token_info.get("email")
        name = token_info.get("name", email.split("@")[0])
        sub = token_info.get("sub")

        if not email or not sub:
            raise HTTPException(status_code=400, detail="Incomplete Google profile fields.")

        role = "admin" if email.lower().strip() == "admin@uphill.ai" else "user"
        user = create_or_get_user(email=email, name=name, provider="google", provider_user_id=sub, role=role)
        session = create_session(user["id"])

        return {
            "session_token": session["session_token"],
            "expires_at": session["expires_at"],
            "user": format_user_response(user),
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Google authentication error: {str(e)}")


@app.post("/api/auth/facebook")
async def auth_facebook(request: FacebookAuthRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.facebook.com/me",
                params={"fields": "id,name,email", "access_token": request.access_token},
            )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Facebook credentials token.")

        token_info = response.json()
        fb_id = token_info.get("id")
        name = token_info.get("name", "")
        email = token_info.get("email") or f"{fb_id}@facebook.uphill.ai"

        if not fb_id:
            raise HTTPException(status_code=400, detail="Incomplete Facebook profile fields.")

        role = "admin" if email.lower().strip() == "admin@uphill.ai" else "user"
        user = create_or_get_user(email=email, name=name, provider="facebook", provider_user_id=fb_id, role=role)
        session = create_session(user["id"])

        return {
            "session_token": session["session_token"],
            "expires_at": session["expires_at"],
            "user": format_user_response(user),
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Facebook authentication error: {str(e)}")


@app.post("/api/auth/register")
async def auth_register(request: RegisterRequest):
    """Register a new user with email + password."""
    email = request.email.lower().strip()
    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    pw_hash = hash_password(request.password)
    user = create_user_with_password(email=email, name=request.name.strip(), password_hash=pw_hash)
    session = create_session(user["id"])
    return {
        "session_token": session["session_token"],
        "expires_at": session["expires_at"],
        "user": format_user_response(user),
    }


@app.post("/api/auth/login")
async def auth_login(request: LoginRequest):
    """Login with email + password."""
    email = request.email.lower().strip()
    user = get_user_by_email(email)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    session = create_session(user["id"])
    return {
        "session_token": session["session_token"],
        "expires_at": session["expires_at"],
        "user": format_user_response(user),
    }


@app.post("/api/auth/set-password")
async def auth_set_password(request: SetPasswordRequest, user: dict[str, Any] = Depends(get_current_user)):
    """Allow OAuth users to add a password to their account."""
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    pw_hash = hash_password(request.password)
    success = set_user_password(user["id"], pw_hash)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set password.")
    return {"message": "Password set successfully."}


# mock-login is only registered in non-production environments.
# In production (ENVIRONMENT=production) this route does not exist.
if not _is_prod:

    @app.post("/api/auth/mock-login")
    def auth_mock_login(request: MockLoginRequest):
        email = request.email.lower().strip()
        user = get_user_by_email(email)
        if not user:
            if email == "admin@uphill.ai":
                user = create_or_get_user(
                    email, "Uphill Admin", "mock", "mock-admin-id", "admin", onboarding_complete=True
                )
            elif email == "athlete@uphill.ai":
                user = create_or_get_user(
                    email, "Uphill Athlete", "mock", "mock-athlete-id", "user", onboarding_complete=True
                )
            else:
                name = email.split("@")[0].capitalize()
                user = create_or_get_user(email, name, "mock", f"mock-{name.lower()}-id", "user")
        session = create_session(user["id"])
        return {
            "session_token": session["session_token"],
            "expires_at": session["expires_at"],
            "user": format_user_response(user),
        }


def _compute_age(dob_str, default_age, today_date):
    if dob_str:
        try:
            from datetime import datetime as dt

            born = dt.strptime(dob_str, "%Y-%m-%d").date()
            return (today_date - born).days // 365
        except ValueError:
            pass
    return default_age


def _parse_time_hours(time_str):
    if not time_str:
        return None
    try:
        parts = time_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) + int(parts[1]) / 60.0 + int(parts[2]) / 3600.0
        elif len(parts) == 2:
            return int(parts[0]) + int(parts[1]) / 60.0
    except Exception:
        pass
    return None


def _calculate_total_weeks(race_date_str, today_date):
    from datetime import datetime as dt
    from datetime import timedelta

    race_date_parsed = dt.strptime(race_date_str, "%Y-%m-%d").date()
    monday_today = today_date - timedelta(days=today_date.weekday())
    monday_race = race_date_parsed - timedelta(days=race_date_parsed.weekday())
    weeks_to_race = max((monday_race - monday_today).days // 7, 3)
    return weeks_to_race + 2


@app.post("/api/auth/onboarding")
async def complete_onboarding(request: OnboardingRequest, user: dict[str, Any] = Depends(get_current_user)):
    """
    Save onboarding answers and create the plan row, then kick off Gemini plan
    generation in the background. Returns immediately with a job_id the frontend
    can poll via GET /api/coach/plan-status/{job_id}.
    """
    import asyncio
    from datetime import date, timedelta

    today = date.today()
    age = _compute_age(request.dob, request.age or user.get("age", 30), today)

    # Estimate HR zones from age if not provided
    max_hr = request.max_hr or (220 - age)
    aet_hr = request.aet_hr or round(max_hr * 0.73)
    ant_hr = request.ant_hr or round(max_hr * 0.89)
    resting_hr = request.resting_hr or 60

    # Determine Zone 2 pace ranges with slow defaults for start_running
    zone2_min = request.zone2_pace_min
    zone2_max = request.zone2_pace_max
    if request.goal_type == "start_running":
        zone2_min = zone2_min if zone2_min and zone2_min != "6:30" else "8:30"
        zone2_max = zone2_max if zone2_max and zone2_max != "5:45" else "7:30"
    else:
        zone2_min = zone2_min or "6:30"
        zone2_max = zone2_max or "5:45"

    onboarding_data = {
        "dob": request.dob,
        "age": age,
        "goal_type": request.goal_type,
        "injury_history": request.injury_history,
        "preferred_run_days": request.preferred_run_days or [],
        "long_run_day": request.long_run_day,
        "days_per_week": request.days_per_week or 4,
        "has_gym_access": request.has_gym_access or False,
        "current_weekly_km": request.current_weekly_km or 30.0,
        "double_session_days": request.double_session_days or [],
        "max_hr": max_hr,
        "resting_hr": resting_hr,
        "aet_hr": aet_hr,
        "ant_hr": ant_hr,
        "zone2_pace_min": zone2_min,
        "zone2_pace_max": zone2_max,
    }
    update_onboarding_profile(user["id"], onboarding_data)

    # Build a plan request from onboarding context
    race_name = request.race_name or _default_plan_name(request.goal_type)
    race_date = request.race_date or (today + timedelta(weeks=_default_weeks(request.goal_type))).strftime("%Y-%m-%d")

    # Determine plan goal type and parse expected finish time
    is_event = request.goal_type in ["race", "distance"]
    plan_goal_type = request.race_goal if is_event else request.goal_type
    if not plan_goal_type:
        plan_goal_type = "finish"

    tth = _parse_time_hours(request.expected_finish_time) if plan_goal_type == "time" else None

    onboarding_start_date = request.plan_start_date or today.strftime("%Y-%m-%d")
    try:
        start_date_parsed = date.fromisoformat(onboarding_start_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan_start_date format. Expected YYYY-MM-DD.")
    total_weeks = _calculate_total_weeks(race_date, start_date_parsed)
    plan_id = create_plan(
        user_id=user["id"],
        race_name=race_name,
        race_date=race_date,
        goal_type=plan_goal_type,
        target_time_hours=tth,
        total_weeks=total_weeks,
        course_distance_km=request.course_distance_km,
        course_elevation_gain_m=request.course_elevation_gain_m,
        preferred_run_days=request.preferred_run_days or [],
        long_run_day=request.long_run_day,
        days_per_week=request.days_per_week or 4,
        double_session_days=request.double_session_days or [],
        start_date=onboarding_start_date,
    )

    # Mark onboarding complete immediately so the user can enter the app
    mark_onboarding_complete(user["id"])

    fresh_user = get_user_by_id(user["id"]) or user
    model_api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY

    race_info = {
        "name": race_name,
        "date": race_date,
        "terrain": request.terrain or "trail",
        "goal_type": plan_goal_type,
        "target_time_hours": tth,
        "course_distance_km": request.course_distance_km,
        "course_elevation_gain_m": request.course_elevation_gain_m,
        "preferred_days": request.preferred_run_days,
        "long_run_day": request.long_run_day,
        "days_per_week": request.days_per_week,
        "double_session_days": request.double_session_days or [],
        "plan_start_date": onboarding_start_date,
        "lang": request.lang or "en",
    }

    # Create a job entry and fire plan generation in the background
    job_id = str(_uuid.uuid4())
    plan_jobs[job_id] = {
        "status": "generating",
        "user_id": user["id"],
        "plan_id": plan_id,
        "workouts": None,
        "error": None,
    }

    async def _run_plan_gen():
        try:
            workouts = await PlanGenerator.generate_plan_workouts(
                plan_id,
                fresh_user,
                race_info,
                total_weeks,
                api_key=model_api_key,
                block_number=1,
                weeks_per_block=2,
            )
            save_workouts(plan_id, workouts)
            plan_jobs[job_id]["workouts"] = workouts
            plan_jobs[job_id]["status"] = "done"
            print(f"[PlanJob][{job_id}] Onboarding plan generation complete — {len(workouts)} workouts saved.")
        except Exception as ex:
            plan_jobs[job_id]["status"] = "error"
            plan_jobs[job_id]["error"] = str(ex)
            print(f"[PlanJob][{job_id}] Onboarding plan generation FAILED: {ex}")

    asyncio.create_task(_run_plan_gen())

    return {
        "job_id": job_id,
        "plan": {
            "id": plan_id,
            "race_name": race_name,
            "race_date": race_date,
            "goal_type": request.goal_type,
            "total_weeks": total_weeks,
        },
        "workouts": [],
        "user": format_user_response(fresh_user),
    }


def _default_plan_name(goal_type: str) -> str:
    return {
        "start_running": "My Running Journey",
        "return": "Getting Back to Running",
        "recovery": "Post-Race Recovery Plan",
        "distance": "Distance Challenge",
        "race": "Race Preparation",
    }.get(goal_type, "Training Plan")


def _default_weeks(goal_type: str) -> int:
    return {
        "start_running": 12,
        "return": 8,
        "recovery": 6,
        "distance": 16,
        "race": 16,
    }.get(goal_type, 12)


@app.get("/api/auth/me")
def auth_me(user: dict[str, Any] = Depends(get_current_user)):
    return format_user_response(user)


@app.post("/api/auth/update-profile")
def update_profile(request: UpdateProfileRequest, user: dict[str, Any] = Depends(get_current_user)):
    data = request.dict()
    success = update_user_profile(user["id"], data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user profile.")
    updated_user = get_user_by_id(user["id"])
    return format_user_response(updated_user)


@app.get("/api/auth/pace-zones")
def get_pace_zones(user: dict[str, Any] = Depends(get_current_user)):
    zones = PlanGenerator.estimate_pace_zones(
        user.get("zone2_pace_min") or "6:30",
        user.get("zone2_pace_max") or "5:45",
        user.get("aet_hr"),
        user.get("ant_hr"),
    )
    hr_zones = TrainingRules.calculate_heart_rate_zones(
        int(user.get("max_hr") or 185), int(user.get("resting_hr") or 60)
    )
    return {
        "zone1_pace": zones["zone1_pace"],
        "zone2_pace": zones["zone2_pace"],
        "zone3_pace": zones["zone3_pace"],
        "zone4_pace": zones["zone4_pace"],
        "zone5_pace": zones["zone5_pace"],
        "zone1_hr": f"{hr_zones['Zone 1']['min']}-{hr_zones['Zone 1']['max']} bpm",
        "zone2_hr": f"{hr_zones['Zone 2']['min']}-{hr_zones['Zone 2']['max']} bpm",
        "zone3_hr": f"{hr_zones['Zone 3']['min']}-{hr_zones['Zone 3']['max']} bpm",
        "zone4_hr": f"{hr_zones['Zone 4']['min']}-{hr_zones['Zone 4']['max']} bpm",
        "zone5_hr": f"{hr_zones['Zone 5']['min']}-{hr_zones['Zone 5']['max']} bpm",
    }


@app.post("/api/auth/logout")
def auth_logout(authorization: str | None = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        delete_session(token)
    return {"message": "Logged out successfully."}


# --- Telemetry Parsers ---


@app.post("/api/parser/fit")
async def parse_fit(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".fit"):
        raise HTTPException(status_code=400, detail="Only .fit files are accepted.")
    try:
        file_bytes = await file.read()
        parsed_data = FitParser.parse(file_bytes)
        return parsed_data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal parsing error: {str(e)}")


@app.post("/api/parser/gpx")
async def parse_gpx(file: UploadFile = File(...), checkpoint_interval_meters: float = Form(5000.0)):
    if not file.filename.lower().endswith(".gpx"):
        raise HTTPException(status_code=400, detail="Only .gpx files are accepted.")
    try:
        file_bytes = await file.read()
        parsed_data = GpxParser.parse(file_bytes, checkpoint_interval_meters)
        return parsed_data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal parsing error: {str(e)}")


# --- RAG Knowledge Source Routes ---


@app.get("/api/rag/sources")
def get_sources(user: dict[str, Any] = Depends(get_current_user)):
    return list_sources()


@app.delete("/api/rag/sources/{source_id}")
def remove_source(source_id: int, admin_user: dict[str, Any] = Depends(require_admin)):
    success = delete_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found.")
    return {"message": "Source deleted successfully."}


@app.post("/api/rag/link")
async def ingest_link(request: LinkIngestRequest, admin_user: dict[str, Any] = Depends(require_admin)):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")

    is_youtube = any(domain in url.lower() for domain in ["youtube.com", "youtu.be"])

    try:
        if is_youtube:
            data = RagService.get_youtube_transcript(url)
            source_id = add_source(
                title=data["title"],
                type_str="youtube",
                content=data["content"],
                url_path=data["url_path"],
                summary=data["content"][:200] + "...",
            )
            return {"id": source_id, "title": data["title"], "type": "youtube"}
        else:
            data = RagService.scrape_web_url(url)
            source_id = add_source(
                title=data["title"],
                type_str="url",
                content=data["content"],
                url_path=data["url_path"],
                summary=data["content"][:200] + "...",
            )
            return {"id": source_id, "title": data["title"], "type": "url"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/api/rag/upload")
async def upload_pdf(file: UploadFile = File(...), admin_user: dict[str, Any] = Depends(require_admin)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
    try:
        file_bytes = await file.read()
        data = RagService.parse_pdf(file_bytes, file.filename)
        source_id = add_source(
            title=data["title"],
            type_str="pdf",
            content=data["content"],
            url_path=data["url_path"],
            summary=data["content"][:200] + "...",
        )
        return {"id": source_id, "title": data["title"], "type": "pdf"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF ingestion failed: {str(e)}")


# --- Training Planner Endpoints ---


@app.get("/api/coach/active-plan")
def get_current_active_plan(user: dict[str, Any] = Depends(get_current_user)):
    plan = get_active_plan(user["id"])
    if not plan:
        return {"active": False}

    workouts = get_plan_workouts(plan["id"])
    return {"active": True, "plan": plan, "workouts": workouts}


@app.post("/api/coach/generate-plan")
async def generate_training_plan(request: PlanGenerateRequest, user: dict[str, Any] = Depends(get_current_user)):
    try:
        import asyncio
        from datetime import datetime, timedelta

        goal = request.goal_type
        is_race_or_dist = goal in ["finish", "time", "optimal"]

        # Parse plan start date (default to today if missing)
        start_date_str = request.plan_start_date or datetime.now().strftime("%Y-%m-%d")
        try:
            start_date_parsed = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid plan_start_date format. Expected YYYY-MM-DD.")

        if is_race_or_dist:
            if not request.race_date:
                raise HTTPException(status_code=400, detail="Race Date is required for race/distance goals.")
            try:
                race_date_parsed = datetime.strptime(request.race_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

            # Find Mondays
            monday_start = start_date_parsed - timedelta(days=start_date_parsed.weekday())
            monday_race = race_date_parsed - timedelta(days=race_date_parsed.weekday())

            weeks_to_race = (monday_race - monday_start).days // 7
            total_weeks = max(3, weeks_to_race + 2)
            race_date_str = request.race_date
            race_name_str = request.race_name or "Target Event"
        else:
            # Non-race goals
            total_weeks = request.plan_duration_weeks or 8
            # Calculate a synthetic race date at the end of the block
            race_date_parsed = start_date_parsed + timedelta(weeks=total_weeks - 1)
            race_date_str = race_date_parsed.strftime("%Y-%m-%d")

            # Clear race-specific parameters for non-race plans
            request.course_distance_km = None
            request.course_elevation_gain_m = None

            if goal == "start_running":
                race_name_str = "Base Building"
            elif goal == "return":
                race_name_str = "Return to Running"
            elif goal == "recovery":
                race_name_str = "Post-Race Recovery"
            else:
                race_name_str = request.race_name or "Training Block"

        plan_id = create_plan(
            user_id=user["id"],
            race_name=race_name_str,
            race_date=race_date_str,
            goal_type=goal,
            target_time_hours=request.target_time_hours,
            total_weeks=total_weeks,
            course_distance_km=request.course_distance_km,
            course_elevation_gain_m=request.course_elevation_gain_m,
            preferred_run_days=request.preferred_days or [],
            long_run_day=request.long_run_day,
            days_per_week=request.days_per_week or 4,
            double_session_days=[],
            start_date=start_date_str,
        )

        race_info = {
            "name": race_name_str,
            "date": race_date_str,
            "terrain": request.terrain,
            "goal_type": request.goal_type,
            "target_time_hours": request.target_time_hours,
            "course_distance_km": request.course_distance_km,
            "course_elevation_gain_m": request.course_elevation_gain_m,
            # Scheduling preferences (plan-level)
            "preferred_days": request.preferred_days,
            "long_run_day": request.long_run_day,
            "days_per_week": request.days_per_week,
            "double_session_days": [],
            # Start date
            "plan_start_date": start_date_str,
            "lang": request.lang or "en",
        }

        # Fetch latest user details from database to ensure fresh physiological values
        fresh_user = get_user_by_id(user["id"]) or user

        # Merge onboarding/non-race context fields into fresh_user dict for plan generator
        fresh_user = dict(fresh_user)
        fresh_user.update(
            {
                "time_away": request.time_away,
                "fitness_feel": request.fitness_feel,
                "race_distance_completed": request.race_distance_completed,
                "days_since_race": request.days_since_race,
                "recovery_feel": request.recovery_feel,
            }
        )

        # Resolve Gemini API Key (per-user key with global settings fallback)
        model_api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
        cutoff = request.cutoff_time_hours

        # Create job entry and fire plan generation in the background
        job_id = str(_uuid.uuid4())
        plan_jobs[job_id] = {
            "status": "generating",
            "user_id": user["id"],
            "plan_id": plan_id,
            "workouts": None,
            "error": None,
        }

        async def _run_gen():
            try:
                workouts = await PlanGenerator.generate_plan_workouts(
                    plan_id,
                    fresh_user,
                    race_info,
                    total_weeks,
                    api_key=model_api_key,
                    cutoff_time_hours=cutoff,
                    block_number=1,
                    weeks_per_block=2,
                )
                save_workouts(plan_id, workouts)
                plan_jobs[job_id]["workouts"] = workouts
                plan_jobs[job_id]["status"] = "done"
                print(f"[PlanJob][{job_id}] generate-plan complete — {len(workouts)} workouts saved.")
            except Exception as ex:
                plan_jobs[job_id]["status"] = "error"
                plan_jobs[job_id]["error"] = str(ex)
                print(f"[PlanJob][{job_id}] generate-plan FAILED: {ex}")

        asyncio.create_task(_run_gen())

        return {
            "job_id": job_id,
            "active": True,
            "plan": {
                "id": plan_id,
                "race_name": race_name_str,
                "race_date": race_date_str,
                "goal_type": request.goal_type,
                "target_time_hours": request.target_time_hours,
                "total_weeks": total_weeks,
                "course_distance_km": request.course_distance_km,
                "course_elevation_gain_m": request.course_elevation_gain_m,
            },
            "workouts": [],
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")


@app.get("/api/coach/plan-status/{job_id}")
async def get_plan_generation_status(job_id: str, user: dict[str, Any] = Depends(get_current_user)):
    """
    Poll the status of an async plan generation job.
    Returns {status, plan_id, workouts?, error?}
    status: 'generating' | 'done' | 'error'
    """
    job = plan_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorised to view this job.")

    response: dict[str, Any] = {
        "status": job["status"],
        "plan_id": job["plan_id"],
    }
    if job["status"] == "done":
        # Return fresh workouts from DB (job store may be large; DB is authoritative)
        response["workouts"] = get_plan_workouts(job["plan_id"])
        response["plan"] = get_active_plan(user["id"])
    if job["status"] == "error":
        response["error"] = job["error"]
    return response


@app.get("/api/coach/recent-plans")
def get_user_recent_plans(user: dict[str, Any] = Depends(get_current_user)):
    plans = get_recent_plans(user["id"], limit=3)
    return {"plans": plans}


# ─── Sequential Plan Endpoints ────────────────────────────────────────────────


def _verify_plan_ownership(plan_id: int, user_id: int):
    """Raise 404 if the plan doesn't belong to this user (prevents IDOR)."""
    recent = get_recent_plans(user_id, limit=100)
    if not any(p["id"] == plan_id for p in recent):
        raise HTTPException(status_code=404, detail="Plan not found.")


@app.get("/api/coach/block-completion/{plan_id}")
def get_plan_block_completion(plan_id: int, user: dict[str, Any] = Depends(get_current_user)):
    """Return completion % for each 2-week block generated so far."""
    _verify_plan_ownership(plan_id, user["id"])
    max_week = get_max_generated_week(plan_id)
    total_blocks = (max_week + 1) // 2  # number of blocks with any workouts
    blocks = []
    for b in range(1, total_blocks + 1):
        blocks.append(get_block_completion(plan_id, b))
    return {"plan_id": plan_id, "blocks": blocks, "max_generated_week": max_week}


@app.post("/api/coach/block-review")
async def submit_block_review(request: BlockReviewRequest, user: dict[str, Any] = Depends(get_current_user)):
    """Save a block check-in (RPE + notes) before generating the next block."""
    _verify_plan_ownership(request.plan_id, user["id"])
    review = save_block_review(
        plan_id=request.plan_id,
        block_number=request.block_number,
        overall_rpe=request.overall_rpe,
        notes=request.notes,
    )
    return {"review": review}


@app.post("/api/coach/generate-next-block")
async def generate_next_block(request: GenerateNextBlockRequest, user: dict[str, Any] = Depends(get_current_user)):
    """
    Generate the next 2-week block for an existing plan.
    Requires the previous block to be ≥70% complete by training hours.
    Injects block review feedback into the generation prompt.
    """
    import asyncio

    # Ownership check FIRST — before any reads or writes on this plan
    recent = get_recent_plans(user["id"], limit=100)
    plan = next((p for p in recent if p["id"] == request.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    # Guard against double-submission: if a block generation job for this plan is
    # already in flight, hand back that job instead of starting a second one that
    # would independently insert a duplicate set of workouts.
    for existing_job_id, job in plan_jobs.items():
        if (
            job.get("plan_id") == request.plan_id
            and job.get("kind") == "next_block"
            and job.get("status") == "generating"
        ):
            return {
                "job_id": existing_job_id,
                "plan_id": request.plan_id,
                "block_number": job.get("block_number", request.block_number),
                "week_start": (job.get("block_number", request.block_number) - 1) * 2 + 1,
                "week_end": min(
                    (job.get("block_number", request.block_number) - 1) * 2 + 2, plan.get("total_weeks", 12)
                ),
            }

    prev_block = request.block_number - 1

    # Enforce 80% completion gate on the preceding block
    if prev_block >= 1:
        completion = get_block_completion(request.plan_id, prev_block)
        if not completion["unlocked"]:
            raise HTTPException(
                status_code=403,
                detail=f"Block {prev_block} is {completion['completion_pct']}% complete. Need ≥70% to unlock the next block.",
            )

    # If the caller passes RPE/notes, save them as the review for the previous block
    if prev_block >= 1 and (request.overall_rpe is not None or request.notes):
        save_block_review(
            plan_id=request.plan_id,
            block_number=prev_block,
            overall_rpe=request.overall_rpe,
            notes=request.notes,
        )

    total_weeks = plan.get("total_weeks", 12)
    block_start = (request.block_number - 1) * 2 + 1
    if block_start > total_weeks:
        raise HTTPException(status_code=400, detail="All blocks for this plan have already been generated.")

    fresh_user = get_user_by_id(user["id"]) or user

    # Build compact block context for previous blocks
    reviews = get_block_reviews(request.plan_id)
    all_workouts = get_plan_workouts(request.plan_id)

    review_map = {r["block_number"]: r for r in (reviews or [])}

    block_context = None
    context_lines: list[str] = []

    for blk in range(1, request.block_number):
        wk_start = (blk - 1) * 2 + 1
        wk_end = blk * 2

        block_wos = [
            w for w in all_workouts if wk_start <= (w.get("week_number") or 0) <= wk_end and w.get("type") != "Rest"
        ]
        completed_wos = [w for w in block_wos if w.get("is_completed") == 1]

        # Planned totals (from generated workouts)
        planned_km = sum(w.get("distance_km") or 0 for w in block_wos)
        planned_min = sum(w.get("duration_minutes") or 0 for w in block_wos)

        # Actual totals (from completed workouts)
        actual_km = sum(w.get("distance_km") or 0 for w in completed_wos)
        actual_min = sum(w.get("duration_minutes") or 0 for w in completed_wos)

        sessions_done = len(completed_wos)
        sessions_total = len(block_wos)
        completion_pct = round(sessions_done / sessions_total * 100) if sessions_total else 0

        # Avg per-session RPE from individual workouts that have it logged
        session_rpes = [w["rpe"] for w in completed_wos if w.get("rpe")]
        avg_session_rpe = round(sum(session_rpes) / len(session_rpes), 1) if session_rpes else None

        # Block-level review (from the review modal)
        rev = review_map.get(blk)
        block_rpe = rev["overall_rpe"] if rev and rev.get("overall_rpe") else avg_session_rpe
        block_note = rev["notes"] if rev and rev.get("notes") else None

        # Collect session-level notes (exclude empty/None)
        session_notes = [
            f'{w.get("day_of_week","?")} W{w.get("week_number","?")}: "{w["notes"]}"'
            for w in completed_wos
            if w.get("notes")
        ]

        # Identify missed sessions (not completed, not Rest)
        missed = [
            f'{w.get("day_of_week","?")} {w.get("title") or w.get("type","?")}'
            for w in block_wos
            if w.get("is_completed") != 1
        ]

        # Compose the compact summary line
        line = (
            f"Block {blk} (Wk {wk_start}-{wk_end}): "
            f"{sessions_done}/{sessions_total} sessions ({completion_pct}%) | "
            f"Actual {actual_km:.1f}km/{actual_min/60:.1f}h vs Planned {planned_km:.1f}km/{planned_min/60:.1f}h"
        )
        if block_rpe:
            line += f" | RPE {block_rpe}/10"
        context_lines.append(line)

        if block_note:
            context_lines.append(f'  Athlete note: "{block_note}"')
        for n in session_notes:
            context_lines.append(f"  Session note — {n}")
        if missed:
            context_lines.append(
                f"  Missed: {', '.join(missed[:3])}"
                + (" +" + str(len(missed) - 3) + " more" if len(missed) > 3 else "")
            )

    if context_lines:
        block_context = "\n".join(context_lines)

    race_info = {
        "name": plan.get("race_name", "Training Plan"),
        "date": plan.get("race_date"),
        "terrain": fresh_user.get("terrain", "trail"),
        "goal_type": plan.get("goal_type"),
        "target_time_hours": plan.get("target_time_hours"),
        "course_distance_km": plan.get("course_distance_km"),
        "course_elevation_gain_m": plan.get("course_elevation_gain_m"),
        "preferred_days": plan.get("preferred_run_days"),
        "long_run_day": plan.get("long_run_day"),
        "days_per_week": plan.get("days_per_week"),
        "double_session_days": plan.get("double_session_days"),
        "plan_start_date": plan.get("start_date"),
        "lang": fresh_user.get("lang", "en"),
    }

    model_api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    _nb_id = settings.NOTEBOOKLM_NOTEBOOK_ID
    _nb_auth = settings.NOTEBOOKLM_AUTH_JSON
    print(
        f"[NextBlock] plan_id={request.plan_id} block={request.block_number} "
        f"notebook_configured={'yes' if (_nb_id and _nb_auth) else 'NO — will use Gemini/rule-based'} "
        f"gemini_key={'yes' if model_api_key else 'NO'} "
        f"plan_start_date={race_info.get('plan_start_date')} "
        f"block_context_lines={len(block_context.splitlines()) if block_context else 0}"
    )

    job_id = str(_uuid.uuid4())
    plan_jobs[job_id] = {
        "status": "generating",
        "user_id": user["id"],
        "plan_id": request.plan_id,
        "kind": "next_block",
        "block_number": request.block_number,
        "workouts": None,
        "error": None,
    }

    async def _run_next_block():
        try:
            workouts = await PlanGenerator.generate_plan_workouts(
                request.plan_id,
                fresh_user,
                race_info,
                total_weeks,
                api_key=model_api_key,
                block_number=request.block_number,
                weeks_per_block=2,
                block_context=block_context,
            )
            save_workouts(request.plan_id, workouts)
            plan_jobs[job_id]["workouts"] = workouts
            plan_jobs[job_id]["status"] = "done"
            print(f"[NextBlock][{job_id}] Block {request.block_number} complete — {len(workouts)} workouts saved.")
        except Exception as ex:
            plan_jobs[job_id]["status"] = "error"
            plan_jobs[job_id]["error"] = str(ex)
            print(f"[NextBlock][{job_id}] Block {request.block_number} FAILED: {ex}")

    asyncio.create_task(_run_next_block())

    return {
        "job_id": job_id,
        "plan_id": request.plan_id,
        "block_number": request.block_number,
        "week_start": block_start,
        "week_end": min(block_start + 1, total_weeks),
    }


@app.post("/api/coach/select-plan")
def select_plan_endpoint(request: SelectPlanRequest, user: dict[str, Any] = Depends(get_current_user)):
    plans = get_recent_plans(user["id"], limit=10)
    plan = next((p for p in plans if p["id"] == request.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    success = set_plan_active(user["id"], request.plan_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to select plan")

    updated_plan = get_active_plan(user["id"])
    workouts = get_plan_workouts(request.plan_id)
    return {"active": True, "plan": updated_plan, "workouts": workouts}


@app.post("/api/coach/modify-calendar")
def modify_calendar_swap(request: ModifyCalendarRequest, user: dict[str, Any] = Depends(get_current_user)):
    # Verify ownership of the plan
    active_plan = get_active_plan(user["id"])
    if not active_plan or active_plan["id"] != request.plan_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this plan.")

    success = swap_workouts(request.plan_id, request.week_number, request.day_1, request.day_2)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to swap workouts. Check date details.")

    updated_workouts = get_plan_workouts(request.plan_id)
    return {"message": "Swapped successfully", "workouts": updated_workouts}


class WorkoutLogRequest(BaseModel):
    workout_id: int
    is_completed: int | None = None
    rpe: int | None = None
    notes: str | None = None


@app.patch("/api/coach/workouts/log")
def log_workout(request: WorkoutLogRequest, user: dict[str, Any] = Depends(get_current_user)):
    """Save RPE, notes, and/or completion status for a workout."""
    active_plan = get_active_plan(user["id"])
    if not active_plan:
        raise HTTPException(status_code=404, detail="No active plan.")
    workouts = get_plan_workouts(active_plan["id"])
    wo_ids = {w["id"] for w in workouts}
    if request.workout_id not in wo_ids:
        raise HTTPException(status_code=403, detail="Workout not in your active plan.")
    ok = update_workout_log(request.workout_id, request.is_completed, request.rpe, request.notes)
    if not ok:
        raise HTTPException(status_code=404, detail="Workout not found.")
    updated = get_plan_workouts(active_plan["id"])
    return {"workouts": updated}


@app.get("/api/coach/export-ics")
def export_ics(
    plan_id: int,
    race_date: str,
    time_pref: str | None = "all_day",
    token: str | None = None,
    authorization: str | None = Header(None),
):
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]
    elif token:
        auth_token = token

    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication token missing.")

    user = verify_session(auth_token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")

    # Verify ownership of the plan
    active_plan = get_active_plan(user["id"])
    if not active_plan or active_plan["id"] != plan_id:
        raise HTTPException(status_code=403, detail="Not authorized to export this plan.")

    workouts = get_plan_workouts(plan_id)
    if not workouts:
        raise HTTPException(status_code=404, detail="No workouts found for this plan.")

    ics_text = CalendarService.generate_ics_string(race_date, workouts, time_pref)

    return Response(
        content=ics_text,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=uphill_ai_training_plan.ics",
            "Cache-Control": "no-cache",
        },
    )


# --- Phase 3 Specialized Routes ---


@app.post("/api/coach/calculate-pacing")
def calculate_pacing(request: PacingRequest):
    """Calculates GPX checkpoint splits and times adjusted for climbing and thin air."""
    try:
        paced_cps = PacingCalculator.calculate_checkpoint_paces(
            checkpoints=request.checkpoints,
            target_flat_pace_min_km=request.target_flat_pace_min_km,
            climb_coef=request.climb_coef,
            descent_coef=request.descent_coef,
        )
        return paced_cps
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate pacing: {str(e)}")


@app.post("/api/coach/calculate-fueling")
async def calculate_fueling(request: NutritionParams):
    """Calculates Precision Hydration targets and gel product recipes via NotebookLM."""
    try:
        strategy = await nutrition_planner.generate_plan(user_profile="", params=request)
        return strategy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile fueling plan: {str(e)}")


@app.post("/api/coach/recommend-shoes")
async def recommend_shoes(request: GearParams):
    """Matches athlete profiles with suitable shoe catalogs via NotebookLM."""
    try:
        recs = await gear_planner.generate_plan(user_profile="", params=request)
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match shoes: {str(e)}")


@app.get("/api/coach/nutrition-catalog")
def get_nutrition_catalog():
    return query_nutrition_catalog()


# --- Dynamic Grounded Chat ---


@app.post("/api/coach/chat")
async def coach_chat(request: ChatRequest):
    """
    Query Gemini model grounded with custom SQLite or NotebookLM documents.
    Dynamic contextual references are injected in the prompt envelope.
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
    profile_summary = f"\nUser Running Profile: {request.user_profile}" if request.user_profile else ""
    context_summary = f"\nContext/Activity Data: {request.context_data}" if request.context_data else ""

    full_system_prompt = (
        f"{COACH_SYSTEM_INSTRUCTION}"
        f"{grounding_context}"
        f"{profile_summary}"
        f"{context_summary}"
        f"\n\nNote: If the user asks questions referring to uploaded documents or materials, retrieve answers from the GROUNDING REFERENCE DATABASE and state which document/link you got it from."
    )

    model_api_key = None
    if request.user_profile:
        model_api_key = request.user_profile.get("gemini_api_key")
    if not model_api_key:
        model_api_key = settings.GEMINI_API_KEY

    if model_api_key:
        try:
            formatted_contents = []
            for msg in request.messages:
                role = "user" if msg.role == "user" else "model"
                formatted_contents.append({"role": role, "parts": [msg.content]})

            last_user = request.messages[-1].content
            print(
                f"[Chat][Gemini] Sending to gemini-2.5-flash | system_prompt={len(full_system_prompt)} chars | history={len(formatted_contents)} msgs"
            )
            print(f"[Chat][Gemini] User message: {last_user[:300]}")

            model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=full_system_prompt)

            # Configure request-safe client bound to custom or global key
            from google.generativeai import client as genai_client

            my_manager = genai_client._ClientManager()
            my_manager.configure(api_key=model_api_key)
            model._client = my_manager.get_default_client("generative")

            import asyncio

            response = await asyncio.to_thread(model.generate_content, formatted_contents)
            print(f"[Chat][Gemini] Response received ({len(response.text)} chars)")
            return {"role": "assistant", "content": response.text}
        except Exception as e:
            print(f"[Chat][Gemini] FAILED: {e}")

    # Mock fallback responder with citations check
    last_user_msg = request.messages[-1].content
    has_sources_note = (
        f" (I noticed we have {len(grounding_docs)} grounding sources registered in SQLite!)" if grounding_docs else ""
    )

    mock_reply = (
        "Hey there! I am currently running in offline mock mode. "
        f"You said: '{last_user_msg}'{has_sources_note}. "
        "Once you configure a Gemini API key in your user profile or the backend environment, I'll be able to read all your uploaded PDFs, "
        "URLs, and YouTube transcripts from the grounding database, then respond with precise citations!"
    )
    return {"role": "assistant", "content": mock_reply}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)

# ─── Knowledge Hub Endpoints ─────────────────────────────────────────────────


@app.get("/api/knowledge/cards")
def get_knowledge_cards(topic: str | None = None, lang: str = "en", user: dict[str, Any] = Depends(get_current_user)):
    """Return all knowledge cards, optionally filtered by topic."""
    cards = get_all_knowledge_cards(topic=topic, lang=lang)
    return {"cards": cards, "total": len(cards)}


@app.get("/api/knowledge/cards/random")
def get_random_cards(n: int = 3, lang: str = "en", user: dict[str, Any] = Depends(get_current_user)):
    """Return n random knowledge cards for the Daily Knowledge widget."""
    cards = get_random_knowledge_cards(n=n, lang=lang)
    return {"cards": cards}


@app.get("/api/knowledge/topics")
def get_topics(user: dict[str, Any] = Depends(get_current_user)):
    """Return distinct list of topics for filter pills."""
    topics = get_knowledge_topics()
    return {"topics": topics}


@app.get("/api/knowledge/extract/status")
def get_extraction_status(user: dict[str, Any] = Depends(get_current_user)):
    """Return current extraction status and card count."""
    status = dict(extraction_status)
    status["card_count"] = get_knowledge_card_count()
    return status


@app.post("/api/knowledge/trigger")
async def trigger_knowledge_extraction(user: dict[str, Any] = Depends(get_current_user)):
    """
    Auto-triggered by the frontend when the Knowledge Hub tab opens and no cards exist.
    Only fires if NotebookLM is configured and not already extracting.
    """
    import asyncio

    from services.knowledge_extractor import extract_knowledge_cards

    if extraction_status["status"] == "extracting":
        return {"status": "already_extracting", "card_count": get_knowledge_card_count()}

    card_count = get_knowledge_card_count()
    if card_count > 0:
        return {"status": "already_done", "card_count": card_count}

    # Use system-level NotebookLM config
    notebook_id = settings.NOTEBOOKLM_NOTEBOOK_ID
    auth_json = settings.NOTEBOOKLM_AUTH_JSON

    if not notebook_id or not auth_json:
        return {"status": "no_notebooklm", "card_count": 0}

    fresh_user = get_user_by_id(user["id"]) or user
    api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    if not api_key:
        return {"status": "no_api_key", "card_count": 0}

    # Fire and forget — runs fully in background
    async def run_extraction():
        try:
            await extract_knowledge_cards(notebook_id, auth_json, api_key, extraction_status)
        except Exception as e:
            extraction_status.update({"status": "error", "message": str(e)})
            print(f"[Knowledge] Extraction failed: {e}")

    asyncio.create_task(run_extraction())
    extraction_status.update({"status": "extracting", "progress": 0, "current_topic": "Starting…"})
    return {"status": "started"}


# ─── KB Distillation (NotebookLM → kb_chunks) ────────────────────────────────

kb_distill_status: dict[str, Any] = {"status": "idle"}
# Strong reference to the running distillation task — the event loop keeps only
# weak refs, and a GC'd multi-hour task would die silently while the status dict
# still said "distilling". Busy-ness is derived from the task, so it self-heals.
kb_distill_task = None


@app.post("/api/kb/distill")
async def trigger_kb_distill(domain: str = "all", user: dict[str, Any] = Depends(require_admin)):
    """Re-distill the knowledge base from the NotebookLM notebooks (admin, background job).
    Operator workflow: add sources to the notebook in NotebookLM, then call this."""
    import asyncio

    from services.kb_distiller import DOMAINS, distill_domain

    global kb_distill_task
    domains = list(DOMAINS) if domain == "all" else [domain]
    if any(d not in DOMAINS for d in domains):
        raise HTTPException(status_code=400, detail=f"domain must be one of {list(DOMAINS)} or 'all'")
    if kb_distill_task is not None and not kb_distill_task.done():
        return {"status": "already_distilling"}

    fresh_user = get_user_by_id(user["id"]) or user
    api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="No Gemini API key configured")

    async def run_distillation():
        async def run_domain(d: str):
            domain_status = kb_distill_status["per_domain"][d]
            try:
                saved = await distill_domain(d, api_key, domain_status)
                domain_status.update({"status": "done", "saved": saved})
            except Exception as e:
                domain_status.update({"status": "error", "message": str(e)})
                print(f"[KB] Distillation failed for '{d}': {e}")

        # The three notebooks are independent, so domains distill concurrently —
        # wall time is the slowest domain, not the sum. Each domain still paces
        # its own NotebookLM queries internally (rate-limit courtesy).
        await asyncio.gather(*(run_domain(d) for d in domains))
        failed = {d: s.get("message") for d, s in kb_distill_status["per_domain"].items() if s.get("status") == "error"}
        kb_distill_status.update({"status": "error" if failed else "done", "errors": failed or None})

    # Fresh status per run — stale keys from a previous run would mislead operators.
    kb_distill_status.clear()
    kb_distill_status.update(
        {"status": "distilling", "domains": domains, "per_domain": {d: {"status": "distilling"} for d in domains}}
    )
    kb_distill_task = asyncio.create_task(run_distillation())
    return {"status": "started", "domains": domains}


@app.get("/api/kb/distill/status")
def get_kb_distill_status(user: dict[str, Any] = Depends(get_current_user)):
    from services.kb_retrieval import scheduler_point_count

    status = dict(kb_distill_status)
    status["counts"] = {d: get_kb_chunk_count(d) for d in ("gear", "nutrition", "scheduler")}
    # None = collection missing/unreachable — scheduler plans would generate
    # without philosophy grounding even if counts.scheduler > 0.
    status["qdrant_scheduler_points"] = scheduler_point_count()
    return status


@app.post("/api/kb/import")
async def import_kb_seed(domain: str = "all", user: dict[str, Any] = Depends(require_admin)):
    """Load committed backend/kb_seed/<domain>.json files into this environment's
    Postgres (+ Qdrant for scheduler). This is how prod gets the KB without re-distilling."""
    import asyncio

    from services.kb_distiller import DOMAINS, load_seed

    domains = list(DOMAINS) if domain == "all" else [domain]
    if any(d not in DOMAINS for d in domains):
        raise HTTPException(status_code=400, detail=f"domain must be one of {list(DOMAINS)} or 'all'")
    api_key = settings.GEMINI_API_KEY
    loaded: dict[str, int] = {}
    errors: dict[str, str] = {}
    for d in domains:
        try:
            loaded[d] = await asyncio.to_thread(load_seed, d, api_key)
        except (FileNotFoundError, RuntimeError) as e:
            errors[d] = str(e)
    if not loaded:
        # If nothing loaded, use 404 only if ALL errors are FileNotFoundError, else 400
        all_missing = all("Seed file not found" in msg for msg in errors.values())
        status_code = 404 if all_missing else 400
        raise HTTPException(status_code=status_code, detail=errors)
    return {"status": "ok" if not errors else "partial", "loaded": loaded, "errors": errors}


# ─── Workout Types ────────────────────────────────────────────────────────────


@app.get("/api/workouts/types")
def list_workout_types(lang: str = "en"):
    """Return all workout type descriptions from the DB. No auth required."""
    return {"types": get_workout_types(lang=lang)}


@app.get("/api/workouts/types/extract/status")
def get_workout_type_extraction_status(user: dict[str, Any] = Depends(get_current_user)):
    status = dict(workout_type_extraction_status)
    status["type_count"] = get_workout_type_count()
    return status


@app.post("/api/workouts/types/extract")
async def trigger_workout_type_extraction(user: dict[str, Any] = Depends(get_current_user)):
    """
    Extract workout type descriptions from NotebookLM and store in DB.
    Can be re-triggered to refresh content. Runs in background.
    """
    import asyncio

    from services.workout_type_extractor import extract_workout_types

    if workout_type_extraction_status["status"] == "extracting":
        return {"status": "already_extracting", "type_count": get_workout_type_count()}

    notebook_id = settings.NOTEBOOKLM_NOTEBOOK_ID
    auth_json = settings.NOTEBOOKLM_AUTH_JSON

    if not notebook_id or not auth_json:
        return {"status": "no_notebooklm", "type_count": 0}

    fresh_user = get_user_by_id(user["id"]) or user
    api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    if not api_key:
        return {"status": "no_api_key", "type_count": 0}

    async def run():
        try:
            await extract_workout_types(notebook_id, auth_json, api_key, workout_type_extraction_status)
        except Exception as e:
            workout_type_extraction_status.update({"status": "error", "message": str(e)})
            print(f"[WorkoutTypes] Extraction failed: {e}")

    asyncio.create_task(run())
    workout_type_extraction_status.update({"status": "extracting", "progress": 0, "current_type": "Starting…"})
    return {"status": "started"}
