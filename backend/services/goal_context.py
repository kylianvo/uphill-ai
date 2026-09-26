"""Gathers everything the goal judge sees (docs/superpowers/specs/
2026-09-26-llm-goal-estimation-design.md).

No LLM and no maths: reads the athlete's profile, race history, UTMB index,
watch trends and training-block progress, trims them into one structure, and
applies the athlete's "What we used" exclusions. Every source is optional; a
failing one is skipped and listed in `missing`, never fails the request.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import db
from log_utils import get_logger
from services import race_history

_logger = get_logger(__name__)

MAX_HISTORY = 15
# users table column defaults: an untouched profile carries these, so they say
# nothing about the athlete and must not become an easy-pace prior.
_DEFAULT_ZONE2 = ("6:30", "5:45")


@dataclass
class GoalContext:
    prompt: dict[str, Any]
    target: dict[str, Any]
    results: list[dict[str, Any]]
    weekly_km: float | None = None
    ultra_finishes: int = 0
    easy_pace_min_km: float | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


def _pace(value: str | None) -> float | None:
    if not value or ":" not in value:
        return None
    minutes, seconds = value.split(":", 1)
    try:
        return int(minutes) + int(seconds) / 60
    except ValueError:
        return None


def _hms(seconds: int) -> str:
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}"


def _safe(label: str, fn: Any, missing: list[str], *args: Any) -> Any:
    try:
        return fn(*args)
    except Exception:
        _logger.warning("goal context source failed", extra={"fields": {"source": label}}, exc_info=True)
        missing.append(label)
        return None


def _history_row(r: dict[str, Any]) -> dict[str, Any]:
    row = {
        "id": r.get("id"),
        "date": r["race_date"],
        "race": (r.get("race_name") or "")[:60],
        "discipline": r.get("discipline"),
        "distance_km": round(r["distance_km"], 1),
        "gain_m": r.get("elevation_gain_m"),
        "time": "DNF" if r.get("is_dnf") else (_hms(r["finish_time_sec"]) if r.get("finish_time_sec") else None),
        "source": r.get("source"),
    }
    if r.get("rank_overall") and r.get("total_overall"):
        row["rank"] = f"{r['rank_overall']}/{r['total_overall']}"
    return row


def manual_result(ref: dict[str, Any]) -> dict[str, Any] | None:
    """A reference result typed into the modal (not linked to the profile)."""
    from services.race_estimator import _parse_hms_to_mins

    mins = _parse_hms_to_mins(ref.get("time"))
    if not mins or not ref.get("distance_km"):
        return None
    return {
        "id": "manual",
        "race_name": ref.get("race_name") or "Manual result",
        "race_date": ref.get("race_date") or date.today().isoformat(),
        "distance_km": float(ref["distance_km"]),
        "elevation_gain_m": ref.get("elevation_gain_m") or 0.0,
        "finish_time_sec": round(mins * 60),
        "is_dnf": False,
        "discipline": ref.get("discipline") or "trail",
        "source": "manual",
    }


def _block_progress(plan: dict[str, Any], user_id: int) -> dict[str, Any] | None:
    from services.matching.block_evaluator import evaluate_block_performance

    weeks_done = int(plan.get("current_week") or 1) - 1
    if weeks_done < 1:
        return None
    done = [
        w
        for w in db.get_plan_workouts(plan["id"])
        if (w.get("week_number") or 0) <= weeks_done and w.get("type") != "Rest"
    ]
    if not done:
        return None
    completed = [w for w in done if w.get("is_completed") == 1]
    block = {
        "weeks_done": weeks_done,
        "total_weeks": plan.get("total_weeks"),
        "sessions_planned": len(done),
        "sessions_completed": len(completed),
        "completion_pct": round(100 * len(completed) / len(done)),
        "planned_km": round(sum(w.get("distance_km") or 0 for w in done), 1),
        "completed_km": round(sum(w.get("distance_km") or 0 for w in completed), 1),
        "planned_vert_m": round(sum(w.get("elevation_gain_m") or 0 for w in done)),
        "completed_vert_m": round(sum(w.get("elevation_gain_m") or 0 for w in completed)),
    }
    evaluation = evaluate_block_performance(user_id, plan["id"], db.block_number_for_week(weeks_done))
    block.update(
        {
            "latest_block_quality_grade": evaluation.get("quality_grade"),
            "latest_block_rpe": evaluation.get("athlete_rpe"),
            "coach_notes": [n[:200] for n in (evaluation.get("coach_notes") or [])][:3],
        }
    )
    return block


def gather(
    *,
    user: dict[str, Any] | None,
    target: dict[str, Any],
    race_date: str | None,
    plan: dict[str, Any] | None = None,
    exclude: set[str] | None = None,
    extra_results: list[dict[str, Any]] | None = None,
    weeks_to_race: float | None = None,
) -> GoalContext:
    """`target` is a course from goal_anchors.resolve_course. Exclusion keys
    match the `key` of each returned source: "result:<id>", "utmb_index",
    "watch", "vo2max", "block"."""
    exclude = exclude or set()
    missing: list[str] = []
    sources: list[dict[str, Any]] = []

    def use(key: str, label: str) -> bool:
        included = key not in exclude
        sources.append({"key": key, "label": label, "included": included})
        return included

    results: list[dict[str, Any]] = []
    athlete: dict[str, Any] = {}
    weekly_km = ultra_finishes = easy_pace = None
    block = None
    if user:
        uid = user["id"]
        rows = _safe("race_history", lambda: race_history._dedupe(race_history.list_results(uid, False)), missing) or []
        for r in rows:
            if r.get("hidden"):
                continue
            label = f"{r['race_name'][:40]} {r['race_date'][:4]} · {'DNF' if r['is_dnf'] else _hms(r['finish_time_sec'] or 0)}"
            if use(f"result:{r['id']}", label):
                results.append(r)
        if not rows:
            missing.append("race_history")

        athlete = {
            "age": user.get("age"),
            "sex": user.get("gender"),
            "weight_kg": user.get("weight_kg"),
            "profile_weekly_km": user.get("current_weekly_km"),
            "max_hr": user.get("max_hr"),
            "aet_hr": user.get("aet_hr"),
            "ant_hr": user.get("ant_hr"),
            "threshold_pace": user.get("threshold_pace"),
        }
        weekly_km = user.get("current_weekly_km")
        zone2 = (user.get("zone2_pace_min"), user.get("zone2_pace_max"))
        if zone2 != _DEFAULT_ZONE2 and all(_pace(p) for p in zone2):
            easy_pace = (_pace(zone2[0]) + _pace(zone2[1])) / 2
            athlete["easy_pace_min_km"] = round(easy_pace, 2)

        vo2 = user.get("coros_vo2max")
        if vo2 and use("vo2max", f"VO2max {vo2:.0f}"):
            athlete["vo2max"] = vo2
        elif not vo2:
            missing.append("vo2max")

        utmb = _safe("utmb_index", db.get_utmb_index, missing, uid)
        if utmb and use("utmb_index", f"UTMB index {utmb}"):
            athlete["utmb_index"] = utmb
        elif not utmb:
            missing.append("utmb_index")

        trend = _safe("watch", db.get_weekly_training_trend, missing, uid)
        if trend and use("watch", f"Watch: {trend['avg_weekly_km']:.0f} km/wk, {trend['avg_weekly_vert_m']} m vert/wk"):
            athlete["watch_8wk"] = trend
            weekly_km = trend["avg_weekly_km"]
            recovery = _safe("daily_metrics", db.get_latest_daily_metrics, missing, uid)
            if recovery:
                athlete["recovery"] = recovery
        elif not trend:
            missing.append("watch")

        if plan:
            block = _safe("block", _block_progress, missing, plan, uid)
            if block and not use("block", f"Training: {block['completion_pct']}% of weeks 1–{block['weeks_done']}"):
                block = None

    for extra in extra_results or []:
        results.append(extra)
        sources.append(
            {
                "key": "result:manual",
                "label": f"{extra['race_name'][:40]} · {_hms(extra['finish_time_sec'])}",
                "included": True,
            }
        )

    finished_trail = [r for r in results if not r.get("is_dnf") and r.get("discipline") == "trail"]
    ultra_finishes = sum(r["distance_km"] > 42.195 for r in finished_trail)
    if not finished_trail:
        missing.append("recent_trail_result")

    field_ = target.get("field") or {}
    curve = field_.get("curve")
    prompt = {
        "race": {
            "name": target.get("race_name"),
            "date": race_date,
            "distance_km": target["distance_km"],
            "gain_m": target["elevation_gain_m"],
            "terrain": target.get("terrain"),
            "key_climbs": target.get("key_climbs"),
            "climate": target.get("climate"),
            "profile_source": target.get("profile_source"),
            "field": {
                "years": field_.get("years"),
                "winner_mins": field_.get("winner_mins"),
                "finishers": field_.get("finishers"),
                "percentile_mins": {f"p{int(p)}": round(m) for p, m in curve} if curve else None,
            }
            if field_
            else None,
        },
        "athlete": {k: v for k, v in athlete.items() if v is not None},
        "history": [_history_row(r) for r in results[:MAX_HISTORY]],
        "block": block,
        "weeks_to_race": round(weeks_to_race) if weeks_to_race is not None else None,
        "current_target_mins": round(plan["target_time_hours"] * 60)
        if plan and plan.get("target_time_hours")
        else None,
    }
    return GoalContext(
        prompt=prompt,
        target=target,
        results=results,
        weekly_km=weekly_km,
        ultra_finishes=ultra_finishes,
        easy_pace_min_km=easy_pace,
        sources=sources,
        missing=sorted(set(missing)),
    )
