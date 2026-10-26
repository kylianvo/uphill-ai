"""Uphill workouts as Garmin Training API workouts. Pure: no I/O.

The training content comes from coros_workouts.build_course, which already turns a
workout into timed sections with heart-rate targets (Process chain, interval groups,
race-day placeholder, fallbacks). This module only re-expresses those sections as
Garmin steps, so both watches get the same session.
"""

from typing import Any

from services.coros_workouts import (
    SECTION_COOLDOWN,
    SECTION_RECOVERY,
    SECTION_TRAINING,
    SECTION_WARMUP,
    TARGET_DISTANCE,
    TARGET_TIME,
    clip_text,
)

PROVIDER_NAME = "Uphill AI"  # shown to the athlete in Garmin Connect (max 20 chars)
MAX_DESCRIPTION = 1024
_INTENSITY = {
    SECTION_WARMUP: "WARMUP",
    SECTION_TRAINING: "ACTIVE",
    SECTION_RECOVERY: "RECOVERY",
    SECTION_COOLDOWN: "COOLDOWN",
}


def _duration(section: dict[str, Any]) -> dict[str, Any]:
    if section.get("targetType") == TARGET_TIME:
        return {"durationType": "TIME", "durationValue": int(section["targetValue"])}
    if section.get("targetType") == TARGET_DISTANCE:
        return {"durationType": "DISTANCE", "durationValue": int(section["targetValue"]), "durationValueType": "METER"}
    return {"durationType": "OPEN", "durationValue": None}


def _target(section: dict[str, Any]) -> dict[str, Any]:
    """Our own bpm range when the workout has one; otherwise the zone number, which the
    watch reads against the athlete's Garmin zones; otherwise no target."""
    if section.get("intensityValueStart") is not None:
        return {
            "targetType": "HEART_RATE",
            "targetValueLow": section["intensityValueStart"],
            "targetValueHigh": section.get("intensityValueEnd", section["intensityValueStart"]),
        }
    if section.get("sectionIntensity") is not None:
        return {"targetType": "HEART_RATE", "targetValue": section["sectionIntensity"]}
    return {"targetType": "OPEN"}


def _steps(sections: list[dict[str, Any]], order: list[int], in_repeat: bool = False) -> list[dict[str, Any]]:
    out = []
    for section in sections:
        order[0] += 1
        if section.get("intervalGroup"):
            group_order = order[0]
            out.append(
                {
                    "type": "WorkoutRepeatStep",
                    "stepOrder": group_order,
                    "repeatType": "REPEAT_UNTIL_STEPS_CMPLT",
                    "repeatValue": section["repeats"],
                    "steps": _steps(section["sets"], order, in_repeat=True),
                }
            )
            continue
        intensity = _INTENSITY.get(section.get("sectionType"), "ACTIVE")
        if in_repeat and intensity == "ACTIVE":
            intensity = "INTERVAL"
        out.append(
            {
                "type": "WorkoutStep",
                "stepOrder": order[0],
                "intensity": intensity,
                **_duration(section),
                **_target(section),
            }
        )
    return out


def to_workout(course: dict[str, Any]) -> dict[str, Any]:
    """One COROS-shaped run course (coros_workouts.build_course) as a Garmin RUNNING workout.
    Garmin has no trail-running workout sport, so every run goes out as RUNNING."""
    steps = _steps(course.get("sections") or [], [0])
    if not steps:
        steps = [{"type": "WorkoutStep", "stepOrder": 1, "intensity": "ACTIVE", "durationType": "OPEN",
                  "durationValue": None, "targetType": "OPEN"}]  # fmt: skip
    return {
        "workoutName": course["courseName"],
        "description": clip_text(course.get("courseDescription") or "", MAX_DESCRIPTION),
        "sport": "RUNNING",
        "workoutProvider": PROVIDER_NAME,
        "workoutSourceId": PROVIDER_NAME,
        "isSessionTransitionEnabled": False,
        "segments": [{"segmentOrder": 1, "sport": "RUNNING", "steps": steps}],
    }
