"""Block performance evaluation engine.

Evaluates an athlete's completed training block (2 weeks) across:
1. Adherence / Completion rate (sessions completed vs planned, volume adherence).
2. Watch Execution Quality (average quality score, quality grade, Zone 2 adherence, cardiac control).
3. Coaching Takeaways & Synthesis (actionable coach insights and guidance for the next block).
4. Human Coach Notes (persisted coach directives for the athlete/plan).
"""

import json
from typing import Any

from db import (
    get_activities_for_block,
    get_block_reviews,
    get_coach_notes,
    get_plan_workouts,
)


def evaluate_block_performance(
    athlete_id: int,
    plan_id: int,
    block_number: int,
) -> dict[str, Any]:
    """Evaluates an athlete's completed training block to produce coach feedback."""
    week_start = (block_number - 1) * 2 + 1
    week_end = block_number * 2

    all_workouts = get_plan_workouts(plan_id)
    block_wos = [
        w for w in all_workouts if week_start <= (w.get("week_number") or 0) <= week_end and w.get("type") != "Rest"
    ]

    completed_wos = [w for w in block_wos if w.get("is_completed") == 1]
    missed_wos = [w for w in block_wos if w.get("is_missed") == 1]

    sessions_total = len(block_wos)
    sessions_done = len(completed_wos)
    completion_pct = round(sessions_done / sessions_total * 100) if sessions_total else 0

    planned_km = sum(w.get("distance_km") or 0 for w in block_wos)
    planned_min = sum(w.get("duration_minutes") or 0 for w in block_wos)
    actual_km = sum(w.get("distance_km") or 0 for w in completed_wos)
    actual_min = sum(w.get("duration_minutes") or 0 for w in completed_wos)

    # Matched watch activities with quality scores
    activities = get_activities_for_block(plan_id, week_start, week_end)
    activities_with_scores = [a for a in activities if a.get("quality_score") is not None]

    avg_quality_score = None
    quality_grade = None
    all_takeaways: list[str] = []

    if activities_with_scores:
        avg_quality_score = round(
            sum(float(a["quality_score"]) for a in activities_with_scores) / len(activities_with_scores),
            1,
        )
        if avg_quality_score >= 90:
            quality_grade = "A"
        elif avg_quality_score >= 80:
            quality_grade = "B"
        elif avg_quality_score >= 70:
            quality_grade = "C"
        elif avg_quality_score >= 60:
            quality_grade = "D"
        else:
            quality_grade = "F"

        for a in activities_with_scores:
            q_det = a.get("quality_details")
            if isinstance(q_det, str):
                try:
                    q_det = json.loads(q_det)
                except Exception:
                    q_det = {}
            if isinstance(q_det, dict):
                t_list = q_det.get("takeaways") or []
                for t in t_list:
                    if t and t not in all_takeaways:
                        all_takeaways.append(t)

    # Human coach notes
    raw_coach_notes = get_coach_notes(athlete_id, target_type="plan", target_id=plan_id)
    raw_coach_notes += get_coach_notes(athlete_id, target_type="block", target_id=block_number)
    coach_notes_texts = [r["note"] for r in raw_coach_notes if r.get("note")]

    # Athlete's review from block_reviews (if submitted)
    reviews = get_block_reviews(plan_id) or []
    block_rev = next((r for r in reviews if r.get("block_number") == block_number), None)
    athlete_rpe = block_rev.get("overall_rpe") if block_rev else None
    athlete_notes = block_rev.get("notes") if block_rev else None

    # Synthesize Coach Summary & Guidance
    if avg_quality_score is not None:
        if avg_quality_score >= 88 and completion_pct >= 85:
            summary = (
                f"Excellent execution across Block {block_number}. "
                f"High aerobic discipline ({avg_quality_score}% Quality, Grade {quality_grade}) "
                f"with {sessions_done}/{sessions_total} sessions completed. Ready for progressive volume."
            )
        elif avg_quality_score >= 75 and completion_pct >= 70:
            summary = (
                f"Good training consistency in Block {block_number} ({completion_pct}% completion, Grade {quality_grade}). "
                f"Aerobic targets were generally respected. Maintain consistent pacing on long sessions."
            )
        elif completion_pct < 70:
            summary = (
                f"Block {block_number} volume fell below target ({completion_pct}% completed). "
                f"Focus on consolidating base volume before adding speed or high intensity."
            )
        else:
            summary = (
                f"Block {block_number} completed with {completion_pct}% consistency. "
                f"Execution score {avg_quality_score}% indicates some intensity drift. Prioritize strict Zone 2 control."
            )
    else:
        # Fallback when no watch activities are synced yet
        if completion_pct >= 85:
            summary = (
                f"Strong consistency in Block {block_number} with {sessions_done}/{sessions_total} sessions completed ({completion_pct}%). "
                f"Great work staying on track with scheduled volume."
            )
        elif completion_pct >= 70:
            summary = (
                f"Solid training consistency in Block {block_number} ({sessions_done}/{sessions_total} sessions, {completion_pct}%). "
                f"Continue building steady weekly momentum."
            )
        else:
            summary = (
                f"Block {block_number} completion was {completion_pct}% ({sessions_done}/{sessions_total} sessions). "
                f"Focus on establishing regular weekly routine before ramping up training load."
            )

    # Default takeaways if watch didn't provide any
    if not all_takeaways:
        if completion_pct >= 80:
            all_takeaways.append("Consistent session completion throughout the block.")
        if actual_km >= planned_km * 0.9 and planned_km > 0:
            all_takeaways.append("Weekly volume targets were met successfully.")
        elif completion_pct < 70:
            all_takeaways.append("Multiple sessions missed; consolidate base before increasing load.")

    return {
        "block_number": block_number,
        "week_start": week_start,
        "week_end": week_end,
        "sessions_total": sessions_total,
        "sessions_completed": sessions_done,
        "sessions_missed": len(missed_wos),
        "completion_pct": completion_pct,
        "planned_km": round(planned_km, 1),
        "actual_km": round(actual_km, 1),
        "planned_minutes": round(planned_min),
        "actual_minutes": round(actual_min),
        "avg_quality_score": avg_quality_score,
        "quality_grade": quality_grade,
        "coaching_takeaways": all_takeaways[:5],
        "coach_summary": summary,
        "coach_notes": coach_notes_texts,
        "athlete_rpe": athlete_rpe,
        "athlete_notes": athlete_notes,
    }
