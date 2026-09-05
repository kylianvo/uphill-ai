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


async def match_user(user_id: int, since: date, until: date) -> dict[str, int]:
    activities = db.get_activities_for_matching(user_id, since, until + timedelta(days=1))
    workouts = db.get_dated_workouts_for_matching(user_id)
    by_date = _workouts_by_date(workouts)

    totals = {"matched": 0, "suggested": 0, "unmatched": 0, "skipped_manual": 0}

    by_day: dict[date, list[dict]] = defaultdict(list)
    for activity in activities:
        if activity.get("match_method") == "manual":
            totals["skipped_manual"] += 1
            continue
        by_day[activity["start_time"].date()].append(activity)

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

            for activity_id in assignment.bundle.activity_ids:
                db.save_match(
                    activity_id=activity_id,
                    workout_id=assignment.workout_id,
                    confidence=assignment.score.total,
                    method=band if band != "unmatched" else "none",
                    details={
                        "reasons": assignment.score.reasons,
                        "components": assignment.score.components,
                        "fragments": assignment.bundle.fragment_count,
                    },
                )

            if band == "auto" and assignment.workout_id and not settings.MATCHING_SHADOW_MODE:
                db.update_workout_log(assignment.workout_id, is_completed=1)

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
