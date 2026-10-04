"""Synthetic model-boundary tests for the shared prescription."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.plan_generator import PlanGenerator

SEGMENTS = [
    {
        "kind": "run",
        "role": "warmup",
        "duration_minutes": 12,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6,
    },
    {
        "kind": "strength",
        "duration_minutes": 24,
        "zone": None,
        "setting": "indoor",
        "exercise": {"name": "Bodyweight Squats", "sets": 3, "reps": 8, "rest_seconds": 75},
    },
    {
        "kind": "run",
        "role": "cooldown",
        "duration_minutes": 6,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6,
    },
]


async def generate(payload, lang="en", *, prepared_methods=None, retry_payload=None, check_starting_volume=False):
    response = MagicMock(text=json.dumps(payload))
    client = MagicMock()
    client.aio.__aenter__.return_value = client.aio
    client.aio.models.generate_content = AsyncMock(side_effect=client.models.generate_content)
    if retry_payload is None:
        client.models.generate_content.return_value = response
    else:
        client.models.generate_content.side_effect = [response, MagicMock(text=json.dumps(retry_payload))]
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        workouts, _ = await PlanGenerator.generate_plan_workouts(
            plan_id=0,
            user_profile={"current_weekly_km": 62, "threshold_pace": "5:00"},
            race_info={
                "lang": lang,
                "goal_type": "finish",
                "date": "2026-12-06",
                "plan_start_date": "2026-10-05",
                "training_environment": "flat",
                "validation_context": {
                    "prepared_methods": prepared_methods or [],
                    # Short accounting boundary cases do not represent a full training week.
                    **({} if check_starting_volume else {"weekly_km_bounds": {}}),
                },
            },
            total_weeks=8,
            api_key="fake-key",
        )
    return workouts, client.models.generate_content.call_count


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "vi"])
async def test_structured_me_overrides_contradictory_totals_and_prose(lang):
    workouts, attempts = await generate(
        [
            {
                "week_number": 1,
                "day_of_week": "Tuesday",
                "type": "Muscular Endurance",
                "title": "ME",
                "duration_minutes": 99,
                "distance_km": 99,
                "description": "Warm-up 99 minutes, run 99 km.",
                "segments": SEGMENTS,
            }
        ],
        lang,
        prepared_methods=["muscular_endurance"],
    )
    wo = workouts[0]
    assert attempts == 1
    assert wo["duration_minutes"] == 42
    assert wo["distance_km"] == 3
    assert "99" not in wo["description"]
    assert "6:00/km" in wo["description"]
    assert "Warm-up" in wo["description"] and "Cool-down" in wo["description"]


@pytest.mark.asyncio
async def test_malformed_segments_trigger_only_one_retry():
    workouts, attempts = await generate(
        [
            {
                "week_number": 1,
                "day_of_week": "Tuesday",
                "type": "Easy",
                "duration_minutes": 30,
                "segments": [
                    {
                        "kind": "run",
                        "duration_minutes": -3,
                        "setting": "flat_outdoor",
                        "zone": "Zone 2",
                        "pace_min_per_km": 6,
                    }
                ],
            }
        ]
    )
    assert attempts == 2
    assert all(w["duration_minutes"] >= 0 for w in workouts)
    assert not any(w.get("segments", [{}])[0].get("duration_minutes", 0) < 0 for w in workouts)


@pytest.mark.asyncio
async def test_single_workout_uses_segment_totals_not_a_second_prose_plan():
    response = MagicMock(
        text=json.dumps(
            {
                "title": "Easy Run",
                "target_zone": "Zone 2",
                "description": "Run 99 minutes.",
                "segments": [
                    SEGMENTS[0],
                    {**SEGMENTS[0], "role": "main", "duration_minutes": 30, "zone": "Zone 2"},
                    SEGMENTS[2],
                ],
            }
        )
    )
    client = MagicMock()
    client.models.generate_content.return_value = response
    with patch("google.genai.Client", return_value=client):
        result = await PlanGenerator.generate_single_workout(
            {"lang": "vi"}, "Easy", 30, "Tuesday", 1, api_key="fake-key"
        )
    assert result["duration_minutes"] == 48
    assert result["distance_km"] == 8
    assert "99" not in result["description"]
    assert "12 phút" in result["description"]


@pytest.mark.asyncio
async def test_legacy_prompt_response_remains_compatible_without_claimed_precision():
    workouts, _ = await generate(
        [
            {
                "week_number": 1,
                "day_of_week": "Tuesday",
                "type": "Easy",
                "duration_minutes": 30,
                "title": "Easy Run",
                "description": "Easy Run with comfortable effort.",
            }
        ]
    )
    assert workouts[0]["duration_minutes"] == 30
    assert "prescription" not in workouts[0]


@pytest.mark.asyncio
async def test_numeric_rationale_is_rejected_instead_of_showing_two_prescriptions():
    workouts, attempts = await generate(
        [
            {
                "week_number": 1,
                "day_of_week": "Tuesday",
                "type": "Muscular Endurance",
                "segments": SEGMENTS,
                "rationale": "Run 99 km.",
            }
        ]
    )
    assert attempts == 2
    assert not any(w.get("rationale") == "Run 99 km." for w in workouts)


@pytest.mark.asyncio
async def test_rule_fallback_has_explicit_prescription_and_vi_numbers():
    with (
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        workouts, _ = await PlanGenerator.generate_plan_workouts(
            plan_id=0,
            user_profile={"current_weekly_km": 62},
            race_info={
                "lang": "vi",
                "goal_type": "finish",
                "date": "2026-12-06",
                "plan_start_date": "2026-10-05",
                "training_environment": "flat",
            },
            total_weeks=8,
            api_key=None,
        )
    for wo in workouts:
        assert "prescription" in wo
        assert wo["duration_minutes"] == wo["prescription"]["duration_minutes"]
        assert (
            "Warm-up" in wo["description"]
            or wo["type"] == "Rest"
            or "Strength" in wo["description"]
            or "Run" in wo["description"]
        )


@pytest.mark.asyncio
async def test_single_workout_segments_cannot_override_coach_main_duration():
    response = MagicMock(text=json.dumps({"title": "Easy Run", "segments": [SEGMENTS[0], SEGMENTS[2]]}))
    client = MagicMock()
    client.models.generate_content.return_value = response
    with patch("google.genai.Client", return_value=client):
        with pytest.raises(ValueError, match="coach"):
            await PlanGenerator.generate_single_workout({}, "Easy", 30, "Tuesday", 1, api_key="fake-key")


@pytest.mark.asyncio
async def test_single_workout_segments_cannot_override_coach_pace():
    response = MagicMock(
        text=json.dumps(
            {
                "title": "Easy Run",
                "segments": [
                    {**SEGMENTS[0], "role": "main", "duration_minutes": 30, "zone": "Zone 2", "pace_min_per_km": 7}
                ],
            }
        )
    )
    client = MagicMock()
    client.models.generate_content.return_value = response
    with patch("google.genai.Client", return_value=client):
        with pytest.raises(ValueError, match="coach pace"):
            await PlanGenerator.generate_single_workout(
                {}, "Easy", 30, "Tuesday", 1, target_pace="5:00 /km", api_key="fake-key"
            )
    assert "5:00 /km" in client.models.generate_content.call_args.kwargs["contents"]


async def final_fallback(total_weeks, distance=80, ascent=4000):
    with (
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        rows, _ = await PlanGenerator.generate_plan_workouts(
            plan_id=0,
            user_profile={"current_weekly_km": 62},
            race_info={
                "lang": "en",
                "goal_type": "finish",
                "date": "2026-10-24",
                "plan_start_date": "2026-10-05",
                "training_environment": "flat",
                "course_distance_km": distance,
                "course_elevation_gain_m": ascent,
            },
            total_weeks=total_weeks,
            api_key=None,
            weeks_per_block=total_weeks,
        )
    return rows


@pytest.mark.asyncio
async def test_fallback_recovery_walk_remains_hiking():
    rows = await final_fallback(2)
    wo = next(w for w in rows if w["title"] == "Post-Race Gentle Hike")
    assert wo["prescription"]["run_km"] == 0
    assert wo["prescription"]["hike_km"] == 2
    assert "Hike: 30 minutes" in wo["description"]


@pytest.mark.asyncio
async def test_fallback_race_preserves_known_course():
    rows = await final_fallback(4)
    wo = next(w for w in rows if w["type"] == "Race")
    assert wo["distance_km"] == 80
    assert wo["elevation_gain_m"] == 4000
    assert wo["duration_minutes"] == 520


@pytest.mark.asyncio
async def test_single_deterministic_run_accounts_for_both_warmup_and_cooldown():
    wo = await PlanGenerator.generate_single_workout({}, "Easy", 30, "Tuesday", 1, target_pace="5:00 /km")
    assert "prescription" in wo
    assert wo["duration_minutes"] == 38
    assert wo["distance_km"] == wo["prescription"]["run_km"]
    assert sum(s["duration_minutes"] for s in wo["segments"]) == 38
    assert [s["role"] for s in wo["segments"]] == ["warmup", "main", "cooldown"]


@pytest.mark.asyncio
async def test_recovery_retry_returns_corrected_segments_not_original_hard_strides():
    def row(zone):
        return {
            "week_number": 1,
            "day_of_week": "Tuesday",
            "type": "Recovery",
            "title": "Recovery Run",
            "phase": "Recovery",
            "segments": [
                {"kind": "run", "duration_minutes": 32, "pace_min_per_km": 6, "zone": zone, "setting": "flat_outdoor"}
            ],
        }

    workouts, attempts = await generate([row("Zone 5")], retry_payload=[row("Zone 2")])
    assert attempts == 2
    assert len(workouts) == 1
    assert workouts[0]["target_zone"] == "Zone 2"
    assert workouts[0]["duration_minutes"] == 32
    assert workouts[0]["distance_km"] == 5.3


@pytest.mark.asyncio
async def test_typed_weekly_load_rejects_overshoot_and_retries_without_scaling():
    def payload(minutes):
        return [
            {
                "week_number": 1,
                "day_of_week": "Tuesday",
                "type": "Easy",
                "phase": "Base",
                "title": "Easy Run",
                "segments": [
                    {
                        "kind": "run",
                        "duration_minutes": minutes,
                        "zone": "Zone 2",
                        "setting": "flat_outdoor",
                        "pace_min_per_km": 6,
                    }
                ],
            }
        ]

    workouts, attempts = await generate(payload(450), retry_payload=payload(360), check_starting_volume=True)
    assert attempts == 2
    assert workouts[0]["distance_km"] == 60
    assert workouts[0]["duration_minutes"] == 360


@pytest.mark.asyncio
async def test_fallback_race_distance_cannot_expand_the_weekly_time_budget():
    rows = await final_fallback(4)
    first_week = [w for w in rows if w["week_number"] == 1]
    # Typed 62 km uses the existing six-minutes-per-km time prior: 372 minutes.
    assert sum(w["prescription"]["aerobic_minutes"] for w in first_week) <= 372
    assert 49.6 <= sum(w["distance_km"] for w in first_week) <= 68.2
