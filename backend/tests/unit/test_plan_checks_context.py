"""Resolved-output checks with explicit synthetic access and calendar context."""

from copy import deepcopy

from services import plan_checks
from services import workout_prescription as wp


def workout(minutes=60, zone="Zone 2", week=1, day="Tuesday", setting="flat_outdoor", phase="Base", **extra):
    wo = {
        "week_number": week,
        "day_of_week": day,
        "type": "Easy",
        "phase": phase,
        "segments": [
            {
                "kind": "run",
                "duration_minutes": minutes,
                "pace_min_per_km": 6,
                "zone": zone,
                "setting": setting,
                **extra,
            }
        ],
    }
    wp.apply_prescription(wo, lang="en")
    return wo


def check(workouts, **context):
    return plan_checks.run_context_checks(workouts, context=context)


def test_arithmetic_detects_mutated_public_totals():
    wo = workout()
    wo["distance_km"] = 12
    assert check([wo])["arithmetic"] is False


def test_access_obeys_day_permissions_not_titles():
    wo = workout(setting="mountain")
    wo["title"] = "Easy Run"
    assert check([wo], day_access={"Tuesday": {"settings": ["flat_outdoor", "indoor"]}})["access"] is False


def test_treadmill_requires_access_and_machine_capacity():
    wo = workout(setting="treadmill", incline_pct=12)
    assert check([wo], day_access={"Tuesday": {"settings": ["treadmill"], "max_incline_pct": 10}})["access"] is False
    assert check([wo], day_access={"Tuesday": {"settings": ["treadmill"], "max_incline_pct": 15}})["access"] is True


def test_unknown_machine_or_stairs_are_not_assumed_available():
    wo = workout(setting="treadmill", incline_pct=12)
    assert check([wo], day_access={"Tuesday": {"settings": ["treadmill"]}})["access"] is None
    strength = {
        "type": "Strength",
        "day_of_week": "Tuesday",
        "week_number": 1,
        "segments": [
            {
                "kind": "strength",
                "duration_minutes": 20,
                "zone": None,
                "setting": "indoor",
                "exercise": {"name": "Step-Ups", "sets": 3, "reps": 8, "rest_seconds": 75, "equipment": ["stairs"]},
            }
        ],
    }
    wp.apply_prescription(strength, lang="en")
    assert (
        check([strength], day_access={"Tuesday": {"settings": ["indoor"], "equipment": ["bodyweight"]}})["access"]
        is False
    )


def test_interval_label_does_not_hide_hard_minutes():
    wo = workout(30)
    wo["type"] = "Interval"
    wo["segments"].append(
        {"kind": "run", "duration_minutes": 70, "pace_min_per_km": 4, "zone": "Zone 4", "setting": "flat_outdoor"}
    )
    wp.apply_prescription(wo, lang="en")
    wo["target_zone"] = "Zone 2"
    assert check([wo])["intensity_accounting"] is False


def test_partial_week_skips_only_full_week_progression():
    result = check([workout(30), workout(90, week=2)], week_coverage={1: 2, 2: 7})
    assert result["progression"] is None
    assert result["arithmetic"] is True


def test_missing_intermediate_week_is_not_adjacent_progression():
    assert check([workout(30), workout(90, week=3)], week_coverage={1: 7, 3: 7})["progression"] is None


def test_full_week_unknown_logging_does_not_change_coverage():
    assert (
        check([workout(60), workout(90, week=2)], week_coverage={1: 7, 2: 7}, logging_state="unknown")["progression"]
        is False
    )


def test_down_week_rebound_uses_previous_healthy_comparable_week():
    workouts = [workout(100), workout(40, week=2, phase="Recovery"), workout(160, week=3)]
    assert check(workouts, week_coverage={1: 7, 2: 7, 3: 7})["progression"] is False


def test_legacy_precision_is_unavailable_not_a_pass():
    result = check([{"type": "Easy", "duration_minutes": 40, "distance_km": 6}])
    assert result["arithmetic"] is None
    assert result["intensity_accounting"] is None
    assert result["access"] is None


def test_invalid_fallback_cannot_bypass_context_validation():
    wo = deepcopy(workout())
    wo["segments"][0]["duration_minutes"] = -10
    assert check([wo])["arithmetic"] is False


def test_unknown_legacy_entry_does_not_hide_invalid_structured_neighbor():
    invalid = workout()
    invalid["distance_km"] = 500
    assert check([{"type": "Easy", "duration_minutes": 40}, invalid])["arithmetic"] is False


def test_treadmill_display_fields_must_match_segments():
    wo = workout(setting="treadmill", incline_pct=12)
    wo["treadmill_incline"] = "4-6"
    assert check([wo])["arithmetic"] is False


def test_legacy_negative_duration_is_rejected_even_without_segments():
    assert check([{"type": "Easy", "duration_minutes": -3, "distance_km": 0}])["arithmetic"] is False


def test_validation_rejects_invalid_fallback_before_storage():
    import pytest

    with pytest.raises(ValueError, match="arithmetic"):
        plan_checks.validate_generated_workouts([{"type": "Easy", "duration_minutes": -3}], context={})
