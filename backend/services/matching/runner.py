"""Runs the matcher over an athlete's activities and records the outcome.

Shadow mode is the default and is deliberate: the thresholds in assigner.py are
provisional, and letting an uncalibrated matcher mark sessions complete would
corrupt the very training history it is meant to describe. In shadow mode the
runner writes match state and nothing else, so its decisions can be reviewed
against reality before it is trusted.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta

import db
from config import settings
from log_utils import get_logger
from services.matching.assigner import assign
from services.matching.bundler import bundle_activities
from services.matching.quality_scorer import score_workout_quality
from services.workout_calendar import plan_start_monday, workout_date

logger = get_logger(__name__)

# workout_calendar.plan_start_monday computes total_weeks from week_number
# lazily -- via a generator inside max() -- only on its legacy fallback path
# (no plans.start_date, no explicit race workout). The existing ICS export
# essentially never exercises that branch (current plans always carry
# start_date), so a corrupted week_number sitting in an old legacy plan has
# never had a chance to raise before now. This runner calls
# plan_start_monday/workout_date directly for every plan an athlete has ever
# had, so it is the first caller that can actually reach that data.
#
# Decision: a malformed schedule must not take down the whole run for an
# athlete who has one bad legacy plan among several healthy ones.
#   - A plan whose anchor (plan_start_monday) can't be computed has no valid
#     placement for ANY of its workouts, so the whole plan's workouts are
#     skipped and logged.
#   - A single workout whose own date offset (workout_date) can't be computed
#     is skipped on its own, leaving its siblings in the same plan intact.
# Either way, an activity that lands on an affected day simply finds no
# workout candidates and is reported as unmatched -- never dropped, never a
# crash.
_MALFORMED_SCHEDULE_ERRORS = (ValueError, TypeError, KeyError)


def _workouts_by_date(workouts: list[dict]) -> dict[date, list[dict]]:
    """Groups workouts by calendar date.

    db.get_dated_workouts_for_matching's real rows carry week_number/
    day_of_week/plans.start_date/plans.race_date and need workout_date derived
    per-plan below. A workout that already carries a "workout_date" (e.g. a
    caller -- or a test double -- that pre-dated it) is grouped directly on
    that value instead: it needs no plan anchor, and folding it into the
    grouped_by_plan pass below would incorrectly pull it into some other
    plan's week_number/total_weeks computation whenever its start_date and
    race_date both happen to be absent.
    """
    by_date: dict[date, list[dict]] = defaultdict(list)

    needs_dating: list[dict] = []
    for workout in workouts:
        when = workout.get("workout_date")
        if when is not None:
            by_date[when].append(workout)
        else:
            needs_dating.append(workout)

    grouped_by_plan: dict[tuple, list[dict]] = defaultdict(list)
    for workout in needs_dating:
        grouped_by_plan[(workout.get("start_date"), workout.get("race_date"))].append(workout)

    for (start_date, race_date), plan_workouts in grouped_by_plan.items():
        parsed_race = race_date
        if isinstance(parsed_race, str):
            try:
                parsed_race = datetime.strptime(parsed_race, "%Y-%m-%d").date()
            except ValueError:
                parsed_race = date.today()

        try:
            start_monday = plan_start_monday(start_date, plan_workouts, parsed_race or date.today())
        except _MALFORMED_SCHEDULE_ERRORS as exc:
            logger.warning(
                "skipping plan with a malformed schedule anchor",
                extra={
                    "fields": {
                        "service": "matching",
                        "event": "malformed_plan_schedule",
                        "workout_ids": [w.get("id") for w in plan_workouts],
                        "error": str(exc),
                    }
                },
            )
            continue

        for workout in plan_workouts:
            try:
                when = workout_date(start_monday, workout["week_number"], workout["day_of_week"])
            except _MALFORMED_SCHEDULE_ERRORS as exc:
                logger.warning(
                    "skipping workout with a malformed week_number or day_of_week",
                    extra={
                        "fields": {
                            "service": "matching",
                            "event": "malformed_workout_schedule",
                            "workout_id": workout.get("id"),
                            "error": str(exc),
                        }
                    },
                )
                continue
            enriched = dict(workout)
            enriched["workout_date"] = when
            by_date[when].append(enriched)
    return by_date


async def match_user(user_id: int, since: date, until: date, plan_id: int | None = None) -> dict[str, int]:
    activities = db.get_activities_for_matching(user_id, since, until + timedelta(days=1))
    workouts = db.get_dated_workouts_for_matching(user_id, plan_id=plan_id)
    by_date = _workouts_by_date(workouts)

    totals = {"matched": 0, "suggested": 0, "unmatched": 0, "skipped_manual": 0}

    athlete_profile = {}
    if hasattr(db, "get_user_by_id"):
        try:
            athlete_profile = db.get_user_by_id(user_id) or {}
        except Exception:
            pass

    matched_workout_ids: set[int] = set()

    by_day: dict[date, list[dict]] = defaultdict(list)
    for activity in activities:
        if activity.get("match_method") == "manual":
            totals["skipped_manual"] += 1
            continue
        by_day[activity["start_time"].date()].append(activity)

    activities_by_id = {a["id"]: a for a in activities}

    for day, day_activities in sorted(by_day.items()):
        bundles = bundle_activities(day_activities)
        candidates = [w for w in by_date.get(day, []) if not w.get("is_completed")]
        for assignment in assign(bundles, candidates):
            band = assignment.confidence_band
            if band == "auto":
                totals["matched"] += 1
            elif band == "suggest":
                totals["suggested"] += 1
            else:
                totals["unmatched"] += 1

            primary_id = assignment.bundle.primary_activity_id
            if primary_id is None and assignment.bundle.activity_ids:
                primary_id = max(
                    assignment.bundle.activity_ids,
                    key=lambda aid: float(activities_by_id.get(aid, {}).get("duration_seconds") or 0.0),
                )

            matched_workout = None
            if assignment.workout_id:
                matched_workout = next((w for w in candidates if w.get("id") == assignment.workout_id), None)

            quality_res = None
            if assignment.workout_id and matched_workout and band in ("auto", "suggest"):
                quality_res = score_workout_quality(matched_workout, assignment.bundle, athlete_profile)

            for activity_id in assignment.bundle.activity_ids:
                is_primary = activity_id == primary_id
                assigned_workout_id = assignment.workout_id if is_primary else None
                fragment_details = {
                    "reasons": assignment.score.reasons,
                    "components": assignment.score.components,
                    "fragments": assignment.bundle.fragment_count,
                    "warmup_distance_km": assignment.bundle.warmup_distance_km,
                }
                if not is_primary:
                    fragment_details["bundle_primary_activity_id"] = primary_id

                q_score = quality_res.overall_score if (is_primary and quality_res) else None
                q_grade = quality_res.grade if (is_primary and quality_res) else None
                q_details = quality_res.to_dict() if (is_primary and quality_res) else None

                db.save_match(
                    activity_id=activity_id,
                    workout_id=assigned_workout_id,
                    confidence=assignment.score.total if is_primary else 0.0,
                    method=band if (is_primary and band != "unmatched") else "none",
                    details=fragment_details,
                    quality_score=q_score,
                    quality_grade=q_grade,
                    quality_details=q_details,
                )

            if assignment.workout_id:
                matched_workout_ids.add(assignment.workout_id)

            if band == "auto" and assignment.workout_id and not settings.MATCHING_SHADOW_MODE:
                db.update_workout_log(assignment.workout_id, is_completed=1)

    # Auto-Skip: Mark past scheduled workouts with no recorded activity and no match as is_missed = 1
    if not settings.MATCHING_SHADOW_MODE:
        today = date.today()
        for day, plan_workouts in by_date.items():
            if day < today:
                for w in plan_workouts:
                    w_id = w.get("id")
                    if (
                        w_id
                        and not w.get("is_completed")
                        and w_id not in matched_workout_ids
                        and w.get("is_missed") != 1
                    ):
                        db.update_workout_log(w_id, is_missed=1)

    logger.info(
        "matching run complete",
        extra={
            "fields": {
                "service": "matching",
                "event": "run_complete",
                "user_id": user_id,
                "shadow": settings.MATCHING_SHADOW_MODE,
                **totals,
            }
        },
    )
    return totals
