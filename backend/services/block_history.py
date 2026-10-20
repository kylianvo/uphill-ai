"""Training-history prompt context shared by next-block generation and Adapt Week, so a
re-plan sees the same past weeks (per-session status, RPE, feedback, coach evaluation)
as a fresh block does."""

from typing import Any

from db import actual_volume_with_ticked, get_block_actual_volume, get_week_planned_volume
from services.calendar_rules import is_upcoming, start_monday, upcoming_note
from services.matching.block_evaluator import evaluate_block_performance


def session_review_status(w: dict[str, Any]) -> str:
    """Three-way status label used in the generation prompts:
    completed (checked off), MISSED (athlete explicitly confirmed), or
    not logged (ambiguous -- may have happened but was never checked off)."""
    if w.get("is_completed") == 1:
        return "completed"
    if w.get("is_missed") == 1:
        return "MISSED"
    return "not logged"


def build_history_lines(
    *,
    plan: dict[str, Any],
    athlete_id: int,
    all_workouts: list[dict[str, Any]],
    reviews: list[dict[str, Any]] | None,
    ranges: list[tuple[int, int, int, bool]],
    today,
    override_note: str | None = None,
) -> tuple[list[str], list[str]]:
    """(lines, coach_notes): one summary line per (block, first_week, last_week, evaluate) range, newest first.
    The first range also gets the per-session breakdown, and the coach evaluation when
    `evaluate` is set (a whole finished block; a partial block has none). Sessions still
    upcoming at `today` are neither missed nor counted against completion. coach_notes are the
    human coach directives on file from the first range's evaluation."""
    review_map = {r["block_number"]: r for r in (reviews or [])}
    plan_monday = start_monday(plan.get("start_date"))
    context_lines: list[str] = []
    coach_notes: list[str] = []
    # Newest first: it carries per-session detail, and this blob is the unbounded tail
    # of the prompt -- older summaries are the right thing to lose if anything is.
    for idx, (blk, wk_start, wk_end, evaluate) in enumerate(ranges):
        block_wos = [
            w for w in all_workouts if wk_start <= (w.get("week_number") or 0) <= wk_end and w.get("type") != "Rest"
        ]
        upcoming_wos = [w for w in block_wos if today is not None and is_upcoming(w, plan_monday, today)]
        upcoming_ids = {w["id"] for w in upcoming_wos}
        due_wos = [w for w in block_wos if w["id"] not in upcoming_ids]
        completed_wos = [w for w in block_wos if w.get("is_completed") == 1]

        # Planned totals (from generated workouts), summed week-by-week; sessions
        # still upcoming are not due yet.
        planned_weeks = [get_week_planned_volume(plan["id"], wk) for wk in range(wk_start, wk_end + 1)]
        planned_km = sum(w["distance_km"] for w in planned_weeks) - sum(w.get("distance_km") or 0 for w in upcoming_wos)
        planned_min = sum(w["duration_minutes"] for w in planned_weeks) - sum(
            w.get("duration_minutes") or 0 for w in upcoming_wos
        )

        # Actual totals (from true GPS watch activities, both matched & unplanned)
        actual_vol = get_block_actual_volume(
            user_id=athlete_id,
            plan_id=plan["id"],
            wk_start=wk_start,
            wk_end=wk_end,
            plan_start_date=plan.get("start_date"),
        )
        actual_km, actual_min, actual_vert = actual_volume_with_ticked(actual_vol, completed_wos)

        unplanned_count = actual_vol.get("unplanned_count", 0)
        unplanned_km = actual_vol.get("unplanned_km", 0.0)

        sessions_done = len(completed_wos)
        sessions_total = len(due_wos)
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
            f'{w.get("day_of_week", "?")} W{w.get("week_number", "?")}: "{w["notes"]}"'
            for w in completed_wos
            if w.get("notes")
        ]

        # block_wos is already filtered to non-Rest workouts (see its
        # definition above, earlier in this loop) -- classify by review status.
        missed = [
            f"{w.get('day_of_week', '?')} {w.get('title') or w.get('type', '?')}"
            for w in due_wos
            if session_review_status(w) == "MISSED"
        ]
        not_logged = [
            f"{w.get('day_of_week', '?')} {w.get('title') or w.get('type', '?')}"
            for w in due_wos
            if session_review_status(w) == "not logged"
        ]

        # Compose the compact summary line
        line = (
            f"Block {blk} (Wk {wk_start}-{wk_end}): "
            f"{sessions_done}/{sessions_total} sessions ({completion_pct}%) | "
            f"Actual {actual_km:.1f}km/{actual_min / 60:.1f}h"
            + (f" (+{actual_vert:.0f}m D+)" if actual_vert > 0 else "")
            + f" vs Planned {planned_km:.1f}km/{planned_min / 60:.1f}h"
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
        if upcoming_wos:
            context_lines.append(f"  {upcoming_note(upcoming_wos)}")

        if block_note:
            context_lines.append(f'  Athlete note: "{block_note}"')

        if idx == 0 and override_note:
            context_lines.append(override_note)

        if idx == 0:
            # Evaluate coach feedback on this most recent block:
            prev_eval = evaluate_block_performance(athlete_id, plan["id"], blk) if evaluate else {}
            if prev_eval.get("coach_summary"):
                context_lines.append(f"  Coach evaluation (Block {blk}): {prev_eval['coach_summary']}")
            if prev_eval.get("avg_quality_score") is not None:
                context_lines.append(
                    f"  Execution quality: {prev_eval['avg_quality_score']}% (Grade {prev_eval['quality_grade']})"
                )
            for tk in prev_eval.get("coaching_takeaways", []):
                context_lines.append(f"  Coach takeaway: {tk}")
            coach_notes = list(prev_eval.get("coach_notes", []))
            for cn in coach_notes:
                context_lines.append(f'  Coach directive on file: "{cn}"')

            # Most recent block: one line per session — performance, feedback,
            # RPE — so the next block reacts to specific sessions, not averages.
            context_lines.append("  Session-by-session (most recent period):")
            for w in block_wos:
                dur = w.get("duration_minutes") or 0
                km = w.get("distance_km") or 0
                planned = f"{w.get('title') or w.get('type', '?')} ({dur:.0f}min" + (f"/{km:.1f}km)" if km else ")")
                status = "upcoming" if w["id"] in upcoming_ids else session_review_status(w)
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

    return context_lines, coach_notes
