"""Complete requested calendars are validated before normalization, without padding."""

import pytest

from services.plan_checks import PrescriptionValidationError
from services.plan_output_schema import expected_calendar_days, validate_calendar_coverage, workout_response_schema


def rows(days):
    return [{"week_number": week, "day_of_week": day} for week, day in sorted(days)]


@pytest.mark.parametrize(
    "start,end,weekday,partial,count",
    [(1, 1, 0, True, 7), (1, 2, 0, True, 14), (1, 2, 3, True, 11), (3, 3, 3, False, 7), (2, 3, 3, False, 14)],
)
def test_calendar_extent_and_provider_minimum(start, end, weekday, partial, count):
    expected = expected_calendar_days(start, end, start_weekday=weekday, partial_first_week=partial)
    assert len(expected) == count
    for structured in (False, True):
        schema = workout_response_schema(structured=structured, minimum_workouts=len(expected))
        assert schema["minItems"] == count
        assert ("segments" in schema["items"]["properties"]) is structured
    validate_calendar_coverage(rows(expected), expected)


def test_doubles_do_not_replace_missing_days():
    expected = expected_calendar_days(1, 1, start_weekday=0, partial_first_week=True)
    complete = rows(expected)
    validate_calendar_coverage(complete + [complete[0]], expected)
    incomplete = [row for row in complete if row["day_of_week"] != "Sunday"] + [complete[0]]
    with pytest.raises(PrescriptionValidationError, match="Incomplete or unexpected calendar") as caught:
        validate_calendar_coverage(incomplete, expected)
    assert "Sunday" in caught.value.retry_instruction
    assert "Sunday" not in str(caught.value)
    assert incomplete[-1] == complete[0]


@pytest.mark.parametrize(
    "bad",
    [
        {"week_number": 3, "day_of_week": "Monday"},
        {"week_number": 1, "day_of_week": "Funday"},
        {"week_number": "1", "day_of_week": "Monday"},
    ],
)
def test_unexpected_days_rejected_before_week_clamping(bad):
    expected = expected_calendar_days(1, 1, start_weekday=0, partial_first_week=True)
    with pytest.raises(PrescriptionValidationError):
        validate_calendar_coverage(rows(expected) + [bad], expected)


def test_partial_first_week_rejects_days_before_start():
    expected = expected_calendar_days(1, 1, start_weekday=3, partial_first_week=True)
    assert expected == {(1, day) for day in ("Thursday", "Friday", "Saturday", "Sunday")}
    with pytest.raises(PrescriptionValidationError):
        validate_calendar_coverage(rows(expected) + [{"week_number": 1, "day_of_week": "Monday"}], expected)
