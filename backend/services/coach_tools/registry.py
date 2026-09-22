"""Per-turn LangChain tool factory. user_id is captured in a closure here,
never accepted as a tool argument -- this is the identity invariant's
actual enforcement point (see Global Constraints in the plan header)."""

from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from services.coach_tools import knowledge_tools, pacing_tools, plan_tools


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


def build_tools(user_id: int, *, kb_api_key: str) -> list[StructuredTool]:
    def _get_week(week_number: int | None = None) -> dict:
        return plan_tools.get_week_impl(user_id=user_id, week_number=week_number).__dict__

    def _pace_strategy(
        race_name: str | None = None,
        target_time_hours: float | None = None,
        strategy: Literal["even", "conservative_start", "aggressive"] = "conservative_start",
    ) -> dict:
        return pacing_tools.pace_strategy_impl(
            user_id=user_id, race_name=race_name, target_time_hours=target_time_hours, strategy=strategy
        ).__dict__

    def _week_review(weeks_ago: int = 0) -> dict:
        return plan_tools.week_review_impl(user_id=user_id, weeks_ago=weeks_ago).__dict__

    def _kb_search(query: str, domain: Literal["all", "scheduler", "nutrition", "race_courses"] = "all") -> dict:
        return knowledge_tools.kb_search_impl(user_id=user_id, query=query, domain=domain, api_key=kb_api_key).__dict__

    return [
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
