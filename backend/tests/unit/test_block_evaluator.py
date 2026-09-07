"""Unit tests for evaluate_block_performance."""

from unittest.mock import patch

from services.matching.block_evaluator import evaluate_block_performance


def test_evaluate_block_performance_with_matched_activities():
    fake_workouts = [
        {
            "id": 1,
            "week_number": 1,
            "day_of_week": "Monday",
            "type": "easy",
            "is_completed": 1,
            "distance_km": 10,
            "duration_minutes": 60,
        },
        {
            "id": 2,
            "week_number": 1,
            "day_of_week": "Wednesday",
            "type": "interval",
            "is_completed": 1,
            "distance_km": 8,
            "duration_minutes": 45,
        },
        {
            "id": 3,
            "week_number": 2,
            "day_of_week": "Saturday",
            "type": "long_run",
            "is_completed": 1,
            "distance_km": 16,
            "duration_minutes": 100,
        },
        {
            "id": 4,
            "week_number": 2,
            "day_of_week": "Sunday",
            "type": "easy",
            "is_completed": 0,
            "is_missed": 1,
            "distance_km": 6,
            "duration_minutes": 40,
        },
    ]
    fake_activities = [
        {
            "activity_id": 101,
            "workout_id": 1,
            "quality_score": 92.0,
            "quality_grade": "A",
            "quality_details": {"takeaways": ["Maintained Zone 2 HR discipline throughout"]},
        },
        {
            "activity_id": 102,
            "workout_id": 2,
            "quality_score": 88.0,
            "quality_grade": "B",
            "quality_details": {"takeaways": ["Target pace achieved on intervals"]},
        },
    ]

    with (
        patch("services.matching.block_evaluator.get_plan_workouts", return_value=fake_workouts),
        patch("services.matching.block_evaluator.get_activities_for_block", return_value=fake_activities),
        patch(
            "services.matching.block_evaluator.get_coach_notes",
            return_value=[{"note": "Keep up the great work on long runs"}],
        ),
        patch("services.matching.block_evaluator.get_block_reviews", return_value=[]),
    ):
        res = evaluate_block_performance(athlete_id=1, plan_id=10, block_number=1)

        assert res["block_number"] == 1
        assert res["week_start"] == 1
        assert res["week_end"] == 2
        assert res["sessions_total"] == 4
        assert res["sessions_completed"] == 3
        assert res["sessions_missed"] == 1
        assert res["completion_pct"] == 75
        assert res["avg_quality_score"] == 90.0
        assert res["quality_grade"] == "A"
        assert "Maintained Zone 2 HR discipline throughout" in res["coaching_takeaways"]
        assert "Target pace achieved on intervals" in res["coaching_takeaways"]
        assert "Keep up the great work on long runs" in res["coach_notes"]
        assert "Block 1" in res["coach_summary"]


def test_evaluate_block_performance_without_activities():
    fake_workouts = [
        {
            "id": 1,
            "week_number": 1,
            "day_of_week": "Monday",
            "type": "easy",
            "is_completed": 1,
            "distance_km": 10,
            "duration_minutes": 60,
        },
        {"id": 2, "week_number": 1, "day_of_week": "Wednesday", "type": "Rest"},
    ]

    with (
        patch("services.matching.block_evaluator.get_plan_workouts", return_value=fake_workouts),
        patch("services.matching.block_evaluator.get_activities_for_block", return_value=[]),
        patch("services.matching.block_evaluator.get_coach_notes", return_value=[]),
        patch("services.matching.block_evaluator.get_block_reviews", return_value=[]),
    ):
        res = evaluate_block_performance(athlete_id=1, plan_id=10, block_number=1)

        assert res["sessions_total"] == 1  # Rest excluded
        assert res["sessions_completed"] == 1
        assert res["completion_pct"] == 100
        assert res["avg_quality_score"] is None
        assert res["quality_grade"] is None
        assert "Strong consistency in Block 1" in res["coach_summary"]
