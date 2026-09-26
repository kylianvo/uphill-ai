"""Goal assessment orchestration: context -> anchors -> judge -> stored row
(docs/superpowers/specs/2026-09-26-llm-goal-estimation-design.md)."""

import hashlib
import json
from datetime import date
from typing import Any

import db
from config import settings
from services import goal_anchors, goal_context, goal_judge

MANUAL_DAILY_LIMIT = 3
# Gemini calls per user per day across the modal and manual re-assess (weekly
# runs are bounded by the plan calendar). Past it, the rules tier answers.
LLM_DAILY_LIMIT = 20
DRIFT_THRESHOLD = 0.03


class RateLimited(Exception):
    pass


def _weeks_until(race_date: str | None) -> float | None:
    if not race_date:
        return None
    try:
        return (date.fromisoformat(race_date[:10]) - date.today()).days / 7.0
    except ValueError:
        return None


def input_hash(prompt: dict[str, Any], anchors: list[dict[str, Any]], lang: str, cutoff_mins: float | None) -> str:
    blob = json.dumps(
        {
            "prompt": prompt,
            "anchors": anchors,
            "lang": lang,
            "cutoff": cutoff_mins,
            "llm": settings.GOAL_LLM_ENABLED,
            "version": goal_judge.PROMPT_VERSION,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def _present(row: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    output = row.get("output") or {}
    summary = row.get("context_summary") or {}
    return {
        "id": row["id"],
        "plan_id": row.get("plan_id"),
        "race_name": row.get("race_name"),
        "race_date": row.get("race_date"),
        "distance_km": row.get("distance_km"),
        "elevation_gain_m": row.get("elevation_gain_m"),
        "goals": output.get("goals"),
        "confidence": row.get("confidence"),
        "reasoning": output.get("reasoning") or [],
        "missing": sorted(set((output.get("missing") or []) + (summary.get("missing") or []))),
        "anchors": row.get("anchors") or [],
        "sources": summary.get("sources") or [],
        "engine": row["engine"],
        "trigger": row.get("trigger"),
        "lang": row.get("lang"),
        "plan_week": row.get("plan_week"),
        "created_at": row.get("created_at"),
        **(extra or {}),
    }


def run(
    *,
    user: dict[str, Any] | None,
    race_name: str | None,
    distance_km: float | None,
    elevation_gain_m: float | None,
    race_date: str | None,
    plan: dict[str, Any] | None = None,
    exclude: set[str] | None = None,
    manual_reference: dict[str, Any] | None = None,
    flat_pace_min_km: float | None = None,
    cutoff_mins: float | None = None,
    lang: str = "en",
    trigger: str = "pre_plan",
) -> dict[str, Any]:
    """One assessment. Raises ValueError when the course has no distance."""
    lang = "vi" if lang == "vi" else "en"
    target = goal_anchors.resolve_course(race_name, distance_km, elevation_gain_m)
    if not target["distance_km"] or target["distance_km"] <= 0:
        raise ValueError("Target course needs a distance (km)")
    weeks = _weeks_until(race_date)
    extra = [r for r in [goal_context.manual_result(manual_reference)] if r] if manual_reference else []
    ctx = goal_context.gather(
        user=user,
        target=target,
        race_date=race_date,
        plan=plan,
        exclude=exclude,
        extra_results=extra,
        weeks_to_race=weeks,
    )
    anchors = goal_anchors.compute_anchors(
        target,
        ctx.results,
        weekly_km=ctx.weekly_km,
        ultra_finishes=ctx.ultra_finishes,
        easy_pace_min_km=ctx.easy_pace_min_km,
        base_pace_min_km=flat_pace_min_km,
    )
    digest = input_hash(ctx.prompt, anchors, lang, cutoff_mins)
    benchmarks = _benchmarks(race_name, target["distance_km"])
    if user:
        previous = db.find_goal_assessment(user["id"], plan["id"] if plan else None, digest)
        if previous:
            return _present(previous, {"benchmarks": benchmarks, "reused": True})
        if trigger == "manual" and db.count_manual_goal_assessments_today(user["id"]) >= MANUAL_DAILY_LIMIT:
            raise RateLimited(f"Re-assess is limited to {MANUAL_DAILY_LIMIT} per day")

    # Signed-out estimates never reach Gemini: the endpoint is unauthenticated,
    # so the server key would be open to anyone. Signed-in users share a daily
    # budget, since changing exclusions or the reference defeats hash reuse.
    llm_allowed = (
        settings.GOAL_LLM_ENABLED
        and user is not None
        and (trigger == "weekly" or db.count_llm_goal_assessments_today(user["id"]) < LLM_DAILY_LIMIT)
    )
    api_key = (user or {}).get("gemini_api_key") or settings.GEMINI_API_KEY
    output = goal_judge.assess(
        ctx.prompt,
        anchors,
        api_key=api_key,
        lang=lang,
        cutoff_mins=cutoff_mins,
        llm_enabled=llm_allowed,
    )
    row = db.insert_goal_assessment(
        {
            "user_id": user["id"] if user else None,
            "plan_id": plan["id"] if plan else None,
            "race_name": target["race_name"],
            "race_date": race_date[:10] if race_date else None,
            "distance_km": target["distance_km"],
            "elevation_gain_m": target["elevation_gain_m"],
            "input_hash": digest,
            "context_summary": {"sources": ctx.sources, "missing": ctx.missing, "weeks_to_race": weeks},
            "anchors": anchors,
            "output": output,
            "engine": output["engine"] if output else "none",
            "confidence": output["confidence"] if output else "low",
            "lang": lang,
            "trigger": trigger,
            "plan_week": (int(plan.get("current_week") or 1) - 1) if plan else None,
        }
    )
    return _present(row, {"benchmarks": benchmarks, "reused": False})


def _benchmarks(race_name: str | None, distance_km: float) -> list[dict[str, Any]] | None:
    from services.race_matcher import race_benchmarks

    bench = race_benchmarks(race_name, distance_km=distance_km) if race_name else None
    return bench["results"] if bench else None


def status(assessment: dict[str, Any] | None, target_time_hours: float | None) -> dict[str, Any]:
    """Plan-header pill state from the latest assessment vs Time Target."""
    goals = (assessment or {}).get("goals")
    if not goals:
        return {"state": "not_assessed", "suggested_mins": None}
    if not target_time_hours:
        return {"state": "no_target", "suggested_mins": goals["b"]}
    target = target_time_hours * 60
    drift = (goals["b"] - target) / target
    if abs(drift) <= DRIFT_THRESHOLD:
        return {"state": "on_track", "suggested_mins": None}
    return {"state": "ahead" if drift < 0 else "behind", "suggested_mins": goals["b"]}


def run_for_plan(
    user: dict[str, Any], plan: dict[str, Any], trigger: str, lang: str = "en", exclude: set[str] | None = None
) -> dict[str, Any]:
    return run(
        user=user,
        race_name=plan.get("race_name"),
        distance_km=plan.get("course_distance_km"),
        elevation_gain_m=plan.get("course_elevation_gain_m"),
        race_date=plan.get("race_date"),
        plan=plan,
        exclude=exclude,
        lang=lang,
        trigger=trigger,
    )


def weekly_due(plan: dict[str, Any]) -> bool:
    """A completed week without a weekly assessment yet."""
    weeks_done = int(plan.get("current_week") or 1) - 1
    return (
        weeks_done >= 1 and plan.get("course_distance_km") and not db.has_weekly_goal_assessment(plan["id"], weeks_done)
    )


def plan_goal(plan: dict[str, Any]) -> dict[str, Any]:
    latest = db.get_latest_goal_assessment(plan["id"])
    assessment = _present(latest) if latest else None
    return {
        "assessment": assessment,
        "status": status(assessment, plan.get("target_time_hours")),
        "target_time_hours": plan.get("target_time_hours"),
    }
