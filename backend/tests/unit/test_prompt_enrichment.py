import datetime
from unittest.mock import MagicMock, patch

import pytest

from db import (
    get_block_actual_volume,
    get_recent_readiness_summary,
    get_user_activity_ceiling,
)
from services.plan_generator import PlanGenerator
from services.race_matcher import _to_matched_race


def test_get_user_activity_ceiling_with_data():
    mock_row = MagicMock()
    mock_row.max_distance_km = 42.195
    mock_row.max_duration_seconds = 14400  # 4 hours
    mock_row.max_elevation_gain_m = 1850.0
    mock_row.total_count = 25

    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = mock_row

        ceiling = get_user_activity_ceiling(user_id=10)

    assert ceiling["max_distance_km"] == 42.2
    assert ceiling["max_duration_hours"] == 4.0
    assert ceiling["max_elevation_gain_m"] == 1850.0
    assert ceiling["total_activities_count"] == 25


def test_get_user_activity_ceiling_empty():
    mock_row = MagicMock()
    mock_row.max_distance_km = 0
    mock_row.max_duration_seconds = 0
    mock_row.max_elevation_gain_m = 0
    mock_row.total_count = 0

    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = mock_row

        ceiling = get_user_activity_ceiling(user_id=99)

    assert ceiling["max_distance_km"] == 0.0
    assert ceiling["max_duration_hours"] == 0.0
    assert ceiling["max_elevation_gain_m"] == 0.0
    assert ceiling["total_activities_count"] == 0


def test_get_recent_readiness_summary_optimal():
    row1 = MagicMock(
        metric_date=datetime.date(2026, 3, 7),
        resting_hr=48,
        hrv_ms=65.0,
        hrv_status="Balanced",
        load_ratio=1.1,
        recovery_percent=85,
    )
    row2 = MagicMock(
        metric_date=datetime.date(2026, 3, 6),
        resting_hr=50,
        hrv_ms=60.0,
        hrv_status="Balanced",
        load_ratio=1.05,
        recovery_percent=80,
    )

    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [row1, row2]

        readiness = get_recent_readiness_summary(user_id=1, days=7)

    assert readiness["days_recorded"] == 2
    assert readiness["avg_hrv_ms"] == 62.5
    assert readiness["avg_resting_hr"] == 49.0
    assert readiness["avg_load_ratio"] == 1.08
    assert readiness["latest_load_ratio"] == 1.1
    # (85 + 80) / 2 = 82.5 -> rounds to 82 in Python 3
    assert readiness["avg_recovery_percent"] == 82
    assert readiness["readiness_flag"] == "optimal"


def test_get_recent_readiness_summary_overreaching_and_fatigued():
    # Overreaching: load_ratio > 1.4
    row_over = MagicMock(
        metric_date=datetime.date(2026, 3, 7),
        resting_hr=55,
        hrv_ms=45.0,
        hrv_status="Balanced",
        load_ratio=1.55,
        recovery_percent=60,
    )
    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [row_over]

        readiness = get_recent_readiness_summary(user_id=1, days=7)
    assert readiness["readiness_flag"] == "overreaching"

    # Fatigued: low recovery (< 45) or low HRV status
    row_fatigued = MagicMock(
        metric_date=datetime.date(2026, 3, 7),
        resting_hr=58,
        hrv_ms=30.0,
        hrv_status="Low",
        load_ratio=1.1,
        recovery_percent=35,
    )
    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [row_fatigued]

        readiness = get_recent_readiness_summary(user_id=1, days=7)
    assert readiness["readiness_flag"] == "fatigued"


def test_get_recent_readiness_summary_empty():
    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []

        readiness = get_recent_readiness_summary(user_id=1, days=7)
    assert readiness["days_recorded"] == 0
    assert readiness["readiness_flag"] == "insufficient_data"


def test_get_block_actual_volume():
    matched1 = MagicMock(
        id=101,
        distance_km=15.0,
        duration_seconds=5400,
        elevation_gain_m=450.0,
        start_time=datetime.datetime(2026, 2, 10, 6, 0),
        activity_type="Trail Run",
    )
    matched2 = MagicMock(
        id=102,
        distance_km=25.0,
        duration_seconds=10800,
        elevation_gain_m=900.0,
        start_time=datetime.datetime(2026, 2, 14, 7, 0),
        activity_type="Trail Run",
    )
    unplanned1 = MagicMock(
        id=103,
        distance_km=8.0,
        duration_seconds=2700,
        elevation_gain_m=100.0,
        start_time=datetime.datetime(2026, 2, 12, 18, 0),
        activity_type="Run",
    )

    with patch("db.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        # 1st call: matched rows, 2nd call: unplanned rows
        mock_conn.execute.return_value.fetchall.side_effect = [
            [matched1, matched2],
            [unplanned1],
        ]

        vol = get_block_actual_volume(user_id=1, plan_id=5, wk_start=1, wk_end=4, plan_start_date="2026-02-01")

    assert vol["matched_km"] == 40.0
    assert vol["matched_vert_m"] == 1350.0
    assert vol["matched_count"] == 2
    assert vol["unplanned_km"] == 8.0
    assert vol["unplanned_vert_m"] == 100.0
    assert vol["unplanned_count"] == 1
    assert vol["total_actual_km"] == 48.0
    assert vol["total_actual_vert_m"] == 1450.0
    assert vol["total_activities_count"] == 3


def test_race_matcher_to_matched_race_enrichment():
    chunk = {
        "payload": {
            "race_name": "Dalat Ultra Trail",
            "distances": [
                {
                    "label": "70km",
                    "distance_km": 70.0,
                    "elevation_gain_m": 3100.0,
                }
            ],
            "terrain": ["pine forest", "mud", "steep descent"],
            "climate": {
                "avg_temp_c": "18-24",
                "humidity_pct": "85%",
                "season": "Dry to early wet",
                "notes": "Expect misty conditions and slippery descents.",
            },
            "key_climbs": ["Langbiang Climb: 800m D+ over 5km (16% avg gradient)"],
            "results": [
                {
                    "distance_km": 70.0,
                    "distance_label": "70km",
                    "winner_time": "07:15:00",
                    "finishers": 450,
                    "percentiles": {"overall": {"p50": "12:30:00"}},
                }
            ],
        },
        "content": "Course overview: Scenic pine trails in Central Highlands.",
    }

    matched = _to_matched_race(chunk, score=95.0, resolved_distance_km=70.0)

    assert matched.race_name == "Dalat Ultra Trail"
    assert "Environmental & Climate Demands:" in matched.course_context
    assert "85%" in matched.course_context
    assert "Key Climbs & Checkpoints:" in matched.course_context
    assert "Langbiang Climb" in matched.course_context
    assert "Race Benchmarks & Historical Times:" in matched.course_context
    assert "Median finisher (p50): 12:30:00" in matched.course_context
    assert matched.course_intelligence["climate"]["humidity_pct"] == "85%"
    assert len(matched.course_intelligence["key_climbs"]) == 1


@pytest.mark.asyncio
async def test_plan_generator_prompt_includes_all_enriched_context():
    mock_resp = MagicMock()
    mock_resp.text = "invalid json to trigger fallback"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    user_profile = {
        "gender": "male",
        "height_cm": 178.0,
        "weight_kg": 68.5,
        "age": 32,
        "current_weekly_km": 45.0,
        "max_hr": 185,
        "resting_hr": 52,
        "aet_hr": 130,
        "ant_hr": 168,  # Gap = 38 bpm (>30) -> Triggers ADS!
        "has_gym_access": True,
        "use_treadmill": False,
        "training_environment": "mixed",
        "historical_ceiling": {
            "max_distance_km": 55.0,
            "max_duration_hours": 8.5,
            "max_elevation_gain_m": 2600,
            "total_activities_count": 42,
        },
        "athlete_notes": "Living in Hanoi on weekdays (flat roads), traveling to Sapa for mountain trails on weekends.",
    }

    race_info = {
        "name": "Vietnam Mountain Marathon",
        "date": "2026-09-20",
        "goal_type": "time",
        "target_time_hours": 12.0,
        "course_distance_km": 70.0,
        "course_elevation_gain_m": 3800.0,
        "course_context": "Deep mud, rocky mountain passes, 90% humidity.",
        "readiness_summary": {
            "days_recorded": 7,
            "avg_hrv_ms": 68.0,
            "latest_hrv_status": "Balanced",
            "avg_resting_hr": 47.0,
            "avg_load_ratio": 1.15,
            "latest_load_ratio": 1.15,
            "avg_recovery_percent": 82,
            "readiness_flag": "optimal",
        },
    }

    with (
        patch("google.genai.Client", return_value=mock_client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        await PlanGenerator.generate_plan_workouts(
            plan_id=1,
            user_profile=user_profile,
            race_info=race_info,
            total_weeks=12,
            api_key="fake-gemini-key",
            block_number=2,
            weeks_per_block=4,
        )

    assert mock_client.models.generate_content.called
    call_args = mock_client.models.generate_content.call_args
    prompt = call_args.kwargs.get("contents", "")

    # 1. Athlete Profile Biomarkers
    assert "Gender: Male" in prompt
    assert "Height: 178.0 cm" in prompt
    assert "Weight: 68.5 kg" in prompt

    # 2. Aerobic Deficiency Syndrome (ADS) Guardrail
    assert "AEROBIC DEFICIENCY SYNDROME (ADS) DETECTED" in prompt
    assert "spread exceeds 30 bpm / 80% threshold" in prompt
    assert "DO NOT prescribe Zone 4/5 speedwork" in prompt

    # 3. Course Steepness Ratio & Terrain Categorization (3800m / 70km = 54.3 m/km > 50)
    assert "Course Steepness Ratio: 54.3 m D+/km" in prompt
    assert "Extreme technical mountain vert / Skyrunning" in prompt

    # 4. Historical Ceiling
    assert "Athlete Historical Ceiling (from wearable activity records):" in prompt
    assert "Longest recorded run: 55.0 km (8.5 hrs)" in prompt
    assert "Max single-run elevation gain: 2600 m D+" in prompt

    # 5. Athlete Notes & Lifestyle Constraints
    assert "Athlete Notes & Special Routine Constraints:" in prompt
    assert "Living in Hanoi on weekdays" in prompt
    assert "Flat/Urban Weekdays vs Weekend Trails" in prompt

    # 6. 7-day Wearable Readiness
    assert "7-DAY WEARABLE BIOLOGICAL READINESS & LOAD RATIO:" in prompt
    assert "Rolling HRV: 68.0 ms" in prompt
    assert "ACWR (Acute:Chronic Load Ratio): 1.15 (Latest: 1.15)" in prompt
    assert "Biological Readiness Flag: OPTIMAL" in prompt

    # 7. Course Intelligence
    assert "COURSE INTELLIGENCE & ENVIRONMENTAL DEMANDS (Curated Race Profile):" in prompt
    assert "Deep mud, rocky mountain passes, 90% humidity." in prompt

    # 8. Science & Methodology Grounding Rules (Training for the Uphill Athlete)
    # Formerly asserted the literal "80/20 Low-Intensity Volume Polarization". That label
    # was hardcoded when every athlete received the same rules block; the split is now
    # tier-dependent (85/15 recreational, 90/10 sub-elite and above), so naming one ratio
    # in the heading would be wrong for most tiers. This athlete is recreational.
    assert "Intensity Distribution" in prompt
    assert "85% of total" in prompt
    assert "Long Run Proportionality Cap" in prompt
    assert "Periodization Phases (Training for the Uphill Athlete)" in prompt
    assert "Base Phase: Aerobic volume accumulation (Zone 1-2) + Maximum Strength" in prompt
    assert "Build Phase: Aerobic base expansion + Muscular Endurance" in prompt
    assert "Deload Adaptation Cycles" in prompt
    assert "Aerobic Deficiency Syndrome (ADS) Rule" in prompt
    assert "Uphill Athlete & Trail Specificity" in prompt
    assert "eccentric quad conditioning" in prompt
    assert "back-to-back weekend long runs" in prompt

    # 9. Fueling Guidelines
    assert "8-10g carbohydrates per kg bodyweight" in prompt
    assert "60-90g carbohydrates per hour" in prompt


@pytest.mark.asyncio
async def test_plan_generator_female_biomarkers_and_healthy_aerobic_base():
    mock_resp = MagicMock()
    mock_resp.text = "invalid json to trigger fallback"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    user_profile = {
        "gender": "female",
        "height_cm": 165.0,
        "weight_kg": 54.0,
        "age": 28,
        "current_weekly_km": 50.0,
        "max_hr": 190,
        "resting_hr": 50,
        "aet_hr": 148,
        "ant_hr": 168,  # Gap = 20 bpm (<=30, 88% of AnT) -> Healthy aerobic base
        "has_gym_access": True,
        "use_treadmill": True,
        "training_environment": "hilly",
    }

    race_info = {
        "name": "Moc Chau Trail 42K",
        "date": "2026-10-15",
        "goal_type": "finish",
        "course_distance_km": 42.0,
        "course_elevation_gain_m": 840.0,  # 840 / 42 = 20 m/km -> Rolling / runnable trail
    }

    with (
        patch("google.genai.Client", return_value=mock_client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        await PlanGenerator.generate_plan_workouts(
            plan_id=2,
            user_profile=user_profile,
            race_info=race_info,
            total_weeks=8,
            api_key="fake-gemini-key",
            block_number=1,
            weeks_per_block=2,
        )

    assert mock_client.models.generate_content.called
    prompt = mock_client.models.generate_content.call_args.kwargs.get("contents", "")

    # Female athlete physiology awareness
    assert "Gender: Female" in prompt
    assert "Height: 165.0 cm, Weight: 54.0 kg" in prompt
    assert "Female Athlete Physiology Considerations" in prompt
    assert "iron/ferritin status monitoring" in prompt

    # Healthy aerobic base (no ADS)
    assert "Aerobic Efficiency: Healthy AeT/AnT spread" in prompt
    assert "AEROBIC DEFICIENCY SYNDROME (ADS) DETECTED" not in prompt

    # Rolling / runnable trail categorization (< 25 m/km)
    assert "Course Steepness Ratio: 20.0 m D+/km — Rolling / Runnable trail" in prompt


@pytest.mark.asyncio
async def test_plan_generator_readiness_clean_formatting_when_none():
    mock_resp = MagicMock()
    mock_resp.text = "invalid json to trigger fallback"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    user_profile = {
        "age": 35,
        "current_weekly_km": 30.0,
    }

    # Partial readiness summary where some metrics are None
    race_info = {
        "name": "Generic Run",
        "date": "2026-11-01",
        "goal_type": "finish",
        "readiness_summary": {
            "days_recorded": 3,
            "avg_hrv_ms": None,
            "latest_hrv_status": "Balanced",
            "avg_resting_hr": None,
            "avg_load_ratio": None,
            "latest_load_ratio": None,
            "avg_recovery_percent": None,
            "readiness_flag": "optimal",
        },
    }

    with (
        patch("google.genai.Client", return_value=mock_client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        await PlanGenerator.generate_plan_workouts(
            plan_id=3,
            user_profile=user_profile,
            race_info=race_info,
            total_weeks=6,
            api_key="fake-gemini-key",
            block_number=1,
            weeks_per_block=2,
        )

    prompt = mock_client.models.generate_content.call_args.kwargs.get("contents", "")
    assert "7-DAY WEARABLE BIOLOGICAL READINESS & LOAD RATIO:" in prompt
    assert "None ms" not in prompt
    assert "None%" not in prompt
    assert "Rolling HRV: N/A" in prompt
    assert "ACWR (Acute:Chronic Load Ratio): N/A (Latest: N/A)" in prompt
