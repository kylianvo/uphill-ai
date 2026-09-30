"""CoachWorkoutCreateRequest accepts an explicit, strictly-boolean is_priority."""

import pytest
from pydantic import ValidationError

from main import CoachWorkoutCreateRequest

BASE = dict(
    week_number=1,
    day_of_week="Monday",
    phase="Base",
    title="Easy",
    type="Easy",
    duration_minutes=45,
    target_zone="Z2",
)


def test_is_priority_defaults_to_none():
    assert CoachWorkoutCreateRequest(**BASE).dict()["is_priority"] is None


def test_is_priority_true_passes_through_dict():
    assert CoachWorkoutCreateRequest(**BASE, is_priority=True).dict()["is_priority"] is True


def test_is_priority_rejects_non_bool():
    with pytest.raises(ValidationError):
        CoachWorkoutCreateRequest(**BASE, is_priority="true")
