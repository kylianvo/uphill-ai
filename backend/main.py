import os
import threading
import uuid as _uuid
from typing import Any

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types as genai_types
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from config import settings
from db import (
    accept_coach_invite,
    add_source,
    approve_workout,
    block_number_for_week,
    coach_update_workout,
    compute_current_week,
    create_beta_signup,
    create_coach_invite,
    create_coach_note,
    create_coach_workout,
    create_or_get_user,
    create_plan,
    create_session,
    create_user_with_password,
    decline_coach_invite,
    delete_plan,
    delete_session,
    delete_source,
    get_active_coach_link_for_athlete,
    get_active_plan,
    get_all_knowledge_cards,
    get_block_actual_volume,
    get_block_completion,
    get_block_reviews,
    get_coach_athlete_by_id,
    get_coach_notes,
    get_draft_plan_for_athlete,
    get_kb_chunk_count,
    get_knowledge_card_count,
    get_knowledge_topics,
    get_matches_for_review,
    get_max_generated_week,
    get_pending_invites_for_athlete,
    get_plan_by_id,
    get_plan_workouts,
    get_random_knowledge_cards,
    get_recent_plans,
    get_recent_readiness_summary,
    get_roster_for_coach,
    get_roster_overview_data,
    get_user_activity_ceiling,
    get_user_by_email,
    get_user_by_id,
    get_week_planned_volume,
    get_week_review,
    get_workout_by_id,
    get_workout_types,
    has_active_coach_link,
    init_db,
    list_sources,
    make_rest_day,
    mark_onboarding_complete,
    query_nutrition_catalog,
    remove_coach_athlete_link,
    save_block_review,
    save_workouts,
    set_max_continuous_jog_min,
    set_plan_active,
    set_plan_athlete_tier,
    set_user_is_coach,
    set_user_password,
    update_onboarding_profile,
    update_plan_schedule,
    update_plan_target_time,
    update_user_profile,
    update_user_weekly_km,
    update_workout_log,
    upsert_block_review_ai_fields,
    verify_session,
    week_range_for_block,
)
from log_utils import get_logger
from parsers.fit_parser import FitParser
from parsers.gpx_parser import GpxParser
from routers.analytics import router as analytics_router
from routers.coach_chat import ChatMessage
from routers.coach_chat import router as coach_chat_router
from routers.integrations import router as integrations_router
from services import calendar_ops, observability, race_history, week_rebuild
from services.auth_service import hash_password, verify_password
from services.calendar_rules import GuardViolation, resolve_today
from services.calendar_service import CalendarService
from services.course_match import resolve_course_match as _resolve_course_match
from services.gear_planner import GearParams, gear_planner
from services.matching.block_evaluator import evaluate_block_performance
from services.nutrition_planner import NutritionParams, nutrition_planner
from services.pacing_calculator import PacingCalculator
from services.plan_generator import PlanGenerator
from services.rag_service import RagService
from services.training_rules import TrainingRules, resolve_zone2_pace
from services.weather_service import WeatherService
from services.week_review_narrative import generate_week_narrative

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
app.include_router(integrations_router, prefix="/api")
app.include_router(coach_chat_router)

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


# Initialize the database schema and LLM observability on startup
_race_worker_stop = None


@app.on_event("startup")
def startup_event():
    init_db()
    observability.init()
    from threading import Event, Thread

    global _race_worker_stop
    if not settings.RACE_HISTORY_WORKER_ENABLED:
        return
    _race_worker_stop = Event()
    Thread(target=race_history.run_worker, args=(_race_worker_stop,), daemon=True, name="race-history-worker").start()


# Deliver any spans still batched in memory before the process exits
@app.on_event("shutdown")
def shutdown_event():
    if _race_worker_stop:
        _race_worker_stop.set()
    observability.flush()


# google-genai's Client is constructed per-request (see chat/plan endpoints below,
# which may use a per-user key instead of the server-wide one) rather than configured
# globally, so this just tracks whether a server-wide key is available at all.
has_gemini = bool(settings.GEMINI_API_KEY)
if has_gemini:
    print("Gemini API key configured.")
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

# Plan generation job store — keyed by job_id (UUID string)
# Each entry: {status, user_id, plan_id, workouts, error}
plan_jobs: dict[str, dict[str, Any]] = {}


# Data Models
# Note: ChatMessage and ChatRequest are imported from routers.coach_chat above
class LinkIngestRequest(BaseModel):
    url: str


class PlanGenerateRequest(BaseModel):
    lang: str | None = "en"
    race_name: str | None = None
    race_date: str | None = None  # YYYY-MM-DD
    goal_type: str  # 'finish', 'time', 'optimal', 'start_running', 'return', 'recovery'
    current_weekly_km: float  # current training volume, entered fresh for every plan
    target_time_hours: float | None = None
    cutoff_time_hours: float | None = None
    terrain: str | None = "trail"
    course_distance_km: float | None = None
    course_elevation_gain_m: float | None = None
    # Scheduling preferences
    preferred_days: list[str] | None = None  # e.g. ["Monday","Wednesday","Saturday"]
    long_run_day: str | None = None  # e.g. "Saturday"
    days_per_week: int | None = None  # 3-7
    double_session_days: list[str] | None = None
    has_gym_access: bool | None = False
    use_treadmill: bool | None = None
    training_environment: str | None = "flat"  # 'flat' | 'hilly' | 'mixed'
    # Non-race / start date fields
    plan_start_date: str | None = None  # YYYY-MM-DD
    plan_duration_weeks: int | None = None
    time_away: str | None = None
    fitness_feel: str | None = None
    race_distance_completed: str | None = None
    days_since_race: int | None = None
    recovery_feel: str | None = None
    # Coach-authored guidance, only meaningful on the coach-triggered path
    # (/api/coaching/athletes/{athlete_id}/generate-plan) -- injected into the
    # generation prompt so the coach's own judgment can override defaults.
    coach_notes: str | None = None
    athlete_notes: str | None = None


class SelectPlanRequest(BaseModel):
    plan_id: int


class ModifyCalendarRequest(BaseModel):
    plan_id: int
    week_number: int
    day_1: str
    day_2: str
    client_today: str | None = None


class CalendarMoveOperation(BaseModel):
    workout_id: int
    target_week: int
    target_day: str


class CalendarMoveRequest(BaseModel):
    plan_id: int
    operations: list[CalendarMoveOperation] = Field(..., min_length=1, max_length=5)
    client_today: str | None = None


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
    lang: str | None = None  # current UI language at click time; falls back to the user's saved lang
    override_gate: bool = False  # explicit athlete confirmation to bypass the 70% completion gate
    # Coach-authored forward guidance for THIS block (distinct from `notes`,
    # which is the athlete's own review of the block just finished) -- only
    # meaningful on the coach-triggered path.
    coach_notes: str | None = None
    # Mid-plan schedule preference edits -- optional; any field left unset
    # (None) leaves that column on the `plans` row unchanged. Same shapes as
    # PlanGenerateRequest's scheduling fields.
    preferred_days: list[str] | None = None
    long_run_day: str | None = None
    days_per_week: int | None = None
    double_session_days: list[str] | None = None
    has_gym_access: bool | None = None
    use_treadmill: bool | None = None
    training_environment: str | None = None
    athlete_notes: str | None = None


class AdaptWeekRequest(BaseModel):
    plan_id: int
    week_number: int  # target week to adapt (1-indexed)
    overall_rpe: int | None = None  # 1-10 fatigue / exertion check
    fatigue_level: str | None = None  # 'easy', 'medium', 'hard', 'exhausted'
    fatigue_notes: str | None = None  # why adapting / fatigue details
    athlete_notes: str | None = None
    coach_notes: str | None = None
    preferred_days: list[str] | None = None
    long_run_day: str | None = None
    days_per_week: int | None = None
    double_session_days: list[str] | None = None
    has_gym_access: bool | None = None
    use_treadmill: bool | None = None
    training_environment: str | None = None
    # Longest unbroken jog in minutes. The beginner progression metric: asked of the
    # athlete rather than parsed out of the model's own prose, because deriving state by
    # reading generated text means the model's formatting drift silently changes the
    # athlete's training.
    max_continuous_jog_min: int | None = None
    lang: str | None = None
    client_today: str | None = None  # the athlete's local date; ±1 day of server UTC (calendar_rules.resolve_today)


# Phase 3 Request Models
class PacingRequest(BaseModel):
    checkpoints: list[dict[str, Any]]
    target_flat_pace_min_km: float | None = None
    target_time_mins: float | None = None  # alternative input: solve base pace from finish time
    split_bias: float = 0.0  # -1..1, positive = negative split (start easier)
    race_start_iso: str | None = None  # e.g. "2026-09-19T05:00" — enables per-segment weather
    runner_weight_kg: float | None = None  # for the energy-cost estimate
    climb_coef: float | None = 10.0  # legacy, ignored by the v2 engine
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


class BetaSignupRequest(BaseModel):
    name: str
    email: str
    referral_source: str
    usage_intent: str


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
    gender: str | None = None  # 'male' | 'female' | 'other'
    height_cm: float | None = None
    weight_kg: float | None = None
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
    training_environment: str | None = "flat"  # 'flat' | 'hilly' | 'mixed'
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
    # Skip generating a plan right now -- save the profile and let the user
    # into the app; they can start a plan later from the Planner tab.
    skip_plan: bool = False
    plan_start_date: str | None = None  # YYYY-MM-DD
    athlete_notes: str | None = None


class UpdateProfileRequest(BaseModel):
    age: int
    max_hr: int
    resting_hr: int
    aet_hr: int
    ant_hr: int
    gemini_api_key: str | None = None
    zone2_pace_min: str | None = None
    zone2_pace_max: str | None = None
    gender: str | None = None  # 'male' | 'female' | 'other'
    height_cm: float | None = None
    weight_kg: float | None = None
    threshold_pace: str | None = None
    coros_vo2max: float | None = None
    coros_running_level: float | None = None
    pace_zone_model: str | None = None
    custom_pace_zones: dict[str, Any] | None = None
    athlete_notes: str | None = None


class SetCoachStatusRequest(BaseModel):
    is_coach: bool


class CoachInviteRequest(BaseModel):
    athlete_email: str


def _resolve_zone_pace_and_hr(
    athlete: dict[str, Any], target_zone: str, duration_minutes: float
) -> tuple[str | None, str | None]:
    """Same zone -> pace/HR math as PlanGenerator.generate_single_workout,
    factored out so coach_update_workout's zone edits use the identical
    computation instead of drifting from it over time."""
    age = int(athlete.get("age", 30))
    max_hr = int(athlete.get("max_hr", 220 - age))
    resting_hr = int(athlete.get("resting_hr", 60))
    aet_hr = int(athlete.get("aet_hr", resting_hr + int((max_hr - resting_hr) * 0.65)))
    ant_hr = int(athlete.get("ant_hr", resting_hr + int((max_hr - resting_hr) * 0.85)))
    hr_zones = TrainingRules.calculate_heart_rate_zones(max_hr, resting_hr, aet_hr, ant_hr)
    est_zones = PlanGenerator.estimate_pace_zones(
        *resolve_zone2_pace(athlete.get("zone2_pace_min"), athlete.get("zone2_pace_max"), athlete.get("goal_type")),
        aet_hr,
        ant_hr,
    )
    pace, _distance_km = PlanGenerator.pace_and_distance_for_zone(target_zone, duration_minutes or 30, est_zones)
    zone_key = target_zone if target_zone in hr_zones else "Zone 2"
    hr_range = f"{hr_zones[zone_key]['min']}-{hr_zones[zone_key]['max']} bpm"
    return pace, hr_range


class CoachWorkoutUpdateRequest(BaseModel):
    day_of_week: str | None = None
    phase: str | None = None
    title: str | None = None
    type: str | None = None
    duration_minutes: float | None = None
    distance_km: float | None = None
    target_zone: str | None = None
    # target_hr_range/target_pace are intentionally NOT accepted here --
    # edit_athlete_workout recomputes both from target_zone server-side so
    # they can never drift from the athlete's actual zones (see its docstring).
    description: str | None = None
    fueling_tip: str | None = None
    interval_reps: int | None = None
    interval_rep_value: float | None = None
    interval_rep_unit: str | None = None


class CoachWorkoutCreateRequest(BaseModel):
    week_number: int
    day_of_week: str
    phase: str
    title: str
    type: str
    duration_minutes: float
    target_zone: str
    distance_km: float | None = None
    target_hr_range: str | None = None
    target_pace: str | None = None
    description: str | None = None
    fueling_tip: str | None = None
    session_slot: str | None = "main"


class CoachWorkoutAiCreateRequest(BaseModel):
    week_number: int
    day_of_week: str
    workout_type: str
    duration_minutes: float  # main set only -- warm-up/cool-down are added on top
    intent: str | None = None  # AI guidance for run types, or literal details for Strength/ME
    target_zone: str | None = None
    target_pace: str | None = None
    interval_reps: int | None = None
    interval_rep_value: float | None = None
    interval_rep_unit: str | None = None


class CoachNoteCreateRequest(BaseModel):
    target_type: str  # 'plan' | 'workout' | 'gear' | 'nutrition' | 'general'
    target_id: int | None = None
    note: str


def _z2_min_for(user: dict[str, Any]) -> str:
    return resolve_zone2_pace(user.get("zone2_pace_min"), user.get("zone2_pace_max"), user.get("goal_type"))[0]


def _z2_max_for(user: dict[str, Any]) -> str:
    return resolve_zone2_pace(user.get("zone2_pace_min"), user.get("zone2_pace_max"), user.get("goal_type"))[1]


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
        "gender": user.get("gender"),
        "height_cm": user.get("height_cm"),
        "weight_kg": user.get("weight_kg"),
        "goal_type": user.get("goal_type"),
        "current_weekly_km": user.get("current_weekly_km", 30.0),
        "max_hr": user.get("max_hr", 185),
        "resting_hr": user.get("resting_hr", 60),
        "aet_hr": user.get("aet_hr", 135),
        "ant_hr": user.get("ant_hr", 165),
        "days_per_week": user.get("days_per_week", 4),
        "preferred_run_days": user.get("preferred_run_days") or "[]",
        "long_run_day": user.get("long_run_day") or "",
        "injury_history": user.get("injury_history") or "",
        "gemini_api_key": user.get("gemini_api_key") or "",
        "zone2_pace_min": _z2_min_for(user),
        "zone2_pace_max": _z2_max_for(user),
        "threshold_pace": user.get("threshold_pace"),
        "coros_vo2max": user.get("coros_vo2max"),
        "coros_running_level": user.get("coros_running_level"),
        "pace_zone_model": user.get("pace_zone_model") or "5_zone",
        "custom_pace_zones": user.get("custom_pace_zones"),
        "is_coach": bool(user.get("is_coach", False)),
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


async def require_coach(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if not user.get("is_coach"):
        raise HTTPException(status_code=403, detail="Coach access required.")
    return user


async def require_athlete_access(athlete_id: int, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Returns the acting user if they may act on athlete_id's data: the
    athlete themself, an admin, or a coach with an active roster link."""
    if user["id"] == athlete_id or user.get("role") == "admin":
        return user
    if user.get("is_coach") and has_active_coach_link(user["id"], athlete_id):
        return user
    raise HTTPException(status_code=403, detail="Not authorized for this athlete.")


COACH_SYSTEM_INSTRUCTION = """
You are Coach Uphill, an elite running coach speaking directly to your athlete — natural, warm, and direct, never robotic.

MUST: Keep every reply to 1-2 short paragraphs or a brief bullet list. NEVER open with a preamble or repeat the athlete's question back to them. NEVER pad with essay-like explanation.
NEVER fabricate a workout detail, product spec, or statistic you are not confident about. If the grounding data below doesn't cover what's asked, say so plainly and answer from general coaching principles instead of inventing specifics.

Domain Boundaries — enforce strictly:
- You ONLY answer questions concerning running (trail, ultra, mountain, road, track), endurance training, strength & mobility for runners, running gear/shoes, injury prevention/recovery, and sports nutrition/hydration.
- If the user asks about ANY topic outside of running, endurance sports, and athletic nutrition (such as coding/software, general trivia, politics, non-sports cooking, mathematics, homework, finance, entertainment, etc.), you MUST politely decline in 1-2 brief sentences and redirect them back to their running and training goals (e.g., "I'm Coach Uphill, specialized exclusively in running, endurance training, and sports nutrition. Let's get back to your training — how can I help with your runs, workouts, or fueling?").

Coaching principles — apply strictly:
1. Trail Running: Scott Johnston's "Training for the Uphill Athlete" principles. Emphasize muscular endurance (e.g., weighted step-ups, hill sprints).
2. Road Running: 80/20 rule — 80% of volume in Zone 1-2, 20% in Zone 3-5.
3. Nutrition: Hydration/electrolyte rates based on sweat rate and target time. Progressive gut-training plans.
4. Gear: Match shoes to foot biomechanics, goals, and surface.
5. Active Training Plan: If calendar workouts appear in Context/Activity Data below, reference them directly for specific pacing, nutrition, or recovery tips.

Tone: warm and encouraging, always actionable — focus on the next concrete step the runner should take.
"""

COACH_COPILOT_SYSTEM_INSTRUCTION = """
You are an AI coaching assistant helping a human coach think through their athlete's training -- you speak TO the coach ABOUT the athlete, never to the athlete directly.

MUST: Keep every reply to 1-2 short paragraphs or a brief bullet list. NEVER open with a preamble or repeat the coach's question back to them.
NEVER fabricate a workout detail, completion status, or statistic about this athlete that isn't in the athlete context below. If the context doesn't cover what's asked, say so plainly rather than guessing, and answer from general coaching principles instead.

Domain Boundaries — enforce strictly:
- Strictly limit discussion to running, endurance training, athlete physiological metrics, workout prescription, recovery, gear, and sports nutrition.
- If prompted about topics unrelated to athlete coaching and endurance sports performance, decline briefly and redirect back to the athlete's training.

Coaching principles — apply strictly:
1. Trail Running: Scott Johnston's "Training for the Uphill Athlete" principles. Emphasize muscular endurance (e.g., weighted step-ups, hill sprints).
2. Road Running: 80/20 rule — 80% of volume in Zone 1-2, 20% in Zone 3-5.
3. When the athlete context below shows missed or incomplete workouts, address that directly and suggest a concrete adjustment.

Tone: direct and pragmatic, like one coach talking shop with another — always actionable, focused on what the coach should do next with this athlete.
"""

COACH_VI_LANGUAGE_INSTRUCTION = """
VIETNAMESE LOCALIZATION & REGISTER CONTRACT (MANDATORY):
The user is using the Vietnamese version (or communicating in Vietnamese). You MUST respond in natural, authentic Vietnamese as spoken by Vietnamese trail and ultra runners:
1. Tone & Register:
   - Speak like an authentic, experienced running coach: warm, direct, encouraging, concise (use second-person 'bạn', active verbs, 1-2 short paragraphs or bullet points).
   - NEVER use stiff corporate/marketing fluff, robotic explanations, or exclamation-mark-heavy cheerleading.
2. KEEP TECHNICAL RUNNING TERMS IN ENGLISH (DO NOT TRANSLATE TO VIETNAMESE):
   - Pacing & Runs: Pace, Easy Run, Long Run, Tempo, Threshold, Interval, Fartlek, Surges, Recovery Run, Hill Repeat, Hill Sprint, Hill Bound, Strides, Warm-up, Cool-down.
   - Training & Physiology: Muscular Endurance (ME), Strength, Zone 1–Zone 5, AeT, AnT, HR, Max HR, Resting HR, RPE, Cadence, Deload, Taper, Block, Split, Checkpoint (CP), Cutoff (COT), DNF, Aerobic, Anaerobic, Aerobic decoupling, Cardiac drift.
   - Terrain & Route: Elevation Gain, D+, GPX, Race, Ultra, Trail, Road, Treadmill.
   - Nutrition & Gear: Gel, Chews, Carbs, Sodium, Electrolytes, Fueling, Gut training, Stack Height, Drop, Carbon Plate, Lug Depth, Rock Plate, Foam Rolling.
   - System: Plan, Coach.
3. MANDATORY FIXED MAPPINGS:
   - Volume / Weekly volume -> 'khối lượng' / 'khối lượng tuần' (ABSOLUTELY NEVER use 'thể tích').
   - Physiology / physical metrics -> 'thể chất', 'chỉ số thể chất' (ABSOLUTELY NEVER use 'sinh lý').
   - Pace -> 'Pace' (NEVER 'tốc độ', which is km/h).
   - Fueling -> 'fueling' or 'dinh dưỡng thi đấu' (NEVER 'tiếp nhiên liệu').
   - Training plan -> 'plan' or 'lịch tập' (NEVER 'giáo án').
   - Workout / session -> 'buổi tập' or 'bài chạy' (NEVER 'bài tập thể dục').
   - Build / generate plan -> 'lên plan' or 'tạo plan' (NEVER 'kiến tạo').
4. STRICT BAN LIST:
   - Absolutely never use: 'kiến tạo', 'bảo chứng', 'chinh phục đỉnh cao', 'bứt phá', 'nâng tầm', 'vượt trội', 'tối ưu hóa', 'toàn diện', 'chuyên sâu', 'độc quyền', 'đột phá', 'mạnh mẽ', 'tuyệt vời', 'uy tín hàng đầu', 'chuẩn mực thế giới', 'đồng hành cùng bạn', 'vận hành', 'tri thức', 'hệ sinh thái', 'giáo án', 'sinh lý', 'thể tích'.
"""


def is_vietnamese_request(
    lang: str | None = None,
    messages: list[ChatMessage] | None = None,
) -> bool:
    """Detect if the user is using the Vietnamese version or requesting in Vietnamese."""
    if lang and str(lang).lower().startswith("vi"):
        return True
    if messages:
        last_msg = messages[-1].content if messages else ""
        vi_chars = set(
            "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ"
        )
        if any(c in vi_chars for c in last_msg):
            return True
    return False


class CoachChatRequest(BaseModel):
    messages: list[ChatMessage]
    lang: str | None = None


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


@app.post("/api/marketing/beta-signup")
def register_beta_signup(req: BetaSignupRequest, request: Request):
    """Save marketing lead beta download request."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    email = req.email.strip().lower()
    name = req.name.strip()
    referral = req.referral_source.strip()
    intent = req.usage_intent.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required.")
    if not referral:
        raise HTTPException(status_code=400, detail="Referral source is required.")
    if not intent:
        raise HTTPException(status_code=400, detail="Usage intent is required.")

    record = create_beta_signup(
        name=name,
        email=email,
        referral_source=referral,
        usage_intent=intent,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    return {
        "status": "ok",
        "message": "Beta signup recorded successfully",
        "id": record.get("id"),
        "ios_url": "https://testflight.apple.com/join/T9WarWaS",
        "android_url": "https://drive.google.com/file/d/17lt8-S1eeyAbUbyR-QSlkr_kBilNnTKB/view?usp=sharing",
    }


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

    # Zone 2 defaults come from the athlete's tier, not from a literal repeated per
    # call site. The old form also treated an explicit "6:30" as "unset" and silently
    # replaced it, so a beginner who genuinely measured 6:30 could not keep it.
    zone2_min, zone2_max = resolve_zone2_pace(request.zone2_pace_min, request.zone2_pace_max, request.goal_type)

    onboarding_data = {
        "dob": request.dob,
        "age": age,
        "gender": request.gender,
        "height_cm": request.height_cm,
        "weight_kg": request.weight_kg,
        "goal_type": request.goal_type,
        "injury_history": request.injury_history,
        "preferred_run_days": request.preferred_run_days or [],
        "long_run_day": request.long_run_day,
        "days_per_week": request.days_per_week or 4,
        "current_weekly_km": request.current_weekly_km or 30.0,
        "max_hr": max_hr,
        "resting_hr": resting_hr,
        "aet_hr": aet_hr,
        "ant_hr": ant_hr,
        "zone2_pace_min": zone2_min,
        "zone2_pace_max": zone2_max,
    }
    update_onboarding_profile(user["id"], onboarding_data)

    if request.skip_plan:
        # Profile saved, no plan row created -- the user starts one later
        # from the Planner tab's own "New Plan" form when they're ready.
        mark_onboarding_complete(user["id"])
        return {"user": format_user_response(get_user_by_id(user["id"]) or user)}

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
    course_context = None
    if is_event:
        request.course_distance_km, request.course_elevation_gain_m, course_context = _resolve_course_match(
            race_name, request.course_distance_km, request.course_elevation_gain_m
        )
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
        has_gym_access=request.has_gym_access or False,
        use_treadmill=request.has_gym_access or False,
        training_environment=request.training_environment or "flat",
        athlete_notes=request.athlete_notes,
    )
    _assess_new_plan(user["id"], plan_id)

    # Mark onboarding complete immediately so the user can enter the app
    mark_onboarding_complete(user["id"])

    fresh_user = get_user_by_id(user["id"]) or user
    model_api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    historical_ceiling = get_user_activity_ceiling(user["id"])

    race_info = {
        "name": race_name,
        "date": race_date,
        "terrain": request.terrain or "trail",
        "goal_type": plan_goal_type,
        "target_time_hours": tth,
        "course_distance_km": request.course_distance_km,
        "course_elevation_gain_m": request.course_elevation_gain_m,
        "course_context": course_context,
        "preferred_days": request.preferred_run_days,
        "long_run_day": request.long_run_day,
        "days_per_week": request.days_per_week,
        "double_session_days": request.double_session_days or [],
        "has_gym_access": request.has_gym_access or False,
        "use_treadmill": request.has_gym_access or False,
        "training_environment": request.training_environment or "flat",
        "plan_start_date": onboarding_start_date,
        "athlete_notes": request.athlete_notes or fresh_user.get("athlete_notes"),
        "historical_ceiling": historical_ceiling,
        # No stored override on a plan being created -- the generator derives the tier.
        "athlete_tier": None,
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
            workouts, resolved_tier = await PlanGenerator.generate_plan_workouts(
                plan_id,
                fresh_user,
                race_info,
                total_weeks,
                api_key=model_api_key,
                block_number=1,
                weeks_per_block=settings.WEEKS_PER_BLOCK,
            )
            save_workouts(plan_id, workouts)
            set_plan_athlete_tier(plan_id, resolved_tier)
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


def _session_review_status(w: dict[str, Any]) -> str:
    """Three-way status label used in the next-block-generation prompt:
    completed (checked off), MISSED (athlete explicitly confirmed), or
    not logged (ambiguous -- may have happened but was never checked off)."""
    if w.get("is_completed") == 1:
        return "completed"
    if w.get("is_missed") == 1:
        return "MISSED"
    return "not logged"


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
def get_pace_zones(model: str | None = None, user: dict[str, Any] = Depends(get_current_user)):
    zone_model = model or user.get("pace_zone_model") or "5_zone"
    threshold_pace = user.get("threshold_pace")

    # If custom pace zones exist and match the requested model, return them directly
    custom_zones = user.get("custom_pace_zones")
    if custom_zones and isinstance(custom_zones, dict) and custom_zones.get("model") == zone_model:
        return custom_zones

    if zone_model == "4_zone":
        if threshold_pace:
            zones = PlanGenerator.calculate_pace_zones_from_threshold(threshold_pace, model="4_zone")
        else:
            zones = PlanGenerator.estimate_pace_zones(
                *resolve_zone2_pace(user.get("zone2_pace_min"), user.get("zone2_pace_max"), user.get("goal_type")),
                user.get("aet_hr"),
                user.get("ant_hr"),
                model="4_zone",
            )
        aet = int(user.get("aet_hr") or 140)
        ant = int(user.get("ant_hr") or 165)
        return {
            "model": "4_zone",
            "threshold_pace": threshold_pace,
            "zone1_pace": zones["zone1_pace"],
            "zone2_pace": zones["zone2_pace"],
            "zone3_pace": zones["zone3_pace"],
            "zone4_pace": zones["zone4_pace"],
            "zone5_pace": zones["zone4_pace"],  # Fallback for legacy 5-zone consumers
            "zone1_hr": f"< {aet} bpm",
            "zone2_hr": f"{aet}-{ant} bpm",
            "zone3_hr": f"{ant}-{ant + 5} bpm",
            "zone4_hr": f"> {ant + 5} bpm",
            "zone5_hr": f"> {ant + 5} bpm",
            "zone_labels": zones.get("zone_labels"),
            "coros_vo2max": user.get("coros_vo2max"),
            "coros_running_level": user.get("coros_running_level"),
        }

    # Default: 5-zone
    zones = PlanGenerator.estimate_pace_zones(
        *resolve_zone2_pace(user.get("zone2_pace_min"), user.get("zone2_pace_max"), user.get("goal_type")),
        user.get("aet_hr"),
        user.get("ant_hr"),
        threshold_pace=threshold_pace,
        model="5_zone",
    )
    hr_zones = TrainingRules.calculate_heart_rate_zones(
        int(user.get("max_hr") or 185),
        int(user.get("resting_hr") or 60),
        user.get("aet_hr"),
        user.get("ant_hr"),
    )
    return {
        "model": "5_zone",
        "threshold_pace": threshold_pace,
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
        "zone_labels": zones.get("zone_labels"),
        "coros_vo2max": user.get("coros_vo2max"),
        "coros_running_level": user.get("coros_running_level"),
    }


@app.post("/api/auth/logout")
def auth_logout(authorization: str | None = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        delete_session(token)
    return {"message": "Logged out successfully."}


# --- Human Coach Roster (Phase 1) ---
# "Coach" here means a human who coaches other users -- distinct from
# "Coach Uphill", the AI persona served by the /api/coach/* endpoints above.
# See docs/superpowers/specs/2026-07-20-coach-role-design.md.


@app.post("/api/admin/users/{user_id}/coach-status")
def set_coach_status(user_id: int, request: SetCoachStatusRequest, admin_user: dict[str, Any] = Depends(require_admin)):
    target = get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    set_user_is_coach(user_id, request.is_coach)
    return format_user_response(get_user_by_id(user_id))


@app.post("/api/coaching/invite")
def invite_athlete(request: CoachInviteRequest, coach: dict[str, Any] = Depends(require_coach)):
    athlete = get_user_by_email(request.athlete_email)
    if not athlete:
        raise HTTPException(
            status_code=404, detail="No account found for that email. Ask the athlete to sign up first."
        )
    if athlete["id"] == coach["id"]:
        raise HTTPException(status_code=400, detail="You cannot invite yourself.")
    existing_active = get_active_coach_link_for_athlete(athlete["id"])
    if existing_active and existing_active["coach_id"] != coach["id"]:
        raise HTTPException(status_code=409, detail="This athlete already has an active coach.")
    return create_coach_invite(coach["id"], athlete["id"])


@app.post("/api/coaching/invites/{invite_id}/accept")
def accept_invite(invite_id: int, user: dict[str, Any] = Depends(get_current_user)):
    invite = get_coach_athlete_by_id(invite_id)
    if not invite or invite["athlete_id"] != user["id"] or invite["status"] != "invited":
        raise HTTPException(status_code=404, detail="Invite not found.")
    existing_active = get_active_coach_link_for_athlete(user["id"])
    if existing_active and existing_active["coach_id"] != invite["coach_id"]:
        raise HTTPException(status_code=409, detail="You already have an active coach.")
    updated = accept_coach_invite(invite_id, user["id"])
    if not updated:
        raise HTTPException(status_code=404, detail="Invite not found.")
    return updated


@app.post("/api/coaching/invites/{invite_id}/decline")
def decline_invite(invite_id: int, user: dict[str, Any] = Depends(get_current_user)):
    updated = decline_coach_invite(invite_id, user["id"])
    if not updated:
        raise HTTPException(status_code=404, detail="Invite not found.")
    return updated


@app.delete("/api/coaching/roster/{link_id}")
def remove_from_roster(link_id: int, user: dict[str, Any] = Depends(get_current_user)):
    updated = remove_coach_athlete_link(link_id, user["id"])
    if not updated:
        raise HTTPException(status_code=404, detail="Roster link not found.")
    return updated


@app.get("/api/coaching/roster")
def get_roster(coach: dict[str, Any] = Depends(require_coach)):
    return get_roster_for_coach(coach["id"])


@app.get("/api/coaching/overview")
def get_coaching_overview(
    days: int = 14,
    athlete_id: int | None = None,
    level: str | None = None,
    coach: dict[str, Any] = Depends(require_coach),
):
    return get_roster_overview_data(coach["id"], days=days, athlete_id=athlete_id, level=level)


@app.get("/api/coaching/my-invites")
def get_my_pending_invites(user: dict[str, Any] = Depends(get_current_user)):
    return get_pending_invites_for_athlete(user["id"])


@app.get("/api/coaching/athletes/{athlete_id}/active-plan")
def get_athlete_active_plan(athlete_id: int, acting_user: dict[str, Any] = Depends(require_athlete_access)):
    plan = get_active_plan(athlete_id)
    if not plan:
        return {"active": False}
    workouts = get_plan_workouts(plan["id"])
    return {"active": True, "plan": plan, "workouts": workouts}


@app.get("/api/coaching/athletes/{athlete_id}/recent-plans")
def get_athlete_recent_plans(athlete_id: int, acting_user: dict[str, Any] = Depends(require_athlete_access)):
    plans = get_recent_plans(athlete_id, limit=3)
    return {"plans": plans}


@app.get("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts")
def get_athlete_plan_workouts(
    athlete_id: int, plan_id: int, acting_user: dict[str, Any] = Depends(require_athlete_access)
):
    _verify_plan_ownership(plan_id, athlete_id)
    return {"workouts": get_plan_workouts(plan_id)}


@app.get("/api/coaching/athletes/{athlete_id}/profile")
def get_athlete_profile(athlete_id: int, acting_user: dict[str, Any] = Depends(require_athlete_access)):
    athlete = get_user_by_id(athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    return format_user_response(athlete)


@app.get("/api/coaching/athletes/{athlete_id}/plans/draft")
def get_athlete_draft_plan(athlete_id: int, acting_user: dict[str, Any] = Depends(require_athlete_access)):
    plan = get_draft_plan_for_athlete(athlete_id)
    if not plan:
        return {"draft": False}
    return {"draft": True, "plan": plan, "workouts": get_plan_workouts(plan["id"])}


@app.put("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts/{workout_id}")
def edit_athlete_workout(
    athlete_id: int,
    plan_id: int,
    workout_id: int,
    request: CoachWorkoutUpdateRequest,
    acting_user: dict[str, Any] = Depends(require_athlete_access),
):
    """Whenever target_zone is part of the edit, target_pace/target_hr_range
    are recomputed from the ATHLETE's own zones (never trusted from the
    client) so an edited workout's pace/HR can never drift from the zone the
    coach actually picked -- see CoachWorkoutUpdateRequest's docstring."""
    plan = get_plan_by_id(plan_id)
    if not plan or plan["user_id"] != athlete_id:
        raise HTTPException(status_code=404, detail="Plan not found.")
    workout = get_workout_by_id(workout_id)
    if not workout or workout["plan_id"] != plan_id:
        raise HTTPException(status_code=404, detail="Workout not found.")
    fields = request.dict(exclude_unset=True)
    if request.target_zone and request.target_zone not in ("Rest",):
        athlete = get_user_by_id(athlete_id)
        fields["target_pace"], fields["target_hr_range"] = _resolve_zone_pace_and_hr(
            athlete, request.target_zone, fields.get("duration_minutes") or workout["duration_minutes"]
        )
    updated = coach_update_workout(workout_id, acting_user["id"], fields)
    return updated


@app.post("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts")
def add_athlete_workout(
    athlete_id: int,
    plan_id: int,
    request: CoachWorkoutCreateRequest,
    acting_user: dict[str, Any] = Depends(require_athlete_access),
):
    plan = get_plan_by_id(plan_id)
    if not plan or plan["user_id"] != athlete_id:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return create_coach_workout(plan_id, acting_user["id"], request.dict())


@app.post("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts/{workout_id}/approve")
def approve_athlete_workout(
    athlete_id: int, plan_id: int, workout_id: int, coach: dict[str, Any] = Depends(require_athlete_access)
):
    """Approves one workout. If this is the first approval on a still-draft
    plan, the plan also flips to 'active' -- there is no separate
    whole-plan-approve action; a draft plan goes live the moment its first
    workout is approved."""
    updated = approve_workout(workout_id, plan_id, athlete_id, coach["id"])
    if not updated:
        raise HTTPException(status_code=404, detail="Workout not found.")
    return updated


@app.post("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts/{workout_id}/remove")
def remove_athlete_workout(
    athlete_id: int, plan_id: int, workout_id: int, acting_user: dict[str, Any] = Depends(require_athlete_access)
):
    """'Removes' a workout by converting it to a rest day in place (no
    delete endpoint exists -- see make_rest_day's docstring for why)."""
    plan = get_plan_by_id(plan_id)
    if not plan or plan["user_id"] != athlete_id:
        raise HTTPException(status_code=404, detail="Plan not found.")
    workout = get_workout_by_id(workout_id)
    if not workout or workout["plan_id"] != plan_id:
        raise HTTPException(status_code=404, detail="Workout not found.")
    return make_rest_day(workout_id, acting_user["id"])


@app.post("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts/ai-create")
async def ai_create_athlete_workout(
    athlete_id: int,
    plan_id: int,
    request: CoachWorkoutAiCreateRequest,
    acting_user: dict[str, Any] = Depends(require_athlete_access),
):
    """Coach co-creation: the coach supplies type/duration/day/intent, Gemini
    fills in the physiological detail grounded in the athlete's own profile.
    The resulting workout is inserted via the same path as a fully-manual
    add (create_coach_workout) -- it starts pending, same as any other new
    or edited workout, and needs its own approve step."""
    plan = get_plan_by_id(plan_id)
    if not plan or plan["user_id"] != athlete_id:
        raise HTTPException(status_code=404, detail="Plan not found.")
    athlete = get_user_by_id(athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    model_api_key = athlete.get("gemini_api_key") or settings.GEMINI_API_KEY
    is_details_only_type = request.workout_type in ("Strength", "Muscular Endurance")
    generated = await PlanGenerator.generate_single_workout(
        user_profile=athlete,
        workout_type=request.workout_type,
        duration_minutes=request.duration_minutes,
        day_of_week=request.day_of_week,
        week_number=request.week_number,
        intent=request.intent,
        api_key=model_api_key,
        target_zone=request.target_zone,
        target_pace=request.target_pace,
        interval_reps=request.interval_reps,
        interval_rep_value=request.interval_rep_value,
        interval_rep_unit=request.interval_rep_unit,
        details=request.intent if is_details_only_type else None,
    )
    return create_coach_workout(plan_id, acting_user["id"], generated)


def _build_athlete_context_block(athlete: dict[str, Any]) -> str:
    """Server-assembled grounding text for the co-pilot -- deliberately not
    trusting any client-supplied context, unlike the self-serve
    /api/coach/chat. Reuses get_active_plan/get_plan_workouts exactly as
    Phase 2's read endpoints do; no new queries."""
    plan = get_active_plan(athlete["id"])
    if not plan:
        return f"Athlete: {athlete.get('name') or athlete.get('email')}\nThis athlete has no active training plan yet."

    workouts = get_plan_workouts(plan["id"])
    current_week = compute_current_week(plan.get("start_date"), plan.get("total_weeks"))
    week_workouts = [w for w in workouts if w["week_number"] == current_week]

    lines = [
        f"Athlete: {athlete.get('name') or athlete.get('email')}",
        f"Active Plan: {plan['race_name']} on {plan['race_date']} ({plan['goal_type']}, week {current_week} of {plan['total_weeks']})",
    ]
    history_text = race_history.prompt_summary(athlete["id"])
    if history_text:
        lines.append(history_text)
    if athlete.get("threshold_pace"):
        lines.append(f"Threshold Pace: {athlete['threshold_pace']}/km | VO2max: {athlete.get('coros_vo2max') or 'N/A'}")

    if not week_workouts:
        lines.append("No workouts recorded for the current week.")
    else:
        lines.append("This week's workouts:")
        for w in week_workouts:
            status = "completed" if w.get("is_completed") else ("missed" if w.get("is_missed") else "not yet completed")
            rpe = f", RPE {w['rpe']}" if w.get("rpe") else ""
            lines.append(
                f"- {w['day_of_week']}: {w['title']} ({w['type']}, {w['duration_minutes']} min, {status}{rpe})"
            )

    # Recent watch activity adherence & execution quality (last 14 days)
    try:
        from datetime import date, timedelta

        until = date.today() + timedelta(days=1)
        since = until - timedelta(days=14)
        recent_matches = get_matches_for_review(athlete["id"], since, until, plan_id=plan["id"])
        if recent_matches:
            lines.append("\nRecent Watch Activities & Execution Quality (Last 14 Days):")
            for act in recent_matches[-6:]:
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
                notes = f" - Notes: {takeaways}" if takeaways else ""
                lines.append(
                    f"  * {str(act.get('start_time'))[:10]}: '{w_title}' - {dist} in {dur}, {hr}. {q_grade}{notes}"
                )
    except Exception as exc:
        print(f"[AthleteContext] Warning loading recent matches: {exc}")

    return "\n".join(lines)


@app.post("/api/coaching/athletes/{athlete_id}/chat")
async def coach_chat_copilot(
    athlete_id: int, request: CoachChatRequest, coach: dict[str, Any] = Depends(require_athlete_access)
):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Message history cannot be empty.")

    athlete = get_user_by_id(athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    athlete_context = _build_athlete_context_block(athlete)

    # Resolved against the COACH, not the athlete -- see the Phase 4 plan's
    # Global Constraints for why this deliberately diverges from Phase 3's
    # plan-generation key resolution.
    fresh_coach = get_user_by_id(coach["id"]) or coach
    model_api_key = fresh_coach.get("gemini_api_key") or settings.GEMINI_API_KEY

    kb_context = ""
    if model_api_key:
        try:
            import asyncio

            from services.kb_context import render_principles_context
            from services.kb_retrieval import search_scheduler_chunks

            last_user_msg = request.messages[-1].content
            hits = await asyncio.to_thread(search_scheduler_chunks, last_user_msg, model_api_key, 6)
            kb_context = render_principles_context(hits, heading="UPHILL ATHLETE PHILOSOPHY (grounding context)")
        except Exception as kb_ex:
            print(f"[CoachCopilot][KB] Retrieval failed (continuing without): {kb_ex}")

    vi_rule = ""
    if is_vietnamese_request(lang=request.lang, messages=request.messages):
        vi_rule = f"\n\n{COACH_VI_LANGUAGE_INSTRUCTION}"

    full_system_prompt = (
        f"{COACH_COPILOT_SYSTEM_INSTRUCTION}"
        f"{vi_rule}"
        f"\n\n=== ATHLETE CONTEXT ===\n{athlete_context}\n=== END ATHLETE CONTEXT ===\n"
        f"{kb_context}"
    )

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
            print(f"[CoachCopilot][Gemini] FAILED: {e}")

    last_user_msg = request.messages[-1].content
    mock_reply = (
        "I'm running in offline mock mode right now. "
        f"You asked: '{last_user_msg}'. "
        "Once a Gemini API key is configured (yours or the server's), I'll answer grounded in this athlete's actual plan and workout data."
    )
    return {"role": "assistant", "content": mock_reply}


_VALID_NOTE_TARGET_TYPES = {"plan", "workout", "gear", "nutrition", "general"}


@app.post("/api/coaching/athletes/{athlete_id}/notes")
def create_athlete_note(
    athlete_id: int, request: CoachNoteCreateRequest, acting_user: dict[str, Any] = Depends(require_athlete_access)
):
    if request.target_type not in _VALID_NOTE_TARGET_TYPES:
        raise HTTPException(status_code=422, detail=f"target_type must be one of {sorted(_VALID_NOTE_TARGET_TYPES)}")
    return create_coach_note(acting_user["id"], athlete_id, request.target_type, request.target_id, request.note)


@app.get("/api/coaching/athletes/{athlete_id}/notes")
def get_athlete_notes(
    athlete_id: int,
    target_type: str | None = None,
    target_id: int | None = None,
    acting_user: dict[str, Any] = Depends(require_athlete_access),
):
    return {"notes": get_coach_notes(athlete_id, target_type, target_id)}


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


async def _generate_plan_for_athlete(
    request: PlanGenerateRequest,
    athlete_id: int,
    created_by_user_id: int,
    plan_status: str,
    job_owner_user_id: int,
) -> dict[str, Any]:
    """Shared core of plan generation, used by both the self-serve
    /api/coach/generate-plan (athlete_id == created_by_user_id ==
    job_owner_user_id, plan_status='active') and the coach-triggered
    /api/coaching/athletes/{athlete_id}/generate-plan (created_by_user_id =
    coach.id, plan_status='draft', job_owner_user_id = coach.id so only the
    coach -- not yet the athlete -- can poll the job)."""
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

    course_context = None
    if is_race_or_dist:
        request.course_distance_km, request.course_elevation_gain_m, course_context = _resolve_course_match(
            race_name_str, request.course_distance_km, request.course_elevation_gain_m
        )

    plan_id = create_plan(
        user_id=athlete_id,
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
        double_session_days=request.double_session_days or [],
        start_date=start_date_str,
        has_gym_access=request.has_gym_access or False,
        use_treadmill=request.use_treadmill,
        training_environment=request.training_environment or "flat",
        created_by_user_id=created_by_user_id,
        plan_status=plan_status,
        athlete_notes=request.athlete_notes,
    )
    _assess_new_plan(athlete_id, plan_id)

    # Fetch latest athlete details from database to ensure fresh physiological values
    fresh_user = get_user_by_id(athlete_id) or {"id": athlete_id}
    historical_ceiling = get_user_activity_ceiling(athlete_id)

    race_info = {
        "name": race_name_str,
        "date": race_date_str,
        "terrain": request.terrain,
        "goal_type": request.goal_type,
        "target_time_hours": request.target_time_hours,
        "course_distance_km": request.course_distance_km,
        "course_elevation_gain_m": request.course_elevation_gain_m,
        "course_context": course_context,
        # Scheduling preferences (plan-level)
        "preferred_days": request.preferred_days,
        "long_run_day": request.long_run_day,
        "days_per_week": request.days_per_week,
        "double_session_days": request.double_session_days or [],
        "has_gym_access": request.has_gym_access or False,
        "use_treadmill": request.use_treadmill
        if request.use_treadmill is not None
        else (request.has_gym_access or False),
        "training_environment": request.training_environment or "flat",
        # Start date
        "plan_start_date": start_date_str,
        "athlete_notes": request.athlete_notes or fresh_user.get("athlete_notes"),
        "historical_ceiling": historical_ceiling,
        # No stored override on a plan being created -- the generator derives the tier.
        "athlete_tier": None,
        "lang": request.lang or "en",
        "coach_notes": request.coach_notes,
    }

    # Merge onboarding/non-race context fields into fresh_user dict for plan generator
    fresh_user = dict(fresh_user)
    fresh_user.update(
        {
            "current_weekly_km": request.current_weekly_km,
            "time_away": request.time_away,
            "fitness_feel": request.fitness_feel,
            "race_distance_completed": request.race_distance_completed,
            "days_since_race": request.days_since_race,
            "recovery_feel": request.recovery_feel,
        }
    )
    # Persist the freshly-entered weekly volume so it stays the source of
    # truth for chat context, gear/nutrition displays, etc. between plans.
    update_user_weekly_km(athlete_id, request.current_weekly_km)

    # Resolve Gemini API Key (per-user key with global settings fallback)
    model_api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    cutoff = request.cutoff_time_hours

    # Create job entry and fire plan generation in the background
    job_id = str(_uuid.uuid4())
    plan_jobs[job_id] = {
        "status": "generating",
        "user_id": job_owner_user_id,
        "plan_id": plan_id,
        "workouts": None,
        "error": None,
    }

    async def _run_gen():
        try:
            workouts, resolved_tier = await PlanGenerator.generate_plan_workouts(
                plan_id,
                fresh_user,
                race_info,
                total_weeks,
                api_key=model_api_key,
                cutoff_time_hours=cutoff,
                block_number=1,
                weeks_per_block=settings.WEEKS_PER_BLOCK,
            )
            save_workouts(plan_id, workouts, auto_approve=(plan_status != "draft"))
            set_plan_athlete_tier(plan_id, resolved_tier)
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


@app.post("/api/coach/generate-plan")
async def generate_training_plan(request: PlanGenerateRequest, user: dict[str, Any] = Depends(get_current_user)):
    try:
        return await _generate_plan_for_athlete(
            request,
            athlete_id=user["id"],
            created_by_user_id=user["id"],
            plan_status="active",
            job_owner_user_id=user["id"],
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")


@app.post("/api/coaching/athletes/{athlete_id}/generate-plan")
async def coach_generate_plan(
    athlete_id: int, request: PlanGenerateRequest, coach: dict[str, Any] = Depends(require_athlete_access)
):
    if not get_user_by_id(athlete_id):
        raise HTTPException(status_code=404, detail="Athlete not found.")
    try:
        return await _generate_plan_for_athlete(
            request,
            athlete_id=athlete_id,
            created_by_user_id=coach["id"],
            plan_status="draft",
            job_owner_user_id=coach["id"],
        )
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
        # Return fresh workouts from DB (job store may be large; DB is authoritative).
        # Fetched by the job's own plan_id, not the poller's "active plan" -- the
        # poller may be a coach reviewing a draft they generated for someone else,
        # in which case get_active_plan(poller_id) would return the wrong plan (or
        # none at all).
        response["workouts"] = get_plan_workouts(job["plan_id"])
        response["plan"] = get_plan_by_id(job["plan_id"])
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
    total_blocks = block_number_for_week(max_week)  # number of blocks with any workouts
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


@app.get("/api/coach/block-evaluation/{plan_id}/{block_number}")
def get_plan_block_evaluation(plan_id: int, block_number: int, user: dict[str, Any] = Depends(get_current_user)):
    """Return coach evaluation & takeaways for a completed 2-week block."""
    _verify_plan_ownership(plan_id, user["id"])
    return evaluate_block_performance(user["id"], plan_id, block_number)


@app.get("/api/coach/week-review/{plan_id}/{week_number}")
def get_plan_week_review(plan_id: int, week_number: int, user: dict[str, Any] = Depends(get_current_user)):
    """Read-only planned-vs-actual review for a single week: completion, distance,
    vert, per-workout breakdown, unplanned activities, and a short narrative.
    Additive alongside block-level review/completion -- does not affect the
    70% next-block gate or block_reviews."""
    _verify_plan_ownership(plan_id, user["id"])
    plan = get_plan_by_id(plan_id)
    review = get_week_review(user["id"], plan_id, week_number, plan.get("start_date") if plan else None)
    review["narrative"] = generate_week_narrative(review)
    return review


@app.delete("/api/coach/plans/{plan_id}")
def delete_plan_endpoint(plan_id: int, user: dict[str, Any] = Depends(get_current_user)):
    """Delete a plan belonging to the current user."""
    _verify_plan_ownership(plan_id, user["id"])
    deleted = delete_plan(plan_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return {"success": True, "message": "Plan deleted successfully", "plan_id": plan_id}


async def _generate_next_block_for_athlete(
    request: GenerateNextBlockRequest, athlete_id: int, job_owner_user_id: int
) -> dict[str, Any]:
    """Shared core of next-block generation, used by both the self-serve
    /api/coach/generate-next-block (athlete_id == job_owner_user_id) and the
    coach-triggered /api/coaching/athletes/{athlete_id}/generate-next-block
    (job_owner_user_id = coach.id, so only the coach who kicked it off polls
    it via the shared /api/coach/plan-status/{job_id}, same pattern as
    _generate_plan_for_athlete).
    """
    import asyncio

    # Ownership check FIRST — before any reads or writes on this plan
    recent = get_recent_plans(athlete_id, limit=100)
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
            _existing_block_num = job.get("block_number", request.block_number)
            _existing_week_start, _existing_week_end = week_range_for_block(_existing_block_num)
            return {
                "job_id": existing_job_id,
                "plan_id": request.plan_id,
                "block_number": _existing_block_num,
                "week_start": _existing_week_start,
                "week_end": min(_existing_week_end, plan.get("total_weeks", 12)),
            }

    prev_block = request.block_number - 1

    # Enforce 70% completion gate on the preceding block, unless the athlete
    # has explicitly confirmed they want to proceed anyway.
    override_used = False
    if prev_block >= 1:
        completion = get_block_completion(request.plan_id, prev_block)
        if not completion["unlocked"]:
            if not request.override_gate:
                raise HTTPException(
                    status_code=403,
                    detail=f"Block {prev_block} is {completion['completion_pct']}% complete. Need ≥70% to unlock the next block.",
                )
            override_used = True

    # If the caller passes RPE/notes, save them as the review for the previous block
    if prev_block >= 1 and (request.overall_rpe is not None or request.notes):
        save_block_review(
            plan_id=request.plan_id,
            block_number=prev_block,
            overall_rpe=request.overall_rpe,
            notes=request.notes,
        )

    total_weeks = plan.get("total_weeks", 12)
    block_start, block_end = week_range_for_block(request.block_number)
    if block_start > total_weeks:
        raise HTTPException(status_code=400, detail="All blocks for this plan have already been generated.")

    # Mid-plan schedule preference edit: if the athlete changed any Schedule
    # Preferences field for this next block, persist it to the plans row
    # BEFORE building race_info below, so this call's own generation uses the
    # new values immediately (nothing else caches the old ones). Placed after
    # every check above that can reject the request (ownership, double-submit,
    # completion gate, all-blocks-generated) so a rejected request never
    # mutates the plan's schedule fields.
    _schedule_fields = (
        request.preferred_days,
        request.long_run_day,
        request.days_per_week,
        request.double_session_days,
        request.has_gym_access,
        request.use_treadmill,
        request.training_environment,
        request.athlete_notes,
    )
    if any(f is not None for f in _schedule_fields):
        updated_plan = update_plan_schedule(
            plan_id=request.plan_id,
            preferred_run_days=request.preferred_days,
            long_run_day=request.long_run_day,
            days_per_week=request.days_per_week,
            double_session_days=request.double_session_days,
            has_gym_access=request.has_gym_access,
            use_treadmill=request.use_treadmill,
            training_environment=request.training_environment,
            athlete_notes=request.athlete_notes,
        )
        if updated_plan:
            plan = updated_plan

    fresh_user = get_user_by_id(athlete_id)
    if not fresh_user:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    # Build compact block context for previous blocks
    reviews = get_block_reviews(request.plan_id)
    all_workouts = get_plan_workouts(request.plan_id)

    review_map = {r["block_number"]: r for r in (reviews or [])}

    block_context = None
    context_lines: list[str] = []

    # Newest block first: it carries per-session detail, and this blob is the
    # unbounded tail of the prompt — older summaries are the right thing to lose
    # if anything is, not last block's session-by-session feedback.
    for blk in range(request.block_number - 1, 0, -1):
        wk_start, wk_end = week_range_for_block(blk)

        block_wos = [
            w for w in all_workouts if wk_start <= (w.get("week_number") or 0) <= wk_end and w.get("type") != "Rest"
        ]
        completed_wos = [w for w in block_wos if w.get("is_completed") == 1]

        # Planned totals (from generated workouts), summed week-by-week
        planned_weeks = [get_week_planned_volume(request.plan_id, wk) for wk in range(wk_start, wk_end + 1)]
        planned_km = sum(w["distance_km"] for w in planned_weeks)
        planned_min = sum(w["duration_minutes"] for w in planned_weeks)

        # Actual totals (from true GPS watch activities, both matched & unplanned)
        actual_vol = get_block_actual_volume(
            user_id=athlete_id,
            plan_id=request.plan_id,
            wk_start=wk_start,
            wk_end=wk_end,
            plan_start_date=plan.get("start_date"),
        )
        if actual_vol.get("total_activities_count", 0) > 0:
            actual_km = actual_vol["total_actual_km"]
            actual_min = actual_vol["total_actual_minutes"]
            actual_vert = actual_vol["total_actual_vert_m"]
        else:
            actual_km = sum(w.get("distance_km") or 0 for w in completed_wos)
            actual_min = sum(w.get("duration_minutes") or 0 for w in completed_wos)
            actual_vert = sum(w.get("elevation_gain_m") or 0 for w in completed_wos)

        unplanned_count = actual_vol.get("unplanned_count", 0)
        unplanned_km = actual_vol.get("unplanned_km", 0.0)

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

        # block_wos is already filtered to non-Rest workouts (see its
        # definition above, earlier in this loop) -- classify by review status.
        missed = [
            f'{w.get("day_of_week","?")} {w.get("title") or w.get("type","?")}'
            for w in block_wos
            if _session_review_status(w) == "MISSED"
        ]
        not_logged = [
            f'{w.get("day_of_week","?")} {w.get("title") or w.get("type","?")}'
            for w in block_wos
            if _session_review_status(w) == "not logged"
        ]

        # Compose the compact summary line
        line = (
            f"Block {blk} (Wk {wk_start}-{wk_end}): "
            f"{sessions_done}/{sessions_total} sessions ({completion_pct}%) | "
            f"Actual {actual_km:.1f}km/{actual_min/60:.1f}h"
            + (f" (+{actual_vert:.0f}m D+)" if actual_vert > 0 else "")
            + f" vs Planned {planned_km:.1f}km/{planned_min/60:.1f}h"
        )
        if unplanned_count > 0:
            line += f" [Includes {unplanned_count} unplanned watch activity: {unplanned_km:.1f}km]"
        if block_rpe:
            if block_rpe <= 2:
                feeling_label = "Very Light"
            elif block_rpe <= 4:
                feeling_label = "Light"
            elif block_rpe <= 6:
                feeling_label = "Moderate"
            elif block_rpe <= 8:
                feeling_label = "Hard"
            else:
                feeling_label = "Max Effort"
            line += f" | Effort: {feeling_label} (RPE {block_rpe}/10)"
        context_lines.append(line)

        if block_note:
            context_lines.append(f'  Athlete note: "{block_note}"')

        if blk == prev_block and override_used:
            context_lines.append(
                f"  ⚠ Block {blk} generated via override at {completion['completion_pct']}% "
                f"(below the 70% threshold)."
            )

        if blk == request.block_number - 1:
            # Evaluate coach feedback on this most recent block:
            prev_eval = evaluate_block_performance(athlete_id, request.plan_id, blk)
            if prev_eval.get("coach_summary"):
                context_lines.append(f"  Coach evaluation (Block {blk}): {prev_eval['coach_summary']}")
            if prev_eval.get("avg_quality_score") is not None:
                context_lines.append(
                    f"  Execution quality: {prev_eval['avg_quality_score']}% (Grade {prev_eval['quality_grade']})"
                )
            for tk in prev_eval.get("coaching_takeaways", []):
                context_lines.append(f"  Coach takeaway: {tk}")
            for cn in prev_eval.get("coach_notes", []):
                context_lines.append(f'  Coach directive on file: "{cn}"')

            # Most recent block: one line per session — performance, feedback,
            # RPE — so the next block reacts to specific sessions, not averages.
            context_lines.append("  Session-by-session (previous block):")
            for w in block_wos:
                dur = w.get("duration_minutes") or 0
                km = w.get("distance_km") or 0
                planned = f"{w.get('title') or w.get('type', '?')} ({dur:.0f}min" + (f"/{km:.1f}km)" if km else ")")
                status = _session_review_status(w)
                if status == "completed":
                    detail = "completed"
                    if w.get("rpe"):
                        r = w["rpe"]
                        f_lbl = (
                            "Very Light"
                            if r <= 2
                            else "Light"
                            if r <= 4
                            else "Moderate"
                            if r <= 6
                            else "Hard"
                            if r <= 8
                            else "Max Effort"
                        )
                        detail += f", Feeling: {f_lbl} (RPE {r}/10)"
                    if w.get("notes"):
                        detail += f', feedback: "{w["notes"]}"'
                else:
                    detail = status
                context_lines.append(
                    f"    W{w.get('week_number', '?')} {w.get('day_of_week', '?')} — {planned}: {detail}"
                )
        else:
            # Older blocks: keep the compact summary form
            for n in session_notes:
                context_lines.append(f"  Session note — {n}")
            if missed:
                context_lines.append(
                    f"  Missed: {', '.join(missed[:3])}"
                    + (" +" + str(len(missed) - 3) + " more" if len(missed) > 3 else "")
                )
            if not_logged:
                context_lines.append(
                    f"  Not logged: {', '.join(not_logged[:3])}"
                    + (" +" + str(len(not_logged) - 3) + " more" if len(not_logged) > 3 else "")
                )

    if context_lines:
        block_context = "\n".join(context_lines)

    _, _, course_context = _resolve_course_match(
        plan.get("race_name"), plan.get("course_distance_km"), plan.get("course_elevation_gain_m")
    )

    active_coach_notes = []
    if request.coach_notes:
        active_coach_notes.append(request.coach_notes)
    if "prev_eval" in locals() and prev_eval.get("coach_notes"):
        for cn in prev_eval["coach_notes"]:
            if cn not in active_coach_notes:
                active_coach_notes.append(cn)

    readiness_summary = get_recent_readiness_summary(athlete_id, days=7)
    historical_ceiling = get_user_activity_ceiling(athlete_id)

    race_info = {
        "name": plan.get("race_name", "Training Plan"),
        "date": plan.get("race_date"),
        "terrain": fresh_user.get("terrain", "trail"),
        "goal_type": plan.get("goal_type"),
        "target_time_hours": plan.get("target_time_hours"),
        "course_distance_km": plan.get("course_distance_km"),
        "course_elevation_gain_m": plan.get("course_elevation_gain_m"),
        "course_context": course_context,
        "preferred_days": plan.get("preferred_run_days"),
        "long_run_day": plan.get("long_run_day"),
        "days_per_week": plan.get("days_per_week"),
        "double_session_days": plan.get("double_session_days"),
        "has_gym_access": plan.get("has_gym_access", False),
        "use_treadmill": plan.get("use_treadmill", False),
        "training_environment": plan.get("training_environment") or "flat",
        "plan_start_date": plan.get("start_date"),
        "athlete_notes": request.athlete_notes or plan.get("athlete_notes") or fresh_user.get("athlete_notes"),
        "historical_ceiling": historical_ceiling,
        # Explicit per-plan tier override; None means the generator derives it.
        "athlete_tier": plan.get("athlete_tier"),
        "readiness_summary": readiness_summary,
        "lang": request.lang or fresh_user.get("lang", "en"),
        "coach_notes": "\n".join(active_coach_notes) if active_coach_notes else None,
    }

    model_api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    print(
        f"[NextBlock] plan_id={request.plan_id} block={request.block_number} "
        f"gemini_key={'yes' if model_api_key else 'NO — will use rule-based'} "
        f"plan_start_date={race_info.get('plan_start_date')} "
        f"block_context_lines={len(block_context.splitlines()) if block_context else 0}"
    )

    job_id = str(_uuid.uuid4())
    plan_jobs[job_id] = {
        "status": "generating",
        "user_id": job_owner_user_id,
        "plan_id": request.plan_id,
        "kind": "next_block",
        "block_number": request.block_number,
        "workouts": None,
        "error": None,
    }

    async def _run_next_block():
        try:
            workouts, resolved_tier = await PlanGenerator.generate_plan_workouts(
                request.plan_id,
                fresh_user,
                race_info,
                total_weeks,
                api_key=model_api_key,
                block_number=request.block_number,
                weeks_per_block=settings.WEEKS_PER_BLOCK,
                block_context=block_context,
            )
            save_workouts(request.plan_id, workouts)
            set_plan_athlete_tier(request.plan_id, resolved_tier)
            plan_jobs[job_id]["workouts"] = workouts
            plan_jobs[job_id]["status"] = "done"
            print(f"[NextBlock][{job_id}] Block {request.block_number} complete — {len(workouts)} workouts saved.")

            # Best-effort athlete-facing narrative, from the same Gemini response
            # context as the generation itself. Never allowed to fail the job --
            # workouts are already saved and the job already marked "done" above.
            try:
                last_week_review, this_week_description = await PlanGenerator.generate_week_narrative(
                    race_info=race_info,
                    block_context=block_context or "",
                    workouts=workouts,
                    api_key=model_api_key,
                )
                if prev_block >= 1 and last_week_review:
                    upsert_block_review_ai_fields(request.plan_id, prev_block, ai_last_week_review=last_week_review)
                if this_week_description:
                    upsert_block_review_ai_fields(
                        request.plan_id, request.block_number, ai_this_week_description=this_week_description
                    )
            except Exception as ex:
                print(f"[NextBlock][{job_id}] Week narrative FAILED (non-fatal): {ex}")
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
        "week_end": min(block_end, total_weeks),
    }


@app.post("/api/coach/generate-next-block")
async def generate_next_block(request: GenerateNextBlockRequest, user: dict[str, Any] = Depends(get_current_user)):
    """
    Generate the next 2-week block for an existing plan.
    Requires the previous block to be ≥70% complete by training hours.
    Injects block review feedback into the generation prompt.
    """
    return await _generate_next_block_for_athlete(request, athlete_id=user["id"], job_owner_user_id=user["id"])


@app.post("/api/coaching/athletes/{athlete_id}/generate-next-block")
async def coach_generate_next_block(
    athlete_id: int, request: GenerateNextBlockRequest, coach: dict[str, Any] = Depends(require_athlete_access)
):
    """Coach-scoped mirror of /api/coach/generate-next-block -- lets a coach
    generate the next block for an athlete they're linked to, instead of only
    the athlete's own session being able to (see coach_generate_plan for the
    same pattern on initial plan generation)."""
    return await _generate_next_block_for_athlete(request, athlete_id=athlete_id, job_owner_user_id=coach["id"])


async def _adapt_week_for_athlete(request: AdaptWeekRequest, athlete_id: int, job_owner_user_id: int) -> dict[str, Any]:
    """Shared core of week adaptation, used by both the self-serve
    /api/coach/adapt-week (athlete_id == job_owner_user_id) and the
    coach-triggered /api/coaching/athletes/{athlete_id}/adapt-week.
    """
    import asyncio
    import uuid as _uuid

    recent = get_recent_plans(athlete_id, limit=100)
    plan = next((p for p in recent if p["id"] == request.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    total_weeks = plan.get("total_weeks", 12)
    if request.week_number < 1 or request.week_number > total_weeks:
        raise HTTPException(status_code=400, detail="Invalid week number.")

    max_week = get_max_generated_week(request.plan_id)
    if request.week_number > max_week:
        raise HTTPException(
            status_code=400,
            detail=f"Week {request.week_number} has not been generated yet. Current generated weeks: 1-{max_week}.",
        )

    # Guard against duplicate concurrent job
    for existing_job_id, job in plan_jobs.items():
        if (
            job.get("plan_id") == request.plan_id
            and job.get("kind") == "adapt_week"
            and job.get("target_week") == request.week_number
            and job.get("status") == "generating"
        ):
            return {
                "job_id": existing_job_id,
                "plan_id": request.plan_id,
                "week_number": request.week_number,
            }

    today = resolve_today(request.client_today, calendar_ops.server_today())
    plan_rows = week_rebuild.load_plan_rows(request.plan_id)
    try:
        rng = week_rebuild.rebuild_range(plan, plan_rows, request.week_number, today)
    except GuardViolation as gv:
        raise HTTPException(status_code=422, detail={"code": gv.code, "params": gv.params})

    # Record the reported jog time BEFORE reading the profile, so this week's tier and
    # prompt reflect what the athlete just told us rather than last week's number.
    if request.max_continuous_jog_min:
        set_max_continuous_jog_min(athlete_id, request.max_continuous_jog_min)

    inputs = week_rebuild.build_rebuild_inputs(
        athlete_id,
        plan,
        plan_rows,
        rng,
        week_rebuild.RebuildRequest(
            **request.model_dump(exclude={"plan_id", "max_continuous_jog_min", "client_today"})
        ),
    )

    job_id = str(_uuid.uuid4())
    plan_jobs[job_id] = {
        "status": "generating",
        "user_id": job_owner_user_id,
        "plan_id": request.plan_id,
        "kind": "adapt_week",
        "target_week": request.week_number,
        "workouts": None,
        "error": None,
    }

    async def _run_adapt_week():
        try:
            draft = await week_rebuild.generate_week_draft(inputs, rng)
            week_rebuild.write_draft(plan, request.week_number, today, draft)
            plan_jobs[job_id]["workouts"] = draft.workouts
            plan_jobs[job_id]["status"] = "done"
            print(f"[AdaptWeek][{job_id}] Week {request.week_number} complete — {len(draft.workouts)} workouts saved.")
        except Exception as ex:
            plan_jobs[job_id]["status"] = "error"
            plan_jobs[job_id]["error"] = str(ex)
            print(f"[AdaptWeek][{job_id}] Week {request.week_number} FAILED: {ex}")

    asyncio.create_task(_run_adapt_week())

    return {
        "job_id": job_id,
        "plan_id": request.plan_id,
        "week_number": request.week_number,
    }


@app.post("/api/coach/adapt-week")
async def adapt_week(request: AdaptWeekRequest, user: dict[str, Any] = Depends(get_current_user)):
    """
    Adapt and regenerate an upcoming week in the current plan based on athlete feedback/fatigue.
    Preserves completed / GPS-matched workouts, updates uncompleted workouts for that week.
    """
    return await _adapt_week_for_athlete(request, athlete_id=user["id"], job_owner_user_id=user["id"])


@app.post("/api/coaching/athletes/{athlete_id}/adapt-week")
async def coach_adapt_week(
    athlete_id: int, request: AdaptWeekRequest, coach: dict[str, Any] = Depends(require_athlete_access)
):
    """Coach-scoped mirror of /api/coach/adapt-week -- lets a coach adapt an upcoming week
    for a linked athlete."""
    return await _adapt_week_for_athlete(request, athlete_id=athlete_id, job_owner_user_id=coach["id"])


@app.get("/api/coaching/athletes/{athlete_id}/block-completion/{plan_id}")
def get_athlete_plan_block_completion(
    athlete_id: int, plan_id: int, coach: dict[str, Any] = Depends(require_athlete_access)
):
    """Coach-scoped mirror of /api/coach/block-completion/{plan_id} -- verifies
    plan ownership against the athlete being viewed, not the caller."""
    _verify_plan_ownership(plan_id, athlete_id)
    max_week = get_max_generated_week(plan_id)
    total_blocks = block_number_for_week(max_week)
    blocks = []
    for b in range(1, total_blocks + 1):
        blocks.append(get_block_completion(plan_id, b))
    return {"plan_id": plan_id, "blocks": blocks, "max_generated_week": max_week}


@app.post("/api/coaching/athletes/{athlete_id}/block-review")
def submit_athlete_block_review(
    athlete_id: int, request: BlockReviewRequest, coach: dict[str, Any] = Depends(require_athlete_access)
):
    """Coach-scoped mirror of /api/coach/block-review."""
    _verify_plan_ownership(request.plan_id, athlete_id)
    review = save_block_review(
        plan_id=request.plan_id,
        block_number=request.block_number,
        overall_rpe=request.overall_rpe,
        notes=request.notes,
    )
    return {"review": review}


@app.get("/api/coaching/athletes/{athlete_id}/block-evaluation/{plan_id}/{block_number}")
def get_athlete_block_evaluation(
    athlete_id: int, plan_id: int, block_number: int, coach: dict[str, Any] = Depends(require_athlete_access)
):
    """Coach-scoped mirror of /api/coach/block-evaluation/{plan_id}/{block_number}."""
    _verify_plan_ownership(plan_id, athlete_id)
    return evaluate_block_performance(athlete_id, plan_id, block_number)


@app.get("/api/coaching/athletes/{athlete_id}/week-review/{plan_id}/{week_number}")
def get_athlete_week_review(
    athlete_id: int, plan_id: int, week_number: int, coach: dict[str, Any] = Depends(require_athlete_access)
):
    """Coach-scoped mirror of /api/coach/week-review/{plan_id}/{week_number}."""
    _verify_plan_ownership(plan_id, athlete_id)
    plan = get_plan_by_id(plan_id)
    review = get_week_review(athlete_id, plan_id, week_number, plan.get("start_date") if plan else None)
    review["narrative"] = generate_week_narrative(review)
    return review


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
    # Routed through the guarded calendar engine (Coach Chat sub-project 4a) so a
    # manual swap can no longer move matched/completed history or push workouts
    # into the past. Response shape unchanged, plus `warnings`.
    if request.day_1 == request.day_2:
        active_plan = get_active_plan(user["id"])
        if not active_plan or active_plan["id"] != request.plan_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this plan.")
        return {"message": "Swapped successfully", "workouts": get_plan_workouts(request.plan_id), "warnings": []}
    today = resolve_today(request.client_today, calendar_ops.server_today())
    op = {"op": "swap_days", "week": request.week_number, "day_1": request.day_1, "day_2": request.day_2}
    try:
        changes = calendar_ops.apply(user["id"], request.plan_id, [op], today, agent=False)
    except GuardViolation as gv:
        if gv.code == "G1_not_owner":
            raise HTTPException(status_code=403, detail="Not authorized to modify this plan.")
        if gv.code in ("NOTHING_to_move", "INVALID_operation"):
            raise HTTPException(status_code=400, detail="Failed to swap workouts. Check date details.")
        raise HTTPException(status_code=422, detail={"code": gv.code, "params": gv.params})
    return {
        "message": "Swapped successfully",
        "workouts": get_plan_workouts(request.plan_id),
        "warnings": changes.warnings,
    }


@app.post("/api/coach/calendar/move")
def calendar_move(request: CalendarMoveRequest, user: dict[str, Any] = Depends(get_current_user)):
    """Per-workout moves (same week, or current <-> next week) through the same
    guarded engine the chat's Apply uses."""
    today = resolve_today(request.client_today, calendar_ops.server_today())
    ops = [{"op": "move", **o.model_dump()} for o in request.operations]
    try:
        changes = calendar_ops.apply(user["id"], request.plan_id, ops, today, agent=False)
    except GuardViolation as gv:
        if gv.code == "G1_not_owner":
            raise HTTPException(status_code=403, detail="Not authorized to modify this plan.")
        raise HTTPException(status_code=422, detail={"code": gv.code, "params": gv.params})
    return {"workouts": get_plan_workouts(request.plan_id), "warnings": changes.warnings}


class WorkoutLogRequest(BaseModel):
    workout_id: int
    is_completed: int | None = None
    is_missed: int | None = None
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
    ok = update_workout_log(request.workout_id, request.is_completed, request.rpe, request.notes, request.is_missed)
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

    ics_text = CalendarService.generate_ics_string(
        race_date, workouts, time_pref, plan_start_date_str=active_plan.get("start_date")
    )

    return Response(
        content=ics_text,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=uphill_ai_training_plan.ics",
            "Cache-Control": "no-cache",
        },
    )


# --- Phase 3 Specialized Routes ---


def _calculate_pacing_core(request: PacingRequest):
    """Calculates GPX checkpoint splits and times adjusted for grade, altitude,
    fatigue, heat, and split strategy. Accepts either a base flat pace or a
    target finish time (solved to a base pace). With race_start_iso, checkpoints
    that carry coordinates get per-segment forecast heat and sunset flags.
    Shared by the self-serve /api/coach/calculate-pacing and the
    coach-triggered /api/coaching/athletes/{athlete_id}/calculate-pacing --
    pure computation over the request body, nothing athlete-specific to
    resolve."""
    if request.target_flat_pace_min_km is None and request.target_time_mins is None:
        raise HTTPException(
            status_code=422,
            detail="Provide target_flat_pace_min_km or target_time_mins",
        )

    def solve_pace() -> float:
        if request.target_flat_pace_min_km is not None:
            return request.target_flat_pace_min_km
        try:
            return PacingCalculator.solve_base_pace(
                checkpoints=request.checkpoints,
                target_time_mins=request.target_time_mins,
                split_bias=request.split_bias,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    try:
        paced_cps = PacingCalculator.calculate_checkpoint_paces(
            checkpoints=request.checkpoints,
            target_flat_pace_min_km=solve_pace(),
            split_bias=request.split_bias,
            runner_weight_kg=request.runner_weight_kg,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate pacing: {str(e)}")

    if request.race_start_iso:
        try:
            from datetime import datetime as dt

            race_start = dt.fromisoformat(request.race_start_iso)
            info = WeatherService.annotate_checkpoints(request.checkpoints, paced_cps, race_start)
            if info["applied"]:
                # heat changes the effort distribution; re-solve so the target stands
                paced_cps = PacingCalculator.calculate_checkpoint_paces(
                    checkpoints=request.checkpoints,
                    target_flat_pace_min_km=solve_pace(),
                    split_bias=request.split_bias,
                    runner_weight_kg=request.runner_weight_kg,
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Warning: weather annotation skipped: {e}")

    return paced_cps


@app.post("/api/coach/calculate-pacing")
def calculate_pacing(request: PacingRequest):
    return _calculate_pacing_core(request)


@app.post("/api/coaching/athletes/{athlete_id}/calculate-pacing")
def coach_calculate_pacing(
    athlete_id: int, request: PacingRequest, coach: dict[str, Any] = Depends(require_athlete_access)
):
    return _calculate_pacing_core(request)


async def _calculate_fueling_core(request: NutritionParams) -> dict[str, Any]:
    """Calculates Precision Hydration targets and gel product recipes.
    Shared by the self-serve /api/coach/calculate-fueling and the
    coach-triggered /api/coaching/athletes/{athlete_id}/calculate-fueling.
    nutrition_planner always uses the server-level Gemini key regardless of
    caller (see CLAUDE.md) -- unaffected by this phase."""
    try:
        return await nutrition_planner.generate_plan(user_profile="", params=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile fueling plan: {str(e)}")


@app.post("/api/coach/calculate-fueling")
async def calculate_fueling(request: NutritionParams):
    return await _calculate_fueling_core(request)


@app.post("/api/coaching/athletes/{athlete_id}/calculate-fueling")
async def coach_calculate_fueling(
    athlete_id: int, request: NutritionParams, coach: dict[str, Any] = Depends(require_athlete_access)
):
    return await _calculate_fueling_core(request)


async def _recommend_shoes_core(request: GearParams) -> dict[str, Any]:
    """Matches athlete profiles with suitable shoe catalogs. Shared by the
    self-serve /api/coach/recommend-shoes and the coach-triggered
    /api/coaching/athletes/{athlete_id}/recommend-shoes. gear_planner
    always uses the server-level Gemini key regardless of caller (see
    CLAUDE.md) -- unaffected by this phase."""
    try:
        return await gear_planner.generate_plan(user_profile="", params=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match shoes: {str(e)}")


@app.post("/api/coach/recommend-shoes")
async def recommend_shoes(request: GearParams):
    return await _recommend_shoes_core(request)


@app.post("/api/coaching/athletes/{athlete_id}/recommend-shoes")
async def coach_recommend_shoes(
    athlete_id: int, request: GearParams, coach: dict[str, Any] = Depends(require_athlete_access)
):
    return await _recommend_shoes_core(request)


@app.get("/api/coach/nutrition-catalog")
def get_nutrition_catalog():
    return query_nutrition_catalog()


# Note: Dynamic Grounded Chat (/api/coach/chat) moved to routers.coach_chat


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)

# ─── Knowledge Hub Endpoints ─────────────────────────────────────────────────


@app.get("/api/knowledge/cards")
def get_knowledge_cards(topic: str | None = None, lang: str = "en"):
    """Return all knowledge cards, optionally filtered by topic. Public: same content for every user, logged in or not."""
    cards = get_all_knowledge_cards(topic=topic, lang=lang)
    return {"cards": cards, "total": len(cards)}


@app.get("/api/knowledge/cards/random")
def get_random_cards(n: int = 3, lang: str = "en"):
    """Return n random knowledge cards for the Daily Knowledge widget. Public: same content for every user, logged in or not."""
    cards = get_random_knowledge_cards(n=n, lang=lang)
    return {"cards": cards}


@app.get("/api/knowledge/topics")
def get_topics():
    """Return distinct list of topics for filter pills. Public: same content for every user, logged in or not."""
    topics = get_knowledge_topics()
    return {"topics": topics}


@app.get("/api/knowledge/extract/status")
def get_extraction_status(user: dict[str, Any] = Depends(get_current_user)):
    """Return current extraction status and card count."""
    status = dict(extraction_status)
    status["card_count"] = get_knowledge_card_count()
    return status


podcast_discovery_status: dict[str, Any] = {"status": "idle"}
podcast_discovery_task = None


@app.post("/api/knowledge/discover-podcast")
async def trigger_podcast_discovery(user: dict[str, Any] = Depends(require_admin)):
    """Discover new Evoke Endurance podcast episodes and append their knowledge cards
    (admin, background job). Incrementally appends cards from newly-found episodes,
    never touching the existing library."""
    import asyncio

    from services.knowledge_extractor import discover_podcast_knowledge_web, save_podcast_knowledge_cards

    global podcast_discovery_task
    if podcast_discovery_task is not None and not podcast_discovery_task.done():
        return {"status": "already_discovering"}
    if not settings.TAVILY_API_KEY:
        raise HTTPException(status_code=400, detail="TAVILY_API_KEY is not configured")

    fresh_user = get_user_by_id(user["id"]) or user
    api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="No Gemini API key configured")

    async def run_podcast_discovery():
        try:
            cards = await discover_podcast_knowledge_web(api_key, settings.TAVILY_API_KEY, podcast_discovery_status)
            saved = await save_podcast_knowledge_cards(cards, api_key)
            podcast_discovery_status.update({"status": "done", "cards_found": len(cards), "cards_saved": saved})
        except Exception as e:
            podcast_discovery_status.update({"status": "error", "message": str(e)})
            print(f"[Knowledge] Podcast discovery failed: {e}")

    podcast_discovery_status.clear()
    podcast_discovery_status.update({"status": "discovering"})
    podcast_discovery_task = asyncio.create_task(run_podcast_discovery())
    return {"status": "started"}


@app.get("/api/knowledge/discover-podcast/status")
def get_podcast_discovery_status(user: dict[str, Any] = Depends(get_current_user)):
    return dict(podcast_discovery_status)


# ─── KB Distillation (web discovery → kb_chunks) ─────────────────────────────

kb_distill_status: dict[str, Any] = {"status": "idle"}
# Strong reference to the running distillation task — the event loop keeps only
# weak refs, and a GC'd multi-hour task would die silently while the status dict
# still said "distilling". Busy-ness is derived from the task, so it self-heals.
kb_distill_task = None


@app.post("/api/kb/distill")
async def trigger_kb_distill(domain: str = "all", user: dict[str, Any] = Depends(require_admin)):
    """Re-distill the gear/nutrition catalogs from live web discovery (admin, background job).
    Only WEB_DOMAINS are reachable here: these sweeps are insert-only, so an unattended run
    can add products but never remove them. The scheduler's curated training philosophy is
    NOT swept here -- it replaces doctrine wholesale, so it is script-only
    (backend/scripts/distill_principles.py)."""
    import asyncio

    from services.kb_distiller import WEB_DOMAINS, distill_domain

    global kb_distill_task
    domains = list(WEB_DOMAINS) if domain == "all" else [domain]
    if any(d not in WEB_DOMAINS for d in domains):
        raise HTTPException(status_code=400, detail=f"domain must be one of {list(WEB_DOMAINS)} or 'all'")
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

        # The domains are independent, so they distill concurrently — wall time is the
        # slowest domain, not the sum. Each domain still paces its own search queries
        # internally (rate-limit courtesy).
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
    status["counts"] = {d: get_kb_chunk_count(d) for d in ("gear", "nutrition", "scheduler", "race_courses")}
    # None = collection missing/unreachable — scheduler plans would generate
    # without philosophy grounding even if counts.scheduler > 0.
    status["qdrant_scheduler_points"] = scheduler_point_count()
    return status


race_results_distill_status: dict[str, Any] = {"status": "idle"}
race_results_distill_task = None


@app.post("/api/kb/distill-race-results")
async def trigger_race_results_distill(user: dict[str, Any] = Depends(require_admin)):
    """Merge newly-discovered race-result stats (winner times, finisher counts,
    percentiles) into the hand-curated race_courses KB. Only enriches races that
    already have a curated `results` block -- never invents results for an
    untracked race, and never overwrites an already-curated (year, distance) entry.
    Background job, same pattern as /api/kb/distill."""
    import asyncio

    from services.kb_distiller import discover_race_results_web, save_race_results

    global race_results_distill_task
    if race_results_distill_task is not None and not race_results_distill_task.done():
        return {"status": "already_distilling"}
    if not settings.TAVILY_API_KEY:
        raise HTTPException(status_code=400, detail="TAVILY_API_KEY is not configured")

    fresh_user = get_user_by_id(user["id"]) or user
    api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="No Gemini API key configured")

    async def run_race_results_distillation():
        try:
            updates = await discover_race_results_web(api_key, settings.TAVILY_API_KEY, race_results_distill_status)
            merged = save_race_results(updates)
            race_results_distill_status.update(
                {"status": "done", "races_updated": len(updates), "entries_merged": merged}
            )
        except Exception as e:
            race_results_distill_status.update({"status": "error", "message": str(e)})
            print(f"[KB] Race results distillation failed: {e}")

    race_results_distill_status.clear()
    race_results_distill_status.update({"status": "distilling"})
    race_results_distill_task = asyncio.create_task(run_race_results_distillation())
    return {"status": "started"}


@app.get("/api/kb/distill-race-results/status")
def get_race_results_distill_status(user: dict[str, Any] = Depends(get_current_user)):
    return dict(race_results_distill_status)


class CourseProfileRequest(BaseModel):
    race_name: str  # exact race_courses KB chunk title
    distance_label: str  # must match an entry in that race's distances[]
    checkpoints: list[dict[str, Any]]  # GpxParser.parse()["checkpoints"], verbatim
    year: int  # the edition year this GPX is for -- required, never inferred
    variant: str | None = None  # optional curator-asserted route tag


@app.post("/api/kb/race-courses/course-profile")
def save_course_profile_endpoint(request: CourseProfileRequest, user: dict[str, Any] = Depends(require_admin)):
    """Attaches a curated GPX-derived elevation profile to a race+distance+
    year in the race_courses KB. Reuses the already-parsed output of
    /api/parser/gpx -- the curator parses a GPX there first, then posts the
    resulting checkpoints here to attach them to the matching KB entry."""
    from services.kb_distiller import save_course_profile

    try:
        return save_course_profile(
            request.race_name, request.distance_label, request.checkpoints, request.year, request.variant
        )
    except ValueError as e:
        detail = str(e)
        status_code = 404 if detail.startswith("No race_courses KB entry") else 422
        raise HTTPException(status_code=status_code, detail=detail)


@app.post("/api/kb/import")
async def import_kb_seed(domain: str = "all", user: dict[str, Any] = Depends(require_admin)):
    """Load committed backend/kb_seed/<domain>.json files into this environment's
    Postgres (+ Qdrant for scheduler). This is how prod gets the KB without re-distilling."""
    import asyncio

    from services.kb_distiller import DOMAINS, HAND_CURATED_DOMAINS, load_seed

    importable_domains = DOMAINS + HAND_CURATED_DOMAINS
    domains = list(importable_domains) if domain == "all" else [domain]
    if any(d not in importable_domains for d in domains):
        raise HTTPException(status_code=400, detail=f"domain must be one of {list(importable_domains)} or 'all'")
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


@app.get("/api/kb/match-race")
def match_race_course(name: str, distance_km: float | None = None, distance_label: str | None = None):
    """Fuzzy-matches a race name (+ optional distance) against the curated
    race_courses KB. Read-only, no auth — used for the live UI confirmation
    chip and disambiguation dropdown. Never guesses: returns matched=false
    below the confidence threshold, and only auto-applies a match when it
    clearly dominates the next-best candidate."""
    from services.race_matcher import match_race_candidates

    result = match_race_candidates(name, distance_km=distance_km, distance_label=distance_label)
    if not result.matched:
        return {"matched": False}
    response = {"matched": True, "auto_apply": result.auto_apply, "match": result.top.to_dict()}
    if not result.auto_apply:
        response["candidates"] = [{**c.to_dict(), "score": c.confidence} for c in result.candidates]
    return response


class RaceClaimRequest(BaseModel):
    source: str
    external_id: str


class RaceBibRequest(BaseModel):
    bib: str


class RaceResultInput(BaseModel):
    discipline: str
    race_name: str
    race_date: str
    distance_km: float
    elevation_gain_m: float | None = None
    finish_time_sec: int | None = None
    is_dnf: bool = False
    rank_overall: int | None = None
    total_overall: int | None = None


class RaceResultPatch(BaseModel):
    selected: bool | None = None
    hidden: bool | None = None
    user_note: str | None = None
    discipline: str | None = None
    race_name: str | None = None
    race_date: str | None = None
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    finish_time_sec: int | None = None
    is_dnf: bool | None = None
    rank_overall: int | None = None
    total_overall: int | None = None


def _validate_race_result(data: dict[str, Any]) -> None:
    from datetime import date

    if data.get("discipline") not in ("trail", "road") or not (data.get("race_name") or "").strip():
        raise HTTPException(status_code=422, detail="Race name and discipline are required")
    try:
        date.fromisoformat(data["race_date"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid race date")
    if not 0 < (data.get("distance_km") or 0) <= 1000:
        raise HTTPException(status_code=422, detail="Invalid race distance")
    if data.get("elevation_gain_m") is not None and data["elevation_gain_m"] < 0:
        raise HTTPException(status_code=422, detail="Invalid elevation gain")
    rank, total = data.get("rank_overall"), data.get("total_overall")
    if (rank is not None and rank < 1) or (total is not None and total < 1) or (rank and total and rank > total):
        raise HTTPException(status_code=422, detail="Invalid overall rank")
    if data.get("is_dnf"):
        data["finish_time_sec"] = None
    elif not data.get("finish_time_sec") or data["finish_time_sec"] <= 0:
        raise HTTPException(status_code=422, detail="Finish time is required for a finish")


@app.get("/api/race-history/search")
def search_race_history(source: str, q: str, user: dict[str, Any] = Depends(get_current_user)):
    if source not in ("utmb", "vbm") or len(q.strip()) < 2 or len(q) > 100:
        raise HTTPException(status_code=422, detail="Choose a source and enter a name")
    if not getattr(settings, f"RACE_HISTORY_{source.upper()}_ENABLED"):
        raise HTTPException(status_code=503, detail="Source temporarily unavailable")
    try:
        rows = race_history.search_utmb(q) if source == "utmb" else race_history.search_vbm(q)
    except Exception:
        raise HTTPException(status_code=503, detail="Source search unavailable")
    wanted = set(race_history.normalize_name(q).split())
    for row in rows:
        found = set(race_history.normalize_name(row.get("display_name") or "").split())
        row["score"] = round(len(wanted & found) / max(1, len(wanted | found)), 3)
    return sorted(rows, key=lambda row: row["score"], reverse=True)


@app.post("/api/race-history/claims", status_code=202)
def create_race_claim(
    request: RaceClaimRequest, background_tasks: BackgroundTasks, user: dict[str, Any] = Depends(get_current_user)
):
    if request.source not in ("utmb", "vbm") or not getattr(settings, f"RACE_HISTORY_{request.source.upper()}_ENABLED"):
        raise HTTPException(status_code=503, detail="Source unavailable")
    try:
        claim = race_history.create_claim(user["id"], request.source, request.external_id.strip())
        background_tasks.add_task(race_history.sync_claim_now, claim["id"])
        return claim
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
            raise HTTPException(status_code=409, detail="Profile already linked")
        raise


@app.get("/api/race-history/claims")
def get_race_claims(user: dict[str, Any] = Depends(get_current_user)):
    return race_history.list_claims(user["id"])


@app.delete("/api/race-history/claims/{claim_id}")
def remove_race_claim(claim_id: int, user: dict[str, Any] = Depends(get_current_user)):
    if not race_history.delete_claim(claim_id, user["id"]):
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"ok": True}


@app.post("/api/race-history/claims/{claim_id}/verify-bib")
def verify_race_bib(claim_id: int, request: RaceBibRequest, user: dict[str, Any] = Depends(get_current_user)):
    claim = race_history.get_claim(claim_id, user["id"])
    if not claim or claim["source"] != "vbm":
        raise HTTPException(status_code=404, detail="VBM claim not found")
    if not any(
        r["claim_id"] == claim_id and r["selected"] and r["bib"] == request.bib.strip()
        for r in race_history.list_results(user["id"])
    ):
        raise HTTPException(status_code=422, detail="Bib does not match a selected result")
    race_history.set_verified_bib(claim_id, user["id"], request.bib.strip())
    return race_history.get_claim(claim_id, user["id"])


@app.post("/api/race-history/claims/{claim_id}/refresh", status_code=202)
def refresh_race_claim(
    claim_id: int, background_tasks: BackgroundTasks, user: dict[str, Any] = Depends(get_current_user)
):
    if not race_history.get_claim(claim_id, user["id"]):
        raise HTTPException(status_code=404, detail="Claim not found")
    if not race_history.queue_refresh(claim_id, user["id"]):
        raise HTTPException(status_code=429, detail="Refresh available once per hour")
    background_tasks.add_task(race_history.sync_claim_now, claim_id)
    return race_history.get_claim(claim_id, user["id"])


def _race_history_payload(user_id: int) -> dict[str, Any]:
    return {
        "claims": race_history.list_claims(user_id),
        "results": race_history.list_results(user_id),
        "summary": race_history.build_summary(user_id),
    }


@app.get("/api/race-history")
def get_race_history(user: dict[str, Any] = Depends(get_current_user)):
    return _race_history_payload(user["id"])


@app.get("/api/coaching/athletes/{athlete_id}/race-history")
def get_coach_race_history(athlete_id: int, acting_user: dict[str, Any] = Depends(require_athlete_access)):
    return _race_history_payload(athlete_id)


@app.post("/api/race-history/results")
def create_manual_race_result(request: RaceResultInput, user: dict[str, Any] = Depends(get_current_user)):
    data = request.model_dump()
    _validate_race_result(data)
    return race_history.create_manual(user["id"], data)


@app.patch("/api/race-history/results/{result_id}")
def patch_race_result(result_id: int, request: RaceResultPatch, user: dict[str, Any] = Depends(get_current_user)):
    existing = race_history.get_result(result_id, user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Result not found")
    changes = request.model_dump(exclude_unset=True)
    if existing["source"] == "manual" and any(
        k in changes for k in ("race_name", "race_date", "distance_km", "finish_time_sec", "is_dnf", "discipline")
    ):
        merged = {**existing, **changes}
        _validate_race_result(merged)
        changes["finish_time_sec"] = merged["finish_time_sec"]
    try:
        return race_history.update_result(result_id, user["id"], changes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.delete("/api/race-history/results/{result_id}")
def remove_manual_race_result(result_id: int, user: dict[str, Any] = Depends(get_current_user)):
    if not race_history.delete_manual(result_id, user["id"]):
        raise HTTPException(status_code=404, detail="Manual result not found")
    return {"ok": True}


@app.get("/api/race-history/admin/mirrors/status")
def get_race_mirror_status(admin: dict[str, Any] = Depends(require_admin)):
    return race_history.mirror_status()


@app.post("/api/race-history/admin/mirrors/refresh", status_code=202)
def refresh_race_mirrors(
    background_tasks: BackgroundTasks, source: str = "all", admin: dict[str, Any] = Depends(require_admin)
):
    """Re-copy the UTMB/VBM runner search index (minutes of paced requests),
    in the background. Poll .../mirrors/status for progress."""
    if source not in ("utmb", "vbm", "all"):
        raise HTTPException(status_code=422, detail="source must be utmb, vbm or all")
    if race_history.mirror_job.get("state") == "running":
        raise HTTPException(status_code=409, detail="Mirror refresh already running")
    background_tasks.add_task(race_history.run_mirror_refresh, ["utmb", "vbm"] if source == "all" else [source])
    return {"queued": source}


@app.post("/api/race-history/admin/sync-claims")
def sync_race_claims(admin: dict[str, Any] = Depends(require_admin)):
    return {"queued": race_history.queue_all_claims()}


@app.delete("/api/race-history/admin/claims/{claim_id}")
def admin_remove_race_claim(claim_id: int, admin: dict[str, Any] = Depends(require_admin)):
    if not race_history.delete_claim(claim_id):
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"ok": True}


class GoalEstimateRequest(BaseModel):
    # target course: a KB race name and/or explicit numbers
    race_name: str | None = None
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    # fitness: a flat base pace OR a past race result
    flat_pace_min_km: float | None = None
    reference_race_name: str | None = None
    reference_distance_km: float | None = None
    reference_elevation_gain_m: float | None = None
    reference_time: str | None = None  # "h:mm:ss" or "h:mm"
    reference_result_id: int | None = None
    weeks_to_race: float | None = None
    race_date: str | None = None  # "YYYY-MM-DD"; derives weeks_to_race when weeks_to_race isn't given directly


def _weeks_until(date_str: str | None) -> float | None:
    if not date_str:
        return None
    from datetime import date as _date

    try:
        race_date = _date.fromisoformat(date_str)
    except ValueError:
        return None
    return (race_date - _date.today()).days / 7.0


def _parse_hms_to_mins(time_str: str | None) -> float | None:
    if not time_str:
        return None
    parts = time_str.strip().split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        return None
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    return h * 60 + m + s / 60


def _variant_filtered_results(
    results: list[dict[str, Any]], variants: dict[int, str | None], target_variant: str | None
) -> list[dict[str, Any]]:
    """Only pool result-years whose curated course-profile variant matches
    target_variant. A None target_variant means no route assertion for this
    race -- pool everything, unchanged from pre-variant behavior. A
    result-year with no curated course-profile entry at all is excluded
    once filtering is active, since it's neither proven compatible nor
    incompatible."""
    if not target_variant:
        return results
    return [r for r in results if variants.get(r.get("year")) == target_variant]


def _goal_estimate_core(request: GoalEstimateRequest) -> dict[str, Any]:
    """Goal Determiner: predicted finish time + A/B/C goals for a target
    course, from either a flat base pace or a past race result. Course
    numbers are backfilled from the race KB when only a name is given, and
    an UltraSignup-style rank-transfer estimate is added when winner times
    are curated for both races. Shared by the self-serve
    /api/coach/goal-estimate and the coach-triggered
    /api/coaching/athletes/{athlete_id}/goal-estimate -- this function
    reads nothing from the database keyed by a user id, so there is no
    athlete-vs-coach resolution to get right here."""
    from services.race_estimator import AMBITIOUS_FACTOR, SAFE_FACTOR, RaceEstimator
    from services.race_matcher import course_profile, course_profile_variants, match_race, race_benchmarks

    distance_km = request.distance_km
    elevation_gain_m = request.elevation_gain_m
    matched_target = None
    if request.race_name:
        matched_target = match_race(request.race_name, distance_km=distance_km)
        if matched_target:
            distance_km = distance_km or matched_target.distance_km
            # 0 counts as missing: a UI race pick may fire before the match
            # resolves, and the KB's climb number beats a silent flat course
            elevation_gain_m = elevation_gain_m or matched_target.elevation_gain_m
    if not distance_km or distance_km <= 0:
        raise HTTPException(status_code=422, detail="Target course needs a distance (km)")
    elevation_gain_m = elevation_gain_m or 0.0

    target_profile = (
        course_profile(request.race_name, matched_target.distance_label)
        if matched_target and matched_target.distance_label
        else None
    )
    target_checkpoints = target_profile["checkpoints"] if target_profile else None
    target_variant = target_profile["variant"] if target_profile else None
    target_course_year = target_profile["year"] if target_profile else None

    ref_distance = request.reference_distance_km
    ref_gain = request.reference_elevation_gain_m
    matched_ref = None
    if request.reference_race_name:
        matched_ref = match_race(request.reference_race_name, distance_km=ref_distance)
        if matched_ref:
            ref_distance = ref_distance or matched_ref.distance_km
            ref_gain = ref_gain or matched_ref.elevation_gain_m

    ref_profile = (
        course_profile(request.reference_race_name, matched_ref.distance_label)
        if matched_ref and matched_ref.distance_label
        else None
    )
    ref_variant = ref_profile["variant"] if ref_profile else None
    ref_course_year = ref_profile["year"] if ref_profile else None

    ref_time_mins = _parse_hms_to_mins(request.reference_time)
    reference = None
    if ref_time_mins and ref_distance:
        reference = {
            "distance_km": ref_distance,
            "elevation_gain_m": ref_gain or 0.0,
            "finish_time_mins": ref_time_mins,
            "terrain_tags": matched_ref.terrain if matched_ref else None,
            "checkpoints": ref_profile["checkpoints"] if ref_profile else None,
        }

    try:
        estimate = RaceEstimator.estimate(
            distance_km=distance_km,
            elevation_gain_m=elevation_gain_m,
            base_flat_pace_min_km=request.flat_pace_min_km,
            reference=reference,
            weeks_to_race=request.weeks_to_race
            if request.weeks_to_race is not None
            else _weeks_until(request.race_date),
            terrain_tags=matched_target.terrain if matched_target else None,
            target_checkpoints=target_checkpoints,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    response: dict[str, Any] = {
        **estimate,
        "distance_km": distance_km,
        "elevation_gain_m": elevation_gain_m,
        "race_name": matched_target.race_name if matched_target else request.race_name,
        "target_course_year": target_course_year,
        "reference_course_year": ref_course_year if estimate.get("reference_profile_source") is not None else None,
    }

    # field-history cross-check (plan §8 layer 3) when results are curated for
    # both races; percentile calibration (docs/superpowers/specs/2026-08-21-
    # goal-determiner-percentile-calibration-design.md) blends into the
    # primary estimate, winner-time rank transfer stays a secondary field.
    target_bench = race_benchmarks(request.race_name, distance_km=distance_km) if request.race_name else None
    # Only look up reference benchmarks when ref_distance resolved to a
    # single value -- otherwise race_benchmarks(distance_km=None) returns
    # ALL curated years unfiltered by distance, which can mix a
    # multi-distance race's years into one meaningless percentile curve.
    # Mirrors the physics reference path's existing `ref_time_mins and
    # ref_distance` guard above.
    ref_bench = (
        race_benchmarks(request.reference_race_name, distance_km=ref_distance)
        if request.reference_race_name and ref_distance
        else None
    )
    if target_bench:
        response["benchmarks"] = target_bench["results"]

    if target_bench and ref_bench and ref_time_mins:
        target_winner = _parse_hms_to_mins((target_bench["results"][0] or {}).get("winner_time"))
        ref_winner = _parse_hms_to_mins((ref_bench["results"][0] or {}).get("winner_time"))
        if target_winner and ref_winner:
            response["rank_transfer_mins"] = round(
                RaceEstimator.rank_transfer_mins(ref_winner, ref_time_mins, target_winner), 1
            )

        target_variants_by_year = (
            course_profile_variants(request.race_name, matched_target.distance_label)
            if matched_target and matched_target.distance_label
            else {}
        )
        ref_variants_by_year = (
            course_profile_variants(request.reference_race_name, matched_ref.distance_label)
            if matched_ref and matched_ref.distance_label
            else {}
        )
        target_results = _variant_filtered_results(target_bench["results"], target_variants_by_year, target_variant)
        ref_results = _variant_filtered_results(ref_bench["results"], ref_variants_by_year, ref_variant)

        target_pct = RaceEstimator.percentile_curve(target_results)
        ref_pct = RaceEstimator.percentile_curve(ref_results)
        if target_pct and ref_pct:
            target_curve, target_years = target_pct
            ref_curve, ref_years = ref_pct
            percentile_transfer = RaceEstimator.percentile_transfer_mins(ref_curve, ref_time_mins, target_curve)
            response["percentile_transfer_mins"] = round(percentile_transfer, 1)
            response["percentile_years_used"] = {"target": target_years, "reference": ref_years}

            # Plausibility floor: an unbounded linear extrapolation (e.g. a
            # mistyped or wildly mismatched reference time) can transfer to
            # a target time faster than that race's own curated winner --
            # physically impossible. Skip applying the blend in that case,
            # but keep reporting percentile_transfer_mins for transparency.
            # If the winner time isn't available/parseable, don't block the
            # blend on it.
            implausible = target_winner is not None and percentile_transfer < target_winner
            if not implausible:
                blended = (response["adjusted_time_mins"] + percentile_transfer) / 2.0
                response["adjusted_time_mins"] = round(blended, 1)
                response["goals"] = {
                    "ambitious": round(blended * AMBITIOUS_FACTOR, 1),
                    "realistic": round(blended, 1),
                    "safe": round(blended * SAFE_FACTOR, 1),
                }

    return response


def _estimate_with_history(request: GoalEstimateRequest, athlete_id: int | None) -> dict[str, Any]:
    if not request.reference_result_id:
        return _goal_estimate_core(request)
    if athlete_id is None:
        raise HTTPException(status_code=401, detail="Sign in to use a saved result")
    result = race_history.get_result(request.reference_result_id, athlete_id)
    if not result or not result["selected"] or result["is_dnf"] or not result["finish_time_sec"]:
        raise HTTPException(status_code=404, detail="Usable reference result not found")
    explicit = [request.reference_distance_km, request.reference_time]
    if any(value is not None for value in explicit) and not all(value is not None for value in explicit):
        raise HTTPException(status_code=422, detail="Provide a complete reference override")
    if all(value is not None for value in explicit):
        return _goal_estimate_core(request)
    seconds = result["finish_time_sec"]
    merged = request.model_copy(
        update={
            "reference_race_name": result["race_name"],
            "reference_distance_km": result["distance_km"],
            "reference_elevation_gain_m": result["elevation_gain_m"] or 0,
            "reference_time": f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}",
        }
    )
    response = _goal_estimate_core(merged)
    if result["discipline"] == "road" and (
        (request.elevation_gain_m or 0) / max(request.distance_km or 1, 1) > 20
        or (request.race_name and "trail" in request.race_name.lower())
    ):
        response["reference_confidence"] = "low"
    return response


@app.post("/api/coach/goal-estimate")
def goal_estimate(request: GoalEstimateRequest, authorization: str | None = Header(None)):
    athlete_id = None
    if authorization and authorization.startswith("Bearer "):
        user = verify_session(authorization.split(" ", 1)[1])
        athlete_id = user["id"] if user else None
    return _estimate_with_history(request, athlete_id)


@app.post("/api/coaching/athletes/{athlete_id}/goal-estimate")
def coach_goal_estimate(
    athlete_id: int, request: GoalEstimateRequest, coach: dict[str, Any] = Depends(require_athlete_access)
):
    return _estimate_with_history(request, athlete_id)


# ─── Goal assessment (LLM goal estimation) ───────────────────────────────────
# docs/superpowers/specs/2026-09-26-llm-goal-estimation-design.md


class GoalReference(BaseModel):
    race_name: str | None = None
    distance_km: float
    elevation_gain_m: float | None = None
    time: str  # "h:mm:ss" or "h:mm"
    race_date: str | None = None
    discipline: str | None = None


class GoalAssessRequest(BaseModel):
    race_name: str | None = None
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    race_date: str | None = None
    cutoff_mins: float | None = None
    exclude: list[str] = []
    reference: GoalReference | None = None
    flat_pace_min_km: float | None = None
    lang: str = "en"


class GoalReassessRequest(BaseModel):
    exclude: list[str] = []
    lang: str = "en"


class GoalApplyRequest(BaseModel):
    target_mins: float


_goal_logger = get_logger("goal_assessment")


def _goal_user(authorization: str | None) -> dict[str, Any] | None:
    if authorization and authorization.startswith("Bearer "):
        user = verify_session(authorization.split(" ", 1)[1])
        if user:
            return get_user_by_id(user["id"]) or user
    return None


def _run_goal(**kwargs: Any) -> dict[str, Any]:
    from services import goal_service

    try:
        return goal_service.run(**kwargs)
    except goal_service.RateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def _goal_assess(request: GoalAssessRequest, user: dict[str, Any] | None) -> dict[str, Any]:
    return _run_goal(
        user=user,
        race_name=request.race_name,
        distance_km=request.distance_km,
        elevation_gain_m=request.elevation_gain_m,
        race_date=request.race_date,
        exclude=set(request.exclude),
        manual_reference=request.reference.model_dump() if request.reference else None,
        flat_pace_min_km=request.flat_pace_min_km,
        cutoff_mins=request.cutoff_mins,
        lang=request.lang,
        trigger="pre_plan",
    )


def _goal_plan(plan_id: int, owner_id: int) -> dict[str, Any]:
    _verify_plan_ownership(plan_id, owner_id)
    plan = get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return plan


def _assess_new_plan(owner_id: int, plan_id: int) -> None:
    """Best effort, off the request thread: the plan already exists, so the
    pill shows "Not assessed" until this lands and a failure is only logged."""

    from services import goal_service

    if not settings.GOAL_ASSESS_ON_PLAN_CREATE:
        return

    def work() -> None:
        try:
            plan = get_plan_by_id(plan_id)
            owner = get_user_by_id(owner_id)
            if plan and owner and plan.get("course_distance_km"):
                goal_service.run_for_plan(owner, plan, "pre_plan")
        except Exception:
            _goal_logger.exception("new plan goal assessment failed", extra={"fields": {"plan_id": plan_id}})

    threading.Thread(target=work, daemon=True).start()


# Plans with a weekly assessment running in this process: the plan page loads
# /goal more than once at a time, and each load would otherwise start one.
# The partial unique index on goal_assessments is the cross-process backstop.
_weekly_goal_inflight: set[int] = set()
_weekly_goal_lock = threading.Lock()


def _run_weekly_goal(owner_id: int, plan_id: int, lang: str = "en") -> None:
    from services import goal_service

    with _weekly_goal_lock:
        if plan_id in _weekly_goal_inflight:
            return
        _weekly_goal_inflight.add(plan_id)
    try:
        plan = get_plan_by_id(plan_id)
        owner = get_user_by_id(owner_id)
        if plan and owner and goal_service.weekly_due(plan):
            goal_service.run_for_plan(owner, plan, "weekly", lang=lang)
    except Exception:
        _goal_logger.exception("weekly goal assessment failed", extra={"fields": {"plan_id": plan_id}})
    finally:
        with _weekly_goal_lock:
            _weekly_goal_inflight.discard(plan_id)


def _get_plan_goal(plan_id: int, owner_id: int, background_tasks: BackgroundTasks, lang: str) -> dict[str, Any]:
    from services import goal_service

    plan = _goal_plan(plan_id, owner_id)
    if goal_service.weekly_due(plan):
        background_tasks.add_task(_run_weekly_goal, owner_id, plan_id, "vi" if lang == "vi" else "en")
    return goal_service.plan_goal(plan)


def _reassess_plan_goal(plan_id: int, owner_id: int, request: GoalReassessRequest) -> dict[str, Any]:
    from services import goal_service

    plan = _goal_plan(plan_id, owner_id)
    owner = get_user_by_id(owner_id)
    assessment = _run_goal(
        user=owner,
        race_name=plan.get("race_name"),
        distance_km=plan.get("course_distance_km"),
        elevation_gain_m=plan.get("course_elevation_gain_m"),
        race_date=plan.get("race_date"),
        plan=plan,
        exclude=set(request.exclude),
        lang=request.lang,
        trigger="manual",
    )
    return {
        "assessment": assessment,
        "status": goal_service.status(assessment, plan.get("target_time_hours")),
        "target_time_hours": plan.get("target_time_hours"),
    }


def _apply_plan_goal(plan_id: int, owner_id: int, request: GoalApplyRequest) -> dict[str, Any]:
    from services import goal_service

    if not 10 <= request.target_mins <= 60 * 120:
        raise HTTPException(status_code=422, detail="Target time out of range")
    _goal_plan(plan_id, owner_id)
    update_plan_target_time(plan_id, round(request.target_mins / 60, 4))
    return goal_service.plan_goal(get_plan_by_id(plan_id))


@app.post("/api/goal/assess")
def goal_assess(request: GoalAssessRequest, authorization: str | None = Header(None)):
    return _goal_assess(request, _goal_user(authorization))


@app.get("/api/plans/{plan_id}/goal")
def get_plan_goal(
    plan_id: int, background_tasks: BackgroundTasks, lang: str = "en", user: dict[str, Any] = Depends(get_current_user)
):
    return _get_plan_goal(plan_id, user["id"], background_tasks, lang)


@app.post("/api/plans/{plan_id}/goal/reassess")
def reassess_plan_goal(plan_id: int, request: GoalReassessRequest, user: dict[str, Any] = Depends(get_current_user)):
    return _reassess_plan_goal(plan_id, user["id"], request)


@app.post("/api/plans/{plan_id}/goal/apply")
def apply_plan_goal(plan_id: int, request: GoalApplyRequest, user: dict[str, Any] = Depends(get_current_user)):
    return _apply_plan_goal(plan_id, user["id"], request)


@app.post("/api/coaching/athletes/{athlete_id}/goal/assess")
def coach_goal_assess(
    athlete_id: int, request: GoalAssessRequest, acting_user: dict[str, Any] = Depends(require_athlete_access)
):
    return _goal_assess(request, get_user_by_id(athlete_id))


@app.get("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/goal")
def coach_get_plan_goal(
    athlete_id: int,
    plan_id: int,
    background_tasks: BackgroundTasks,
    lang: str = "en",
    acting_user: dict[str, Any] = Depends(require_athlete_access),
):
    return _get_plan_goal(plan_id, athlete_id, background_tasks, lang)


@app.post("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/goal/reassess")
def coach_reassess_plan_goal(
    athlete_id: int,
    plan_id: int,
    request: GoalReassessRequest,
    acting_user: dict[str, Any] = Depends(require_athlete_access),
):
    return _reassess_plan_goal(plan_id, athlete_id, request)


@app.post("/api/coaching/athletes/{athlete_id}/plans/{plan_id}/goal/apply")
def coach_apply_plan_goal(
    athlete_id: int,
    plan_id: int,
    request: GoalApplyRequest,
    acting_user: dict[str, Any] = Depends(require_athlete_access),
):
    return _apply_plan_goal(plan_id, athlete_id, request)


@app.get("/api/coach/pace-strategy/benchmarks")
def pace_strategy_benchmarks(name: str, distance_km: float | None = None):
    """Hand-curated past-results benchmarks (winner times, finisher counts,
    cutoffs, percentiles where curated) for a race in the courses KB.
    Read-only, no auth — rendered as context bands under the Pace Strategy
    finish-time slider."""
    from services.race_matcher import race_benchmarks

    bench = race_benchmarks(name, distance_km=distance_km)
    if not bench:
        return {"matched": False}
    return {"matched": True, **bench}


# ─── Workout Types ────────────────────────────────────────────────────────────


@app.get("/api/workouts/types")
def list_workout_types(lang: str = "en"):
    """Return all workout type descriptions from the DB. No auth required."""
    return {"types": get_workout_types(lang=lang)}
