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


def _generate(session: dict) -> dict:
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps([session]), usage_metadata=None)
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=client),
    ):
        workouts, _tier = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=999999,
                user_profile={"age": 34, "max_hr": 188, "resting_hr": 52},
                race_info={"lang": "en", "terrain": "trail"},
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
    assert note.strip() == "climbing legs."


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
