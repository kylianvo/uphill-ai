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
        "exercise": {
            "name": "Bodyweight Squats",
            "sets": 3,
            "reps": 8,
            "rest_seconds": 75,
            "equipment": ["bodyweight"],
        },
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


async def generate(
    payload,
    lang="en",
    *,
    prepared_methods=None,
    retry_payload=None,
    check_starting_volume=False,
    total_weeks=8,
    target_week=None,
):
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
            total_weeks=total_weeks,
            target_week=target_week,
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


async def final_fallback(total_weeks, distance=80, ascent=4000, weekly_km=62):
    with (
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        rows, _ = await PlanGenerator.generate_plan_workouts(
            plan_id=0,
            user_profile={"current_weekly_km": weekly_km},
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


@pytest.mark.asyncio
@pytest.mark.parametrize("weekly_km", [15, 19, 100, 150, 200])
async def test_fallback_authors_load_using_resolved_paces(weekly_km):
    rows = await final_fallback(8, weekly_km=weekly_km)
    for week in [1, 2]:
        total = sum(w["distance_km"] for w in rows if w["week_number"] == week)
        assert weekly_km * 0.8 <= total <= weekly_km * 1.1


@pytest.mark.asyncio
async def test_event_taper_violation_retries_without_relabelling_the_workout():
    def row(phase):
        return {
            "week_number": 2,
            "day_of_week": "Tuesday",
            "phase": phase,
            "type": "Easy",
            "title": "Easy Run",
            "segments": [
                {
                    "kind": "run",
                    "duration_minutes": 32,
                    "zone": "Zone 2",
                    "setting": "flat_outdoor",
                    "pace_min_per_km": 6,
                }
            ],
        }

    rows, attempts = await generate([row("Build")], retry_payload=[row("Taper")], total_weeks=4, target_week=2)
    assert attempts == 2
    assert rows[0]["phase"] == "Taper"
    assert rows[0]["duration_minutes"] == 32


@pytest.mark.asyncio
async def test_single_filler_cannot_infer_stair_access_from_exercise_name():
    payload = {
        "title": "Strength",
        "segments": [
            {
                "kind": "strength",
                "duration_minutes": 10,
                "zone": None,
                "setting": "indoor",
                "exercise": {"name": "Step-Ups", "sets": 2, "reps": 6, "rest_seconds": 45, "equipment": ["stairs"]},
            }
        ],
    }
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(text=json.dumps(payload))
    with patch("google.genai.Client", return_value=client):
        with pytest.raises(ValueError, match="access"):
            await PlanGenerator.generate_single_workout({}, "Easy", 10, "Tuesday", 1, api_key="fake-key")
        trusted = {"validation_context": {"day_access": {"Tuesday": {"settings": ["indoor"], "equipment": ["stairs"]}}}}
        row = await PlanGenerator.generate_single_workout(trusted, "Easy", 10, "Tuesday", 1, api_key="fake-key")
        assert row["segments"][0]["exercise"]["name"] == "Step-Ups"
        assert row["duration_minutes"] == 10


@pytest.mark.asyncio
@pytest.mark.parametrize("goal", ["start_running", "return", "recovery"])
async def test_non_event_fallback_respects_goal_and_never_invents_race(goal):
    with (
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        rows, _ = await PlanGenerator.generate_plan_workouts(
            plan_id=0,
            user_profile={"current_weekly_km": 20},
            race_info={
                "goal_type": goal,
                "lang": "en",
                "plan_start_date": "2026-10-05",
                "training_environment": "flat",
            },
            total_weeks=8,
            weeks_per_block=8,
            api_key=None,
        )
    assert len(rows) == 56
    assert all(w["type"] != "Race" and w["phase"] not in {"Taper", "Race Week", "Peak"} for w in rows)
    assert all(s.get("zone") in {None, "Zone 1", "Zone 2"} for w in rows for s in w["segments"])
    if goal == "start_running":
        for week in range(1, 9):
            sessions = [w for w in rows if w["week_number"] == week and w["type"] != "Rest"]
            assert [w["day_of_week"] for w in sessions] == ["Tuesday", "Thursday", "Saturday"]
            assert all(
                w["duration_minutes"] == 20
                and any(s["kind"] == "hike" for s in w["segments"])
                and any(s["kind"] == "run" for s in w["segments"])
                for w in sessions
            )
    elif goal == "return":
        assert sum(w["distance_km"] for w in rows if w["week_number"] == 1) == pytest.approx(10, abs=0.2)
    else:
        assert all(w["type"] == "Rest" for w in rows if w["week_number"] <= 2)


@pytest.mark.asyncio
async def test_finish_goal_beginner_fallback_uses_resolved_walk_run_tier():
    with (
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        rows, tier = await PlanGenerator.generate_plan_workouts(
            plan_id=0,
            user_profile={"current_weekly_km": 2},
            race_info={
                "goal_type": "finish",
                "date": "2026-11-21",
                "lang": "en",
                "plan_start_date": "2026-10-05",
                "training_environment": "flat",
            },
            total_weeks=8,
            weeks_per_block=8,
            api_key=None,
        )
    assert tier == "beginner"
    assert len(rows) == 56
    for week in range(1, 9):
        sessions = [w for w in rows if w["week_number"] == week and w["type"] != "Rest"]
        assert [w["day_of_week"] for w in sessions] == ["Tuesday", "Thursday", "Saturday"]
        assert all(w["duration_minutes"] == 20 and w["phase"] == "Base" for w in sessions)
        assert all([s["kind"] for s in w["segments"]] == ["hike", "run"] * 10 for w in sessions)
        assert all(s["zone"] == "Zone 1" for w in sessions for s in w["segments"])
    assert not any(w["type"] == "Race" for w in rows)


@pytest.mark.asyncio
@pytest.mark.parametrize("goal", ["return", "recovery"])
async def test_beginner_fallback_preserves_named_goal_budget(goal):
    with (
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        rows, tier = await PlanGenerator.generate_plan_workouts(
            plan_id=0,
            user_profile={"current_weekly_km": 2},
            race_info={
                "goal_type": goal,
                "lang": "en",
                "plan_start_date": "2026-10-05",
                "training_environment": "flat",
            },
            total_weeks=4,
            weeks_per_block=4,
            api_key=None,
        )
    assert tier == "beginner"
    if goal == "return":
        assert sum(w["distance_km"] for w in rows if w["week_number"] == 1) == pytest.approx(1, abs=0.2)
    else:
        assert all(w["type"] == "Rest" for w in rows if w["week_number"] <= 2)
        assert [w["duration_minutes"] for w in rows if w["week_number"] == 3 and w["type"] != "Rest"] == [30] * 3
    assert all({s["kind"] for s in w["segments"]} == {"run", "hike"} for w in rows if w["type"] != "Rest")
