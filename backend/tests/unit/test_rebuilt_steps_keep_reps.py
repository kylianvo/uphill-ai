"""Only Interval / Walk-Run sessions carry rep fields: the app shows them as the main set (prod plan 129 showed
'5 x 15 s' on an easy run whose steps said '20 min steady Zone 2'). On other runs the strides or hill sprints move
into their own step of the text; gym / ME text reads warm-up → one exercise per step → cool-down."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.plan_generator import PlanGenerator


def _session(title: str, typ: str, minutes: int, reps: int, value: int, description: str) -> dict:
    return {
        "week_number": 1,
        "day_of_week": "Friday",
        "phase": "Base",
        "title": title,
        "type": typ,
        "duration_minutes": minutes,
        "target_zone": "Zone 2",
        "distance_km": round(minutes / 6, 1),
        "elevation_gain_m": 0,
        "interval_reps": reps,
        "interval_rep_value": value,
        "interval_rep_unit": "s",
        "description": description,
        "fueling_tip": "Water only.",
    }


def _generate(session: dict, user: dict | None = None, tier: str | None = None) -> dict:
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps([session]), usage_metadata=None)
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=client),
    ):
        workouts, _tier = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=999999,
                user_profile=user or {"age": 34, "max_hr": 188, "resting_hr": 52},
                # A Monday start: week 1 drops days before the start, so "today" would drop Friday on weekends.
                race_info={
                    "lang": "en",
                    "terrain": "trail",
                    "plan_start_date": "2026-10-19",
                    **({"athlete_tier": tier} if tier else {}),
                },
                total_weeks=8,
                api_key="test-key",
                block_number=1,
            )
        )
    return next(w for w in workouts if w["day_of_week"] == "Friday" and w["type"] != "Rest")


def test_easy_run_strides_become_their_own_step_before_the_cooldown():
    # the steps already add up (prod case), so nothing else rewrites the text
    wo = _generate(
        _session(
            "Aerobic Base Run + Strides",
            "Easy",
            40,
            5,
            15,
            "Warm-up 5 min easy → 30 min steady Zone 2 → Cool-down 5 min easy.",
        )
    )
    assert wo["interval_reps"] is None
    steps = wo["description"].rstrip(".").split(" → ")
    assert steps[-2] == "5 × 15 s strides with easy jog back between"
    assert steps[-1].startswith("Cool-down")


def test_rep_fields_without_strides_or_sprints_are_dropped():
    wo = _generate(
        _session(
            "Recovery Run + Core",
            "Easy",
            40,
            3,
            45,
            "Warm-up 5 min easy → 30 min steady Zone 2 → Cool-down 5 min easy.",
        )
    )
    assert wo["interval_reps"] is None and wo["interval_rep_value"] is None
    assert "×" not in wo["description"]


def test_gym_session_gets_warmup_and_cooldown_steps_around_its_exercises():
    wo = _generate(
        _session(
            "Gym ME",
            "Muscular Endurance",
            45,
            0,
            0,
            "Process: Step-ups 4x10/leg, 30s rest → Walking Lunges 4x10/leg, 30s rest. Overall: climbing legs.",
        )
    )
    body, note = wo["description"].split(" Overall:")
    steps = body.removeprefix("Process: ").rstrip(".").split(" → ")
    assert steps[0].startswith("Warm-up") and steps[-1].startswith("Cool-down")
    assert steps[1:3] == ["Step-ups 4x10/leg, 30s rest", "Walking Lunges 4x10/leg, 30s rest"]
    overall, rest = note.split(" Reason:")
    assert overall.strip() == "climbing legs."  # the AI's note stays; the missing sections come from the defaults
    assert " Benefit:" in rest and " Warning:" in rest


def test_run_plus_strength_keeps_its_exercises():
    # prod (Dylan): a 45 min Easy run + strength; its run steps add up to 35 min because the exercises carry no
    # minutes. It must not be rebuilt into a plain run.
    desc = (
        "Warm up 5 min easy walking → 25 min easy recovery run in Zone 1 → Bodyweight Squats: 3x10, 90s rest "
        "→ Plank: 3x45s, 60s rest → Cool down 5 min gentle stretching."
    )
    wo = _generate(_session("Aerobic Recovery Run & General Strength", "Easy", 45, 3, 45, desc))
    assert wo["title"] == "Aerobic Recovery Run & General Strength"
    assert "Bodyweight Squats: 3x10, 90s rest → Plank: 3x45s, 60s rest" in wo["description"]
    assert wo["interval_reps"] is None


def test_hill_sprints_typed_interval_at_an_easy_zone_read_as_an_easy_run():
    # Haiku plans 2026-10-22: "Treadmill Hill Sprint Session", type Interval, Zone 1 - the app showed it as hard work
    session = _session(
        "Hill Sprint Session",
        "Interval",
        45,
        6,
        10,
        "Warm-up 15 min easy → 30 min steady Zone 2 with 6 x 10 s hill sprints → Cool-down 5 min easy.",
    )
    session["target_zone"] = "Zone 1"
    wo = _generate(session)
    assert wo["type"] == "Easy"
    assert "sprint" in wo["description"].lower()


def test_a_zone3_interval_keeps_its_type():
    session = _session(
        "Uphill Intervals",
        "Interval",
        50,
        4,
        6,
        "Warm-up 15 min easy → 4 x 6 min Zone 3 uphill, 2 min jog between → Cool-down 11 min easy.",
    )
    session["target_zone"] = "Zone 3"
    session["interval_rep_unit"] = "min"
    athlete = {"age": 34, "max_hr": 190, "resting_hr": 45, "aet_hr": 156, "ant_hr": 168, "threshold_source": "lab",
               "current_weekly_km": 90.0}  # fmt: skip
    assert _generate(session, athlete, "sub_elite")["type"] == "Interval"
