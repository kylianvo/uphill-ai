"""Hand-derived synthetic accounting expectations, no network/database."""

import pytest

from services import workout_prescription as wp


def run(minutes=12, pace=6, **extra):
    return {
        "kind": "run",
        "duration_minutes": minutes,
        "pace_min_per_km": pace,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        **extra,
    }


def test_mixed_me_counts_movement_once():
    result = wp.resolve_prescription(
        [run(), {"kind": "strength", "duration_minutes": 24, "zone": None, "setting": "indoor"}, run(6)], lang="en"
    )
    assert result["run_km"] == 3
    assert result["strength_minutes"] == 24
    assert result["aerobic_minutes"] == 18
    assert result["duration_minutes"] == 42


def test_pure_strength_never_inflates_running():
    result = wp.resolve_prescription(
        [{"kind": "strength", "duration_minutes": 27, "zone": None, "setting": "indoor"}], lang="vi"
    )
    assert result["run_km"] == 0
    assert result["aerobic_minutes"] == 0
    assert result["strength_minutes"] == 27


def test_hiking_and_passive_recovery_are_separate():
    result = wp.resolve_prescription(
        [
            run(6),
            {"kind": "hike", "duration_minutes": 30, "pace_min_per_km": 15, "zone": "Zone 2", "setting": "mountain"},
            {"kind": "recovery", "duration_minutes": 4, "zone": None, "setting": "unknown"},
        ],
        lang="en",
    )
    assert result["run_km"] == 1
    assert result["hike_km"] == 2
    assert result["aerobic_minutes"] == 36
    assert result["passive_minutes"] == 4
    assert result["duration_minutes"] == 40


@pytest.mark.parametrize("bad", [-2, float("nan"), float("inf"), "oops", True])
def test_invalid_durations_are_rejected(bad):
    with pytest.raises(ValueError):
        wp.resolve_prescription([run(bad)], lang="en")


@pytest.mark.parametrize(
    "segment",
    [
        run(pace=0),
        run(incline_pct=8),
        run(zone="Zone 7"),
        run(kind="strength"),
        run(setting="invented"),
        run(kind="invented"),
    ],
)
def test_contradictory_segments_are_rejected(segment):
    with pytest.raises(ValueError):
        wp.resolve_prescription([segment], lang="en")


def test_repeated_intervals_are_valid_but_duplicate_ids_are_not():
    assert wp.resolve_prescription([run(3), run(3)], lang="en")["run_km"] == 1
    with pytest.raises(ValueError):
        wp.resolve_prescription([run(id="a"), run(id="a")], lang="en")


def test_round_only_aggregate_totals():
    assert wp.resolve_prescription([run(1, 6)] * 3, lang="en")["run_km"] == 0.5


def test_treadmill_ascent_uses_belt_path_geometry_and_is_estimated():
    result = wp.resolve_prescription([run(30, 6, setting="treadmill", incline_pct=10)], lang="en")
    assert result["run_km"] == 5
    assert result["estimated_indoor_ascent_m"] == 498
    assert "estimated" in result["description"]


@pytest.mark.parametrize(
    "lang, expected",
    [
        ("en", "Warm-up: 12 minutes in Zone 1, pace 6:00/km."),
        ("vi", "Warm-up: 12 phút ở Zone 1, pace 6:00/km."),
    ],
)
def test_bilingual_warmup_preserves_quantities(lang, expected):
    result = wp.resolve_prescription([run(role="warmup")], lang=lang)
    assert result["description"] == expected
    assert wp.render_prescription(result, lang=lang) == expected


def test_rest_and_empty_prescriptions():
    with pytest.raises(ValueError):
        wp.resolve_prescription([], lang="en")
    result = wp.resolve_prescription(
        [{"kind": "rest", "duration_minutes": 0, "zone": None, "setting": "unknown"}], lang="vi"
    )
    assert result["duration_minutes"] == 0
    assert result["run_km"] == 0


def test_render_ranges_and_stop_condition_have_meaning_parity():
    segment = run(pace=[6, 7], role="cooldown", stop_if_power_drops=True)
    en = wp.resolve_prescription([segment], lang="en")
    vi = wp.resolve_prescription([segment], lang="vi")
    assert "6:00-7:00/km" in en["description"]
    assert "6:00-7:00/km" in vi["description"]
    assert "Stop if power drops." in en["description"]
    assert "Dừng nếu power giảm." in vi["description"]
    assert en["run_km"] == vi["run_km"] == 1.8


def test_strength_exercise_prescription_and_recovery_survive_rendering():
    result = wp.resolve_prescription(
        [
            {
                "kind": "strength",
                "duration_minutes": 18,
                "zone": None,
                "setting": "indoor",
                "exercise": {"name": "Bodyweight Squats", "sets": 3, "reps": 8, "rest_seconds": 75},
            }
        ],
        lang="vi",
    )
    assert "Bodyweight Squats: 3 x 8" in result["description"]
    assert "75 s" in result["description"]
    assert result["run_km"] == 0


def test_exercise_quantities_are_not_hidden_unvalidated_prose():
    with pytest.raises(ValueError):
        wp.resolve_prescription(
            [
                {
                    "kind": "strength",
                    "duration_minutes": 18,
                    "zone": None,
                    "setting": "indoor",
                    "exercise": {"name": "Squats", "sets": -1, "reps": 8, "rest_seconds": 75},
                }
            ],
            lang="en",
        )


def test_mountain_ascent_is_explicit_not_inferred_from_race():
    segment = run(setting="mountain", elevation_gain_m=240)
    workout = {"type": "Easy", "segments": [segment]}
    wp.apply_prescription(workout, lang="en")
    assert workout["elevation_gain_m"] == 240
    assert workout["grade_percent"] == 12


def test_flat_segments_cannot_claim_mountain_ascent():
    with pytest.raises(ValueError):
        wp.resolve_prescription([run(elevation_gain_m=120)], lang="en")


def test_vi_resolved_title_is_short_and_notes_do_not_enter_execution():
    workout = {
        "type": "Easy",
        "title": "Tái Nạp ATP",
        "rationale": "Bạn giữ sức cho buổi tiếp theo.",
        "segments": [
            {"kind": "run", "duration_minutes": 36, "pace_min_per_km": 6, "zone": "Zone 2", "setting": "flat_outdoor"}
        ],
    }
    from services.workout_prescription import apply_prescription

    apply_prescription(workout, lang="vi")
    assert workout["title"] == "Easy Run"
    assert workout["distance_km"] == 6
    assert workout["description"] == "Run: 36 phút ở Zone 2, pace 6:00/km. Reason: Bạn giữ sức cho buổi tiếp theo."


@pytest.mark.parametrize("lang", ["en", "vi"])
@pytest.mark.parametrize(
    "minutes, expected_carbs", [(74.9, "No Carbs"), (75, "30-60"), (150, "30-60"), (150.1, "60-90")]
)
def test_fueling_uses_resolved_duration_and_preserves_existing_band_boundaries(lang, minutes, expected_carbs):
    wo = {"type": "Easy", "segments": [run(minutes)], "fueling_tip": "Invented metabolic threshold claim"}
    wp.apply_prescription(wo, lang=lang)
    assert "metabolic" not in wo["fueling_tip"]
    if expected_carbs == "No Carbs":
        assert ("No Carbs" if lang == "en" else "Không cần Carbs") in wo["fueling_tip"]
    else:
        assert expected_carbs + " g Carbs" in wo["fueling_tip"]
    assert "Sodium" in wo["fueling_tip"]


def test_mixed_fueling_counts_strength_minutes_not_just_running():
    wo = {
        "type": "Easy",
        "segments": [run(55), {"kind": "strength", "duration_minutes": 25, "zone": None, "setting": "indoor"}],
    }
    wp.apply_prescription(wo, lang="vi")
    assert "80 phút" in wo["fueling_tip"]
    assert "30-60 g Carbs" in wo["fueling_tip"]


def test_race_fueling_is_preserved_for_the_existing_event_specific_policy():
    wo = {"type": "Race", "segments": [run(50)], "fueling_tip": "Existing event-specific instructions"}
    wp.apply_prescription(wo, lang="en")
    assert wo["fueling_tip"] == "Existing event-specific instructions"


def hold_segment(**changes):
    return {
        "kind": "strength",
        "duration_minutes": 3,
        "zone": None,
        "setting": "indoor",
        "exercise": {"name": "Front Plank", "sets": 2, "hold_seconds": 38.5, "rest_seconds": 47, **changes},
    }


@pytest.mark.parametrize(
    "lang, target",
    [("en", "2 x 38.5 s hold, 47 s rest between sets"), ("vi", "2 x 38.5 s giữ, 47 s nghỉ giữa các set")],
)
def test_hold_target_retains_explicit_seconds_and_rest_in_both_languages(lang, target):
    resolved = wp.resolve_prescription([hold_segment()], lang=lang)
    assert target in resolved["description"]
    assert resolved["duration_minutes"] == 3
    assert resolved["strength_minutes"] == 3
    assert resolved["run_km"] == 0


@pytest.mark.parametrize("name", ["Plank", "Side Plank", "Forearm Plank", "Wall Sit", "Hollow Body Hold"])
def test_recognised_static_holds_reject_rep_only_targets(name):
    segment = hold_segment(name=name, reps=1)
    del segment["exercise"]["hold_seconds"]
    with pytest.raises(ValueError, match="hold_seconds"):
        wp.resolve_prescription([segment], lang="en")


@pytest.mark.parametrize(
    "changes", [{"reps": 8}, {"hold_seconds": 0}, {"hold_seconds": -5}, {"hold_seconds": float("nan")}]
)
def test_hold_targets_reject_ambiguous_or_invalid_quantities(changes):
    with pytest.raises(ValueError):
        wp.resolve_prescription([hold_segment(**changes)], lang="en")


def test_holds_and_between_set_rests_must_fit_the_segment_time():
    segment = hold_segment(sets=3, hold_seconds=25, rest_seconds=20)
    segment["duration_minutes"] = 1
    with pytest.raises(ValueError, match="duration"):
        wp.resolve_prescription([segment], lang="en")


def test_dynamic_plank_shoulder_taps_keep_rep_targets():
    segment = hold_segment(name="Plank Shoulder Taps", reps=14)
    del segment["exercise"]["hold_seconds"]
    resolved = wp.resolve_prescription([segment], lang="en")
    assert "Plank Shoulder Taps: 2 x 14, 47 s rest" in resolved["description"]
