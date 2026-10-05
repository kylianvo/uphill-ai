"""Resolved-output checks with explicit synthetic access and calendar context."""

from copy import deepcopy

import pytest

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


def test_legacy_rest_does_not_hide_structured_access_failure():
    import pytest

    rows = [{"type": "Rest", "duration_minutes": 0}, workout(setting="mountain")]
    context = {"day_access": {"Tuesday": {"settings": ["flat_outdoor"]}}}
    assert check(rows, **context)["access"] is False
    with pytest.raises(ValueError, match="access"):
        plan_checks.validate_generated_workouts(rows, context=context)


def test_down_week_rebound_cannot_bridge_absent_observations():
    rows = [workout(100), workout(30, week=3, phase="Recovery"), workout(140, week=4)]
    assert check(rows, week_coverage={1: 7, 2: 7, 3: 7, 4: 7})["progression"] is None


def test_generation_rejects_unconfirmed_positive_treadmill_incline():
    import pytest

    wo = workout(setting="treadmill", incline_pct=15)
    context = {"day_access": {"Tuesday": {"settings": ["treadmill"]}}}
    assert check([wo], **context)["access"] is None
    with pytest.raises(ValueError, match="capability"):
        plan_checks.validate_generated_workouts([wo], context=context)


def test_recovery_rejects_brief_hard_strides_even_when_easy_share_passes():
    import pytest

    wo = workout(48, phase="Recovery")
    wo["segments"].append(
        {"kind": "run", "duration_minutes": 0.2, "pace_min_per_km": 4, "zone": "Zone 5", "setting": "flat_outdoor"}
    )
    wp.apply_prescription(wo, lang="en")
    assert check([wo])["intensity_accounting"] is True
    with pytest.raises(ValueError, match="recovery_intensity"):
        plan_checks.validate_generated_workouts([wo], context={})


def test_explicit_recovery_limit_applies_to_every_moving_segment():
    import pytest

    with pytest.raises(ValueError, match="recovery_intensity"):
        plan_checks.validate_generated_workouts([workout(zone="Zone 3")], context={"max_zone": 2})
    plan_checks.validate_generated_workouts([workout()], context={"max_zone": 2})


def test_resolved_volume_rejects_outside_budget_without_scaling():
    import pytest

    wo = workout(480)  # 480 / 6 = 80 km, independently calculated.
    context = {"weekly_km_bounds": {1: [56, 78]}, "week_coverage": {1: 7}}
    with pytest.raises(ValueError, match="volume_fit"):
        plan_checks.validate_generated_workouts([wo], context=context)
    assert wo["distance_km"] == 80
    plan_checks.validate_generated_workouts([workout(420)], context=context)


def test_healthy_volume_floor_does_not_apply_to_recovery_or_partial_week():
    context = {"weekly_km_bounds": {1: [56, 78]}, "week_coverage": {1: 7}}
    plan_checks.validate_generated_workouts([workout(60, phase="Recovery")], context=context)
    plan_checks.validate_generated_workouts([workout(60)], context={**context, "week_coverage": {1: 2}})


def test_power_requires_documented_preparation_not_tier_or_equipment():
    import pytest

    wo = workout(20)
    wo["training_method"] = "power"
    with pytest.raises(ValueError, match="strength_readiness"):
        plan_checks.validate_generated_workouts([wo], context={"athlete_tier": "elite", "has_gym_access": True})
    plan_checks.validate_generated_workouts([wo], context={"prepared_methods": ["power"]})


def test_advanced_exercise_cannot_hide_behind_generic_strength_label():
    import pytest

    wo = {
        "type": "Strength",
        "day_of_week": "Tuesday",
        "week_number": 1,
        "segments": [
            {
                "kind": "strength",
                "duration_minutes": 18,
                "setting": "indoor",
                "exercise": {"name": "Split Jump Squats", "sets": 4, "reps": 6, "rest_seconds": 90},
            }
        ],
    }
    wp.apply_prescription(wo, lang="en")
    with pytest.raises(ValueError, match="strength_readiness"):
        plan_checks.validate_generated_workouts([wo], context={})


def test_snapshot_budget_uses_first_full_week_and_existing_growth_cap():
    from types import SimpleNamespace

    rows = [workout(24), workout(420, week=2)]
    context = plan_checks.generation_context(
        {
            "plan_start_date": "2026-10-10",
            "fitness_snapshot": SimpleNamespace(weekly_km=70, readiness=None),
            "max_weekly_progression": 0.10,
        },
        rows,
    )
    assert context["weekly_km_bounds"] == {2: [56, 77]}


def test_recovery_feedback_suspends_healthy_budget_without_changing_snapshot():
    from types import SimpleNamespace

    snap = SimpleNamespace(weekly_km=70, readiness=None)
    context = plan_checks.generation_context(
        {
            "plan_start_date": "2026-10-05",
            "fitness_snapshot": snap,
            "training_feedback": {"overall_rpe": 9, "confirmed_missed_sessions": 0},
        },
        [workout()],
    )
    assert context["max_zone"] == 2
    assert "weekly_km_bounds" not in context
    assert snap.weekly_km == 70


def test_short_maximal_uphill_efforts_require_power_preparation_without_a_method_tag():
    wo = workout(minutes=0.2, zone="Zone 5", setting="mountain")
    wo["type"] = "Interval"
    assert check([wo])["strength_readiness"] is False
    assert check([wo], prepared_methods=["power"])["strength_readiness"] is True
    # Sustained aerobic climbing is a different stimulus.
    assert check([workout(minutes=30, setting="mountain")])["strength_readiness"] is None


def test_progression_counts_running_inside_strength_without_loosening_growth_limit():
    mixed = workout(minutes=40)
    mixed["type"] = "Strength"
    mixed["segments"].append(
        {
            "kind": "strength",
            "duration_minutes": 30,
            "zone": None,
            "setting": "indoor",
            "exercise": {"name": "Bodyweight Squats", "sets": 3, "reps": 10, "rest_seconds": 60},
        }
    )
    wp.apply_prescription(mixed, lang="en")
    week1 = workout(minutes=60)
    assert plan_checks.check_progression([mixed, week1, workout(minutes=115, week=2)]) is True
    assert plan_checks.check_progression([mixed, week1, workout(minutes=116, week=2)]) is False


def test_typed_starting_volume_uses_existing_floor_and_growth_cap():
    context = plan_checks.generation_context(
        {"plan_start_date": "2026-10-05", "current_weekly_km": 72, "max_weekly_progression": 0.10},
        [workout(), workout(week=2)],
    )
    assert context["weekly_km_bounds"] == {1: [57.6, 79.2], 2: [57.6, 79.2]}
    with pytest.raises(ValueError, match="volume_fit"):
        plan_checks.validate_generated_workouts([workout(minutes=486), workout(minutes=459, week=2)], context=context)
    assert (
        plan_checks.validate_generated_workouts([workout(minutes=459), workout(minutes=459, week=2)], context=context)[
            "volume_fit"
        ]
        is True
    )


def test_measured_snapshot_precedes_typed_volume_in_validation():
    from types import SimpleNamespace

    context = plan_checks.generation_context(
        {
            "plan_start_date": "2026-10-05",
            "current_weekly_km": 108,
            "fitness_snapshot": SimpleNamespace(weekly_km=72, readiness=None),
        },
        [workout()],
    )
    assert context["weekly_km_bounds"] == {1: [57.6, 79.2]}


@pytest.mark.parametrize("km", [None, 0])
def test_missing_or_zero_typed_volume_does_not_invent_a_healthy_budget(km):
    context = plan_checks.generation_context(
        {"plan_start_date": "2026-10-05", "current_weekly_km": km},
        [workout()],
    )
    assert "weekly_km_bounds" not in context


def test_recovery_feedback_suspends_typed_volume_floor():
    context = plan_checks.generation_context(
        {"plan_start_date": "2026-10-05", "current_weekly_km": 72, "training_feedback": {"overall_rpe": 8}},
        [workout()],
    )
    assert "weekly_km_bounds" not in context
    assert context["max_zone"] == 2


def test_typed_budget_skips_partial_first_week():
    context = plan_checks.generation_context(
        {"plan_start_date": "2026-10-10", "current_weekly_km": 72},
        [workout(), workout(week=2)],
    )
    assert context["weekly_km_bounds"] == {2: [57.6, 79.2]}


@pytest.mark.parametrize("goal", ["start_running", "return", "recovery"])
def test_goal_specific_progress_is_not_forced_to_healthy_distance_floor(goal):
    rows = [workout(60)]
    context = plan_checks.generation_context(
        {"current_weekly_km": 20, "goal_type": goal, "plan_start_date": "2026-10-05"}, rows
    )
    assert "weekly_km_bounds" not in context
    if goal in {"return", "recovery"}:
        assert context["max_zone"] == 2


def test_resolved_walk_run_tier_keeps_duration_progress_even_for_event_goal():
    rows = [workout(60)]
    context = plan_checks.generation_context(
        {"current_weekly_km": 2, "goal_type": "finish", "uses_walk_run": True, "plan_start_date": "2026-10-05"}, rows
    )
    assert "weekly_km_bounds" not in context
