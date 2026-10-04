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
