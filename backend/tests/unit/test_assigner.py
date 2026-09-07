"""Unit tests for one-to-one assignment -- pure functions, no DB."""

from datetime import UTC, datetime, timedelta

from services.matching.assigner import (
    AUTO_ACCEPT_THRESHOLD,
    SUGGEST_THRESHOLD,
    assign,
)
from services.matching.bundler import SessionBundle

BASE = datetime(2026, 9, 2, 6, 0, tzinfo=UTC)


def bundle(offset_h=0, duration_s=3600.0, km=10.0, hr=150, ids=(1,)):
    return SessionBundle(
        start_time=BASE + timedelta(hours=offset_h),
        duration_seconds=duration_s,
        distance_km=km,
        elevation_gain_m=100.0,
        avg_hr=hr,
        activity_ids=list(ids),
        activity_types={"outdoor_run"},
    )


def workout(id_, duration=60.0, km=10.0, hr="140-155"):
    return {
        "id": id_,
        "type": "EASY",
        "duration_minutes": duration,
        "distance_km": km,
        "elevation_gain_m": 100.0,
        "target_hr_range": hr,
        "target_pace": None,
        "interval_reps": None,
    }


class TestAssignment:
    def test_matches_the_single_obvious_pair(self):
        result = assign([bundle()], [workout(1)])
        assert len(result) == 1 and result[0].workout_id == 1

    def test_never_assigns_one_workout_to_two_bundles(self):
        result = assign([bundle(ids=(1,)), bundle(offset_h=8, ids=(2,))], [workout(1)])
        assigned = [a for a in result if a.workout_id is not None]
        assert len(assigned) == 1

    def test_never_assigns_two_workouts_to_one_bundle(self):
        result = assign([bundle()], [workout(1), workout(2)])
        assert len({a.workout_id for a in result if a.workout_id}) == 1

    def test_a_double_session_day_matches_both_pairs(self):
        morning = bundle(offset_h=0, duration_s=3600, km=10.0, ids=(1,))
        evening = bundle(offset_h=9, duration_s=1800, km=5.0, ids=(2,))
        result = assign([morning, evening], [workout(1, 60.0, 10.0), workout(2, 30.0, 5.0)])
        assert {a.workout_id for a in result} == {1, 2}

    def test_the_better_pairing_wins_when_two_are_possible(self):
        long_bundle = bundle(duration_s=5400, km=15.0, ids=(1,))
        short_bundle = bundle(offset_h=9, duration_s=1800, km=5.0, ids=(2,))
        result = assign([long_bundle, short_bundle], [workout(1, 90.0, 15.0), workout(2, 30.0, 5.0)])
        by_ids = {tuple(a.bundle.activity_ids): a.workout_id for a in result}
        assert by_ids[(1,)] == 1 and by_ids[(2,)] == 2

    def test_assignment_is_stable_across_input_order(self):
        a, b = bundle(ids=(1,)), bundle(offset_h=9, duration_s=1800, km=5.0, ids=(2,))
        forward = {
            tuple(x.bundle.activity_ids): x.workout_id for x in assign([a, b], [workout(1), workout(2, 30.0, 5.0)])
        }
        reverse = {
            tuple(x.bundle.activity_ids): x.workout_id for x in assign([b, a], [workout(2, 30.0, 5.0), workout(1)])
        }
        assert forward == reverse


class TestConfidenceBands:
    def test_a_strong_match_is_auto(self):
        assert assign([bundle()], [workout(1)])[0].confidence_band == "auto"

    def test_a_middling_match_is_suggested_not_auto(self):
        # 90 min / 14 km against a planned 60 min / 10 km scores ~0.67 -- clearly
        # between the bands. Deliberately not a near-threshold fixture: a test
        # sitting 0.008 from a boundary flips on any weight tweak.
        result = assign([bundle(duration_s=5400, km=14.0)], [workout(1)])
        assert result[0].confidence_band == "suggest"

    def test_a_poor_match_is_left_unmatched(self):
        result = assign([bundle(duration_s=400, km=0.8, hr=105)], [workout(1)])
        assert result[0].workout_id is None
        assert result[0].confidence_band == "unmatched"

    def test_thresholds_are_ordered_sensibly(self):
        assert 0.0 < SUGGEST_THRESHOLD < AUTO_ACCEPT_THRESHOLD <= 1.0

    def test_a_bundle_with_no_workouts_that_day_is_unmatched(self):
        result = assign([bundle()], [])
        assert len(result) == 1 and result[0].workout_id is None
