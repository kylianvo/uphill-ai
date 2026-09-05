"""Unit tests for bundle-vs-workout scoring -- pure functions, no DB."""

from datetime import UTC, datetime

import pytest

from services.matching.bundler import SessionBundle
from services.matching.scorer import parse_hr_range, parse_pace_to_seconds, score_bundle


def bundle(duration_s=3600.0, km=10.0, elev=100.0, hr=150):
    return SessionBundle(
        start_time=datetime(2026, 9, 2, 6, 0, tzinfo=UTC),
        duration_seconds=duration_s,
        distance_km=km,
        elevation_gain_m=elev,
        avg_hr=hr,
        activity_ids=[1],
        activity_types={"outdoor_run"},
    )


def workout(**overrides):
    base = {
        "id": 1,
        "type": "EASY",
        "duration_minutes": 60.0,
        "distance_km": 10.0,
        "elevation_gain_m": 100.0,
        "target_hr_range": "140-155",
        "target_pace": "6:00",
        "interval_reps": None,
    }
    base.update(overrides)
    return base


class TestParsers:
    def test_parses_a_heart_rate_range(self):
        assert parse_hr_range("140-155") == (140, 155)

    def test_returns_none_for_a_missing_heart_rate_range(self):
        assert parse_hr_range(None) is None

    def test_returns_none_for_an_unparseable_heart_rate_range(self):
        assert parse_hr_range("zone 2") is None

    def test_parses_a_single_pace(self):
        assert parse_pace_to_seconds("5:30") == 330.0

    def test_parses_a_pace_range_to_its_midpoint(self):
        assert parse_pace_to_seconds("5:30-6:30") == 360.0


class TestScoring:
    def test_a_perfect_match_scores_near_one(self):
        assert score_bundle(bundle(), workout()).total > 0.95

    def test_a_wildly_different_session_scores_low(self):
        assert score_bundle(bundle(duration_s=600, km=1.5, elev=0, hr=110), workout()).total < 0.4

    def test_the_gym_jog_fragment_alone_scores_worse_than_the_full_bundle(self):
        # This is the whole reason bundling exists.
        fragment = score_bundle(bundle(duration_s=212, km=0.57, elev=0, hr=120), workout())
        bundled = score_bundle(bundle(duration_s=3864, km=11.48, elev=100, hr=148), workout())
        assert bundled.total > fragment.total

    def test_missing_planned_distance_does_not_penalise_the_candidate(self):
        # A time-only workout must not always lose to a distance-specified one.
        time_only = score_bundle(bundle(), workout(distance_km=None, target_pace=None))
        assert time_only.total > 0.9

    def test_a_workout_with_no_scorable_fields_returns_zero_not_a_crash(self):
        empty = workout(
            duration_minutes=None, distance_km=None, elevation_gain_m=None, target_hr_range=None, target_pace=None
        )
        assert score_bundle(bundle(), empty).total == 0.0

    def test_heart_rate_inside_the_target_range_scores_full_marks(self):
        assert score_bundle(bundle(hr=150), workout())._component("hr") == pytest.approx(1.0)

    def test_heart_rate_far_outside_the_target_range_scores_poorly(self):
        assert score_bundle(bundle(hr=185), workout())._component("hr") < 0.5

    def test_missing_avg_hr_omits_the_component_rather_than_scoring_zero(self):
        scored = score_bundle(bundle(hr=None), workout())
        assert "hr" not in scored.components

    def test_reasons_explain_the_score_for_the_athlete(self):
        scored = score_bundle(bundle(duration_s=1800), workout())
        assert any("duration" in r.lower() for r in scored.reasons)


class TestFixRound1ElevationAndNegativeGuards:
    """Fix round 1: elevation_gain_m is REAL DEFAULT 0.0 (never NULL) in the
    workouts table, so a flat prescription (0.0) is indistinguishable from
    "unspecified" under the old falsy check -- and flat prescriptions (easy
    road runs, track intervals, treadmill sessions) are the common case, not
    an edge case. These tests pin the fixed behaviour: presence is `is None`,
    and a *given* 0.0 target is always scored (via absolute deviation, since
    _ratio_score's relative-error formula divides by target and cannot handle
    a zero target)."""

    def test_flat_prescription_matched_by_flat_actual_scores_full_marks_and_is_present(self):
        scored = score_bundle(bundle(elev=0.0), workout(elevation_gain_m=0.0))
        assert scored._component("elevation") == pytest.approx(1.0)
        assert "elevation" in scored.components

    def test_flat_prescription_with_800m_of_climbing_scores_zero_and_drags_the_total_down(self):
        # A bare `== 0.0` assertion on the component alone would still pass
        # under the OLD skip-the-component behaviour (component simply
        # absent). Comparing totals against the same bundle scored with the
        # elevation key absent is what actually proves the component is
        # being scored (and penalising), not silently dropped.
        with_elevation = score_bundle(bundle(elev=800.0), workout(elevation_gain_m=0.0))
        without_elevation = score_bundle(bundle(elev=800.0), workout(elevation_gain_m=None))
        assert with_elevation._component("elevation") == pytest.approx(0.0)
        assert with_elevation.total < without_elevation.total

    def test_flat_prescription_with_100m_of_climbing_scores_about_two_thirds(self):
        scored = score_bundle(bundle(elev=100.0), workout(elevation_gain_m=0.0))
        assert scored._component("elevation") == pytest.approx(1.0 - 100.0 / 300.0)

    def test_missing_or_none_elevation_key_excludes_the_component_and_renormalises(self):
        via_none = score_bundle(bundle(), workout(elevation_gain_m=None))
        assert "elevation" not in via_none.components

        workout_without_key = {k: v for k, v in workout().items() if k != "elevation_gain_m"}
        via_absent_key = score_bundle(bundle(), workout_without_key)
        assert "elevation" not in via_absent_key.components

    def test_negative_planned_duration_is_treated_as_absent_not_scored_as_zero(self):
        scored = score_bundle(bundle(), workout(duration_minutes=-5))
        assert "duration" not in scored.components
