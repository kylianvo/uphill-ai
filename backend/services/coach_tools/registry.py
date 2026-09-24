"""Per-turn LangChain tool factory. user_id is captured in a closure here,
never accepted as a tool argument -- this is the identity invariant's
actual enforcement point (see Global Constraints in the plan header)."""

import datetime as dt
from dataclasses import dataclass
from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

import db
from services.coach_tools import knowledge_tools, pacing_tools, plan_tools, proposal_tools


@dataclass(frozen=True)
class ProposalContext:
    """Per-turn, server-derived context for the proposal tool -- never from the model."""

    thread_id: int
    plan_id: int
    today: dt.date


class GetWeekInput(BaseModel):
    week_number: int | None = Field(
        default=None,
        description="The 1-based week number of the plan to inspect. If omitted, fetches the current active training week.",
    )


class PaceStrategyInput(BaseModel):
    race_name: str | None = Field(
        default=None,
        description="Name of the race from the curated knowledge base (e.g. 'Dalat Ultra Trail', 'UTMB Mont-Blanc').",
    )
    target_time_hours: float | None = Field(
        default=None,
        description="Target finish time in hours (e.g. 14.5).",
    )
    strategy: Literal["even", "conservative_start", "aggressive"] = Field(
        default="conservative_start",
        description="Pacing distribution strategy.",
    )
    distance_km: float | None = Field(
        default=None,
        description="Race distance in km (e.g. 75). Pass it whenever the athlete names a distance; needed for races offering several distances.",
    )
    elevation_gain_m: float | None = Field(
        default=None,
        description="Total course elevation gain in meters, if the athlete states it.",
    )


class WeekReviewInput(BaseModel):
    weeks_ago: int = Field(
        default=0,
        description="0 for the current week up to today, 1 for last week, 2 for two weeks ago.",
    )


class KbSearchInput(BaseModel):
    query: str = Field(
        description="Search query or question regarding uphill training, heart rate zones, or race specifics."
    )
    domain: Literal["all", "scheduler", "nutrition", "race_courses"] = Field(
        default="all",
        description="Domain filter for retrieval.",
    )


class ScheduleOperation(BaseModel):
    op: Literal["move", "swap_days"] = Field(description="'move' one workout, or 'swap_days' within one week.")
    workout_id: int | None = Field(default=None, description="move: id of the workout (from get_week).")
    target_week: int | None = Field(default=None, description="move: 1-based plan week to move it to.")
    target_day: str | None = Field(default=None, description="move: Monday..Sunday.")
    week: int | None = Field(default=None, description="swap_days: the plan week.")
    day_1: str | None = Field(default=None, description="swap_days: Monday..Sunday.")
    day_2: str | None = Field(default=None, description="swap_days: Monday..Sunday.")


class ProposeScheduleChangeInput(BaseModel):
    operations: list[ScheduleOperation] = Field(
        min_length=1,
        max_length=5,
        description="All the changes as ONE proposal (1-5). Moves stack onto the target day. "
        "Cross-week moves only between this week and next week.",
    )
    rationale: str = Field(max_length=300, description="One short sentence explaining why, shown on the card.")


def _monday_aligned_week(user_id: int, today: dt.date) -> int | None:
    """The plan week containing `today`, Monday-aligned like the calendar engine
    (not db.compute_current_week), clamped to the plan for the lookup."""
    # Imported lazily: services.calendar_rules imports services.coach_tools.base
    # at module scope, so a module-level import here would cycle the packages.
    from services.calendar_rules import current_week, start_monday

    plan = db.get_active_plan(user_id)
    monday = start_monday(plan.get("start_date")) if plan else None
    if monday is None:
        return None
    week = current_week(monday, today)
    total_weeks = int(plan.get("total_weeks") or 0)
    return max(1, min(week, total_weeks)) if total_weeks else max(1, week)


def build_tools(user_id: int, *, kb_api_key: str, proposals: ProposalContext | None = None) -> list[StructuredTool]:
    def _get_week(week_number: int | None = None) -> dict:
        if week_number is None and proposals is not None:
            week_number = _monday_aligned_week(user_id, proposals.today)
        return plan_tools.get_week_impl(user_id=user_id, week_number=week_number).__dict__

    def _pace_strategy(
        race_name: str | None = None,
        target_time_hours: float | None = None,
        strategy: Literal["even", "conservative_start", "aggressive"] = "conservative_start",
        distance_km: float | None = None,
        elevation_gain_m: float | None = None,
    ) -> dict:
        return pacing_tools.pace_strategy_impl(
            user_id=user_id,
            race_name=race_name,
            target_time_hours=target_time_hours,
            strategy=strategy,
            distance_km=distance_km,
            elevation_gain_m=elevation_gain_m,
        ).__dict__

    def _week_review(weeks_ago: int = 0) -> dict:
        return plan_tools.week_review_impl(user_id=user_id, weeks_ago=weeks_ago).__dict__

    def _kb_search(query: str, domain: Literal["all", "scheduler", "nutrition", "race_courses"] = "all") -> dict:
        return knowledge_tools.kb_search_impl(user_id=user_id, query=query, domain=domain, api_key=kb_api_key).__dict__

    tools = [
        StructuredTool.from_function(
            func=_get_week,
            name="get_week",
            description="Fetch the scheduled workouts and volume targets for a specific week number of the athlete's active training plan. Defaults to the current week if week_number is omitted.",
            args_schema=GetWeekInput,
        ),
        StructuredTool.from_function(
            func=_pace_strategy,
            name="pace_strategy",
            description="Calculate distance, elevation, target pace, estimated split time, and cutoff margins for race checkpoints using course elevation profiles and athlete ability.",
            args_schema=PaceStrategyInput,
        ),
        StructuredTool.from_function(
            func=_week_review,
            name="week_review",
            description="Inspect completed workouts, total volume (km & elevation), compliance against the scheduled plan, and acute training load for the athlete's recent week.",
            args_schema=WeekReviewInput,
        ),
        StructuredTool.from_function(
            func=_kb_search,
            name="kb_search",
            description="Search the Scott Johnston 'Training for the Uphill Athlete' knowledge base for physiology rules, strength protocols, aerobic threshold guidelines, and curated race course profiles.",
            args_schema=KbSearchInput,
        ),
    ]

    if proposals is not None:

        def _propose_schedule_change(operations: list, rationale: str) -> dict:
            ops = [
                (
                    o.model_dump(exclude_none=True)
                    if isinstance(o, BaseModel)
                    else {k: v for k, v in o.items() if v is not None}
                )
                for o in operations
            ]
            # extra keys the model might invent (e.g. user_id) never reach the engine
            allowed = {"op", "workout_id", "target_week", "target_day", "week", "day_1", "day_2"}
            ops = [{k: v for k, v in o.items() if k in allowed} for o in ops]
            return proposal_tools.propose_schedule_change_impl(
                user_id=user_id, ctx=proposals, operations=ops, rationale=rationale
            ).__dict__

        tools.append(
            StructuredTool.from_function(
                func=_propose_schedule_change,
                name="propose_schedule_change",
                description="Propose moving/swapping workouts in the athlete's plan. Creates a proposal card with "
                "Apply/Discard buttons; it changes NOTHING until the athlete taps Apply. Call get_week first to get "
                "workout ids.",
                args_schema=ProposeScheduleChangeInput,
            )
        )
    return tools
